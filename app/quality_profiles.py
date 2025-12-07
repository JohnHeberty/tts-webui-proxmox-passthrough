"""
Quality Profiles System - Engine-Specific Audio Quality Presets
Perfis de qualidade separados por engine (XTTS e F5-TTS) com armazenamento Redis
"""
from enum import Enum
from typing import Optional, Dict, List, Any, Union, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import json


class TTSEngine(str, Enum):
    """Engines TTS suportados"""
    XTTS = "xtts"


class BaseQualityProfile(BaseModel):
    """Base model para perfis de qualidade"""
    id: str = Field(..., description="ID único do perfil")
    name: str = Field(..., description="Nome do perfil")
    description: Optional[str] = Field(None, description="Descrição do perfil")
    engine: TTSEngine = Field(..., description="Engine TTS (apenas xtts)")
    is_default: bool = Field(False, description="Se é perfil padrão do engine")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True


class XTTSQualityProfile(BaseQualityProfile):
    """
    Perfil de qualidade específico para XTTS.
    
    Parâmetros otimizados para controlar:
    - Temperatura: Criatividade vs Estabilidade
    - Repetition Penalty: Evitar repetições
    - Top-P/Top-K: Amostragem probabilística
    - Length Penalty: Controle de duração
    - Speed: Velocidade da fala
    """
    engine: Literal[TTSEngine.XTTS] = Field(default=TTSEngine.XTTS)
    
    # === Parâmetros XTTS ===
    temperature: float = Field(
        default=0.75,
        ge=0.1,
        le=1.0,
        description="Temperatura (0.1-1.0): Maior = mais criativo, Menor = mais estável"
    )
    repetition_penalty: float = Field(
        default=1.5,
        ge=1.0,
        le=3.0,
        description="Penalidade de repetição (1.0-3.0): Maior = menos repetições"
    )
    top_p: float = Field(
        default=0.9,
        ge=0.5,
        le=1.0,
        description="Top-P nucleus sampling (0.5-1.0): Diversidade da amostragem"
    )
    top_k: int = Field(
        default=60,
        ge=10,
        le=100,
        description="Top-K sampling (10-100): Número de tokens candidatos"
    )
    length_penalty: float = Field(
        default=1.2,
        ge=0.5,
        le=2.0,
        description="Penalidade de comprimento (0.5-2.0): Controle de duração"
    )
    speed: float = Field(
        default=1.0,
        ge=0.5,
        le=2.0,
        description="Velocidade da fala (0.5-2.0): Multiplier de velocidade"
    )
    enable_text_splitting: bool = Field(
        default=False,
        description="Dividir texto longo em sentenças (melhor para textos grandes)"
    )
    
    # === Metadados de qualidade ===
    quality_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Score de qualidade esperado (0-10)"
    )
    latency_ms: Optional[int] = Field(
        None,
        description="Latência esperada em ms"
    )
    stability_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=10.0,
        description="Score de estabilidade (0-10)"
    )


# Union type mantido apenas com XTTS
QualityProfile = XTTSQualityProfile


class QualityProfileCreate(BaseModel):
    """Request para criar perfil de qualidade"""
    name: str = Field(..., description="Nome do perfil")
    description: Optional[str] = Field(None, description="Descrição")
    engine: TTSEngine = Field(..., description="Engine (apenas xtts)")
    is_default: bool = Field(False, description="Definir como padrão")
    parameters: Dict[str, Any] = Field(..., description="Parâmetros específicos do engine")


class QualityProfileUpdate(BaseModel):
    """Request para atualizar perfil de qualidade"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None


class QualityProfileList(BaseModel):
    """Response com lista de perfis XTTS e F5-TTS (vazio)"""
    xtts_profiles: List[XTTSQualityProfile] = Field(default_factory=list)
    f5tts_profiles: List[Any] = Field(default_factory=list)  # Empty for compatibility
    total_count: int = 0


# === Perfis Padrão XTTS ===

DEFAULT_XTTS_PROFILES = {
    "balanced": XTTSQualityProfile(
        id="xtts_balanced",
        name="Balanced (Recomendado)",
        description="Equilíbrio entre qualidade e velocidade. Ideal para uso geral.",
        engine=TTSEngine.XTTS,
        is_default=True,
        temperature=0.75,
        repetition_penalty=1.5,
        top_p=0.9,
        top_k=60,
        length_penalty=1.2,
        speed=1.0,
        enable_text_splitting=False,
        quality_score=8.0,
        latency_ms=500,
        stability_score=9.0
    ),
    "expressive": XTTSQualityProfile(
        id="xtts_expressive",
        name="Expressive (Máxima Emoção)",
        description="Máxima expressividade e emoção. Pode ter pequenos artefatos.",
        engine=TTSEngine.XTTS,
        is_default=False,
        temperature=0.85,
        repetition_penalty=1.3,
        top_p=0.95,
        top_k=70,
        length_penalty=1.3,
        speed=0.98,
        enable_text_splitting=False,
        quality_score=7.5,
        latency_ms=550,
        stability_score=7.0
    ),
    "stable": XTTSQualityProfile(
        id="xtts_stable",
        name="Stable (Produção Segura)",
        description="Máxima estabilidade. Ideal para produção em larga escala.",
        engine=TTSEngine.XTTS,
        is_default=False,
        temperature=0.70,
        repetition_penalty=1.7,
        top_p=0.85,
        top_k=55,
        length_penalty=1.1,
        speed=1.0,
        enable_text_splitting=True,
        quality_score=8.5,
        latency_ms=450,
        stability_score=10.0
    )
}
