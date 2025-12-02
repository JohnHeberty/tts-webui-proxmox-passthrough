"""
Construção do metadata.csv para F5-TTS

Este script gera o arquivo metadata.csv no formato esperado pelo F5-TTS:
    wavs/audio_0001.wav|texto em português aqui

Uso:
    python -m train.scripts.build_metadata_csv
"""
import json
import logging
import sys
from pathlib import Path

import yaml

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('train/logs/build_metadata.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Carrega configuração do dataset"""
    config_path = project_root / "train" / "config" / "dataset_config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    """Main function"""
    logger.info("=" * 80)
    logger.info("CONSTRUÇÃO DO METADATA.CSV")
    logger.info("=" * 80)
    
    # Load config
    config = load_config()
    
    # Paths
    data_dir = project_root / "train" / "data"
    processed_dir = data_dir / "processed"
    f5_dataset_dir = data_dir / "f5_dataset"
    wavs_dir = f5_dataset_dir / "wavs"
    
    # Criar diretórios
    wavs_dir.mkdir(parents=True, exist_ok=True)
    
    # Carregar transcrições
    transcriptions_file = processed_dir / "transcriptions.json"
    
    if not transcriptions_file.exists():
        logger.error(f"❌ Arquivo não encontrado: {transcriptions_file}")
        logger.error("   Execute primeiro: python -m train.scripts.transcribe_or_subtitles")
        sys.exit(1)
    
    with open(transcriptions_file, 'r', encoding='utf-8') as f:
        transcriptions = json.load(f)
    
    logger.info(f"📋 {len(transcriptions)} transcrições carregadas\n")
    
    # Copiar/mover WAVs para f5_dataset/wavs/
    import shutil
    
    logger.info("📁 Organizando arquivos WAV...")
    
    metadata_lines = []
    durations = []
    
    for i, item in enumerate(transcriptions):
        # Path original
        original_path = project_root / "train" / "data" / item['audio_path']
        
        # Novo nome (simplificado)
        new_filename = f"audio_{i+1:05d}.wav"
        new_path = wavs_dir / new_filename
        
        # Copiar arquivo
        if original_path.exists():
            shutil.copy2(original_path, new_path)
        else:
            logger.warning(f"⚠️  Arquivo não encontrado: {original_path}")
            continue
        
        # Formato: relative_path|text
        relative_path = f"wavs/{new_filename}"
        text = item['text']
        
        metadata_lines.append(f"{relative_path}|{text}")
        durations.append(item['duration'])
        
        if (i + 1) % 100 == 0:
            logger.info(f"   Processados {i + 1}/{len(transcriptions)}...")
    
    logger.info(f"   ✅ {len(metadata_lines)} arquivos organizados\n")
    
    # Salvar metadata.csv
    metadata_file = f5_dataset_dir / "metadata.csv"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(metadata_lines))
    
    logger.info(f"✅ metadata.csv salvo: {metadata_file}")
    logger.info(f"   {len(metadata_lines)} linhas")
    
    # Salvar duration.json
    duration_file = f5_dataset_dir / "duration.json"
    with open(duration_file, 'w', encoding='utf-8') as f:
        json.dump({'duration': durations}, f)
    
    logger.info(f"✅ duration.json salvo: {duration_file}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("RESUMO DO DATASET")
    logger.info("=" * 80)
    logger.info(f"📊 Total de amostras: {len(metadata_lines)}")
    logger.info(f"⏱️  Duração total: {sum(durations) / 3600:.2f}h")
    logger.info(f"⏱️  Duração média: {sum(durations) / len(durations):.2f}s")
    logger.info(f"📁 Dataset em: {f5_dataset_dir}")
    logger.info("=" * 80)
    logger.info("\n✅ Metadata.csv pronto!")
    logger.info("   Próximo passo: python -m train.scripts.prepare_f5_dataset")


if __name__ == "__main__":
    main()
