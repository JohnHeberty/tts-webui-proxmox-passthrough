"""
Tests for XTTSService - Sprint ARCH-1

Testa o novo service layer com SOLID principles.
"""
import pytest
from pathlib import Path
import numpy as np

from app.services.xtts_service import XTTSService
from app.exceptions import TTSEngineException


class TestXTTSService:
    """Test suite for XTTSService"""
    
    def test_initialization_cpu(self):
        """Test service initialization on CPU"""
        service = XTTSService(device="cpu")
        assert service.device == "cpu"
        assert not service.is_ready
        assert service._initialized == False
    
    def test_quality_profiles_exist(self):
        """Test que perfis de qualidade estão definidos"""
        service = XTTSService(device="cpu")
        
        assert "fast" in service.quality_profiles
        assert "balanced" in service.quality_profiles
        assert "high_quality" in service.quality_profiles
        
        # Validar estrutura dos perfis
        for profile_name, params in service.quality_profiles.items():
            assert "temperature" in params
            assert "speed" in params
            assert "top_p" in params
            assert "denoise" in params
    
    def test_language_normalization(self):
        """Test normalização de códigos de linguagem"""
        service = XTTSService(device="cpu")
        
        assert service._normalize_language("pt-BR") == "pt"
        assert service._normalize_language("pt_BR") == "pt"
        assert service._normalize_language("PT-BR") == "pt"
        assert service._normalize_language("en-US") == "en"
        assert service._normalize_language("fr") == "fr"
    
    def test_get_profile_params(self):
        """Test obtenção de parâmetros de perfil"""
        service = XTTSService(device="cpu")
        
        # Perfil válido
        params = service._get_profile_params("balanced")
        assert params["temperature"] == 0.75
        assert params["speed"] == 1.0
        
        # Perfil inválido deve retornar 'balanced' por padrão
        params = service._get_profile_params("invalid_profile")
        assert params["temperature"] == 0.75  # balanced
    
    def test_supported_languages(self):
        """Test lista de linguagens suportadas"""
        service = XTTSService(device="cpu")
        langs = service.get_supported_languages()
        
        assert 'pt' in langs
        assert 'en' in langs
        assert 'es' in langs
        assert len(langs) >= 16  # XTTS suporta 16+ linguagens
    
    def test_synthesize_not_initialized(self):
        """Test que synthesize falha se serviço não inicializado"""
        service = XTTSService(device="cpu")
        
        with pytest.raises(TTSEngineException) as exc_info:
            # Usar asyncio para rodar método async
            import asyncio
            asyncio.run(service.synthesize(
                text="test",
                speaker_wav=Path("/tmp/fake.wav"),
                language="pt"
            ))
        
        assert "not initialized" in str(exc_info.value).lower()
    
    def test_get_status_before_init(self):
        """Test status antes de inicializar"""
        service = XTTSService(device="cpu")
        status = service.get_status()
        
        assert status["initialized"] == False
        assert status["ready"] == False
        assert status["device"] == "cpu"
        assert status["model_name"] == "tts_models/multilingual/multi-dataset/xtts_v2"
    
    @pytest.mark.skipif(
        not Path("/app/models/xtts").exists(),
        reason="XTTS model not available"
    )
    def test_initialization_and_warmup(self):
        """
        Test completo de inicialização (requer modelo XTTS).
        SKIP se modelo não disponível.
        """
        service = XTTSService(device="cpu")  # CPU para CI
        service.initialize()
        
        assert service.is_ready
        assert service._initialized
        
        status = service.get_status()
        assert status["ready"] == True
        assert status["initialized"] == True


class TestXTTSServiceIntegration:
    """Integration tests (requerem modelo XTTS carregado)"""
    
    @pytest.mark.integration
    @pytest.mark.skipif(
        not Path("/app/voice_profiles/default.wav").exists(),
        reason="Default voice profile not available"
    )
    def test_full_synthesis_flow(self):
        """
        Test fluxo completo de síntese.
        Requer: modelo XTTS + voice profile default
        """
        import asyncio
        
        service = XTTSService(device="cpu")
        service.initialize()
        
        # Sintetizar
        audio, sr = asyncio.run(service.synthesize(
            text="Teste de síntese XTTS",
            speaker_wav=Path("/app/voice_profiles/default.wav"),
            language="pt",
            quality_profile="fast"
        ))
        
        # Validar output
        assert isinstance(audio, np.ndarray)
        assert sr == 24000  # XTTS sempre usa 24kHz
        assert len(audio) > 0
        assert audio.dtype == np.float32
