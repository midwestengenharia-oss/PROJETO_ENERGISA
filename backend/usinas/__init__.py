"""
Usinas - Gestão de usinas solares e GD
"""

from backend.usinas.router import router
from backend.usinas.service import usinas_service
from backend.usinas.schemas import (
    UsinaResponse,
    UsinaCreateRequest,
    UsinaUpdateRequest,
)

__all__ = [
    "router",
    "usinas_service",
    "UsinaResponse",
    "UsinaCreateRequest",
    "UsinaUpdateRequest",
]
