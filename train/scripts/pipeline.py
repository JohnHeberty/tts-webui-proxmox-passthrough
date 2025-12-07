"""
Pipeline completo de preparação de dataset XTTS-v2

Este script orquestra todo o processo de preparação de dados:
  1. Download de áudios do YouTube (download_youtube.py)
  2. Segmentação com VAD (segment_audio.py)
  3. Transcrição com Whisper (transcribe_audio.py)
  4. Construção do dataset LJSpeech (build_ljs_dataset.py)

Uso:
    # Pipeline completo
    python -m train.scripts.pipeline_v2
    
    # Pular etapas (se já executou antes)
    python -m train.scripts.pipeline_v2 --skip-download
    python -m train.scripts.pipeline_v2 --skip-download --skip-segment
    
    # Executar apenas uma etapa
    python -m train.scripts.pipeline_v2 --only-step download
    python -m train.scripts.pipeline_v2 --only-step segment
    python -m train.scripts.pipeline_v2 --only-step transcribe
    python -m train.scripts.pipeline_v2 --only-step build

Diferenças da v1:
    - Usa imports diretos ao invés de subprocess (melhor prática Python)
    - Melhor tratamento de erros e stack traces
    - Reduz overhead de spawn de processos
    - Type hints para melhor IDE support

Dependências:
    - yt-dlp: pip install yt-dlp
    - whisper: pip install openai-whisper
    - num2words: pip install num2words
    - pyyaml: pip install pyyaml
    - numpy, soundfile, scipy (para processamento de áudio)
"""

import logging
from pathlib import Path
import sys
from typing import Callable, List, Tuple

import click
import yaml


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(project_root / "train" / "logs" / "pipeline_v2.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> dict:
    """Carrega configuração do dataset"""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_step(step_name: str, step_function: Callable[[], None]) -> bool:
    """
    Executa um step do pipeline usando import direto (boa prática Python)
    
    Args:
        step_name: Nome descritivo do step
        step_function: Função main() do script a executar
    
    Returns:
        True se sucesso, False se falhou
    """
    logger.info("=" * 80)
    logger.info(f"STEP: {step_name}")
    logger.info("=" * 80)
    
    try:
        # Executar função diretamente (evita subprocess overhead)
        step_function()
        logger.info(f"✅ {step_name} completado com sucesso!\n")
        return True
        
    except SystemExit as e:
        # Click usa sys.exit() para erros (código 0 = sucesso, >0 = erro)
        if e.code != 0:
            logger.error(f"❌ {step_name} falhou com código {e.code}")
            return False
        logger.info(f"✅ {step_name} completado com sucesso!\n")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao executar {step_name}: {e}")
        logger.exception(e)  # Log stack trace completo para debug
        return False


@click.command()
@click.option(
    "--config",
    type=click.Path(exists=True),
    default="train/config/dataset_config.yaml",
    help="Path para o arquivo de configuração",
)
@click.option("--skip-download", is_flag=True, help="Pular download (usar raw/ existente)")
@click.option("--skip-segment", is_flag=True, help="Pular segmentação")
@click.option("--skip-transcribe", is_flag=True, help="Pular transcrição")
@click.option("--skip-build", is_flag=True, help="Pular construção do dataset")
@click.option(
    "--only-step",
    type=click.Choice(["download", "segment", "transcribe", "build"]),
    help="Executar apenas um step específico",
)
def run_pipeline(config, skip_download, skip_segment, skip_transcribe, skip_build, only_step):
    """
    Executa pipeline completo de preparação de dataset XTTS-v2
    
    Pipeline:
      1. download_youtube.py   → train/data/raw/
      2. segment_audio.py      → train/data/processed/
      3. transcribe_audio.py   → train/data/processed/transcriptions.json
      4. build_ljs_dataset.py  → train/data/MyTTSDataset/metadata.csv
    """
    logger.info("\n")
    logger.info("╔" + "═" * 78 + "╗")
    logger.info("║" + " " * 20 + "XTTS-v2 DATASET PIPELINE V2" + " " * 31 + "║")
    logger.info("╚" + "═" * 78 + "╝")
    logger.info("\n")
    
    # Carregar config
    config_path = project_root / config
    cfg = load_config(config_path)
    logger.info(f"📝 Config carregada: {cfg['audio']['target_sample_rate']}Hz, "
                f"Duração: {cfg['segmentation']['min_duration']}-{cfg['segmentation']['max_duration']}s, "
                f"Whisper: {cfg['transcription']['whisper_model']}\n")
    
    # Import lazy (só quando necessário, evita carregar módulos pesados)
    steps: List[Tuple[str, Callable[[], None]]] = []
    
    if only_step:
        # Executar apenas um step
        if only_step == "download":
            from train.scripts.download_youtube import main as download_main
            steps = [("Download YouTube", download_main)]
        elif only_step == "segment":
            from train.scripts.segment_audio import main as segment_main
            steps = [("Segmentação VAD", segment_main)]
        elif only_step == "transcribe":
            from train.scripts.transcribe_audio import main as transcribe_main
            steps = [("Transcrição Whisper", transcribe_main)]
        elif only_step == "build":
            from train.scripts.build_ljs_dataset import main as build_main
            steps = [("Build LJSpeech Dataset", build_main)]
    else:
        # Pipeline completo (com skips)
        if not skip_download:
            from train.scripts.download_youtube import main as download_main
            steps.append(("Download YouTube", download_main))
        if not skip_segment:
            from train.scripts.segment_audio import main as segment_main
            steps.append(("Segmentação VAD", segment_main))
        if not skip_transcribe:
            from train.scripts.transcribe_audio import main as transcribe_main
            steps.append(("Transcrição Whisper", transcribe_main))
        if not skip_build:
            from train.scripts.build_ljs_dataset import main as build_main
            steps.append(("Build LJSpeech Dataset", build_main))
    
    if not steps:
        logger.warning("⚠️  Nenhum step selecionado para executar!")
        logger.info("   Use --help para ver opções disponíveis")
        return
    
    logger.info(f"📋 Steps a executar: {len(steps)}")
    for i, (name, _) in enumerate(steps, 1):
        logger.info(f"   {i}. {name}")
    logger.info("\n")
    
    # Executar pipeline
    success_count = 0
    failed_count = 0
    
    for i, (step_name, step_func) in enumerate(steps, 1):
        logger.info(f"\n[{i}/{len(steps)}] Iniciando: {step_name}...\n")
        
        success = run_step(step_name, step_func)
        
        if success:
            success_count += 1
        else:
            failed_count += 1
            logger.error(f"❌ Pipeline interrompido no step: {step_name}")
            break
    
    # Summary final
    logger.info("\n")
    logger.info("╔" + "═" * 78 + "╗")
    logger.info("║" + " " * 30 + "RESUMO FINAL" + " " * 36 + "║")
    logger.info("╚" + "═" * 78 + "╝")
    logger.info(f"✅ Steps completados: {success_count}/{len(steps)}")
    if failed_count > 0:
        logger.info(f"❌ Steps falhados: {failed_count}")
    logger.info("=" * 80)
    
    if failed_count == 0:
        logger.info("\n🎉 Pipeline completado com sucesso!")
        logger.info("   Dataset pronto em: train/data/MyTTSDataset/")
        logger.info("   Próximo passo: python -m train.scripts.train_xtts")
    else:
        logger.error("\n❌ Pipeline falhou. Verifique os logs acima.")
        sys.exit(1)


if __name__ == "__main__":
    run_pipeline()
