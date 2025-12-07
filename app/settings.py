"""
Centralized Configuration using Pydantic Settings

Substitui app/config.py com validação automática e type-safety.
Carrega de .env automaticamente.
"""
from pathlib import Path
from typing import Optional, Dict, Any
import torch
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuração global do TTS WebUI.
    
    Todas as configurações são carregadas de variáveis de ambiente (.env)
    com validação automática via Pydantic.
    """
    
    # === PATHS ===
    base_dir: Path = Field(default=Path("/app"), description="Base directory")
    models_dir: Path = Field(default=Path("/app/models"), description="Models directory")
    xtts_model_path: Path = Field(default=Path("/app/models/xtts"), description="XTTS models")
    voice_profiles_dir: Path = Field(default=Path("/app/voice_profiles"))
    temp_dir: Path = Field(default=Path("/app/temp"))
    processed_dir: Path = Field(default=Path("/app/processed"))
    uploads_dir: Path = Field(default=Path("/app/uploads"))
    logs_dir: Path = Field(default=Path("/app/logs"))
    
    # === XTTS SETTINGS ===
    xtts_model_name: str = Field(
        default="tts_models/multilingual/multi-dataset/xtts_v2",
        description="XTTS model name from Coqui TTS"
    )
    xtts_device: str = Field(default="cuda", env="DEVICE", description="cuda or cpu")
    xtts_sample_rate: int = Field(default=24000, description="XTTS sample rate (fixed)")
    xtts_default_language: str = Field(default="pt", description="Default language")
    
    # === REDIS & CELERY ===
    redis_host: str = Field(default="redis", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_url: str = Field(default="redis://redis:6379/0", env="REDIS_URL")
    
    celery_broker_url: str = Field(default="redis://redis:6379/0")
    celery_result_backend: str = Field(default="redis://redis:6379/0")
    celery_task_timeout: int = Field(default=300, description="Task timeout in seconds")
    
    # === API SETTINGS ===
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8005)
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # === TRAINING SETTINGS ===
    train_epochs: int = Field(default=20, ge=1, le=1000, description="Training epochs")
    train_batch_size: int = Field(default=2, ge=1, le=16, description="Batch size")
    train_sample_rate: int = Field(default=24000, description="Training sample rate (must match XTTS)")
    train_max_audio_length: int = Field(default=12, description="Max audio length in seconds")
    
    # === VOICE CLONING ===
    max_audio_file_size_mb: int = Field(default=50, description="Max upload size")
    supported_audio_formats: list = Field(
        default_factory=lambda: ["wav", "mp3", "ogg", "flac", "m4a", "opus"]
    )
    
    # === FEATURE FLAGS ===
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    enable_webui: bool = Field(default=True, description="Enable WebUI")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignora vars extras do .env
    )
    
    @field_validator("xtts_model_path", "voice_profiles_dir", "temp_dir", "processed_dir")
    @classmethod
    def validate_paths_exist(cls, v: Path) -> Path:
        """Valida que paths críticos existem (cria se necessário)"""
        if not v.exists():
            try:
                v.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {v}")
            except Exception as e:
                raise ValueError(f"Cannot create path {v}: {e}")
        return v
    
    @field_validator("xtts_device")
    @classmethod
    def validate_device(cls, v: str) -> str:
        """Valida device CUDA"""
        if v == "cuda":
            if not torch.cuda.is_available():
                print("WARNING: CUDA not available, falling back to CPU")
                return "cpu"
        return v
    
    @field_validator("train_sample_rate")
    @classmethod
    def validate_sample_rate_alignment(cls, v: int, info) -> int:
        """Valida que train_sample_rate == xtts_sample_rate"""
        # Pydantic v2: values já validados estão em info.data
        xtts_sr = info.data.get('xtts_sample_rate', 24000)
        if v != xtts_sr:
            raise ValueError(
                f"train_sample_rate ({v}) must match xtts_sample_rate ({xtts_sr})"
            )
        return v
    
    def get_redis_url(self) -> str:
        """Gera Redis URL a partir de componentes"""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def get_celery_config(self) -> Dict[str, Any]:
        """Retorna configuração do Celery"""
        return {
            "broker_url": self.celery_broker_url,
            "result_backend": self.celery_result_backend,
            "task_time_limit": self.celery_task_timeout,
            "task_soft_time_limit": self.celery_task_timeout - 30,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte settings para dict (compatibilidade com código legado)"""
        return {
            "device": self.xtts_device,
            "models_dir": str(self.models_dir),
            "xtts_model_path": str(self.xtts_model_path),
            "voice_profiles_dir": str(self.voice_profiles_dir),
            "temp_dir": str(self.temp_dir),
            "processed_dir": str(self.processed_dir),
            "uploads_dir": str(self.uploads_dir),
            "redis_url": self.redis_url,
            "log_level": self.log_level,
        }


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Retorna singleton de Settings.
    Carrega do .env na primeira chamada.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Backward compatibility function (deprecar futuramente)
def get_settings_dict() -> Dict[str, Any]:
    """
    DEPRECATED: Use get_settings() diretamente.
    
    Mantido para compatibilidade com código existente que espera dict.
    """
    return get_settings().to_dict()


# Funções de conveniência (mantidas para compatibilidade)
def is_language_supported(language: str) -> bool:
    """Verifica se linguagem é suportada pelo XTTS"""
    supported = [
        'en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr',
        'ru', 'nl', 'cs', 'ar', 'zh-cn', 'ja', 'hu', 'ko'
    ]
    # Normalizar (pt-BR → pt)
    lang = language.lower().split('-')[0]
    return lang in supported


def get_supported_languages() -> list:
    """Retorna lista de linguagens suportadas"""
    return [
        'en', 'es', 'fr', 'de', 'it', 'pt', 'pl', 'tr',
        'ru', 'nl', 'cs', 'ar', 'zh-cn', 'ja', 'hu', 'ko'
    ]


# Voice presets (movido de config.py)
VOICE_PRESETS = {
    "default": {
        "name": "Default Voice",
        "description": "Voice padrão do sistema",
        "file": "default.wav"
    },
    "narrator": {
        "name": "Narrator",
        "description": "Voz de narrador profissional",
        "file": "narrator.wav"
    }
}


def get_voice_presets() -> dict:
    """Retorna voice presets disponíveis"""
    return VOICE_PRESETS


def is_voice_preset_valid(preset_id: str) -> bool:
    """Verifica se preset ID é válido"""
    return preset_id in VOICE_PRESETS
