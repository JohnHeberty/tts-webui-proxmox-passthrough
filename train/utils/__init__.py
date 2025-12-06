"""
Utilidades compartilhadas para pipeline de treinamento
"""

import logging
from pathlib import Path
from typing import Optional

import torch


def setup_logger(name: str, log_file: str | None = None, level=logging.INFO):
    """
    Configura logger com handlers para arquivo e console

    Args:
        name: Nome do logger
        log_file: Path do arquivo de log (opcional)
        level: Nível de logging

    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_device(device_str: str = "auto") -> torch.device:
    """
    Determina o device PyTorch (cuda/cpu)

    Args:
        device_str: 'auto', 'cuda', ou 'cpu'

    Returns:
        torch.device
    """
    if device_str == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(device_str)

    return device


def format_duration(seconds: float) -> str:
    """
    Formata duração em segundos para string legível

    Args:
        seconds: Duração em segundos

    Returns:
        String formatada (ex: "2h 15m 30s")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def count_parameters(model) -> int:
    """
    Conta parâmetros treináveis de um modelo

    Args:
        model: Modelo PyTorch

    Returns:
        Número de parâmetros
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def check_disk_space(path: Path, required_gb: float = 1.0) -> bool:
    """
    Verifica se há espaço em disco suficiente

    Args:
        path: Path para verificar
        required_gb: GB necessários

    Returns:
        True se há espaço, False caso contrário
    """
    import shutil

    stat = shutil.disk_usage(path)
    available_gb = stat.free / (1024**3)

    return available_gb >= required_gb


def validate_youtube_url(url: str) -> bool:
    """
    Valida se URL é do YouTube

    Args:
        url: URL para validar

    Returns:
        True se válido, False caso contrário
    """
    import re

    youtube_regex = r"(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/"
    return bool(re.match(youtube_regex, url))
