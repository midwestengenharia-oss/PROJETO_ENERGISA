"""
Admin Schemas - Modelos Pydantic para Administração
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal


# ========================
# Dashboard
# ========================

class DashboardStatsResponse(BaseModel):
    """Estatísticas gerais do dashboard"""
    # Usuários
    total_usuarios: int
    usuarios_ativos: int
    novos_usuarios_mes: int

    # Usinas
    total_usinas: int
    usinas_ativas: int
    capacidade_total_kwp: Decimal

    # Beneficiários
    total_beneficiarios: int
    beneficiarios_ativos: int
    novos_beneficiarios_mes: int

    # UCs
    total_ucs: int
    ucs_geradoras: int
    ucs_beneficiarias: int

    # Financeiro
    valor_total_cobrancas_mes: Decimal
    valor_recebido_mes: Decimal
    valor_pendente_mes: Decimal
    taxa_inadimplencia: Decimal


class DashboardGraficoRequest(BaseModel):
    """Parâmetros para gráficos do dashboard"""
    tipo: str = Field(..., description="Tipo do gráfico: cobrancas, usuarios, energia")
    periodo: str = Field(default="12m", description="Período: 6m, 12m, 24m")
    usina_id: Optional[int] = None


class DashboardGraficoResponse(BaseModel):
    """Dados para gráfico"""
    labels: List[str]
    datasets: List[Dict[str, Any]]


# ========================
# Configurações
# ========================

class ConfiguracaoSistemaResponse(BaseModel):
    """Configurações do sistema"""
    id: int
    chave: str
    valor: str
    descricao: Optional[str] = None
    tipo: str  # string, number, boolean, json
    editavel: bool
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConfiguracaoUpdateRequest(BaseModel):
    """Atualizar configuração"""
    valor: str


class TaxasConfiguracao(BaseModel):
    """Taxas configuráveis"""
    taxa_administrativa_padrao: Decimal = Field(ge=0, le=1)
    desconto_padrao: Decimal = Field(ge=0, le=1)
    valor_minimo_saque: Decimal = Field(ge=0)
    taxa_transferencia: Decimal = Field(ge=0, le=1)


# ========================
# Logs e Auditoria
# ========================

class LogAuditoriaResponse(BaseModel):
    """Log de auditoria"""
    id: int
    usuario_id: str
    usuario_nome: Optional[str] = None
    acao: str
    entidade: str
    entidade_id: Optional[str] = None
    dados_anteriores: Optional[Dict[str, Any]] = None
    dados_novos: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    criado_em: datetime

    class Config:
        from_attributes = True


class LogAuditoriaListResponse(BaseModel):
    """Lista de logs de auditoria"""
    logs: List[LogAuditoriaResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


# ========================
# Relatórios
# ========================

class RelatorioRequest(BaseModel):
    """Parâmetros para geração de relatório"""
    tipo: str = Field(..., description="Tipo: financeiro, usuarios, usinas, beneficiarios")
    data_inicio: date
    data_fim: date
    usina_id: Optional[int] = None
    formato: str = Field(default="json", pattern="^(json|csv|pdf|xlsx)$")
    filtros: Optional[Dict[str, Any]] = None


class RelatorioResponse(BaseModel):
    """Resposta de relatório"""
    tipo: str
    periodo: str
    gerado_em: datetime
    dados: Dict[str, Any]
    total_registros: int


class RelatorioFinanceiroResponse(BaseModel):
    """Relatório financeiro"""
    periodo: str
    total_cobrancas: int
    valor_total: Decimal
    valor_recebido: Decimal
    valor_pendente: Decimal
    por_usina: List[Dict[str, Any]]
    por_mes: List[Dict[str, Any]]


# ========================
# Backup e Manutenção
# ========================

class BackupResponse(BaseModel):
    """Informações de backup"""
    id: int
    tipo: str  # completo, incremental
    status: str  # em_progresso, concluido, falha
    tamanho_bytes: Optional[int] = None
    arquivo_path: Optional[str] = None
    iniciado_em: datetime
    concluido_em: Optional[datetime] = None
    erro: Optional[str] = None

    class Config:
        from_attributes = True


class ManutencaoStatusResponse(BaseModel):
    """Status de manutenção do sistema"""
    manutencao_ativa: bool
    mensagem: Optional[str] = None
    previsao_termino: Optional[datetime] = None
    permitir_admins: bool


class ManutencaoRequest(BaseModel):
    """Ativar/desativar manutenção"""
    ativar: bool
    mensagem: Optional[str] = None
    previsao_termino: Optional[datetime] = None
    permitir_admins: bool = True


# ========================
# Integrações
# ========================

class IntegracaoStatusResponse(BaseModel):
    """Status de integração externa"""
    nome: str
    status: str  # online, offline, erro
    ultima_verificacao: datetime
    ultima_sincronizacao: Optional[datetime] = None
    mensagem: Optional[str] = None


class IntegracoesSistemaResponse(BaseModel):
    """Status de todas as integrações"""
    supabase: IntegracaoStatusResponse
    energisa: IntegracaoStatusResponse
    email: IntegracaoStatusResponse


# ========================
# Jobs e Tarefas
# ========================

class JobResponse(BaseModel):
    """Status de um job/tarefa"""
    id: str
    nome: str
    status: str  # pendente, executando, concluido, falha
    progresso: Optional[int] = None  # 0-100
    mensagem: Optional[str] = None
    iniciado_em: Optional[datetime] = None
    concluido_em: Optional[datetime] = None
    resultado: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Lista de jobs"""
    jobs: List[JobResponse]
    total: int


# ========================
# Respostas genéricas
# ========================

class MessageResponse(BaseModel):
    """Resposta genérica com mensagem"""
    message: str
    success: bool = True
