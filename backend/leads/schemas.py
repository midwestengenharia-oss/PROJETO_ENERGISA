"""
Leads Schemas - Modelos Pydantic para Leads/Simulações
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import re


class StatusLead(str, Enum):
    """Status possíveis de um lead"""
    NOVO = "NOVO"
    SIMULACAO = "SIMULACAO"
    CONTATO = "CONTATO"
    NEGOCIACAO = "NEGOCIACAO"
    CONVERTIDO = "CONVERTIDO"
    PERDIDO = "PERDIDO"


class OrigemLead(str, Enum):
    """Origem do lead"""
    LANDING_PAGE = "LANDING_PAGE"
    INDICACAO = "INDICACAO"
    GOOGLE_ADS = "GOOGLE_ADS"
    FACEBOOK = "FACEBOOK"
    INSTAGRAM = "INSTAGRAM"
    WHATSAPP = "WHATSAPP"
    TELEFONE = "TELEFONE"
    OUTROS = "OUTROS"


# ========================
# Request Schemas
# ========================

class LeadCreateRequest(BaseModel):
    """Criar novo lead (landing page)"""
    nome: str = Field(..., min_length=3, max_length=100)
    email: Optional[str] = None
    telefone: Optional[str] = None
    cpf: str = Field(..., min_length=11, max_length=14)
    cidade: Optional[str] = None
    uf: Optional[str] = Field(None, max_length=2)
    origem: OrigemLead = Field(default=OrigemLead.LANDING_PAGE)
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, v):
        cpf = re.sub(r"\D", "", v)
        if len(cpf) != 11:
            raise ValueError("CPF deve ter 11 dígitos")

        # Verifica se todos os dígitos são iguais (CPF inválido)
        if cpf == cpf[0] * 11:
            raise ValueError("CPF inválido")

        # Calcula primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto

        if int(cpf[9]) != digito1:
            raise ValueError("CPF inválido")

        # Calcula segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto

        if int(cpf[10]) != digito2:
            raise ValueError("CPF inválido")

        return v


class LeadSimulacaoRequest(BaseModel):
    """Dados da simulação do lead"""
    lead_id: int
    valor_fatura_media: Decimal = Field(..., gt=0)
    consumo_medio_kwh: Optional[int] = None
    quantidade_ucs: int = Field(default=1, ge=1)


class LeadContatoRequest(BaseModel):
    """Registrar contato com lead"""
    lead_id: int
    tipo_contato: str = Field(..., description="whatsapp, telefone, email")
    descricao: str = Field(..., min_length=10)
    proximo_contato: Optional[datetime] = None


class LeadUpdateRequest(BaseModel):
    """Atualizar lead"""
    nome: Optional[str] = Field(None, min_length=3, max_length=100)
    email: Optional[str] = None
    telefone: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = Field(None, max_length=2)
    status: Optional[StatusLead] = None
    observacoes: Optional[str] = None
    responsavel_id: Optional[str] = None


class LeadConverterRequest(BaseModel):
    """Converter lead em beneficiário"""
    lead_id: int
    usina_id: int
    desconto_percentual: Decimal = Field(..., ge=0, le=1)
    percentual_rateio: Optional[Decimal] = Field(None, ge=0, le=100)


# ========================
# Response Schemas
# ========================

class SimulacaoResponse(BaseModel):
    """Resultado da simulação"""
    id: int
    lead_id: int
    valor_fatura_media: Decimal
    consumo_medio_kwh: Optional[int] = None
    quantidade_ucs: int

    # Economia calculada
    desconto_aplicado: Decimal
    economia_mensal: Decimal
    economia_anual: Decimal
    percentual_economia: Decimal

    criado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContatoResponse(BaseModel):
    """Registro de contato"""
    id: int
    lead_id: int
    tipo_contato: str
    descricao: str
    proximo_contato: Optional[datetime] = None
    realizado_por: Optional[str] = None
    criado_em: datetime

    class Config:
        from_attributes = True


class LeadResponse(BaseModel):
    """Dados completos do lead"""
    id: int
    nome: str
    email: Optional[str] = None
    telefone: Optional[str] = None
    cpf: str
    cidade: Optional[str] = None
    uf: Optional[str] = None

    # Status e origem
    status: str
    origem: str

    # UTM
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None

    # Responsável
    responsavel_id: Optional[str] = None
    responsavel_nome: Optional[str] = None

    # Observações
    observacoes: Optional[str] = None

    # Conversão
    convertido_em: Optional[datetime] = None
    beneficiario_id: Optional[int] = None

    # Timestamps
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    # Relacionamentos
    simulacoes: Optional[List[SimulacaoResponse]] = None
    contatos: Optional[List[ContatoResponse]] = None

    class Config:
        from_attributes = True


class LeadResumoResponse(BaseModel):
    """Resumo do lead para listagens"""
    id: int
    nome: str
    telefone: Optional[str] = None
    cidade: Optional[str] = None
    status: str
    origem: str
    criado_em: datetime

    class Config:
        from_attributes = True


class LeadListResponse(BaseModel):
    """Lista de leads com paginação"""
    leads: List[LeadResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# ========================
# Estatísticas
# ========================

class EstatisticasLeadResponse(BaseModel):
    """Estatísticas de leads"""
    total_leads: int
    leads_novos: int
    leads_em_contato: int
    leads_convertidos: int
    leads_perdidos: int
    taxa_conversao: Decimal
    economia_total_simulada: Decimal

    por_origem: List[Dict[str, Any]]
    por_status: List[Dict[str, Any]]


class FunilLeadResponse(BaseModel):
    """Funil de vendas"""
    etapas: List[Dict[str, Any]]
    total: int
    taxa_conversao_geral: Decimal


# ========================
# Respostas genéricas
# ========================

class MessageResponse(BaseModel):
    """Resposta genérica com mensagem"""
    message: str
    success: bool = True
