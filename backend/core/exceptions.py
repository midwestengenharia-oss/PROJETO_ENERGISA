"""
Exceptions - Exceções customizadas da plataforma
"""

from fastapi import HTTPException, status
from typing import Optional, Any


class PlataformaException(HTTPException):
    """
    Exceção base da plataforma.
    Todas as exceções customizadas herdam desta.
    """

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "Erro interno do servidor",
        headers: Optional[dict] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class AuthenticationError(PlataformaException):
    """Erro de autenticação (401)"""

    def __init__(self, detail: str = "Não autenticado"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(PlataformaException):
    """Erro de autorização (403)"""

    def __init__(self, detail: str = "Acesso negado"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


# Alias para compatibilidade
ForbiddenError = AuthorizationError


class NotFoundError(PlataformaException):
    """Recurso não encontrado (404)"""

    def __init__(self, resource: str = "Recurso", detail: Optional[str] = None):
        message = detail or f"{resource} não encontrado"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )


class ValidationError(PlataformaException):
    """Erro de validação (422)"""

    def __init__(self, detail: str = "Dados inválidos", errors: Optional[list] = None):
        message = detail
        if errors:
            message = f"{detail}: {', '.join(errors)}"
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message
        )


class ConflictError(PlataformaException):
    """Conflito de dados (409)"""

    def __init__(self, detail: str = "Conflito de dados"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class BadRequestError(PlataformaException):
    """Requisição inválida (400)"""

    def __init__(self, detail: str = "Requisição inválida"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class RateLimitError(PlataformaException):
    """Rate limit excedido (429)"""

    def __init__(self, detail: str = "Muitas requisições. Tente novamente em alguns minutos."):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )


# ========================
# Exceções específicas de domínio
# ========================


class EnergisaError(PlataformaException):
    """Erro relacionado à integração com a Energisa"""

    def __init__(
        self,
        detail: str = "Erro na comunicação com a Energisa",
        error_code: Optional[str] = None
    ):
        message = detail
        if error_code:
            message = f"[{error_code}] {detail}"
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=message
        )


class EnergisaSessionExpiredError(EnergisaError):
    """Sessão da Energisa expirada"""

    def __init__(self):
        super().__init__(
            detail="Sessão com a Energisa expirada. Faça login novamente.",
            error_code="SESSION_EXPIRED"
        )


class EnergisaSMSError(EnergisaError):
    """Erro ao enviar/validar SMS da Energisa"""

    def __init__(self, detail: str = "Erro na validação do SMS"):
        super().__init__(detail=detail, error_code="SMS_ERROR")


class UCNotFoundError(NotFoundError):
    """UC não encontrada"""

    def __init__(self, uc_codigo: Optional[str] = None):
        detail = "Unidade Consumidora não encontrada"
        if uc_codigo:
            detail = f"UC {uc_codigo} não encontrada"
        super().__init__(resource="UC", detail=detail)


class UsinaNotFoundError(NotFoundError):
    """Usina não encontrada"""

    def __init__(self, usina_id: Optional[int] = None):
        detail = "Usina não encontrada"
        if usina_id:
            detail = f"Usina #{usina_id} não encontrada"
        super().__init__(resource="Usina", detail=detail)


class BeneficiarioNotFoundError(NotFoundError):
    """Beneficiário não encontrado"""

    def __init__(self, beneficiario_id: Optional[int] = None):
        detail = "Beneficiário não encontrado"
        if beneficiario_id:
            detail = f"Beneficiário #{beneficiario_id} não encontrado"
        super().__init__(resource="Beneficiário", detail=detail)


class ContratoNotFoundError(NotFoundError):
    """Contrato não encontrado"""

    def __init__(self, contrato_id: Optional[int] = None):
        detail = "Contrato não encontrado"
        if contrato_id:
            detail = f"Contrato #{contrato_id} não encontrado"
        super().__init__(resource="Contrato", detail=detail)


class FaturaNotFoundError(NotFoundError):
    """Fatura não encontrada"""

    def __init__(self, fatura_id: Optional[int] = None):
        detail = "Fatura não encontrada"
        if fatura_id:
            detail = f"Fatura #{fatura_id} não encontrada"
        super().__init__(resource="Fatura", detail=detail)


class ConviteExpiradoError(PlataformaException):
    """Convite expirado ou inválido"""

    def __init__(self, detail: str = "Convite expirado ou inválido"):
        super().__init__(
            status_code=status.HTTP_410_GONE,
            detail=detail
        )


class LimitExceededError(PlataformaException):
    """Limite excedido"""

    def __init__(self, resource: str, limit: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Limite de {limit} {resource} excedido"
        )
