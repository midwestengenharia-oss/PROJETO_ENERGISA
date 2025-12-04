"""
Core - Núcleo do sistema
"""

from .database import get_supabase, get_supabase_admin
from .security import (
    get_current_user,
    get_current_active_user,
    verify_supabase_token,
)
from .exceptions import (
    PlataformaException,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    EnergisaError,
)

__all__ = [
    # Database
    "get_supabase",
    "get_supabase_admin",
    # Security
    "get_current_user",
    "get_current_active_user",
    "verify_supabase_token",
    # Exceptions
    "PlataformaException",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "EnergisaError",
]
