"""
Testes de seleção de engine para clonagem de voz
Garante que bug de engine selection não retorne

Ref: RESULT.md - Root Cause Analysis
Sprint: SPRINT-02
Data: 2024-12-04
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import io
import wave
import numpy as np
import time

from app.main import app
from app.models import JobStatus


client = TestClient(app)


def create_test_audio(duration_secs=1.0, sample_rate=24000):
    """
    Cria arquivo WAV de teste em memória
    
    Args:
        duration_secs: Duração do áudio em segundos
        sample_rate: Taxa de amostragem (Hz)
    
    Returns:
        BytesIO com WAV válido
    """
    # Gera sinal senoidal simples (440 Hz = Lá)
    t = np.linspace(0, duration_secs, int(sample_rate * duration_secs))
    audio_data = np.sin(2 * np.pi * 440 * t)
    
    # Normaliza para 16-bit
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Cria WAV em memória
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    wav_io.seek(0)
    return wav_io


def wait_for_job_completion(job_id: str, max_wait_secs: int = 60, poll_interval: int = 2):
    """
    Aguarda job completar com polling
    
    Args:
        job_id: ID do job
        max_wait_secs: Tempo máximo de espera
        poll_interval: Intervalo entre polls (segundos)
    
    Returns:
        Job data (dict)
    
    Raises:
        AssertionError: Se timeout ou job falhou
    """
    start_time = time.time()
    
    while time.time() - start_time < max_wait_secs:
        response = client.get(f"/jobs/{job_id}")
        assert response.status_code == 200, f"Failed to get job {job_id}"
        
        job = response.json()
        status = job.get("status")
        
        if status == JobStatus.COMPLETED:
            return job
        elif status == JobStatus.FAILED:
            error_msg = job.get("error_message", "Unknown error")
            pytest.fail(f"Job {job_id} failed: {error_msg}")
        
        time.sleep(poll_interval)
    
    pytest.fail(f"Job {job_id} timeout after {max_wait_secs}s")


@pytest.mark.asyncio
async def test_clone_voice_with_xtts_engine():
    """
    Teste: Clonagem com XTTS (default) deve usar XTTS
    
    Verifica:
    - Endpoint aceita tts_engine='xtts'
    - Job é criado com engine correto
    - Worker usa XTTS engine
    """
    audio_file = create_test_audio()
    
    response = client.post(
        "/voices/clone",
        data={
            "name": "TestVoiceXTTS",
            "language": "pt",
            "tts_engine": "xtts",  # ✅ Explicitamente XTTS
            "description": "Test voice with XTTS"
        },
        files={"file": ("test_xtts.wav", audio_file, "audio/wav")}
    )
    
    # Validação do response
    assert response.status_code == 202, f"Expected 202, got {response.status_code}: {response.json()}"
    data = response.json()
    
    assert "job_id" in data
    assert data["status"] == JobStatus.QUEUED
    
    job_id = data["job_id"]
    
    # Aguardar processamento
    job = wait_for_job_completion(job_id, max_wait_secs=60)
    
    # ✅ Verificar engine usado
    assert job["tts_engine"] == "xtts", f"Expected 'xtts', got '{job['tts_engine']}'"
    
    # Verificar voice profile criado
    assert job.get("voice_id") is not None
    
    voice_response = client.get(f"/voices/{job['voice_id']}")
    assert voice_response.status_code == 200


@pytest.mark.asyncio
async def test_clone_voice_with_f5tts_engine():
    """
    🔴 TESTE CRÍTICO: Clonagem com F5-TTS deve usar F5-TTS
    
    Este teste GARANTE que o bug não retorne.
    Se falhar, significa que:
    - Fix da SPRINT-01 foi revertido acidentalmente
    - Regressão foi introduzida
    
    Verifica:
    - Endpoint aceita tts_engine='f5tts'
    - Job é criado com engine='f5tts' (NÃO 'xtts')
    - Worker usa F5-TTS engine (NÃO XTTS)
    """
    audio_file = create_test_audio()
    
    response = client.post(
        "/voices/clone",
        data={
            "name": "TestVoiceF5TTS",
            "language": "pt",
            "tts_engine": "f5tts",  # ✅ CRÍTICO: Deve usar F5-TTS
            "description": "Test voice with F5-TTS",
            "ref_text": "Esta é uma frase de teste para o F5-TTS."
        },
        files={"file": ("test_f5tts.wav", audio_file, "audio/wav")}
    )
    
    # Validação do response
    assert response.status_code == 202, f"Expected 202, got {response.status_code}: {response.json()}"
    data = response.json()
    
    assert "job_id" in data
    assert data["status"] == JobStatus.QUEUED
    
    job_id = data["job_id"]
    
    # Aguardar processamento (F5-TTS pode ser mais lento)
    job = wait_for_job_completion(job_id, max_wait_secs=120)
    
    # 🔴 VERIFICAÇÃO CRÍTICA: Engine DEVE ser f5tts
    assert job["tts_engine"] == "f5tts", \
        f"❌ BUG RETORNOU! Expected 'f5tts', got '{job['tts_engine']}'"
    
    # Verificar voice profile criado
    assert job.get("voice_id") is not None
    
    voice_response = client.get(f"/voices/{job['voice_id']}")
    assert voice_response.status_code == 200


@pytest.mark.asyncio
async def test_clone_voice_invalid_engine():
    """
    Teste: Engine inválido deve retornar erro 400
    
    Verifica validação adicionada na SPRINT-01
    """
    audio_file = create_test_audio()
    
    response = client.post(
        "/voices/clone",
        data={
            "name": "TestVoiceInvalid",
            "language": "pt",
            "tts_engine": "invalid_engine",  # ❌ Engine inválido
        },
        files={"file": ("test_invalid.wav", audio_file, "audio/wav")}
    )
    
    # Deve retornar 400 Bad Request
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    error = response.json()
    assert "tts_engine" in error["detail"].lower()
    assert "invalid" in error["detail"].lower()


@pytest.mark.asyncio
async def test_clone_voice_default_engine():
    """
    Teste: Sem especificar engine deve usar XTTS (default)
    
    Backward compatibility: código antigo sem tts_engine continua funcionando
    """
    audio_file = create_test_audio()
    
    response = client.post(
        "/voices/clone",
        data={
            "name": "TestVoiceDefault",
            "language": "pt",
            # tts_engine NÃO especificado - deve usar default
        },
        files={"file": ("test_default.wav", audio_file, "audio/wav")}
    )
    
    assert response.status_code == 202
    data = response.json()
    job_id = data["job_id"]
    
    # Aguardar e verificar
    job = wait_for_job_completion(job_id, max_wait_secs=60)
    
    # Default deve ser XTTS
    assert job["tts_engine"] == "xtts", f"Expected 'xtts' (default), got '{job['tts_engine']}'"


@pytest.mark.asyncio
async def test_clone_voice_case_insensitive():
    """
    Teste: Engine selection deve ser case-insensitive
    
    Aceitar variações: XTTS, xtts, XtTs, etc.
    """
    test_cases = [
        ("XTTS", "xtts"),  # Uppercase
        ("XtTs", "xtts"),  # Mixed case
        ("F5TTS", "f5tts"),  # Uppercase
        ("F5tts", "f5tts"),  # Mixed case
    ]
    
    for engine_input, expected_engine in test_cases:
        audio_file = create_test_audio()
        
        response = client.post(
            "/voices/clone",
            data={
                "name": f"TestVoice_{engine_input}",
                "language": "pt",
                "tts_engine": engine_input,
            },
            files={"file": (f"test_{engine_input}.wav", audio_file, "audio/wav")}
        )
        
        # NOTA: Atualmente validação é case-sensitive
        # Se quiser case-insensitive, precisa modificar validação em main.py
        # Este teste documenta comportamento atual
        if engine_input.lower() in ['xtts', 'f5tts']:
            assert response.status_code == 202, \
                f"Engine '{engine_input}' should be accepted (case-insensitive)"
        else:
            # Por ora, só lowercase é aceito
            pass


class TestEngineSelectionRegression:
    """
    Testes de regressão - garantir que bugs antigos não retornem
    
    Ref: RESULT.md - Root Cause Analysis
    Data: 2024-12-04
    """
    
    @pytest.mark.regression
    @pytest.mark.asyncio
    async def test_f5tts_selection_not_ignored(self):
        """
        REGRESSÃO BUG: Engine f5tts era ignorado
        
        Histórico:
        - 2024-12-04: Bug descoberto (RESULT.md)
        - 2024-12-04: Fix implementado (SPRINT-01)
        
        Este teste GARANTE que fix permanece.
        Se falhar = regressão = BLOCKER CRÍTICO
        """
        audio_file = create_test_audio()
        
        response = client.post(
            "/voices/clone",
            data={
                "name": "RegressionTestF5TTS",
                "language": "pt",
                "tts_engine": "f5tts",  # 🔴 NÃO PODE SER IGNORADO
                "ref_text": "Teste de regressão do bug de engine selection."
            },
            files={"file": ("regression_f5tts.wav", audio_file, "audio/wav")}
        )
        
        assert response.status_code == 202
        job_id = response.json()["job_id"]
        
        # Aguardar job
        job = wait_for_job_completion(job_id, max_wait_secs=120)
        
        # 🔴 CRÍTICO: Se retornar 'xtts', bug voltou
        assert job["tts_engine"] == "f5tts", \
            "❌ REGRESSION DETECTED! F5-TTS selection is being ignored again!"
    
    @pytest.mark.regression
    def test_fastapi_form_enum_parsing(self):
        """
        Teste unitário: Validação de string para engine
        
        Garante que validação funciona corretamente
        """
        from app.models import TTSEngine
        
        # Valores válidos
        valid_engines = ['xtts', 'f5tts']
        for value in valid_engines:
            # Simular conversão
            assert value in [e.value for e in TTSEngine], \
                f"'{value}' should be valid TTSEngine"
        
        # Valores inválidos
        invalid_engines = ['invalid', 'gpt', 'elevenlabs', '']
        for value in invalid_engines:
            assert value not in [e.value for e in TTSEngine], \
                f"'{value}' should NOT be valid TTSEngine"
