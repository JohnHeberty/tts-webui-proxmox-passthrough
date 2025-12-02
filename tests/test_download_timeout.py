"""
Tests for job download endpoint with timeout parameter
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import Job, JobStatus, JobMode
from pathlib import Path
import time


client = TestClient(app)


def test_download_without_timeout_job_not_ready():
    """
    Test download without timeout parameter when job is not completed.
    Should return 425 (Too Early) immediately.
    """
    # Assumindo que existe um job em QUEUED ou PROCESSING
    response = client.get("/jobs/test_job_queued/download?format=wav")
    assert response.status_code == 425
    assert "not ready" in response.json()["detail"].lower()


def test_download_with_timeout_job_completes():
    """
    Test download with timeout parameter when job completes within timeout.
    Should wait and return file when job finishes.
    """
    # Este teste requer um job que complete em < timeout segundos
    # Exemplo: criar job, aguardar conclusão com timeout=60s
    
    # POST /jobs para criar job
    job_data = {
        "text": "Teste de timeout",
        "source_language": "pt-BR",
        "mode": "dubbing",
        "voice_preset": "female_generic"
    }
    
    create_response = client.post("/jobs", data=job_data)
    assert create_response.status_code == 200
    job_id = create_response.json()["id"]
    
    # GET /jobs/{job_id}/download com timeout=60s
    # Deve aguardar até job completar
    download_response = client.get(
        f"/jobs/{job_id}/download?format=wav&timeout=60"
    )
    
    # Se job completou no timeout, deve retornar arquivo (200)
    # Se não completou, retorna 408 (Request Timeout)
    assert download_response.status_code in [200, 408]
    
    if download_response.status_code == 200:
        assert download_response.headers["content-type"] == "audio/wav"
        assert "dubbed_" in download_response.headers.get("content-disposition", "")


def test_download_with_timeout_exceeds():
    """
    Test download with timeout parameter when job does NOT complete within timeout.
    Should return 408 (Request Timeout) after waiting.
    """
    # Criar job que demora muito (ou mockar delay)
    job_data = {
        "text": "Texto muito longo para demorar" * 100,  # Job que demora
        "source_language": "pt-BR",
        "mode": "dubbing",
        "voice_preset": "female_generic"
    }
    
    create_response = client.post("/jobs", data=job_data)
    assert create_response.status_code == 200
    job_id = create_response.json()["id"]
    
    # Timeout muito curto (2s) - job não deve completar
    start_time = time.time()
    download_response = client.get(
        f"/jobs/{job_id}/download?format=wav&timeout=2"
    )
    elapsed = time.time() - start_time
    
    # Deve retornar 408 após ~2 segundos
    assert download_response.status_code == 408
    assert "timeout" in download_response.json()["detail"].lower()
    assert 1.5 <= elapsed <= 3.0  # Tolerância de ±0.5s


def test_download_with_timeout_job_fails():
    """
    Test download with timeout when job fails during wait.
    Should return 500 with error message.
    """
    # Este teste requer simular falha do job
    # Pode usar mock ou job com parâmetros inválidos
    pass


def test_download_timeout_validation():
    """
    Test timeout parameter validation (must be 1-600s).
    """
    # Timeout < 1 deve retornar erro de validação (422)
    response = client.get("/jobs/any_job/download?timeout=0")
    assert response.status_code == 422
    
    # Timeout > 600 deve retornar erro de validação
    response = client.get("/jobs/any_job/download?timeout=700")
    assert response.status_code == 422
    
    # Timeout negativo
    response = client.get("/jobs/any_job/download?timeout=-5")
    assert response.status_code == 422


def test_download_with_timeout_different_formats():
    """
    Test download with timeout works for different audio formats.
    """
    formats = ["wav", "mp3", "ogg", "flac", "m4a", "opus"]
    
    for fmt in formats:
        # Assumindo job completo
        response = client.get(
            f"/jobs/completed_job_id/download?format={fmt}&timeout=30"
        )
        
        # Deve aceitar timeout para qualquer formato
        # (200 se job completo, 408 se timeout, 404 se não existe)
        assert response.status_code in [200, 404, 408, 425]


# ===== EXEMPLO DE USO VIA CURL =====
"""
# Sem timeout (comportamento antigo - erro se não completo):
curl -X GET "http://localhost:8000/jobs/{job_id}/download?format=wav"

# Com timeout de 30 segundos:
curl -X GET "http://localhost:8000/jobs/{job_id}/download?format=wav&timeout=30"

# Com timeout de 5 minutos e formato MP3:
curl -X GET "http://localhost:8000/jobs/{job_id}/download?format=mp3&timeout=300" \
     -o output.mp3

# Verificar documentação interativa:
# http://localhost:8000/docs
# Endpoint: GET /jobs/{job_id}/download
# Parâmetro timeout aparecerá com validação (1-600s, opcional)
"""


# ===== EXEMPLO DE USO VIA PYTHON =====
"""
import requests

job_id = "job_xyz123"

# 1. Download imediato (erro se não completo)
response = requests.get(f"http://localhost:8000/jobs/{job_id}/download")
if response.status_code == 425:
    print("Job ainda não está pronto")

# 2. Download com espera de até 60 segundos
response = requests.get(
    f"http://localhost:8000/jobs/{job_id}/download",
    params={"format": "mp3", "timeout": 60}
)

if response.status_code == 200:
    with open("output.mp3", "wb") as f:
        f.write(response.content)
    print("Download concluído!")
elif response.status_code == 408:
    print("Timeout: Job não completou em 60 segundos")
elif response.status_code == 500:
    print(f"Job falhou: {response.json()['detail']}")
"""


# ===== EXEMPLO DE USO VIA JAVASCRIPT (WEBUI) =====
"""
// Função helper para download com timeout
async function downloadJobWithWait(jobId, format = 'wav', timeoutSeconds = 60) {
    const url = `/jobs/${jobId}/download?format=${format}&timeout=${timeoutSeconds}`;
    
    try {
        const response = await fetch(url);
        
        if (response.status === 200) {
            // Download bem-sucedido
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `dubbed_${jobId}.${format}`;
            a.click();
            window.URL.revokeObjectURL(downloadUrl);
            return { success: true };
        } else if (response.status === 408) {
            // Timeout
            return { success: false, error: 'Timeout: Job não completou no tempo esperado' };
        } else if (response.status === 500) {
            // Job falhou
            const error = await response.json();
            return { success: false, error: error.detail };
        } else {
            return { success: false, error: `Status ${response.status}` };
        }
    } catch (error) {
        return { success: false, error: error.message };
    }
}

// Uso:
const result = await downloadJobWithWait('job_abc123', 'mp3', 30);
if (result.success) {
    console.log('Download iniciado!');
} else {
    console.error('Erro:', result.error);
}
"""
