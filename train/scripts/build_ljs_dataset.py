"""
Construção do metadata.csv para XTTS-v2 (formato LJSpeech)

Este script gera o arquivo metadata.csv no formato esperado pelo XTTS-v2:
    wavs/audio_00001.wav|texto em português aqui

Uso:
    python -m train.scripts.build_ljs_dataset
"""

import json
import logging
from pathlib import Path
import random
import sys

import yaml


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("train/logs/build_metadata.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Carrega configuração do dataset"""
    config_path = project_root / "train" / "config" / "dataset_config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    """Main function"""
    logger.info("=" * 80)
    logger.info("CONSTRUÇÃO DO METADATA.CSV (XTTS-v2 / LJSpeech)")
    logger.info("=" * 80)

    # Load config
    config = load_config()

    # Paths (XTTS-v2: MyTTSDataset, não f5_dataset!)
    data_dir = project_root / "train" / "data"
    processed_dir = data_dir / "processed"
    dataset_dir = data_dir / "MyTTSDataset"
    wavs_dir = dataset_dir / "wavs"

    # Criar diretórios
    wavs_dir.mkdir(parents=True, exist_ok=True)

    # Carregar transcrições
    transcriptions_file = processed_dir / "transcriptions.json"

    if not transcriptions_file.exists():
        logger.error(f"❌ Arquivo não encontrado: {transcriptions_file}")
        logger.error("   Execute primeiro: python -m train.scripts.transcribe_audio")
        sys.exit(1)

    with open(transcriptions_file, encoding="utf-8") as f:
        transcriptions = json.load(f)

    logger.info(f"📋 {len(transcriptions)} transcrições carregadas\n")

    # Copiar/mover WAVs para MyTTSDataset/wavs/
    import shutil

    logger.info("📁 Organizando arquivos WAV...")

    metadata_lines = []
    durations = []
    filtered_count = 0

    for i, item in enumerate(transcriptions):
        # Aplicar filtros de qualidade (se habilitado)
        if config.get("quality_filters", {}).get("enabled", False):
            duration = item.get("duration", 0)
            text = item.get("text", "")
            word_count = len(text.split())
            
            min_duration = config["segmentation"]["min_duration"]
            max_duration = config["segmentation"]["max_duration"]
            min_words = config["quality_filters"].get("min_words", 3)
            max_words = config["quality_filters"].get("max_words", 50)
            
            # Filtrar por duração
            if not (min_duration <= duration <= max_duration):
                logger.debug(f"Filtrado por duração: {duration:.1f}s (esperado {min_duration}-{max_duration}s)")
                filtered_count += 1
                continue
            
            # Filtrar por palavras
            if not (min_words <= word_count <= max_words):
                logger.debug(f"Filtrado por palavras: {word_count} (esperado {min_words}-{max_words})")
                filtered_count += 1
                continue

        # Path original
        original_path = project_root / "train" / "data" / item["audio_path"]

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
        text = item["text"]

        metadata_lines.append(f"{relative_path}|{text}")
        durations.append(item["duration"])

        if (i + 1) % 100 == 0:
            logger.info(f"   Processados {i + 1}/{len(transcriptions)}...")

    logger.info(f"   ✅ {len(metadata_lines)} arquivos organizados")
    if filtered_count > 0:
        logger.info(f"   🗑️  {filtered_count} filtrados por qualidade\n")

    # Shuffle e split train/val
    if config["dataset"]["shuffle"]:
        random.seed(config["dataset"]["seed"])
        combined = list(zip(metadata_lines, durations))
        random.shuffle(combined)
        metadata_lines, durations = zip(*combined)
        metadata_lines = list(metadata_lines)
        durations = list(durations)

    split_idx = int(len(metadata_lines) * config["dataset"]["train_split"])
    train_lines = metadata_lines[:split_idx]
    val_lines = metadata_lines[split_idx:]
    train_durations = durations[:split_idx]
    val_durations = durations[split_idx:]

    # Salvar metadata.csv completo
    metadata_file = dataset_dir / "metadata.csv"
    with open(metadata_file, "w", encoding="utf-8") as f:
        f.write("\n".join(metadata_lines))

    logger.info(f"✅ metadata.csv salvo: {metadata_file}")
    logger.info(f"   {len(metadata_lines)} linhas")

    # Salvar splits
    metadata_train = dataset_dir / "metadata_train.csv"
    with open(metadata_train, "w", encoding="utf-8") as f:
        f.write("\n".join(train_lines))
    logger.info(f"✅ metadata_train.csv salvo: {len(train_lines)} amostras")

    metadata_val = dataset_dir / "metadata_val.csv"
    with open(metadata_val, "w", encoding="utf-8") as f:
        f.write("\n".join(val_lines))
    logger.info(f"✅ metadata_val.csv salvo: {len(val_lines)} amostras")

    # Salvar duration.json
    duration_file = dataset_dir / "duration.json"
    with open(duration_file, "w", encoding="utf-8") as f:
        json.dump({"duration": durations}, f)

    logger.info(f"✅ duration.json salvo: {duration_file}")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("RESUMO DO DATASET (XTTS-v2)")
    logger.info("=" * 80)
    logger.info(f"📊 Total de amostras: {len(metadata_lines)}")
    logger.info(f"   📈 Train: {len(train_lines)} ({len(train_lines)/len(metadata_lines)*100:.1f}%)")
    logger.info(f"   📉 Val: {len(val_lines)} ({len(val_lines)/len(metadata_lines)*100:.1f}%)")
    logger.info(f"⏱️  Duração total: {sum(durations) / 3600:.2f}h")
    logger.info(f"   Train: {sum(train_durations) / 3600:.2f}h")
    logger.info(f"   Val: {sum(val_durations) / 3600:.2f}h")
    logger.info(f"⏱️  Duração média: {sum(durations) / len(durations):.2f}s")
    logger.info(f"📁 Dataset em: {dataset_dir}")
    logger.info("=" * 80)
    logger.info("\n✅ Metadata.csv pronto para XTTS-v2!")
    logger.info("   Próximo passo: python -m train.scripts.train_xtts")


if __name__ == "__main__":
    main()
