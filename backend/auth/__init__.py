"""
Auth - Módulo de autenticação com Supabase Auth
"""

from backend.auth.router import router
from backend.auth.service import auth_service
from backend.auth.schemas import (
    SignUpRequest,
    SignInRequest,
    UserResponse,
    AuthTokens,
)

__all__ = [
    "router",
    "auth_service",
    "SignUpRequest",
    "SignInRequest",
    "UserResponse",
    "AuthTokens",
]
