"""
Preparação do dataset para F5-TTS (formato Arrow)

Este script converte metadata.csv + wavs/ no formato Arrow esperado pelo F5-TTS.
Baseado nos scripts prepare_csv_wavs.py e prepare_emilia.py do F5-TTS oficial.

Uso:
    python -m train.scripts.prepare_f5_dataset
"""

import json
import logging
from pathlib import Path
import sys

import yaml


# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Carregar config do .env
from train.utils.env_loader import get_training_config


env_config = get_training_config()

try:
    from datasets.arrow_writer import ArrowWriter
    import soundfile as sf
except ImportError as e:
    print(f"❌ Dependência não encontrada: {e}")
    print("Instale com: pip install datasets soundfile")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("train/logs/prepare_f5_dataset.log"), logging.StreamHandler()],
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
    logger.info("PREPARAÇÃO DO DATASET F5-TTS (ARROW FORMAT)")
    logger.info("=" * 80)

    # Load config
    config = load_config()

    # Paths (usar .env quando possível)
    data_base = env_config.get("dataset_path", "train/data/f5_dataset").rsplit("/", 1)[0]
    data_dir = project_root / data_base
    dataset_name = env_config.get("train_dataset_name", "f5_dataset")
    f5_dataset_dir = data_dir / dataset_name
    metadata_file = f5_dataset_dir / "metadata.csv"

    if not metadata_file.exists():
        logger.error(f"❌ Arquivo não encontrado: {metadata_file}")
        logger.error("   Execute primeiro: python -m train.scripts.build_metadata_csv")
        sys.exit(1)

    # Ler metadata.csv
    logger.info("📄 Lendo metadata.csv...")

    with open(metadata_file, encoding="utf-8") as f:
        lines = f.readlines()

    logger.info(f"   {len(lines)} linhas encontradas\n")

    # Processar cada linha
    result = []
    duration_list = []
    text_vocab_set = set()
    skipped = 0

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        parts = line.split("|")
        if len(parts) != 2:
            logger.warning(f"⚠️  Linha malformada ignorada: {line[:50]}...")
            skipped += 1
            continue

        audio_path_rel, text = parts

        # Path absoluto
        audio_path = f5_dataset_dir / audio_path_rel

        if not audio_path.exists():
            logger.warning(f"⚠️  Arquivo não encontrado: {audio_path_rel}")
            skipped += 1
            continue

        # Obter duração
        try:
            info = sf.info(audio_path)
            duration = info.duration
        except Exception as e:
            logger.warning(f"⚠️  Erro ao ler {audio_path_rel}: {e}")
            skipped += 1
            continue

        # Filtrar por duração
        seg_config = config["segmentation"]
        if duration < seg_config["min_duration"] or duration > seg_config["max_duration"]:
            logger.warning(f"⚠️  Duração fora do range ({duration:.2f}s): {audio_path_rel}")
            skipped += 1
            continue

        # Adicionar ao resultado
        result.append({"audio_path": str(audio_path), "text": text, "duration": duration})

        duration_list.append(duration)
        text_vocab_set.update(list(text))

        if (i + 1) % 100 == 0:
            logger.info(f"   Processados {i + 1}/{len(lines)}...")

    logger.info(f"\n✅ {len(result)} amostras válidas ({skipped} ignoradas)\n")

    # Salvar em formato Arrow
    logger.info("💾 Salvando dataset em formato Arrow...")

    raw_arrow_path = f5_dataset_dir / "raw.arrow"

    with ArrowWriter(path=str(raw_arrow_path)) as writer:
        for item in result:
            writer.write(item)
        writer.finalize()

    logger.info(f"✅ raw.arrow salvo: {raw_arrow_path}\n")

    # Atualizar duration.json
    logger.info("💾 Atualizando duration.json...")

    duration_file = f5_dataset_dir / "duration.json"
    with open(duration_file, "w", encoding="utf-8") as f:
        json.dump({"duration": duration_list}, f)

    logger.info(f"✅ duration.json atualizado: {duration_file}\n")

    # Copiar vocab.txt do modelo base pt-br
    logger.info("📝 Configurando vocab.txt...")

    vocab_file = f5_dataset_dir / "vocab.txt"

    # Tentar copiar do modelo base
    base_vocab_paths = [
        project_root / "models" / "f5tts" / "pt-br" / "vocab.txt",
        Path.home()
        / ".cache"
        / "huggingface"
        / "hub"
        / "models--firstpixel--F5-TTS-pt-br"
        / "snapshots"
        / "vocab.txt",
    ]

    vocab_copied = False
    for base_vocab_path in base_vocab_paths:
        if base_vocab_path.exists():
            import shutil

            shutil.copy2(base_vocab_path, vocab_file)
            logger.info(f"✅ vocab.txt copiado de: {base_vocab_path}")
            vocab_copied = True
            break

    if not vocab_copied:
        logger.warning("⚠️  vocab.txt do modelo base não encontrado!")
        logger.warning("   Gerando vocab.txt a partir do dataset...")

        with open(vocab_file, "w", encoding="utf-8") as f:
            for char in sorted(text_vocab_set):
                f.write(char + "\n")

        logger.info(f"✅ vocab.txt gerado com {len(text_vocab_set)} caracteres")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("DATASET F5-TTS PRONTO!")
    logger.info("=" * 80)
    logger.info(f"📊 Total de amostras: {len(result)}")
    logger.info(f"⏱️  Duração total: {sum(duration_list) / 3600:.2f}h")
    logger.info(f"⏱️  Duração média: {sum(duration_list) / len(duration_list):.2f}s")
    logger.info(f"📝 Vocab size: {len(text_vocab_set)} caracteres")
    logger.info(f"📁 Dataset salvo em: {f5_dataset_dir}")
    logger.info("   - raw.arrow")
    logger.info("   - duration.json")
    logger.info("   - vocab.txt")
    logger.info("   - wavs/")
    logger.info("=" * 80)
    logger.info("\n✅ Dataset preparado!")
    logger.info("   Próximo passo: python -m train.run_training")


if __name__ == "__main__":
    main()
