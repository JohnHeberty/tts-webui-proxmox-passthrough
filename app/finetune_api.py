"""
Fine-Tuning API Endpoints

Endpoints para gerenciar fine-tuning de modelos XTTS-v2 e inferência.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/v1/finetune", tags=["fine-tuning"])


# ============================================================================
# MODELS
# ============================================================================

class FinetuneCheckpoint(BaseModel):
    """Checkpoint de fine-tuning"""
    name: str = Field(..., description="Nome do checkpoint")
    path: str = Field(..., description="Path do arquivo")
    size_mb: float = Field(..., description="Tamanho em MB")
    created_at: str = Field(..., description="Data de criação")
    global_step: Optional[int] = Field(None, description="Step do treinamento")
    val_loss: Optional[float] = Field(None, description="Validation loss")
    is_best: bool = Field(False, description="Melhor modelo")


class FinetuneCheckpointList(BaseModel):
    """Lista de checkpoints"""
    checkpoints: List[FinetuneCheckpoint]
    total: int


class XTTSSynthesizeRequest(BaseModel):
    """Request para síntese com XTTS fine-tunado"""
    text: str = Field(..., description="Texto para sintetizar")
    language: str = Field("pt", description="Código do idioma")
    checkpoint: Optional[str] = Field(None, description="Nome do checkpoint (None = base model)")
    speaker_wav: Optional[str] = Field(None, description="Path do áudio de referência")
    speed: float = Field(1.0, ge=0.5, le=2.0, description="Velocidade da fala")
    temperature: float = Field(0.75, ge=0.0, le=1.0, description="Temperatura de geração")


class XTTSSynthesizeResponse(BaseModel):
    """Response de síntese"""
    success: bool
    audio_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


class ModelInfo(BaseModel):
    """Informações do modelo XTTS"""
    model_type: str
    checkpoint: str
    device: str
    sample_rate: int
    languages: List[str]
    checkpoint_step: Optional[int] = None
    checkpoint_val_loss: Optional[float] = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/checkpoints", response_model=FinetuneCheckpointList)
async def list_checkpoints():
    """
    Lista todos os checkpoints de fine-tuning disponíveis.
    
    Returns:
        Lista de checkpoints com metadata
    """
    try:
        checkpoints_dir = Path("train/output/checkpoints")
        
        if not checkpoints_dir.exists():
            return FinetuneCheckpointList(checkpoints=[], total=0)
        
        checkpoints = []
        
        for checkpoint_file in checkpoints_dir.glob("*.pt"):
            # Calcular tamanho
            size_mb = checkpoint_file.stat().st_size / (1024 * 1024)
            
            # Ler metadata do checkpoint
            import torch
            try:
                checkpoint_data = torch.load(checkpoint_file, map_location="cpu")
                global_step = checkpoint_data.get("global_step")
                val_loss = checkpoint_data.get("val_loss")
            except Exception:
                global_step = None
                val_loss = None
            
            # Criar entry
            checkpoint = FinetuneCheckpoint(
                name=checkpoint_file.name,
                path=str(checkpoint_file),
                size_mb=round(size_mb, 2),
                created_at=str(checkpoint_file.stat().st_mtime),
                global_step=global_step,
                val_loss=val_loss,
                is_best=(checkpoint_file.name == "best_model.pt")
            )
            checkpoints.append(checkpoint)
        
        # Ordenar por data (mais recente primeiro)
        checkpoints.sort(key=lambda x: x.created_at, reverse=True)
        
        return FinetuneCheckpointList(
            checkpoints=checkpoints,
            total=len(checkpoints)
        )
        
    except Exception as e:
        logger.error(f"Erro ao listar checkpoints: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/checkpoints/{checkpoint_name}")
async def get_checkpoint(checkpoint_name: str):
    """
    Retorna informações detalhadas de um checkpoint específico.
    
    Args:
        checkpoint_name: Nome do checkpoint (ex: 'best_model.pt')
    
    Returns:
        Metadata do checkpoint
    """
    try:
        checkpoint_path = Path(f"train/output/checkpoints/{checkpoint_name}")
        
        if not checkpoint_path.exists():
            raise HTTPException(status_code=404, detail=f"Checkpoint não encontrado: {checkpoint_name}")
        
        # Ler metadata
        import torch
        checkpoint_data = torch.load(checkpoint_path, map_location="cpu")
        
        metadata = {
            "name": checkpoint_name,
            "path": str(checkpoint_path),
            "size_mb": round(checkpoint_path.stat().st_size / (1024 * 1024), 2),
            "created_at": str(checkpoint_path.stat().st_mtime),
            "global_step": checkpoint_data.get("global_step"),
            "val_loss": checkpoint_data.get("val_loss"),
            "train_loss": checkpoint_data.get("train_loss"),
            "config": checkpoint_data.get("config"),
        }
        
        return metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao ler checkpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/synthesize", response_model=XTTSSynthesizeResponse)
async def synthesize_xtts(request: XTTSSynthesizeRequest):
    """
    Sintetiza áudio usando modelo XTTS-v2 (base ou fine-tunado).
    
    Args:
        request: Dados da síntese
    
    Returns:
        Path do áudio gerado
    
    Example:
        ```json
        {
            "text": "Olá, este é um teste",
            "language": "pt",
            "checkpoint": "best_model.pt",
            "speed": 1.0
        }
        ```
    """
    try:
        from train.scripts.xtts_inference import get_inference_engine
        import tempfile
        from datetime import datetime
        
        # Resolver checkpoint path
        checkpoint_path = None
        if request.checkpoint:
            checkpoint_path = Path(f"train/output/checkpoints/{request.checkpoint}")
            if not checkpoint_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Checkpoint não encontrado: {request.checkpoint}"
                )
        
        # Obter inference engine
        engine = get_inference_engine(
            checkpoint_path=checkpoint_path,
            force_reload=(request.checkpoint is not None)
        )
        
        # Criar arquivo temporário para output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("temp/finetune_outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"xtts_{timestamp}.wav"
        
        # Sintetizar
        logger.info(f"Sintetizando com XTTS: '{request.text[:50]}...'")
        
        audio_path = engine.synthesize_to_file(
            text=request.text,
            output_path=output_path,
            language=request.language,
            speaker_wav=request.speaker_wav,
            speed=request.speed,
            temperature=request.temperature,
        )
        
        # Calcular duração
        import soundfile as sf
        audio, sr = sf.read(audio_path)
        duration = len(audio) / sr
        
        return XTTSSynthesizeResponse(
            success=True,
            audio_path=str(audio_path),
            duration_seconds=round(duration, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na síntese XTTS: {e}")
        return XTTSSynthesizeResponse(
            success=False,
            error=str(e)
        )


@router.get("/synthesize/{filename}")
async def download_synthesis(filename: str):
    """
    Faz download de um áudio sintetizado.
    
    Args:
        filename: Nome do arquivo (ex: 'xtts_20251206_173000.wav')
    
    Returns:
        Arquivo de áudio
    """
    file_path = Path(f"temp/finetune_outputs/{filename}")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {filename}")
    
    return FileResponse(
        file_path,
        media_type="audio/wav",
        filename=filename
    )


@router.get("/model/info", response_model=ModelInfo)
async def get_model_info(checkpoint: Optional[str] = None):
    """
    Retorna informações sobre o modelo XTTS carregado.
    
    Args:
        checkpoint: Nome do checkpoint (None = base model)
    
    Returns:
        Informações do modelo
    """
    try:
        from train.scripts.xtts_inference import get_inference_engine
        
        checkpoint_path = None
        if checkpoint:
            checkpoint_path = Path(f"train/output/checkpoints/{checkpoint}")
        
        engine = get_inference_engine(checkpoint_path=checkpoint_path)
        info = engine.get_model_info()
        
        return ModelInfo(**info)
        
    except Exception as e:
        logger.error(f"Erro ao obter info do modelo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/checkpoints/{checkpoint_name}")
async def delete_checkpoint(checkpoint_name: str):
    """
    Deleta um checkpoint de fine-tuning.
    
    Args:
        checkpoint_name: Nome do checkpoint
    
    Returns:
        Status da deleção
    
    Note:
        Não permite deletar 'best_model.pt' para segurança
    """
    if checkpoint_name == "best_model.pt":
        raise HTTPException(
            status_code=403,
            detail="Não é permitido deletar o best_model.pt"
        )
    
    try:
        checkpoint_path = Path(f"train/output/checkpoints/{checkpoint_name}")
        
        if not checkpoint_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Checkpoint não encontrado: {checkpoint_name}"
            )
        
        checkpoint_path.unlink()
        
        return {
            "success": True,
            "message": f"Checkpoint deletado: {checkpoint_name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar checkpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
