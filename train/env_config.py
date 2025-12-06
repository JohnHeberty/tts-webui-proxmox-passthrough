"""
Environment configuration loader for train/ project

Loads configuration from .env file and provides defaults.
"""

import os
from pathlib import Path
from typing import Optional


# Project root
TRAIN_ROOT = Path(__file__).parent

# Try to load .env file if exists
env_file = TRAIN_ROOT / ".env"
if env_file.exists():
    # Simple .env parser (no dependencies)
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()


def get_env_int(key: str, default: int) -> int:
    """Get environment variable as integer"""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_env_float(key: str, default: float) -> float:
    """Get environment variable as float"""
    value = os.environ.get(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def get_env_bool(key: str, default: bool) -> bool:
    """Get environment variable as boolean"""
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def get_env_str(key: str, default: str) -> str:
    """Get environment variable as string"""
    return os.environ.get(key, default)


def auto_detect_whisper_workers() -> int:
    """
    Auto-detect optimal number of Whisper workers based on available VRAM
    
    Returns:
        Number of workers (1-8)
    """
    try:
        import torch
        if not torch.cuda.is_available():
            return 1
        
        # Get free VRAM in MB
        free_vram_mb = torch.cuda.mem_get_info()[0] / 1024 / 1024
        
        # Conservative estimates (Whisper memory usage)
        # base: ~2GB, small: ~3GB, medium: ~5GB, large: ~10GB
        whisper_model = get_env_str("WHISPER_MODEL", "base")
        
        memory_per_worker = {
            "tiny": 1000,   # 1GB
            "base": 2000,   # 2GB
            "small": 3000,  # 3GB
            "medium": 5000, # 5GB
            "large": 10000, # 10GB
        }.get(whisper_model, 2000)
        
        # Reserve minimum free VRAM
        min_free = get_env_int("WHISPER_MIN_FREE_VRAM_MB", 2048)
        usable_vram = free_vram_mb - min_free
        
        if usable_vram <= 0:
            return 1
        
        # Calculate max workers
        max_workers = int(usable_vram / memory_per_worker)
        
        # Clamp between 1 and 8
        return max(1, min(max_workers, 8))
        
    except Exception:
        return 1  # Fallback to single worker


# Transcrição - Paralelização
WHISPER_NUM_WORKERS = get_env_int("WHISPER_NUM_WORKERS", 0) or auto_detect_whisper_workers()
WHISPER_MIN_FREE_VRAM_MB = get_env_int("WHISPER_MIN_FREE_VRAM_MB", 2048)
WHISPER_BATCH_SIZE = get_env_int("WHISPER_BATCH_SIZE", 1)
WHISPER_DEVICE = get_env_str("WHISPER_DEVICE", "cuda")
WHISPER_MODEL = get_env_str("WHISPER_MODEL", "base")

# Audio Processing
VAD_NUM_WORKERS = get_env_int("VAD_NUM_WORKERS", 4)

# Training
TRAIN_BATCH_SIZE = get_env_int("TRAIN_BATCH_SIZE", 4)
TRAIN_GRADIENT_ACCUMULATION = get_env_int("TRAIN_GRADIENT_ACCUMULATION", 2)
TRAIN_MIXED_PRECISION = get_env_str("TRAIN_MIXED_PRECISION", "fp16")

# Logging
LOG_LEVEL = get_env_str("LOG_LEVEL", "INFO")
LOG_TO_FILE = get_env_bool("LOG_TO_FILE", True)

# Paths
DATA_DIR = TRAIN_ROOT / get_env_str("DATA_DIR", "data")
OUTPUT_DIR = TRAIN_ROOT / get_env_str("OUTPUT_DIR", "output")
LOGS_DIR = TRAIN_ROOT / get_env_str("LOGS_DIR", "logs")
MODELS_DIR = TRAIN_ROOT / get_env_str("MODELS_DIR", "models")


# Debug info
if __name__ == "__main__":
    print("🔧 Train Environment Configuration")
    print("=" * 60)
    print(f"WHISPER_NUM_WORKERS: {WHISPER_NUM_WORKERS}")
    print(f"WHISPER_MIN_FREE_VRAM_MB: {WHISPER_MIN_FREE_VRAM_MB}")
    print(f"WHISPER_BATCH_SIZE: {WHISPER_BATCH_SIZE}")
    print(f"WHISPER_DEVICE: {WHISPER_DEVICE}")
    print(f"WHISPER_MODEL: {WHISPER_MODEL}")
    print(f"VAD_NUM_WORKERS: {VAD_NUM_WORKERS}")
    print(f"TRAIN_BATCH_SIZE: {TRAIN_BATCH_SIZE}")
    print(f"LOG_LEVEL: {LOG_LEVEL}")
    print("=" * 60)
    
    # Show auto-detected workers
    print(f"\n💡 Auto-detected Whisper workers: {auto_detect_whisper_workers()}")
    
    # Show VRAM info
    try:
        import torch
        if torch.cuda.is_available():
            free, total = torch.cuda.mem_get_info()
            print(f"🎮 GPU VRAM: {free/1024/1024:.0f}MB free / {total/1024/1024:.0f}MB total")
    except:
        pass
