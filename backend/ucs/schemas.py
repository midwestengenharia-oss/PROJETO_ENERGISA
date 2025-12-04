"""
UCs Schemas - Modelos Pydantic para Unidades Consumidoras
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ========================
# Request Schemas
# ========================

class UCVincularRequest(BaseModel):
    """Vincular UC ao usuário"""
    cod_empresa: int = Field(default=6, description="Código da empresa (6=Energisa MT)")
    cdc: int = Field(..., description="Número da UC (CDC)")
    digito_verificador: int = Field(..., ge=0, le=9, description="Dígito verificador")
    usuario_titular: bool = Field(default=False, description="Se o usuário é o titular da UC")


class UCVincularPorFormatoRequest(BaseModel):
    """Vincular UC pelo formato de exibição"""
    uc_formatada: str = Field(..., description="UC no formato 6/4242904-3")
    usuario_titular: bool = Field(default=False)
    # Dados opcionais da Energisa para preencher automaticamente
    nome_titular: Optional[str] = None
    endereco: Optional[str] = None
    numero_imovel: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    classe_leitura: Optional[str] = None
    grupo_leitura: Optional[str] = None
    is_geradora: Optional[bool] = None  # Se geracaoDistribuida != null na Energisa

    @field_validator("uc_formatada")
    @classmethod
    def validate_formato(cls, v: str) -> str:
        import re
        # Aceita: cod_empresa/cdc-digito (digito pode ter 1 ou mais chars)
        pattern = r"^\d+/\d+-\d+$"
        if not re.match(pattern, v):
            raise ValueError("Formato inválido. Use: cod_empresa/cdc-digito (ex: 6/4242904-3)")
        return v


class UCUpdateRequest(BaseModel):
    """Atualizar dados da UC"""
    apelido: Optional[str] = Field(None, max_length=100, description="Apelido/nome personalizado da UC")
    nome_titular: Optional[str] = None
    endereco: Optional[str] = None
    numero_imovel: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = Field(None, max_length=2)
    cep: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None


class UCConfigGDRequest(BaseModel):
    """Configurar UC como geradora ou beneficiária de GD"""
    is_geradora: bool = Field(default=False, description="Se é uma UC geradora")
    geradora_id: Optional[int] = Field(None, description="ID da UC geradora (se beneficiária)")
    percentual_rateio: Optional[Decimal] = Field(None, ge=0, le=100, description="Percentual de rateio")


# ========================
# Response Schemas
# ========================

class UCResponse(BaseModel):
    """Dados completos da UC"""
    id: int
    usuario_id: str

    # Identificação
    cod_empresa: int
    cdc: int
    digito_verificador: int
    uc_formatada: Optional[str] = None  # Calculado: cod_empresa/cdc-digito
    apelido: Optional[str] = None  # Nome personalizado da UC

    # Titular
    cpf_cnpj_titular: Optional[str] = None
    nome_titular: Optional[str] = None
    usuario_titular: bool = False

    # Endereço
    endereco: Optional[str] = None
    numero_imovel: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    cep: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None

    # Dados técnicos
    tipo_ligacao: Optional[str] = None
    classe_leitura: Optional[str] = None
    grupo_leitura: Optional[str] = None
    numero_medidor: Optional[str] = None

    # Status
    uc_ativa: bool = True
    uc_cortada: bool = False
    contrato_ativo: bool = True
    baixa_renda: bool = False

    # GD
    is_geradora: bool = False
    geradora_id: Optional[int] = None
    percentual_rateio: Optional[Decimal] = None
    saldo_acumulado: int = 0

    # Sincronização
    ultima_sincronizacao: Optional[datetime] = None
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True

    def __init__(self, **data):
        super().__init__(**data)
        # Calcula uc_formatada
        if not self.uc_formatada:
            self.uc_formatada = f"{self.cod_empresa}/{self.cdc}-{self.digito_verificador}"


class UCListResponse(BaseModel):
    """Lista de UCs com paginação"""
    ucs: List[UCResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class UCResumoResponse(BaseModel):
    """Resumo da UC para listagens"""
    id: int
    uc_formatada: str
    apelido: Optional[str] = None
    nome_titular: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    is_geradora: bool = False
    uc_ativa: bool = True

    class Config:
        from_attributes = True


class UCComFaturasResponse(BaseModel):
    """UC com últimas faturas"""
    uc: UCResponse
    faturas: List["FaturaResumoResponse"] = []


class FaturaResumoResponse(BaseModel):
    """Resumo de fatura para listagem"""
    id: int
    mes_referencia: int
    ano_referencia: int
    valor_fatura: Decimal
    data_vencimento: datetime
    situacao_pagamento: Optional[str] = None


# ========================
# Filtros
# ========================

class UCFiltros(BaseModel):
    """Filtros para busca de UCs"""
    usuario_id: Optional[str] = None
    cdc: Optional[int] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    is_geradora: Optional[bool] = None
    uc_ativa: Optional[bool] = None
    usuario_titular: Optional[bool] = None


# ========================
# GD / Geração Distribuída
# ========================

class UCGDInfoResponse(BaseModel):
    """Informações de GD da UC"""
    uc_id: int
    uc_formatada: str
    is_geradora: bool
    saldo_acumulado: int
    beneficiarias: List["UCBeneficiariaResponse"] = []


class UCBeneficiariaResponse(BaseModel):
    """UC beneficiária de uma geradora"""
    id: int
    uc_formatada: str
    nome_titular: Optional[str] = None
    percentual_rateio: Optional[Decimal] = None


# ========================
# Histórico de GD
# ========================

class HistoricoGDResponse(BaseModel):
    """Registro mensal de histórico de GD"""
    id: int
    uc_id: int
    mes_referencia: int
    ano_referencia: int
    saldo_anterior_conv: Optional[int] = None
    injetado_conv: Optional[int] = None
    total_recebido_rede: Optional[int] = None
    consumo_recebido_conv: Optional[int] = None
    consumo_injetado_compensado: Optional[int] = None
    consumo_transferido_conv: Optional[int] = None
    consumo_compensado_conv: Optional[int] = None
    saldo_compensado_anterior: Optional[int] = None
    dados_api: Optional[dict] = None
    sincronizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class UCComGDResponse(BaseModel):
    """UC com dados completos de GD"""
    uc: UCResponse
    is_geradora: bool = False
    is_beneficiaria: bool = False
    tem_dados_gd: bool = False
    saldo_creditos: int = 0
    historico: List[HistoricoGDResponse] = []
    beneficiarias: List["UCBeneficiariaResponse"] = []
    geradora: Optional["UCBeneficiariaResponse"] = None
    percentual_rateio: Optional[Decimal] = None


class GDResumoResponse(BaseModel):
    """Resumo geral de GD do usuário"""
    total_ucs_com_gd: int = 0
    total_creditos: int = 0
    total_gerado_mes: int = 0
    total_compensado_mes: int = 0
    ucs: List[UCComGDResponse] = []


# ========================
# Respostas genéricas
# ========================

class MessageResponse(BaseModel):
    """Resposta genérica com mensagem"""
    message: str
    success: bool = True


# Resolve forward references
UCComFaturasResponse.model_rebuild()
UCGDInfoResponse.model_rebuild()
UCComGDResponse.model_rebuild()
