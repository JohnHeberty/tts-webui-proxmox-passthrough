"""
FastAPI Dependencies - Dependency Injection Pattern

Fornece dependências reutilizáveis para injeção nos endpoints.
"""
from fastapi import Depends, HTTPException
from typing import Optional

from .services.xtts_service import XTTSService


# Global service instance (inicializado no startup)
_xtts_service: Optional[XTTSService] = None


def set_xtts_service(service: XTTSService) -> None:
    """
    Define a instância global do XTTS service.
    Chamado no startup do main.py
    """
    global _xtts_service
    _xtts_service = service


async def get_xtts_service() -> XTTSService:
    """
    Dependency para injetar XTTSService nos endpoints.
    
    Garante que o serviço está inicializado antes de processar request.
    
    Raises:
        HTTPException: 503 se serviço não está pronto
    
    Returns:
        XTTSService instance
    """
    if _xtts_service is None:
        raise HTTPException(
            status_code=503,
            detail="XTTS service not initialized. Server is starting up."
        )
    
    if not _xtts_service.is_ready:
        raise HTTPException(
            status_code=503,
            detail="XTTS service not ready. Models are loading."
        )
    
    return _xtts_service
