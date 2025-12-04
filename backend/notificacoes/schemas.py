"""
Notificações Schemas - Modelos Pydantic para Notificações
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TipoNotificacao(str, Enum):
    """Tipos de notificação"""
    INFO = "INFO"
    SUCESSO = "SUCESSO"
    AVISO = "AVISO"
    ERRO = "ERRO"
    COBRANCA = "COBRANCA"
    FATURA = "FATURA"
    CONTRATO = "CONTRATO"
    SISTEMA = "SISTEMA"


class CanalNotificacao(str, Enum):
    """Canais de envio"""
    APP = "APP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
    PUSH = "PUSH"


# ========================
# Request Schemas
# ========================

class NotificacaoCreateRequest(BaseModel):
    """Criar nova notificação"""
    usuario_id: str = Field(..., description="ID do usuário destinatário")
    tipo: TipoNotificacao = Field(default=TipoNotificacao.INFO)
    titulo: str = Field(..., min_length=3, max_length=100)
    mensagem: str = Field(..., min_length=5, max_length=500)
    link: Optional[str] = None
    dados: Optional[Dict[str, Any]] = None
    canais: List[CanalNotificacao] = Field(default=[CanalNotificacao.APP])


class NotificacaoLoteRequest(BaseModel):
    """Enviar notificação em lote"""
    usuario_ids: Optional[List[str]] = None
    perfis: Optional[List[str]] = None  # Enviar para todos com determinado perfil
    usina_id: Optional[int] = None  # Enviar para todos de uma usina
    tipo: TipoNotificacao = Field(default=TipoNotificacao.INFO)
    titulo: str = Field(..., min_length=3, max_length=100)
    mensagem: str = Field(..., min_length=5, max_length=500)
    link: Optional[str] = None
    canais: List[CanalNotificacao] = Field(default=[CanalNotificacao.APP])


class PreferenciaNotificacaoRequest(BaseModel):
    """Atualizar preferências de notificação"""
    email_cobrancas: Optional[bool] = None
    email_faturas: Optional[bool] = None
    email_contratos: Optional[bool] = None
    email_marketing: Optional[bool] = None
    sms_cobrancas: Optional[bool] = None
    sms_faturas: Optional[bool] = None
    whatsapp_cobrancas: Optional[bool] = None
    whatsapp_faturas: Optional[bool] = None
    push_habilitado: Optional[bool] = None


# ========================
# Response Schemas
# ========================

class NotificacaoResponse(BaseModel):
    """Dados completos da notificação"""
    id: int
    usuario_id: str
    tipo: str
    titulo: str
    mensagem: str
    link: Optional[str] = None
    dados: Optional[Dict[str, Any]] = None

    # Status
    lida: bool = False
    lida_em: Optional[datetime] = None

    # Canais
    enviado_app: bool = False
    enviado_email: bool = False
    enviado_sms: bool = False
    enviado_whatsapp: bool = False
    enviado_push: bool = False

    # Timestamps
    criado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificacaoResumoResponse(BaseModel):
    """Resumo da notificação para listagens"""
    id: int
    tipo: str
    titulo: str
    lida: bool
    criado_em: datetime

    class Config:
        from_attributes = True


class NotificacaoListResponse(BaseModel):
    """Lista de notificações com paginação"""
    notificacoes: List[NotificacaoResponse]
    total: int
    nao_lidas: int
    page: int
    per_page: int
    total_pages: int


class PreferenciasNotificacaoResponse(BaseModel):
    """Preferências de notificação do usuário"""
    usuario_id: str
    email_cobrancas: bool = True
    email_faturas: bool = True
    email_contratos: bool = True
    email_marketing: bool = False
    sms_cobrancas: bool = True
    sms_faturas: bool = False
    whatsapp_cobrancas: bool = True
    whatsapp_faturas: bool = True
    push_habilitado: bool = True

    class Config:
        from_attributes = True


# ========================
# Templates
# ========================

class TemplateNotificacaoResponse(BaseModel):
    """Template de notificação"""
    id: int
    codigo: str
    tipo: str
    titulo_template: str
    mensagem_template: str
    canais_padrao: List[str]
    ativo: bool

    class Config:
        from_attributes = True


# ========================
# Estatísticas
# ========================

class EstatisticasNotificacaoResponse(BaseModel):
    """Estatísticas de notificações"""
    total_enviadas: int
    total_lidas: int
    taxa_leitura: float
    por_tipo: List[Dict[str, Any]]
    por_canal: List[Dict[str, Any]]


# ========================
# Respostas genéricas
# ========================

class MessageResponse(BaseModel):
    """Resposta genérica com mensagem"""
    message: str
    success: bool = True


class ContadorNotificacoesResponse(BaseModel):
    """Contador de notificações não lidas"""
    nao_lidas: int
