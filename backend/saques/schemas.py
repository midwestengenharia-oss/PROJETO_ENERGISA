"""
Saques Schemas - Modelos Pydantic para Saques/Comissões
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class StatusSaque(str, Enum):
    """Status possíveis de um saque"""
    PENDENTE = "PENDENTE"
    APROVADO = "APROVADO"
    PROCESSANDO = "PROCESSANDO"
    PAGO = "PAGO"
    REJEITADO = "REJEITADO"
    CANCELADO = "CANCELADO"


class TipoSaque(str, Enum):
    """Tipos de saque"""
    COMISSAO_GESTOR = "COMISSAO_GESTOR"
    COMISSAO_PARCEIRO = "COMISSAO_PARCEIRO"
    BONIFICACAO = "BONIFICACAO"
    OUTROS = "OUTROS"


class TipoConta(str, Enum):
    """Tipos de conta bancária"""
    CORRENTE = "CORRENTE"
    POUPANCA = "POUPANCA"
    PIX = "PIX"


# ========================
# Request Schemas
# ========================

class DadosBancariosRequest(BaseModel):
    """Dados bancários para saque"""
    tipo_conta: TipoConta
    banco: str = Field(..., min_length=3)
    agencia: str = Field(..., min_length=4)
    conta: str = Field(..., min_length=4)
    digito: Optional[str] = None
    pix_chave: Optional[str] = None
    pix_tipo: Optional[str] = None  # cpf, cnpj, email, telefone, aleatoria
    titular_nome: str = Field(..., min_length=3)
    titular_cpf_cnpj: str


class SaqueCreateRequest(BaseModel):
    """Solicitar novo saque"""
    tipo: TipoSaque = Field(default=TipoSaque.COMISSAO_GESTOR)
    valor: Decimal = Field(..., gt=0, description="Valor do saque")
    dados_bancarios: DadosBancariosRequest
    observacoes: Optional[str] = None


class SaqueAprovarRequest(BaseModel):
    """Aprovar saque"""
    observacoes: Optional[str] = None


class SaqueRejeitarRequest(BaseModel):
    """Rejeitar saque"""
    motivo: str = Field(..., min_length=10)


class SaquePagarRequest(BaseModel):
    """Registrar pagamento do saque"""
    data_pagamento: date
    comprovante_url: Optional[str] = None
    numero_transacao: Optional[str] = None
    observacoes: Optional[str] = None


# ========================
# Response Schemas
# ========================

class DadosBancariosResponse(BaseModel):
    """Dados bancários do saque"""
    tipo_conta: str
    banco: str
    agencia: str
    conta: str
    digito: Optional[str] = None
    pix_chave: Optional[str] = None
    pix_tipo: Optional[str] = None
    titular_nome: str
    titular_cpf_cnpj: str

    class Config:
        from_attributes = True


class SolicitanteResponse(BaseModel):
    """Dados do solicitante do saque"""
    id: str
    nome_completo: str
    email: str
    cpf: Optional[str] = None

    class Config:
        from_attributes = True


class SaqueResponse(BaseModel):
    """Dados completos do saque"""
    id: int
    tipo: str
    solicitante_id: str

    # Valores
    valor: Decimal
    taxa_transferencia: Optional[Decimal] = None
    valor_liquido: Optional[Decimal] = None

    # Status
    status: str
    data_solicitacao: datetime
    data_aprovacao: Optional[datetime] = None
    data_pagamento: Optional[date] = None

    # Dados bancários
    dados_bancarios: Optional[DadosBancariosResponse] = None

    # Comprovante
    comprovante_url: Optional[str] = None
    numero_transacao: Optional[str] = None

    # Observações
    observacoes: Optional[str] = None
    motivo_rejeicao: Optional[str] = None

    # Aprovação
    aprovado_por: Optional[str] = None

    # Timestamps
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    # Relacionamentos
    solicitante: Optional[SolicitanteResponse] = None

    class Config:
        from_attributes = True


class SaqueResumoResponse(BaseModel):
    """Resumo do saque para listagens"""
    id: int
    tipo: str
    solicitante_nome: str
    valor: Decimal
    status: str
    data_solicitacao: datetime

    class Config:
        from_attributes = True


class SaqueListResponse(BaseModel):
    """Lista de saques com paginação"""
    saques: List[SaqueResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# ========================
# Saldo e Comissões
# ========================

class SaldoComissaoResponse(BaseModel):
    """Saldo de comissões do usuário"""
    saldo_disponivel: Decimal
    saldo_pendente: Decimal
    total_recebido: Decimal
    ultimo_saque: Optional[date] = None


class ComissaoResponse(BaseModel):
    """Detalhes de uma comissão"""
    id: int
    tipo: str
    usina_id: Optional[int] = None
    usina_nome: Optional[str] = None
    mes_referencia: int
    ano_referencia: int
    valor_base: Decimal
    percentual_comissao: Decimal
    valor_comissao: Decimal
    status: str
    data_geracao: datetime

    class Config:
        from_attributes = True


class ComissaoListResponse(BaseModel):
    """Lista de comissões"""
    comissoes: List[ComissaoResponse]
    total: int
    saldo_disponivel: Decimal


# ========================
# Estatísticas
# ========================

class EstatisticasSaqueResponse(BaseModel):
    """Estatísticas de saques"""
    total_saques: int
    valor_total_solicitado: Decimal
    valor_total_pago: Decimal
    saques_pendentes: int
    saques_aprovados: int
    saques_pagos: int
    saques_rejeitados: int


class MessageResponse(BaseModel):
    """Resposta genérica com mensagem"""
    message: str
    success: bool = True
