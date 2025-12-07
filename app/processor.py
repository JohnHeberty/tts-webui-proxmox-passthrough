"""
Processor para jobs de dublagem e clonagem de voz
v2.0: Integrado com XTTSService (SOLID architecture)
"""
import logging
from pathlib import Path
from typing import Optional

from .models import Job, VoiceProfile, JobMode, JobStatus
from .settings import get_settings
from .exceptions import DubbingException, VoiceCloneException
from .resilience import CircuitBreaker
from .quality_profile_mapper import map_quality_profile_for_fallback
from .services.xtts_service import XTTSService

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """
    Processa jobs de dublagem e clonagem de voz.
    
    v2.0 Changes:
    - Usa XTTSService via dependency injection
    - Sem lazy loading de engines (XTTS já eager loaded)
    - Simplificado para usar apenas XTTS
    """
    
    def __init__(self, xtts_service: XTTSService):
        """
        Inicializa o processador com XTTS service injetado.
        
        Args:
            xtts_service: Instância do XTTSService (eager loaded)
        """
        self.settings = get_settings()
        self.xtts_service = xtts_service
        
        # Circuit breaker para proteção contra falhas
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            timeout_seconds=60
        )
        
        self.job_store = None  # Será injetado no main.py
    
    def _load_engine(self, engine_type: str):
        """
        Carrega engine TTS usando factory pattern (lazy initialization)
        
        Args:
            engine_type: 'xtts' ou 'f5tts'
        """
        if engine_type in self.engines:
            return  # Já carregado
        
        from .engines import create_engine_with_fallback
        logger.info(f"Initializing {engine_type} engine")
        
        try:
            self.engines[engine_type] = create_engine_with_fallback(
                engine_type=engine_type,
                settings=self.settings,
                fallback_engine='xtts'  # Sempre fallback para XTTS
            )
            logger.info(f"✅ {engine_type} engine loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load {engine_type} engine: {e}", exc_info=True)
            raise
    
    def _get_engine(self, engine_type: str):
        """
        Obtém engine TTS (lazy load se necessário)
        
        Args:
            engine_type: 'xtts' ou 'f5tts'
        
        Returns:
            TTSEngine instance
        """
        if engine_type not in self.engines:
            self._load_engine(engine_type)
        return self.engines[engine_type]
    
    async def process_dubbing_job(self, job: Job, voice_profile: Optional[VoiceProfile] = None) -> Job:
        """
        Processa job de dublagem usando XTTS service.
        
        Args:
            job: Job a processar
            voice_profile: Perfil de voz clonada (se mode=dubbing_with_clone)
        
        Returns:
            Job atualizado
        """
        try:
            logger.info(f"Processing dubbing job {job.id}: mode={job.mode}")
            
            # v2.0: Sempre usa XTTS (único engine disponível)
            job.tts_engine_requested = "xtts"
            job.tts_engine_used = "xtts"
            job.engine_fallback = False
            
            job.status = JobStatus.PROCESSING
            job.progress = 10.0
            if self.job_store:
                self.job_store.update_job(job)
            
            # Gera áudio usando XTTSService
            from io import BytesIO
            audio_bytes = await self.xtts_service.synthesize_async(
                text=job.text,
                language=job.source_language or job.target_language or 'en',
                speaker_wav=voice_profile.profile_path if voice_profile else None,
                quality_profile_id=job.quality_profile
            )
            
            # Calculate duration from audio
            import soundfile as sf
            audio_data, sample_rate = sf.read(BytesIO(audio_bytes))
            duration = len(audio_data) / sample_rate
            
            job.progress = 80.0
            if self.job_store:
                self.job_store.update_job(job)
            
            # Salva áudio
            processed_dir = Path(self.settings.processed_dir)
            processed_dir.mkdir(exist_ok=True, parents=True)
            
            output_path = processed_dir / f"{job.id}.wav"
            with open(output_path, 'wb') as f:
                f.write(audio_bytes)
            
            job.output_file = str(output_path)
            job.duration = duration
            job.file_size_output = len(audio_bytes)
            job.audio_url = f"/jobs/{job.id}/download"
            job.progress = 100.0
            job.status = JobStatus.COMPLETED
            
            import datetime
            job.completed_at = datetime.datetime.now()
            
            if self.job_store:
                self.job_store.update_job(job)
            
            logger.info("Dubbing job %s completed: %.2fs", job.id, duration)
            
            return job
            
        except Exception as e:
            logger.error("Dubbing job %s failed: %s", job.id, e, exc_info=True)
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            if self.job_store:
                self.job_store.update_job(job)
            raise DubbingException(str(e)) from e
    
    async def process_clone_job(self, job: Job) -> VoiceProfile:
        """
        Processa job de clonagem de voz usando XTTS service.
        
        Returns:
            VoiceProfile criado
        """
        import datetime
        start_time = datetime.datetime.now()
        
        try:
            # v2.0: Sempre usa XTTS
            job.tts_engine_requested = "xtts"
            job.tts_engine_used = "xtts"
            job.engine_fallback = False
            
            logger.info(
                f"🎬 Starting voice clone: {job.voice_name}",
                extra={
                    "job_id": job.id,
                    "voice_name": job.voice_name,
                    "language": job.source_language
                }
            )
            
            # Validação
            if not job.input_file:
                error_msg = f"Job {job.id} missing input_file"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            job.status = JobStatus.PROCESSING
            job.progress = 20.0
            if self.job_store:
                self.job_store.update_job(job)
            
            # Cria VoiceProfile usando XTTSService
            voice_profile = await self.xtts_service.create_voice_profile(
                audio_path=job.input_file,
                voice_name=job.voice_name,
                language=job.source_language or 'en',
                description=job.voice_description
            )
            
            job.progress = 90.0
            if self.job_store:
                self.job_store.update_job(job)
            
            # Salva perfil no store
            if self.job_store:
                self.job_store.save_voice_profile(voice_profile)
            
            job.progress = 100.0
            job.status = JobStatus.COMPLETED
            job.output_file = voice_profile.profile_path
            job.voice_id = voice_profile.id
            
            job.completed_at = datetime.datetime.now()
            
            if self.job_store:
                self.job_store.update_job(job)
            
            # ✅ Logging estruturado de sucesso
            duration_secs = (job.completed_at - start_time).total_seconds()
            logger.info(
                "✅ Voice clone completed",
                extra={
                    "job_id": job.id,
                    "voice_id": voice_profile.id,
                    "voice_name": job.voice_name,
                    "engine_used": job.tts_engine_used,
                    "duration_secs": round(duration_secs, 2),
                    "status": "success"
                }
            )
            
            logger.info("Voice clone job %s completed: %s", job.id, voice_profile.id)
            
            return voice_profile
            
        except Exception as e:
            logger.error("Voice clone job %s failed: %s", job.id, e, exc_info=True)
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            if self.job_store:
                self.job_store.update_job(job)
            raise VoiceCloneException(str(e)) from e
