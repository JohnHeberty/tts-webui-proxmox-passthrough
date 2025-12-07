"""
Integration tests for XTTS Fine-tuning Pipeline
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
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


@pytest.fixture
def checkpoint_dir():
    """Fixture para diretório de checkpoints"""
    return Path(project_root) / "train" / "checkpoints"


@pytest.fixture
def dataset_dir():
    """Fixture para diretório do dataset"""
    return Path(project_root) / "train" / "data" / "MyTTSDataset"


class TestPipelineIntegration:
    """Testes de integração do pipeline completo"""
    
    def test_checkpoint_exists(self, checkpoint_dir):
        """Verifica que checkpoints existem após treinamento"""
        checkpoints = list(checkpoint_dir.glob("*.pt"))
        assert len(checkpoints) > 0, "Nenhum checkpoint encontrado"
    
    def test_dataset_exists(self, dataset_dir):
        """Verifica que dataset foi processado"""
        metadata_train = dataset_dir / "metadata_train.csv"
        metadata_val = dataset_dir / "metadata_val.csv"
        wavs_dir = dataset_dir / "wavs"
        
        assert metadata_train.exists(), "metadata_train.csv não encontrado"
        assert metadata_val.exists(), "metadata_val.csv não encontrado"
        assert wavs_dir.exists(), "Diretório wavs não encontrado"
        
        # Verificar que tem WAVs
        wav_files = list(wavs_dir.glob("*.wav"))
        assert len(wav_files) > 0, "Nenhum arquivo WAV encontrado"
    
    def test_tensorboard_logs_exist(self):
        """Verifica que logs do TensorBoard foram criados"""
        runs_dir = Path(project_root) / "train" / "runs"
        event_files = list(runs_dir.glob("events.out.tfevents.*"))
        
        assert len(event_files) > 0, "Nenhum arquivo de evento do TensorBoard encontrado"
    
    def test_inference_engine_loads_checkpoint(self, checkpoint_dir):
        """Testa que engine carrega checkpoint corretamente"""
        best_model = checkpoint_dir / "best_model.pt"
        
        if not best_model.exists():
            pytest.skip("best_model.pt not available")
        
        engine = XTTSInference(checkpoint_path=str(best_model), device="cpu")
        
        assert engine.model is not None
        assert engine.checkpoint_path == str(best_model)
        
        # Verificar info do modelo
        info = engine.get_model_info()
        assert info["checkpoint_loaded"] == str(best_model)


class TestEndToEndWorkflow:
    """Testes E2E completos"""
    
    @pytest.mark.slow
    def test_full_training_to_inference(self, checkpoint_dir, dataset_dir):
        """Testa pipeline: dataset → training → inference → API"""
        # 1. Verificar dataset processado
        metadata_train = dataset_dir / "metadata_train.csv"
        assert metadata_train.exists()
        
        # 2. Verificar checkpoints de treinamento
        checkpoints = list(checkpoint_dir.glob("*.pt"))
        assert len(checkpoints) > 0
        
        # 3. Carregar checkpoint em engine de inferência
        best_model = checkpoint_dir / "best_model.pt"
        if not best_model.exists():
            best_model = checkpoints[0]
        
        engine = XTTSInference(checkpoint_path=str(best_model), device="cpu")
        
        # 4. Sintetizar áudio
        text = "Teste end-to-end completo."
        audio = engine.synthesize(text=text, language="pt")
        
        assert audio is not None
        assert audio.shape[0] > 0
        
        # 5. Testar via API
        api_request = {
            "text": text,
            "language": "pt",
            "checkpoint_name": best_model.name
        }
        
        response = client.post("/v1/finetune/synthesize", json=api_request)
        assert response.status_code == 200
        
        filename = response.json()["filename"]
        
        # 6. Download via API
        download_response = client.get(f"/v1/finetune/synthesize/{filename}")
        assert download_response.status_code == 200
    
    @pytest.mark.slow
    def test_voice_cloning_workflow(self, dataset_dir):
        """Testa workflow de clonagem de voz"""
        # Obter um WAV de referência
        wavs_dir = dataset_dir / "wavs"
        wav_files = list(wavs_dir.glob("*.wav"))[:1]
        
        if not wav_files:
            pytest.skip("No WAV files for testing")
        
        speaker_wav = str(wav_files[0])
        
        # 1. Via engine diretamente
        engine = get_inference_engine()
        audio = engine.synthesize(
            text="Teste de clonagem de voz com referência.",
            language="pt",
            speaker_wav=speaker_wav
        )
        
        assert audio is not None
        
        # 2. Via API
        api_request = {
            "text": "Teste de clonagem via API.",
            "language": "pt",
            "speaker_wav": speaker_wav
        }
        
        response = client.post("/v1/finetune/synthesize", json=api_request)
        assert response.status_code == 200


class TestAPICheckpointIntegration:
    """Testes de integração entre API e checkpoints"""
    
    def test_list_checkpoints_matches_filesystem(self, checkpoint_dir):
        """Verifica que API lista checkpoints corretos"""
        # Obter checkpoints via filesystem
        fs_checkpoints = {cp.name for cp in checkpoint_dir.glob("*.pt")}
        
        # Obter checkpoints via API
        response = client.get("/v1/finetune/checkpoints")
        assert response.status_code == 200
        
        api_checkpoints = {cp["name"] for cp in response.json()["checkpoints"]}
        
        # Verificar que são iguais
        assert fs_checkpoints == api_checkpoints
    
    def test_checkpoint_metadata_correct(self, checkpoint_dir):
        """Verifica que metadados de checkpoints estão corretos"""
        response = client.get("/v1/finetune/checkpoints")
        data = response.json()
        
        for checkpoint in data["checkpoints"]:
            name = checkpoint["name"]
            size_mb = checkpoint["size_mb"]
            
            # Verificar arquivo existe
            checkpoint_path = checkpoint_dir / name
            assert checkpoint_path.exists()
            
            # Verificar tamanho correto
            actual_size_mb = checkpoint_path.stat().st_size / (1024 * 1024)
            assert abs(size_mb - actual_size_mb) < 0.1  # Tolerância de 0.1 MB


class TestInferenceConsistency:
    """Testes de consistência da inferência"""
    
    def test_same_text_similar_length(self):
        """Verifica que mesmo texto gera áudio de tamanho similar"""
        engine = get_inference_engine()
        text = "Teste de consistência de inferência."
        
        audio1 = engine.synthesize(text=text, language="pt")
        audio2 = engine.synthesize(text=text, language="pt")
        
        # Áudios devem ter tamanho similar (tolerância de 10%)
        ratio = audio1.shape[0] / audio2.shape[0]
        assert 0.9 < ratio < 1.1
    
    def test_longer_text_longer_audio(self):
        """Verifica que texto mais longo gera áudio mais longo"""
        engine = get_inference_engine()
        
        short_text = "Curto."
        long_text = "Este é um texto muito mais longo que deve gerar um áudio significativamente maior."
        
        audio_short = engine.synthesize(text=short_text, language="pt")
        audio_long = engine.synthesize(text=long_text, language="pt")
        
        assert audio_long.shape[0] > audio_short.shape[0]


class TestErrorRecovery:
    """Testes de recuperação de erros"""
    
    def test_api_handles_invalid_checkpoint_gracefully(self):
        """Verifica que API retorna erro apropriado para checkpoint inválido"""
        request_data = {
            "text": "Teste",
            "language": "pt",
            "checkpoint_name": "invalid_checkpoint.pt"
        }
        
        response = client.post("/v1/finetune/synthesize", json=request_data)
        
        assert response.status_code == 404
        assert "detail" in response.json()
    
    def test_engine_handles_invalid_speaker_wav(self):
        """Verifica que engine lida com speaker_wav inválido"""
        engine = get_inference_engine()
        
        with pytest.raises((FileNotFoundError, Exception)):
            engine.synthesize(
                text="Teste",
                language="pt",
                speaker_wav="/path/invalid.wav"
            )


# Configuração de pytest
def pytest_configure(config):
    """Configuração global do pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (use with --runslow)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "not slow"])
