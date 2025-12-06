"""
Carrega configurações do arquivo .env
"""

from pathlib import Path
from typing import Any


def str_to_bool(value: str) -> bool:
    """Converte string para bool"""
    return value.lower() in ("true", "1", "yes", "on")


def load_env(env_file: Path = None) -> dict[str, Any]:
    """
    Carrega variáveis do arquivo .env

    Args:
        env_file: Path do arquivo .env (default: train/.env)

    Returns:
        Dict com configurações
    """
    if env_file is None:
        env_file = Path(__file__).parent.parent / ".env"

    if not env_file.exists():
        # Usar .env.example como fallback
        env_file = Path(__file__).parent.parent / ".env.example"
        if not env_file.exists():
            return {}

    config = {}

    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # Ignorar comentários e linhas vazias
            if not line or line.startswith("#"):
                continue

            # Parse KEY=VALUE
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Remover aspas se houver
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]

                # Converter tipos
                if value.lower() in ("true", "false", "yes", "no", "on", "off"):
                    value = str_to_bool(value)
                elif value.isdigit():
                    value = int(value)
                elif value.replace(".", "", 1).isdigit():
                    value = float(value)

                config[key] = value

    return config


def get_training_config() -> dict[str, Any]:
    """
    Retorna configuração de treinamento do .env
    """
    env = load_env()

    return {
        "epochs": env.get("EPOCHS", 1000),
        "batch_size": env.get("BATCH_SIZE", 4),
        "batch_size_type": env.get("BATCH_SIZE_TYPE", "frame"),
        "learning_rate": env.get("LEARNING_RATE", 0.0001),
        "grad_accumulation_steps": env.get("GRAD_ACCUMULATION_STEPS", 4),
        "max_grad_norm": env.get("MAX_GRAD_NORM", 1.0),
        "early_stop_patience": env.get("EARLY_STOP_PATIENCE", 5),
        "early_stop_min_delta": env.get("EARLY_STOP_MIN_DELTA", 0.001),
        "save_per_updates": env.get("SAVE_PER_UPDATES", 500),
        "last_per_updates": env.get("LAST_PER_UPDATES", 50),
        "keep_last_n_checkpoints": env.get("KEEP_LAST_N_CHECKPOINTS", 10),
        "log_samples_per_updates": env.get("LOG_SAMPLES_PER_UPDATES", 250),
        "warmup_steps": env.get("NUM_WARMUP_UPDATES", 200),
        "train_dataset_name": env.get("DATASET_NAME", "ptbr_youtube_custom"),
        "dataset_path": env.get("DATASET_PATH", "train/data/f5_dataset"),
        "pretrained_model_path": env.get("PRETRAIN_MODEL_PATH"),
        "base_model": env.get("BASE_MODEL", "firstpixel/F5-TTS-pt-br"),
        "auto_download_pretrained": env.get("AUTO_DOWNLOAD_PRETRAINED", False),
        "output_dir": env.get("OUTPUT_DIR", "train/output/ptbr_finetuned"),
        "tensorboard_dir": env.get("TENSORBOARD_DIR", "train/runs"),
        "tensorboard_port": env.get("TENSORBOARD_PORT", 6006),
        "log_dir": env.get("LOG_DIR", "train/logs"),
        "device": env.get("DEVICE", "cuda"),
        "num_workers": env.get("NUM_WORKERS", 4),
        "dataloader_workers": env.get("DATALOADER_WORKERS", 8),  # Workers para DataLoader
        "mixed_precision": env.get("MIXED_PRECISION", "fp16"),
        "max_samples": env.get("MAX_SAMPLES", 32),
        "logger": env.get("LOGGER", "tensorboard"),
        "log_samples": env.get("LOG_SAMPLES", True),
        "log_samples_per_epochs": env.get("LOG_SAMPLES_PER_EPOCHS", 1),
        "seed": env.get("SEED", 666),
        # Novas configurações
        "exp_name": env.get("EXP_NAME", "F5TTS_Base"),
        "model_filename": env.get("MODEL_FILENAME", "pt-br/model_200000.pt"),
        "f5tts_base_dir": env.get("F5TTS_BASE_DIR", "/root/.local/lib/python3.11"),
        "f5tts_ckpts_dir": env.get("F5TTS_CKPTS_DIR", "/root/.local/lib/python3.11/ckpts"),
        "local_pretrained_path": env.get(
            "LOCAL_PRETRAINED_PATH", "models/f5tts/pt-br/model_last.pt"
        ),
        # Data preparation
        "raw_data_dir": env.get("RAW_DATA_DIR", "train/data/raw"),
        "processed_data_dir": env.get("PROCESSED_DATA_DIR", "train/data/processed"),
        "videos_csv": env.get("VIDEOS_CSV", "train/data/videos.csv"),
        "config_dir": env.get("CONFIG_DIR", "train/config"),
    }


if __name__ == "__main__":
    # Testar carregamento
    config = get_training_config()
    print("Configurações carregadas do .env:")
    for key, value in config.items():
        print(f"  {key}: {value}")
