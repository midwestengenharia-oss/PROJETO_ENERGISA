"""
Auth Schemas - Modelos Pydantic para autenticação
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
import re


# ========================
# Request Schemas
# ========================

class SignUpRequest(BaseModel):
    """Requisição de cadastro"""
    email: EmailStr
    password: str = Field(..., min_length=6, description="Senha (mínimo 6 caracteres)")
    nome_completo: str = Field(..., min_length=3, max_length=255)
    cpf: str = Field(..., description="CPF no formato 000.000.000-00 ou 00000000000")
    telefone: Optional[str] = Field(None, description="Telefone no formato (00) 00000-0000")

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        # Remove formatação
        cpf = re.sub(r'\D', '', v)

        if len(cpf) != 11:
            raise ValueError("CPF deve ter 11 dígitos")

        # Validação do dígito verificador
        if cpf == cpf[0] * 11:
            raise ValueError("CPF inválido")

        # Calcula primeiro dígito
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        d1 = (soma * 10 % 11) % 10

        # Calcula segundo dígito
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        d2 = (soma * 10 % 11) % 10

        if cpf[-2:] != f"{d1}{d2}":
            raise ValueError("CPF inválido")

        # Retorna formatado
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

    @field_validator("telefone")
    @classmethod
    def validate_telefone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None

        # Remove formatação
        tel = re.sub(r'\D', '', v)

        if len(tel) not in [10, 11]:
            raise ValueError("Telefone deve ter 10 ou 11 dígitos")

        # Retorna formatado
        if len(tel) == 11:
            return f"({tel[:2]}) {tel[2:7]}-{tel[7:]}"
        return f"({tel[:2]}) {tel[2:6]}-{tel[6:]}"


class SignInRequest(BaseModel):
    """Requisição de login"""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Requisição de refresh token"""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Requisição de troca de senha"""
    current_password: str
    new_password: str = Field(..., min_length=6)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Nova senha deve ter no mínimo 6 caracteres")
        return v


class UpdateProfileRequest(BaseModel):
    """Requisição de atualização de perfil"""
    nome_completo: Optional[str] = Field(None, min_length=3, max_length=255)
    telefone: Optional[str] = None

    @field_validator("telefone")
    @classmethod
    def validate_telefone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None

        tel = re.sub(r'\D', '', v)

        if len(tel) not in [10, 11]:
            raise ValueError("Telefone deve ter 10 ou 11 dígitos")

        if len(tel) == 11:
            return f"({tel[:2]}) {tel[2:7]}-{tel[7:]}"
        return f"({tel[:2]}) {tel[2:6]}-{tel[6:]}"


class ForgotPasswordRequest(BaseModel):
    """Requisição de recuperação de senha"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Requisição de reset de senha"""
    token: str
    new_password: str = Field(..., min_length=6)


# ========================
# Response Schemas
# ========================

class PerfilResponse(BaseModel):
    """Perfil do usuário"""
    perfil: str
    ativo: bool


class UserResponse(BaseModel):
    """Resposta com dados do usuário"""
    id: str  # UUID do Supabase
    auth_id: str
    nome_completo: str
    email: str
    cpf: Optional[str] = None
    telefone: Optional[str] = None
    is_superadmin: bool = False
    ativo: bool = True
    email_verificado: bool = False
    perfis: List[str] = []
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuthTokens(BaseModel):
    """Tokens de autenticação"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos


class SignUpResponse(BaseModel):
    """Resposta de cadastro"""
    message: str
    user: UserResponse
    tokens: AuthTokens


class SignInResponse(BaseModel):
    """Resposta de login"""
    message: str
    user: UserResponse
    tokens: AuthTokens
    perfis_disponiveis: List[str]


class RefreshResponse(BaseModel):
    """Resposta de refresh token"""
    tokens: AuthTokens


class MeResponse(BaseModel):
    """Resposta do endpoint /me"""
    user: UserResponse
    perfis: List[PerfilResponse]


class MessageResponse(BaseModel):
    """Resposta genérica com mensagem"""
    message: str
    success: bool = True


class PerfisResponse(BaseModel):
    """Resposta com perfis disponíveis"""
    perfis: List[PerfilResponse]
    perfil_ativo: Optional[str] = None
