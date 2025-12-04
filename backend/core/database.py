"""
Database - Conexão com Supabase
"""

from supabase import create_client, Client
from functools import lru_cache
from typing import Optional

from backend.config import settings


@lru_cache()
def get_supabase() -> Client:
    """
    Retorna cliente Supabase com chave anônima (para operações de usuário).
    Usa cache para manter uma única instância.
    """
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY
    )


@lru_cache()
def get_supabase_admin() -> Client:
    """
    Retorna cliente Supabase com service_role key (para operações administrativas).
    ATENÇÃO: Usar apenas no backend, nunca expor ao frontend.
    Bypass das políticas RLS.
    """
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY
    )


class SupabaseClient:
    """
    Classe wrapper para operações com Supabase.
    Facilita o uso e adiciona métodos utilitários.
    """

    def __init__(self, admin: bool = False):
        """
        Inicializa cliente Supabase.

        Args:
            admin: Se True, usa service_role key (bypass RLS)
        """
        self._client = get_supabase_admin() if admin else get_supabase()
        self._admin = admin

    @property
    def client(self) -> Client:
        """Retorna o cliente Supabase"""
        return self._client

    @property
    def auth(self):
        """Acesso ao módulo de autenticação"""
        return self._client.auth

    def table(self, name: str):
        """
        Acesso a uma tabela específica.

        Args:
            name: Nome da tabela

        Returns:
            QueryBuilder para a tabela
        """
        return self._client.table(name)

    def rpc(self, fn: str, params: Optional[dict] = None):
        """
        Chama uma função RPC (stored procedure) no Supabase.

        Args:
            fn: Nome da função
            params: Parâmetros da função

        Returns:
            Resultado da função
        """
        return self._client.rpc(fn, params or {})

    def storage(self):
        """Acesso ao módulo de storage"""
        return self._client.storage

    # ========================
    # Métodos utilitários para tabelas comuns
    # ========================

    def usuarios(self):
        """Acesso à tabela usuarios"""
        return self.table("usuarios")

    def perfis_usuario(self):
        """Acesso à tabela perfis_usuario"""
        return self.table("perfis_usuario")

    def unidades_consumidoras(self):
        """Acesso à tabela unidades_consumidoras"""
        return self.table("unidades_consumidoras")

    def usinas(self):
        """Acesso à tabela usinas"""
        return self.table("usinas")

    def beneficiarios(self):
        """Acesso à tabela beneficiarios"""
        return self.table("beneficiarios")

    def faturas(self):
        """Acesso à tabela faturas"""
        return self.table("faturas")

    def cobrancas(self):
        """Acesso à tabela cobrancas"""
        return self.table("cobrancas")

    def contratos(self):
        """Acesso à tabela contratos"""
        return self.table("contratos")

    def saques(self):
        """Acesso à tabela saques"""
        return self.table("saques")

    def leads(self):
        """Acesso à tabela leads"""
        return self.table("leads")

    def notificacoes(self):
        """Acesso à tabela notificacoes"""
        return self.table("notificacoes")

    def tokens_energisa(self):
        """Acesso à tabela tokens_energisa"""
        return self.table("tokens_energisa")

    def config_plataforma(self):
        """Acesso à tabela config_plataforma"""
        return self.table("config_plataforma")

    # ========================
    # Métodos utilitários
    # ========================

    async def get_config(self, chave: str) -> Optional[str]:
        """
        Busca uma configuração da plataforma.

        Args:
            chave: Chave da configuração

        Returns:
            Valor da configuração ou None
        """
        result = self.config_plataforma().select("valor").eq("chave", chave).single().execute()
        if result.data:
            return result.data.get("valor")
        return None

    async def set_config(self, chave: str, valor: str) -> bool:
        """
        Define uma configuração da plataforma.

        Args:
            chave: Chave da configuração
            valor: Novo valor

        Returns:
            True se sucesso
        """
        result = self.config_plataforma().upsert({
            "chave": chave,
            "valor": valor
        }).execute()
        return bool(result.data)


# Instâncias globais para uso direto
db = SupabaseClient(admin=False)
db_admin = SupabaseClient(admin=True)
