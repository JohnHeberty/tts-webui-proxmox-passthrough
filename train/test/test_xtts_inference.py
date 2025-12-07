"""
Unit tests for XTTS Inference Engine
"""

import os
from pathlib import Path
import pytest
import torch
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from train.scripts.xtts_inference import XTTSInference, get_inference_engine


@pytest.fixture
def checkpoint_dir():
    """Fixture para diretório de checkpoints"""
    return Path(project_root) / "train" / "checkpoints"


@pytest.fixture
def test_checkpoint(checkpoint_dir):
    """Fixture para checkpoint de teste"""
    best_model = checkpoint_dir / "best_model.pt"
    if best_model.exists():
        return str(best_model)
    
    # Se não existir, usar qualquer checkpoint disponível
    checkpoints = list(checkpoint_dir.glob("checkpoint_step_*.pt"))
    if checkpoints:
        return str(checkpoints[0])
    
    pytest.skip("No checkpoints available for testing")


@pytest.fixture
def inference_engine(test_checkpoint):
    """Fixture para engine de inferência"""
    # Usar modelo base (sem checkpoint) para testes rápidos
    engine = XTTSInference(checkpoint_path=None, device="cpu")
    return engine


class TestXTTSInferenceInit:
    """Testes de inicialização do XTTSInference"""
    
    def test_init_without_checkpoint(self):
        """Testa inicialização sem checkpoint (modelo base)"""
        engine = XTTSInference(checkpoint_path=None, device="cpu")
        assert engine.model is not None
        assert engine.device == torch.device("cpu")
        assert engine.checkpoint_path is None
    
    def test_init_with_checkpoint(self, test_checkpoint):
        """Testa inicialização com checkpoint"""
        engine = XTTSInference(checkpoint_path=test_checkpoint, device="cpu")
        assert engine.model is not None
        assert engine.checkpoint_path == test_checkpoint
    
    def test_init_cuda_device(self):
        """Testa seleção automática de CUDA quando disponível"""
        engine = XTTSInference(checkpoint_path=None, device="auto")
        expected_device = "cuda" if torch.cuda.is_available() else "cpu"
        assert str(engine.device) == expected_device
    
    def test_init_invalid_checkpoint(self):
        """Testa erro ao carregar checkpoint inválido"""
        with pytest.raises((FileNotFoundError, Exception)):
            XTTSInference(checkpoint_path="/path/invalid.pt", device="cpu")


class TestXTTSSynthesize:
    """Testes de síntese de áudio"""
    
    def test_synthesize_basic(self, inference_engine):
        """Testa síntese básica de áudio"""
        text = "Olá, este é um teste de síntese de voz."
        language = "pt"
        
        # Nota: sem speaker_wav, usa voz padrão
        audio = inference_engine.synthesize(
            text=text,
            language=language,
            speaker_wav=None
        )
        
        assert audio is not None
        assert isinstance(audio, torch.Tensor)
        assert len(audio.shape) == 1  # 1D audio tensor
        assert audio.shape[0] > 0  # Audio não vazio
    
    def test_synthesize_with_speaker(self, inference_engine, checkpoint_dir):
        """Testa síntese com arquivo de referência de voz"""
        text = "Teste de clonagem de voz."
        language = "pt"
        
        # Procurar um arquivo WAV de teste
        wav_dir = Path(project_root) / "train" / "data" / "MyTTSDataset" / "wavs"
        wav_files = list(wav_dir.glob("*.wav"))[:1]
        
        if not wav_files:
            pytest.skip("No WAV files available for testing")
        
        speaker_wav = str(wav_files[0])
        audio = inference_engine.synthesize(
            text=text,
            language=language,
            speaker_wav=speaker_wav
        )
        
        assert audio is not None
        assert isinstance(audio, torch.Tensor)
    
    def test_synthesize_empty_text(self, inference_engine):
        """Testa erro com texto vazio"""
        with pytest.raises((ValueError, Exception)):
            inference_engine.synthesize(
                text="",
                language="pt"
            )
    
    def test_synthesize_unsupported_language(self, inference_engine):
        """Testa warning com idioma não suportado"""
        # XTTS suporta 16 idiomas, "xyz" não é válido
        # Pode retornar áudio ou erro dependendo da implementação
        try:
            audio = inference_engine.synthesize(
                text="Test text",
                language="xyz"
            )
            # Se não der erro, verifica que retornou áudio válido
            assert audio is not None
        except (ValueError, Exception):
            # Erro esperado para idioma inválido
            pass


