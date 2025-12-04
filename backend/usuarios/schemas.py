"""
Usuarios Schemas - Modelos Pydantic para gestão de usuários
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import re


class PerfilTipo(str, Enum):
    """Tipos de perfil do usuário"""
    SUPERADMIN = "superadmin"
    PROPRIETARIO = "proprietario"
    GESTOR = "gestor"
    BENEFICIARIO = "beneficiario"
    USUARIO = "usuario"
    PARCEIRO = "parceiro"


# ========================
# Request Schemas
# ========================

class UsuarioCreateRequest(BaseModel):
    """Criar novo usuário (admin)"""
    nome_completo: str = Field(..., min_length=3, max_length=200)
    email: EmailStr
    cpf: str = Field(..., description="CPF no formato 000.000.000-00 ou 00000000000")
    telefone: Optional[str] = None
    is_superadmin: bool = False
    perfis: List[PerfilTipo] = [PerfilTipo.USUARIO]

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        cpf = re.sub(r'\D', '', v)
        if len(cpf) != 11:
            raise ValueError("CPF deve ter 11 dígitos")
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
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

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


class UsuarioUpdateRequest(BaseModel):
    """Atualizar usuário"""
    nome_completo: Optional[str] = Field(None, min_length=3, max_length=200)
    telefone: Optional[str] = None
    avatar_url: Optional[str] = None
    preferencias: Optional[dict] = None
    ativo: Optional[bool] = None

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


class PerfilUpdateRequest(BaseModel):
    """Atualizar perfis do usuário"""
    perfis: List[PerfilTipo]


class AtribuirPerfilRequest(BaseModel):
    """Atribuir perfil a usuário"""
    perfil: PerfilTipo
    dados_perfil: Optional[dict] = None


# ========================
# Response Schemas
# ========================

class PerfilUsuarioResponse(BaseModel):
    """Perfil do usuário"""
    id: int
    perfil: str
    ativo: bool
    dados_perfil: Optional[dict] = None
    criado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class UsuarioResponse(BaseModel):
    """Dados completos do usuário"""
    id: str  # UUID
    auth_id: Optional[str] = None
    nome_completo: str
    email: str
    cpf: Optional[str] = None
    telefone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_superadmin: bool = False
    ativo: bool = True
    email_verificado: bool = False
    perfis: List[str] = []
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None
    ultimo_acesso: Optional[datetime] = None

    class Config:
        from_attributes = True


class UsuarioListResponse(BaseModel):
    """Lista de usuários com paginação"""
    usuarios: List[UsuarioResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class UsuarioResumoResponse(BaseModel):
    """Resumo do usuário para listagens"""
    id: str
    nome_completo: str
    email: str
    ativo: bool
    perfis: List[str] = []

    class Config:
        from_attributes = True


# ========================
# Filtros
# ========================

class UsuarioFiltros(BaseModel):
    """Filtros para busca de usuários"""
    nome: Optional[str] = None
    email: Optional[str] = None
    cpf: Optional[str] = None
    perfil: Optional[PerfilTipo] = None
    ativo: Optional[bool] = None
    is_superadmin: Optional[bool] = None


# ========================
# Respostas genéricas
# ========================

class MessageResponse(BaseModel):
    """Resposta genérica com mensagem"""
    message: str
    success: bool = True
