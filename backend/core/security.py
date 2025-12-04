"""
Security - Autenticação e autorização com Supabase Auth
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import logging

from backend.config import settings
from backend.core.database import db_admin, get_supabase

logger = logging.getLogger(__name__)

# Security scheme para Swagger/OpenAPI
security = HTTPBearer(auto_error=False)


class UserToken(BaseModel):
    """Dados extraídos do token JWT do Supabase"""
    auth_id: str  # UUID do Supabase Auth (sub)
    email: str
    exp: int  # Timestamp de expiração
    iat: int  # Timestamp de criação


class CurrentUser(BaseModel):
    """Usuário atual com dados completos da tabela usuarios"""
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


def verify_supabase_token(token: str) -> UserToken:
    """
    Verifica e decodifica um token JWT do Supabase.
    Primeiro tenta validar via API do Supabase, depois tenta decodificação local.

    Args:
        token: Token JWT do Supabase

    Returns:
        UserToken com dados do token

    Raises:
        HTTPException: Se token inválido ou expirado
    """
    # Método 1: Validar via Supabase Auth API (mais confiável)
    try:
        supabase = get_supabase()
        user_response = supabase.auth.get_user(token)

        if user_response and user_response.user:
            user = user_response.user
            return UserToken(
                auth_id=user.id,
                email=user.email or "",
                exp=0,  # Não disponível via API
                iat=0   # Não disponível via API
            )
    except Exception as e:
        logger.debug(f"Supabase API validation failed: {e}, trying local decode")

    # Método 2: Fallback - Decodificação local do JWT
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False}
        )

        auth_id = payload.get("sub")
        email = payload.get("email")
        exp = payload.get("exp")
        iat = payload.get("iat")

        if not auth_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: auth_id não encontrado",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return UserToken(
            auth_id=auth_id,
            email=email or "",
            exp=exp or 0,
            iat=iat or 0
        )

    except JWTError as e:
        logger.warning(f"JWT decode failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_by_auth_id(auth_id: str) -> Optional[dict]:
    """
    Busca usuário na tabela usuarios pelo auth_id do Supabase.

    Args:
        auth_id: UUID do Supabase Auth

    Returns:
        Dict com dados do usuário ou None
    """
    try:
        result = db_admin.usuarios().select(
            "*",
            "perfis_usuario(perfil, ativo)"
        ).eq("auth_id", auth_id).maybe_single().execute()

        return result.data if result.data else None
    except Exception as e:
        # Se o erro for PGRST116 (nenhuma linha encontrada), retorna None
        error_str = str(e)
        if "PGRST116" in error_str or "0 rows" in error_str:
            return None
        raise


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    Dependency para obter o usuário atual a partir do token.

    Args:
        credentials: Credenciais HTTP Bearer

    Returns:
        CurrentUser com dados completos

    Raises:
        HTTPException: Se não autenticado ou usuário não encontrado
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verifica o token
    token_data = verify_supabase_token(credentials.credentials)

    # Busca usuário no banco
    user_data = await get_user_by_auth_id(token_data.auth_id)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado no sistema",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extrai perfis ativos
    perfis = []
    if user_data.get("perfis_usuario"):
        perfis = [
            p["perfil"] for p in user_data["perfis_usuario"]
            if p.get("ativo", True)
        ]

    return CurrentUser(
        id=user_data["id"],
        auth_id=user_data["auth_id"],
        nome_completo=user_data["nome_completo"],
        email=user_data["email"],
        cpf=user_data.get("cpf"),
        telefone=user_data.get("telefone"),
        is_superadmin=user_data.get("is_superadmin", False),
        ativo=user_data.get("ativo", True),
        email_verificado=user_data.get("email_verificado", False),
        perfis=perfis
    )


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Dependency para garantir que o usuário está ativo.

    Args:
        current_user: Usuário atual

    Returns:
        CurrentUser se ativo

    Raises:
        HTTPException: Se usuário inativo
    """
    if not current_user.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado"
        )
    return current_user


def require_perfil(*perfis_permitidos: str):
    """
    Cria uma dependency que verifica se o usuário tem um dos perfis permitidos.

    Args:
        perfis_permitidos: Lista de perfis que podem acessar

    Returns:
        Dependency function

    Usage:
        @router.get("/admin", dependencies=[Depends(require_perfil("superadmin", "gestor"))])
        async def admin_route():
            ...
    """
    async def verify_perfil(
        current_user: CurrentUser = Depends(get_current_active_user)
    ) -> CurrentUser:
        # Superadmin sempre tem acesso
        if current_user.is_superadmin:
            return current_user

        # Verifica se tem algum dos perfis permitidos
        if not any(perfil in current_user.perfis for perfil in perfis_permitidos):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Perfis permitidos: {', '.join(perfis_permitidos)}"
            )

        return current_user

    return verify_perfil


def require_superadmin():
    """
    Cria uma dependency que verifica se o usuário é superadmin.

    Returns:
        Dependency function
    """
    async def verify_superadmin(
        current_user: CurrentUser = Depends(get_current_active_user)
    ) -> CurrentUser:
        if not current_user.is_superadmin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso restrito a administradores"
            )
        return current_user

    return verify_superadmin


class OptionalAuth:
    """
    Classe para rotas que aceitam autenticação opcional.
    Útil para rotas que funcionam tanto para usuários logados quanto não logados.
    """

    async def __call__(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Optional[CurrentUser]:
        """
        Tenta obter o usuário atual, mas não falha se não autenticado.

        Returns:
            CurrentUser se autenticado, None caso contrário
        """
        if not credentials:
            return None

        try:
            token_data = verify_supabase_token(credentials.credentials)
            user_data = await get_user_by_auth_id(token_data.auth_id)

            if not user_data or not user_data.get("ativo", True):
                return None

            perfis = []
            if user_data.get("perfis_usuario"):
                perfis = [
                    p["perfil"] for p in user_data["perfis_usuario"]
                    if p.get("ativo", True)
                ]

            return CurrentUser(
                id=user_data["id"],
                auth_id=user_data["auth_id"],
                nome_completo=user_data["nome_completo"],
                email=user_data["email"],
                cpf=user_data.get("cpf"),
                telefone=user_data.get("telefone"),
                is_superadmin=user_data.get("is_superadmin", False),
                ativo=user_data.get("ativo", True),
                email_verificado=user_data.get("email_verificado", False),
                perfis=perfis
            )
        except HTTPException:
            return None


# Instância para uso em rotas com auth opcional
optional_auth = OptionalAuth()