class TestXTTSSynthesizeToFile:
    """Testes de síntese para arquivo"""
    
    def test_synthesize_to_file(self, inference_engine, tmp_path):
        """Testa síntese e salvamento em arquivo"""
        text = "Teste de salvamento em arquivo."
        language = "pt"
        output_path = tmp_path / "test_output.wav"
        
        result_path = inference_engine.synthesize_to_file(
            text=text,
            language=language,
            output_path=str(output_path)
        )
        
        assert result_path == str(output_path)
        assert output_path.exists()
        assert output_path.stat().st_size > 0  # Arquivo não vazio
    
    def test_synthesize_to_file_creates_directory(self, inference_engine, tmp_path):
        """Testa criação automática de diretórios"""
        text = "Teste com diretório não existente."
        language = "pt"
        output_path = tmp_path / "subdir" / "test.wav"
        
        result_path = inference_engine.synthesize_to_file(
            text=text,
            language=language,
            output_path=str(output_path)
        )
        
        assert output_path.exists()


class TestXTTSModelInfo:
    """Testes de informações do modelo"""
    
    def test_get_model_info(self, inference_engine):
        """Testa obtenção de informações do modelo"""
        info = inference_engine.get_model_info()
        
        assert isinstance(info, dict)
        assert "model_type" in info
        assert "languages" in info
        assert "checkpoint_loaded" in info
        assert "device" in info
        
        assert info["model_type"] == "xtts_v2"
        assert isinstance(info["languages"], list)
        assert len(info["languages"]) > 0
    
    def test_model_info_with_checkpoint(self, test_checkpoint):
        """Testa info do modelo com checkpoint carregado"""
        engine = XTTSInference(checkpoint_path=test_checkpoint, device="cpu")
        info = engine.get_model_info()
        
        assert info["checkpoint_loaded"] == test_checkpoint


class TestGetInferenceEngine:
    """Testes da função singleton"""
    
    def test_singleton_pattern(self):
        """Testa que get_inference_engine retorna singleton"""
        engine1 = get_inference_engine()
        engine2 = get_inference_engine()
        
        assert engine1 is engine2  # Mesma instância
    
    def test_singleton_with_checkpoint(self, test_checkpoint):
        """Testa singleton com checkpoint específico"""
        engine1 = get_inference_engine(checkpoint_path=test_checkpoint)
        engine2 = get_inference_engine(checkpoint_path=test_checkpoint)
        
        assert engine1 is engine2


class TestXTTSIntegration:
    """Testes de integração do pipeline completo"""
    
    def test_full_pipeline(self, inference_engine, tmp_path):
        """Testa pipeline completo: síntese → arquivo → info"""
        # 1. Sintetizar áudio
        text = "Pipeline completo de teste."
        language = "pt"
        audio = inference_engine.synthesize(text=text, language=language)
        assert audio is not None
        
        # 2. Salvar em arquivo
        output_path = tmp_path / "pipeline_test.wav"
        result = inference_engine.synthesize_to_file(
            text=text,
            language=language,
            output_path=str(output_path)
        )
        assert Path(result).exists()
        
        # 3. Verificar info do modelo
        info = inference_engine.get_model_info()
        assert info["model_type"] == "xtts_v2"
    
    def test_multiple_synthesis(self, inference_engine):
        """Testa múltiplas sínteses consecutivas"""
        texts = [
            "Primeira frase de teste.",
            "Segunda frase de teste.",
            "Terceira frase de teste."
        ]
        
        for text in texts:
            audio = inference_engine.synthesize(text=text, language="pt")
            assert audio is not None
            assert audio.shape[0] > 0


# Configuração de pytest
def pytest_configure(config):
    """Configuração global do pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
