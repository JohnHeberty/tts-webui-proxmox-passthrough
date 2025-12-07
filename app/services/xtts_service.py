"""
XTTS-v2 Service - Single Responsibility Principle

Responsável APENAS por síntese TTS, sem HTTP, sem processamento de jobs.
Implementa eager loading para eliminar atraso da primeira request.
"""
from pathlib import Path
from typing import Optional, Dict, Tuple
import torch
import numpy as np
import soundfile as sf
import io
from TTS.api import TTS

from ..logging_config import get_logger
from ..exceptions import TTSEngineException

logger = get_logger(__name__)


class XTTSService:
    """
    Service layer para XTTS-v2.
    
    Principles:
    - SRP: Só TTS synthesis, nada mais
    - Eager load: Modelos carregados no startup
    - Stateless: Sem cache interno (use Redis se necessário)
    """
    
    def __init__(
        self,
        model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        device: str = "cuda",
        models_dir: Optional[Path] = None
    ):
        """
        Inicializa XTTS service.
        
        Args:
            model_name: Nome do modelo XTTS no Coqui TTS
            device: 'cuda' ou 'cpu'
            models_dir: Diretório para cache de modelos (opcional)
        """
        self.model_name = model_name
        self.device = device
        self.models_dir = models_dir
        self.tts: Optional[TTS] = None
        self._initialized = False
        
        # Quality profiles (fast/balanced/high_quality)
        self.quality_profiles = {
            "fast": {
                "temperature": 0.7,
                "speed": 1.2,
                "top_p": 0.85,
                "repetition_penalty": 5.0,
                "denoise": False
            },
            "balanced": {
                "temperature": 0.75,
                "speed": 1.0,
                "top_p": 0.9,
                "repetition_penalty": 5.0,
                "denoise": False
            },
            "high_quality": {
                "temperature": 0.6,
                "speed": 0.95,
                "top_p": 0.95,
                "repetition_penalty": 3.0,
                "denoise": True
            }
        }
    
    def initialize(self) -> None:
        """
        Eager load do modelo no startup.
        Chamado via @app.on_event("startup") no main.py
        
        Raises:
            TTSEngineException: Se falhar ao carregar modelo
        """
        if self._initialized:
            logger.warning("XTTS already initialized, skipping")
            return
        
        # Accept Coqui TTS ToS programmatically
        import os
        os.environ['COQUI_TOS_AGREED'] = '1'
        
        logger.info(f"🚀 Loading XTTS-v2 model: {self.model_name}")
        logger.info(f"   Device: {self.device}")
        
        try:
            # Validar CUDA disponível
            if self.device == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA not available, falling back to CPU")
                self.device = "cpu"
            
            # Carregar modelo
            gpu = (self.device == "cuda")
            self.tts = TTS(
                model_name=self.model_name,
                gpu=gpu,
                progress_bar=False
            )
            
            # Se models_dir especificado, configurar cache
            if self.models_dir:
                self.models_dir.mkdir(parents=True, exist_ok=True)
            
            self._initialized = True
            
            # Log de sucesso
            if self.device == "cuda":
                vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
                logger.info(f"✅ XTTS-v2 loaded on GPU (VRAM: {vram_gb:.1f}GB)")
            else:
                logger.info("✅ XTTS-v2 loaded on CPU")
            
        except Exception as e:
            logger.error(f"Failed to load XTTS model: {e}", exc_info=True)
            raise TTSEngineException(f"XTTS initialization failed: {e}") from e
    
    async def synthesize(
        self,
        text: str,
        speaker_wav: Path,
        language: str = "pt",
        quality_profile: str = "balanced"
    ) -> Tuple[np.ndarray, int]:
        """
        Sintetiza áudio usando XTTS-v2.
        
        Args:
            text: Texto para sintetizar
            speaker_wav: Path do áudio de referência para clonagem
            language: Código da linguagem (pt, en, es, fr, de, etc.)
            quality_profile: 'fast' | 'balanced' | 'high_quality'
        
        Returns:
            Tuple[np.ndarray, int]: (audio_array, sample_rate)
        
        Raises:
            TTSEngineException: Se serviço não inicializado ou erro na síntese
        """
        if not self._initialized or self.tts is None:
            raise TTSEngineException(
                "XTTS service not initialized. Call initialize() first."
            )
        
        # Validar inputs
        if not text or not text.strip():
            raise TTSEngineException("Empty text provided")
        
        if not speaker_wav.exists():
            raise TTSEngineException(f"Speaker WAV not found: {speaker_wav}")
        
        # Normalizar linguagem (pt-BR → pt)
        language = self._normalize_language(language)
        
        # Obter parâmetros do perfil
        params = self._get_profile_params(quality_profile)
        
        try:
            logger.info(
                f"Synthesizing: {len(text)} chars, lang={language}, "
                f"profile={quality_profile}, speaker={speaker_wav.name}"
            )
            
            # Síntese XTTS
            wav = self.tts.tts(
                text=text,
                speaker_wav=str(speaker_wav),
                language=language,
                temperature=params["temperature"],
                speed=params["speed"],
                top_p=params["top_p"],
                repetition_penalty=params["repetition_penalty"]
            )
            
            # Converter para numpy array
            audio_array = np.array(wav, dtype=np.float32)
            sample_rate = 24000  # XTTS sempre usa 24kHz
            
            # Denoise se high_quality (placeholder - implementar futuramente)
            if params.get("denoise", False):
                logger.debug("Denoise requested (not implemented yet)")
                # TODO: Implementar com noisereduce
            
            duration = len(audio_array) / sample_rate
            logger.info(f"✅ Synthesis complete: {duration:.2f}s audio generated")
            
            return audio_array, sample_rate
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}", exc_info=True)
            raise TTSEngineException(f"XTTS synthesis error: {e}") from e
    
    def _normalize_language(self, language: str) -> str:
        """
        Normaliza código de linguagem para formato XTTS.
        XTTS usa 'pt' para português (não aceita 'pt-BR').
        """
        lang_map = {
            'pt-br': 'pt',
            'pt_br': 'pt',
            'en-us': 'en',
            'en_us': 'en',
            'es-es': 'es',
            'es_es': 'es',
        }
        return lang_map.get(language.lower(), language.lower())
    
    def _get_profile_params(self, profile: str) -> Dict:
        """
        Retorna parâmetros do perfil de qualidade.
        
        Args:
            profile: Nome do perfil
        
        Returns:
            Dict com parâmetros (temperature, speed, top_p, etc.)
        """
        if profile not in self.quality_profiles:
            logger.warning(
                f"Unknown quality profile '{profile}', using 'balanced'"
            )
            profile = "balanced"
        
        return self.quality_profiles[profile]
    
    def get_supported_languages(self) -> list:
        """Retorna lista de linguagens suportadas pelo XTTS"""
        return [
            'en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr',
            'ru', 'nl', 'cs', 'ar', 'zh-cn', 'ja', 'hu', 'ko'
        ]
    
    @property
    def is_ready(self) -> bool:
        """Healthcheck: retorna True se modelo carregado"""
        return self._initialized and self.tts is not None
    
    def get_status(self) -> Dict:
        """
        Retorna status detalhado do serviço.
        
        Returns:
            Dict com informações de status
        """
        status = {
            "initialized": self._initialized,
            "device": self.device,
            "model_name": self.model_name,
            "ready": self.is_ready
        }
        
        if self.device == "cuda" and torch.cuda.is_available():
            status["gpu"] = {
                "available": True,
                "device_name": torch.cuda.get_device_name(0),
                "vram_allocated_gb": round(
                    torch.cuda.memory_allocated(0) / 1e9, 2
                ),
                "vram_reserved_gb": round(
                    torch.cuda.memory_reserved(0) / 1e9, 2
                )
            }
        else:
            status["gpu"] = {"available": False}
        
        return status
