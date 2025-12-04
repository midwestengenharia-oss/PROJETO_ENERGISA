"""
UCs - Gestão de Unidades Consumidoras
"""

from backend.ucs.router import router
from backend.ucs.service import ucs_service
from backend.ucs.schemas import (
    UCResponse,
    UCVincularRequest,
    UCUpdateRequest,
)

__all__ = [
    "router",
    "ucs_service",
    "UCResponse",
    "UCVincularRequest",
    "UCUpdateRequest",
]
