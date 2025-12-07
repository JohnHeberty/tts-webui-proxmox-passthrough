"""
Unit tests for Fine-tuning API endpoints
"""

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.main import app
from app.finetune_api import router


# Test client
client = TestClient(app)


@pytest.fixture
def checkpoint_dir():
    """Fixture para diretório de checkpoints"""
    return Path(project_root) / "train" / "checkpoints"


@pytest.fixture
def test_checkpoint_name(checkpoint_dir):
    """Fixture para nome de checkpoint de teste"""
    # Procurar um checkpoint que não seja best_model
    checkpoints = [
        cp.name for cp in checkpoint_dir.glob("checkpoint_step_*.pt")
    ]
    if checkpoints:
        return checkpoints[0]
    pytest.skip("No test checkpoints available")


class TestListCheckpoints:
    """Testes do endpoint GET /v1/finetune/checkpoints"""
    
    def test_list_checkpoints_success(self):
        """Testa listagem de checkpoints com sucesso"""
        response = client.get("/v1/finetune/checkpoints")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "checkpoints" in data
        assert isinstance(data["checkpoints"], list)
    
    def test_list_checkpoints_structure(self):
        """Testa estrutura dos checkpoints retornados"""
        response = client.get("/v1/finetune/checkpoints")
        data = response.json()
        
        if len(data["checkpoints"]) > 0:
            checkpoint = data["checkpoints"][0]
            assert "name" in checkpoint
            assert "size_mb" in checkpoint
            assert "created_at" in checkpoint
            assert "is_best" in checkpoint
    
    def test_list_checkpoints_includes_best(self, checkpoint_dir):
        """Testa que best_model.pt é incluído se existir"""
        response = client.get("/v1/finetune/checkpoints")
        data = response.json()
        
        best_model_path = checkpoint_dir / "best_model.pt"
        if best_model_path.exists():
            names = [cp["name"] for cp in data["checkpoints"]]
            assert "best_model.pt" in names
            
            # Verificar flag is_best
            best_cp = next(cp for cp in data["checkpoints"] if cp["name"] == "best_model.pt")
            assert best_cp["is_best"] is True


