"""
Contratos Schemas - Modelos Pydantic para Contratos
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class StatusContrato(str, Enum):
    """Status possíveis de um contrato"""
    RASCUNHO = "RASCUNHO"
    AGUARDANDO_ASSINATURA = "AGUARDANDO_ASSINATURA"
    ATIVO = "ATIVO"
    SUSPENSO = "SUSPENSO"
    CANCELADO = "CANCELADO"
    ENCERRADO = "ENCERRADO"


class TipoContrato(str, Enum):
    """Tipos de contrato"""
    BENEFICIO_GD = "BENEFICIO_GD"
    GESTAO_USINA = "GESTAO_USINA"
    PARCERIA = "PARCERIA"
    OUTROS = "OUTROS"


# ========================
# Request Schemas
# ========================

class ContratoCreateRequest(BaseModel):
    """Criar novo contrato"""
    tipo: TipoContrato = Field(default=TipoContrato.BENEFICIO_GD)
    beneficiario_id: Optional[int] = None
    usina_id: Optional[int] = None
    parceiro_id: Optional[str] = None

    # Termos
    desconto_percentual: Decimal = Field(..., ge=0, le=1, description="Desconto (0.30 = 30%)")
    taxa_administrativa: Optional[Decimal] = Field(None, ge=0, le=1)
    prazo_meses: int = Field(default=12, ge=1, le=120)
    data_inicio: date
    data_fim: Optional[date] = None

    # Valores
    valor_adesao: Optional[Decimal] = Field(None, ge=0)
    multa_rescisao: Optional[Decimal] = Field(None, ge=0)

    # Documento
    clausulas: Optional[str] = None
    observacoes: Optional[str] = None


class ContratoUpdateRequest(BaseModel):
    """Atualizar contrato"""
    desconto_percentual: Optional[Decimal] = Field(None, ge=0, le=1)
    taxa_administrativa: Optional[Decimal] = Field(None, ge=0, le=1)
    prazo_meses: Optional[int] = Field(None, ge=1, le=120)
    data_fim: Optional[date] = None
    status: Optional[StatusContrato] = None
    clausulas: Optional[str] = None
    observacoes: Optional[str] = None


class ContratoAssinarRequest(BaseModel):
    """Assinar contrato"""
    ip_assinatura: Optional[str] = None
    dispositivo: Optional[str] = None
    aceite_termos: bool = Field(..., description="Aceite dos termos do contrato")


class ContratoRescindirRequest(BaseModel):
    """Rescindir contrato"""
    motivo: str = Field(..., min_length=10)
    data_rescisao: date
    aplicar_multa: bool = False


# ========================
# Response Schemas
# ========================

class BeneficiarioContratoResponse(BaseModel):
    """Beneficiário resumido para contrato"""
    id: int
    nome: Optional[str] = None
    cpf: str
    email: Optional[str] = None

    class Config:
        from_attributes = True


class UsinaContratoResponse(BaseModel):
    """Usina resumida para contrato"""
    id: int
    nome: str
    capacidade_kwp: Optional[Decimal] = None

    class Config:
        from_attributes = True


class ContratoResponse(BaseModel):
    """Dados completos do contrato"""
    id: int
    tipo: str
    numero_contrato: Optional[str] = None

    # Partes
    beneficiario_id: Optional[int] = None
    usina_id: Optional[int] = None
    parceiro_id: Optional[str] = None

    # Termos
    desconto_percentual: Decimal
    taxa_administrativa: Optional[Decimal] = None
    prazo_meses: int
    data_inicio: date
    data_fim: Optional[date] = None

    # Valores
    valor_adesao: Optional[Decimal] = None
    multa_rescisao: Optional[Decimal] = None

    # Status
    status: str
    data_assinatura: Optional[datetime] = None
    ip_assinatura: Optional[str] = None
    assinatura_hash: Optional[str] = None

    # Documento
    clausulas: Optional[str] = None
    observacoes: Optional[str] = None
    pdf_path: Optional[str] = None

    # Timestamps
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    # Relacionamentos
    beneficiario: Optional[BeneficiarioContratoResponse] = None
    usina: Optional[UsinaContratoResponse] = None

    class Config:
        from_attributes = True


class ContratoResumoResponse(BaseModel):
    """Resumo do contrato para listagens"""
    id: int
    numero_contrato: Optional[str] = None
    tipo: str
    beneficiario_nome: Optional[str] = None
    usina_nome: Optional[str] = None
    desconto_percentual: Decimal
    status: str
    data_inicio: date
    data_fim: Optional[date] = None

    class Config:
        from_attributes = True


class ContratoListResponse(BaseModel):
    """Lista de contratos com paginação"""
    contratos: List[ContratoResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# ========================
# Estatísticas
# ========================

class EstatisticasContratoResponse(BaseModel):
    """Estatísticas de contratos"""
    total_contratos: int
    contratos_ativos: int
    contratos_aguardando: int
    contratos_cancelados: int
    valor_total_adesao: Decimal
    desconto_medio: Decimal


# ========================
# Histórico
# ========================

class HistoricoContratoResponse(BaseModel):
    """Histórico de alterações do contrato"""
    id: int
    contrato_id: int
    acao: str
    descricao: str
    usuario_id: str
    criado_em: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Resposta genérica com mensagem"""
    message: str
    success: bool = True
