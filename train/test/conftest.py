"""
Configuração e fixtures do pytest para testes de Voice Cloning.
"""

import pytest
import sys
from pathlib import Path

# Setup paths
TEST_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TEST_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def pytest_configure(config):
    """Configuração global do pytest."""
    # Aplicar patch PyTorch 2.6 uma única vez
    import torch
    
    if not hasattr(torch.load, '_patched'):
        original_load = torch.load
        
        def patched_load(*args, **kwargs):
            if 'weights_only' not in kwargs:
                kwargs['weights_only'] = False
            return original_load(*args, **kwargs)
        
        patched_load._patched = True
        torch.load = patched_load
    
    # Aceitar ToS do Coqui TTS
    import os
    os.environ['COQUI_TOS_AGREED'] = '1'
    
    # Markers customizados
    config.addinivalue_line(
        "markers", "slow: marca testes que demoram mais de 30 segundos"
    )
    config.addinivalue_line(
        "markers", "gpu: marca testes que requerem GPU (atualmente desabilitados)"
    )


@pytest.fixture(scope="session")
def test_dir():
    """Retorna diretório de testes."""
    return TEST_DIR


@pytest.fixture(scope="session")
def results_dir(test_dir):
    """Retorna diretório de resultados, criando se necessário."""
    results = test_dir / "results"
    results.mkdir(parents=True, exist_ok=True)
    return results


@pytest.fixture(scope="session")
def audio_dir(test_dir):
    """Retorna diretório de áudio."""
    return test_dir / "audio"


@pytest.fixture(scope="session")
def reference_audio(audio_dir):
    """Retorna caminho do áudio de referência."""
    ref = audio_dir / "reference_test.wav"
    if not ref.exists():
        pytest.fail(f"Áudio de referência não encontrado: {ref}")
    return ref
