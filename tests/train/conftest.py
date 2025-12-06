"""
Test configuration for training tests

Fixtures and utilities used across all training tests.
"""
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_audio_path(temp_dir):
    """Create sample audio file for testing."""
    import numpy as np
    import soundfile as sf

    audio_path = temp_dir / "sample.wav"
    sample_rate = 24000
    duration = 3.0  # 3 seconds
    samples = int(sample_rate * duration)

    # Generate sine wave
    frequency = 440  # A4
    t = np.linspace(0, duration, samples)
    audio = 0.5 * np.sin(2 * np.pi * frequency * t)

    sf.write(str(audio_path), audio, sample_rate)
    return audio_path


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return "Este é um texto de exemplo para testes de síntese de voz."


@pytest.fixture
def sample_config_dict():
    """Sample configuration dict for testing."""
    return {
        "paths": {
            "dataset_name": "test_dataset",
            "output_dir": "/tmp/test_output",
            "data_dir": "/tmp/test_data",
        },
        "model": {
            "name": "F5TTS_Base",
            "dim": 1024,
            "depth": 22,
            "heads": 16,
        },
        "training": {
            "batch_size": 32,
            "gradient_accumulation_steps": 1,
            "epochs": 10,
            "learning_rate": 1e-4,
        },
        "audio": {"sample_rate": 24000, "hop_length": 256, "n_fft": 1024, "n_mels": 100},
        "optimization": {
            "mixed_precision": True,
            "gradient_checkpointing": False,
            "num_workers": 4,
        },
    }