class TestGetCheckpoint:
    """Testes do endpoint GET /v1/finetune/checkpoints/{name}"""
    
    def test_get_checkpoint_success(self, test_checkpoint_name):
        """Testa obtenção de checkpoint específico"""
        response = client.get(f"/v1/finetune/checkpoints/{test_checkpoint_name}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == test_checkpoint_name
        assert "size_mb" in data
        assert "created_at" in data
    
    def test_get_checkpoint_not_found(self):
        """Testa erro 404 para checkpoint inexistente"""
        response = client.get("/v1/finetune/checkpoints/nonexistent.pt")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_checkpoint_path_traversal(self):
        """Testa proteção contra path traversal"""
        response = client.get("/v1/finetune/checkpoints/../../../etc/passwd")
        
        # Deve retornar 404 (não encontrado) ou 400 (bad request)
        assert response.status_code in [400, 404]


class TestSynthesize:
    """Testes do endpoint POST /v1/finetune/synthesize"""
    
    def test_synthesize_with_base_model(self):
        """Testa síntese com modelo base (sem checkpoint)"""
        request_data = {
            "text": "Olá, este é um teste de síntese.",
            "language": "pt"
        }
        
        response = client.post("/v1/finetune/synthesize", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "filename" in data
        assert "duration" in data
        assert data["filename"].endswith(".wav")
    
    def test_synthesize_with_checkpoint(self, test_checkpoint_name):
        """Testa síntese com checkpoint específico"""
        request_data = {
            "text": "Teste com checkpoint.",
            "language": "pt",
            "checkpoint_name": test_checkpoint_name
        }
        
        response = client.post("/v1/finetune/synthesize", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
    
    def test_synthesize_missing_text(self):
        """Testa erro com texto faltando"""
        request_data = {
            "language": "pt"
        }
        
        response = client.post("/v1/finetune/synthesize", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_synthesize_empty_text(self):
        """Testa erro com texto vazio"""
        request_data = {
            "text": "",
            "language": "pt"
        }
        
        response = client.post("/v1/finetune/synthesize", json=request_data)
        
        # Pode ser 422 (validation) ou 400 (bad request)
        assert response.status_code in [400, 422]
    
    def test_synthesize_invalid_checkpoint(self):
        """Testa erro com checkpoint inválido"""
        request_data = {
            "text": "Teste",
            "language": "pt",
            "checkpoint_name": "invalid_checkpoint.pt"
        }
        
        response = client.post("/v1/finetune/synthesize", json=request_data)
        
        assert response.status_code == 404
    
    def test_synthesize_with_speaker_wav(self):
        """Testa síntese com arquivo de referência de voz"""
        # Procurar um WAV de teste
        wav_dir = Path(project_root) / "train" / "data" / "MyTTSDataset" / "wavs"
        wav_files = list(wav_dir.glob("*.wav"))[:1]
        
        if not wav_files:
            pytest.skip("No WAV files for testing")
        
        request_data = {
            "text": "Teste com clonagem de voz.",
            "language": "pt",
            "speaker_wav": str(wav_files[0])
        }
        
        response = client.post("/v1/finetune/synthesize", json=request_data)
        
        assert response.status_code == 200


class TestDownloadSynthesized:
    """Testes do endpoint GET /v1/finetune/synthesize/{filename}"""
    
    def test_download_after_synthesis(self):
        """Testa download de áudio sintetizado"""
        # Primeiro sintetizar
        request_data = {
            "text": "Teste de download.",
            "language": "pt"
        }
        
        synth_response = client.post("/v1/finetune/synthesize", json=request_data)
        assert synth_response.status_code == 200
        
        filename = synth_response.json()["filename"]
        
        # Depois baixar
        download_response = client.get(f"/v1/finetune/synthesize/{filename}")
        
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "audio/wav"
        assert len(download_response.content) > 0
    
    def test_download_nonexistent_file(self):
        """Testa erro 404 para arquivo inexistente"""
        response = client.get("/v1/finetune/synthesize/nonexistent.wav")
        
        assert response.status_code == 404
    
    def test_download_path_traversal(self):
        """Testa proteção contra path traversal"""
        response = client.get("/v1/finetune/synthesize/../../etc/passwd")
        
        assert response.status_code in [400, 404]


class TestModelInfo:
    """Testes do endpoint GET /v1/finetune/model/info"""
    
    def test_get_model_info(self):
        """Testa obtenção de informações do modelo"""
        response = client.get("/v1/finetune/model/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "model_type" in data
        assert "languages" in data
        assert "device" in data
        
        assert data["model_type"] == "xtts_v2"
        assert isinstance(data["languages"], list)
        assert len(data["languages"]) > 0


class TestDeleteCheckpoint:
    """Testes do endpoint DELETE /v1/finetune/checkpoints/{name}"""
    
    def test_delete_best_model_protected(self):
        """Testa que best_model.pt não pode ser deletado"""
        response = client.delete("/v1/finetune/checkpoints/best_model.pt")
        
        assert response.status_code == 400
        assert "best_model" in response.json()["detail"].lower()
    
    def test_delete_nonexistent_checkpoint(self):
        """Testa erro 404 ao deletar checkpoint inexistente"""
        response = client.delete("/v1/finetune/checkpoints/nonexistent.pt")
        
        assert response.status_code == 404
    
    def test_delete_checkpoint_success(self, checkpoint_dir, tmp_path):
        """Testa deleção bem-sucedida de checkpoint (usando temp)"""
        # Criar checkpoint temporário para teste
        test_checkpoint = checkpoint_dir / "test_delete_me.pt"
        test_checkpoint.write_text("test checkpoint content")
        
        try:
            response = client.delete("/v1/finetune/checkpoints/test_delete_me.pt")
            
            assert response.status_code == 200
            assert not test_checkpoint.exists()
            
            data = response.json()
            assert "message" in data
            assert "test_delete_me.pt" in data["message"]
        finally:
            # Limpar se falhou
            if test_checkpoint.exists():
                test_checkpoint.unlink()


class TestAPIIntegration:
    """Testes de integração da API"""
    
    def test_full_workflow(self):
        """Testa workflow completo: list → synthesize → download"""
        # 1. Listar checkpoints
        list_response = client.get("/v1/finetune/checkpoints")
        assert list_response.status_code == 200
        
        # 2. Sintetizar áudio
        synth_request = {
            "text": "Workflow completo de teste.",
            "language": "pt"
        }
        synth_response = client.post("/v1/finetune/synthesize", json=synth_request)
        assert synth_response.status_code == 200
        
        filename = synth_response.json()["filename"]
        
        # 3. Baixar áudio
        download_response = client.get(f"/v1/finetune/synthesize/{filename}")
        assert download_response.status_code == 200
        assert len(download_response.content) > 0
        
        # 4. Verificar info do modelo
        info_response = client.get("/v1/finetune/model/info")
        assert info_response.status_code == 200
    
    def test_multiple_synthesis_requests(self):
        """Testa múltiplas requisições de síntese"""
        texts = [
            "Primeira síntese.",
            "Segunda síntese.",
            "Terceira síntese."
        ]
        
        for text in texts:
            request_data = {
                "text": text,
                "language": "pt"
            }
            response = client.post("/v1/finetune/synthesize", json=request_data)
            assert response.status_code == 200
            assert "filename" in response.json()


# Configuração de pytest
def pytest_configure(config):
    """Configuração global do pytest"""
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
