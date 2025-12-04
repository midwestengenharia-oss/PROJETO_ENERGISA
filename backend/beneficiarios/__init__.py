"""
Beneficiarios - Gestão de beneficiários de créditos GD
"""

from backend.beneficiarios.router import router
from backend.beneficiarios.service import beneficiarios_service
from backend.beneficiarios.schemas import (
    BeneficiarioResponse,
    BeneficiarioCreateRequest,
    BeneficiarioUpdateRequest,
)

__all__ = [
    "router",
    "beneficiarios_service",
    "BeneficiarioResponse",
    "BeneficiarioCreateRequest",
    "BeneficiarioUpdateRequest",
]
