"""
Usinas Schemas - Modelos Pydantic para Usinas de Geração Distribuída
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class UsinaStatus(str, Enum):
    """Status da usina"""
    ATIVA = "ATIVA"
    INATIVA = "INATIVA"
    PENDENTE = "PENDENTE"


class TipoGeracao(str, Enum):
    """Tipo de geração"""
    SOLAR = "SOLAR"
    EOLICA = "EOLICA"
    HIDRICA = "HIDRICA"
    BIOMASSA = "BIOMASSA"


# ========================
# Request Schemas
# ========================

class UsinaCreateRequest(BaseModel):
    """Criar nova usina"""
    nome: str = Field(..., min_length=3, max_length=200)
    uc_geradora_id: int = Field(..., description="ID da UC geradora")
    empresa_id: Optional[int] = Field(None, description="ID da empresa proprietária")
    capacidade_kwp: Optional[Decimal] = Field(None, ge=0, description="Capacidade em kWp")
    tipo_geracao: TipoGeracao = TipoGeracao.SOLAR
    data_conexao: Optional[date] = None
    desconto_padrao: Decimal = Field(default=Decimal("0.30"), ge=0, le=1, description="Desconto padrão (0-1)")
    endereco: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None


class UsinaUpdateRequest(BaseModel):
    """Atualizar usina"""
    nome: Optional[str] = Field(None, min_length=3, max_length=200)
    capacidade_kwp: Optional[Decimal] = Field(None, ge=0)
    tipo_geracao: Optional[TipoGeracao] = None
    data_conexao: Optional[date] = None
    desconto_padrao: Optional[Decimal] = Field(None, ge=0, le=1)
    status: Optional[UsinaStatus] = None
    endereco: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None


class GestorUsinaRequest(BaseModel):
    """Adicionar gestor à usina"""
    gestor_id: str = Field(..., description="ID do usuário gestor")
    comissao_percentual: Decimal = Field(default=Decimal("0"), ge=0, le=1)


class RateioRequest(BaseModel):
    """Configurar rateio de beneficiários"""
    beneficiarios: List["RateioBeneficiarioRequest"]


class RateioBeneficiarioRequest(BaseModel):
    """Configuração de rateio por beneficiário"""
    beneficiario_id: int
    percentual: Decimal = Field(..., ge=0, le=100, description="Percentual do rateio (0-100)")


# ========================
# Response Schemas
# ========================

class EmpresaResumoResponse(BaseModel):
    """Resumo da empresa"""
    id: int
    cnpj: Optional[str] = None
    razao_social: Optional[str] = None
    nome_fantasia: Optional[str] = None

    class Config:
        from_attributes = True


class UCResumoResponse(BaseModel):
    """Resumo da UC geradora"""
    id: int
    uc_formatada: str
    nome_titular: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    saldo_acumulado: int = 0

    class Config:
        from_attributes = True


class GestorUsinaResponse(BaseModel):
    """Gestor da usina"""
    id: int
    gestor_id: str
    nome_gestor: Optional[str] = None
    email_gestor: Optional[str] = None
    comissao_percentual: Decimal
    ativo: bool
    criado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class BeneficiarioResumoResponse(BaseModel):
    """Resumo do beneficiário"""
    id: int
    cpf: str
    nome: Optional[str] = None
    email: Optional[str] = None
    percentual_rateio: Decimal
    desconto: Decimal
    status: str
    uc_formatada: Optional[str] = None

    class Config:
        from_attributes = True


class UsinaResponse(BaseModel):
    """Dados completos da usina"""
    id: int
    nome: str
    empresa_id: Optional[int] = None
    uc_geradora_id: int
    capacidade_kwp: Optional[Decimal] = None
    tipo_geracao: str = "SOLAR"
    data_conexao: Optional[date] = None
    desconto_padrao: Decimal = Decimal("0.30")
    status: str = "ATIVA"
    endereco: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    # Relacionamentos
    empresa: Optional[EmpresaResumoResponse] = None
    uc_geradora: Optional[UCResumoResponse] = None
    gestores: List[GestorUsinaResponse] = []
    beneficiarios: List[BeneficiarioResumoResponse] = []

    # Métricas
    total_beneficiarios: int = 0
    total_gestores: int = 0
    percentual_rateio_alocado: Decimal = Decimal("0")

    class Config:
        from_attributes = True


class UsinaListResponse(BaseModel):
    """Lista de usinas com paginação"""
    usinas: List[UsinaResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class UsinaResumoResponse(BaseModel):
    """Resumo da usina para listagens"""
    id: int
    nome: str
    capacidade_kwp: Optional[Decimal] = None
    status: str
    total_beneficiarios: int = 0
    uc_formatada: Optional[str] = None

    class Config:
        from_attributes = True


# ========================
# Filtros
# ========================

class UsinaFiltros(BaseModel):
    """Filtros para busca de usinas"""
    nome: Optional[str] = None
    empresa_id: Optional[int] = None
    status: Optional[UsinaStatus] = None
    tipo_geracao: Optional[TipoGeracao] = None
    gestor_id: Optional[str] = None


# ========================
# Respostas genéricas
# ========================

class MessageResponse(BaseModel):
    """Resposta genérica com mensagem"""
    message: str
    success: bool = True


# Resolve forward references
RateioRequest.model_rebuild()
