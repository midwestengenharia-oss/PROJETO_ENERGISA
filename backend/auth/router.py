"""
Auth Router - Endpoints de autenticação
"""

from fastapi import APIRouter, Depends, status
from typing import Annotated

from backend.auth.schemas import (
    SignUpRequest,
    SignInRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    UpdateProfileRequest,
    SignUpResponse,
    SignInResponse,
    RefreshResponse,
    MeResponse,
    MessageResponse,
    PerfisResponse,
    UserResponse,
)
from backend.auth.service import auth_service
from backend.core.security import (
    CurrentUser,
    get_current_active_user,
)

router = APIRouter()


@router.post(
    "/signup",
    response_model=SignUpResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo usuário",
    description="Cria um novo usuário na plataforma com Supabase Auth + tabela usuarios"
)
async def signup(data: SignUpRequest):
    """
    Cadastra um novo usuário.

    - Valida CPF (dígitos verificadores)
    - Cria usuário no Supabase Auth
    - Cria registro na tabela usuarios
    - Adiciona perfil 'usuario' padrão
    - Retorna tokens de autenticação
    """
    user, tokens = await auth_service.signup(data)

    return SignUpResponse(
        message="Usuário cadastrado com sucesso",
        user=user,
        tokens=tokens
    )


@router.post(
    "/signin",
    response_model=SignInResponse,
    summary="Login",
    description="Autentica usuário e retorna tokens"
)
async def signin(data: SignInRequest):
    """
    Realiza login do usuário.

    - Autentica no Supabase Auth
    - Busca dados na tabela usuarios
    - Detecta perfis disponíveis automaticamente
    - Retorna tokens de autenticação
    """
    user, tokens, perfis_disponiveis = await auth_service.signin(data)

    return SignInResponse(
        message="Login realizado com sucesso",
        user=user,
        tokens=tokens,
        perfis_disponiveis=perfis_disponiveis
    )


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Renovar tokens",
    description="Renova tokens usando refresh_token"
)
async def refresh_token(data: RefreshTokenRequest):
    """
    Renova tokens de autenticação.

    Use o refresh_token recebido no login para obter novos tokens
    quando o access_token expirar.
    """
    tokens = await auth_service.refresh_token(data.refresh_token)

    return RefreshResponse(tokens=tokens)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout",
    description="Encerra sessão do usuário"
)
async def logout(
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)]
):
    """
    Realiza logout do usuário atual.

    Invalida a sessão no Supabase Auth.
    """
    await auth_service.logout()

    return MessageResponse(
        message="Logout realizado com sucesso",
        success=True
    )


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Dados do usuário logado",
    description="Retorna dados do usuário autenticado"
)
async def get_me(
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)]
):
    """
    Retorna dados do usuário autenticado.

    Inclui informações completas e lista de perfis.
    """
    user = await auth_service.get_user_by_id(current_user.id)
    perfis = await auth_service.get_user_perfis(current_user.id)

    return MeResponse(user=user, perfis=perfis)


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Atualizar perfil",
    description="Atualiza dados do usuário logado"
)
async def update_me(
    data: UpdateProfileRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)]
):
    """
    Atualiza dados do perfil do usuário.

    Campos atualizáveis:
    - nome_completo
    - telefone

    CPF e email não podem ser alterados.
    """
    user = await auth_service.update_profile(
        user_id=current_user.id,
        nome_completo=data.nome_completo,
        telefone=data.telefone
    )

    return user


@router.post(
    "/me/senha",
    response_model=MessageResponse,
    summary="Trocar senha",
    description="Altera a senha do usuário logado"
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)]
):
    """
    Troca a senha do usuário autenticado.

    Requer a senha atual para confirmação.
    """
    await auth_service.change_password(
        current_password=data.current_password,
        new_password=data.new_password
    )

    return MessageResponse(
        message="Senha alterada com sucesso",
        success=True
    )


@router.get(
    "/perfis",
    response_model=PerfisResponse,
    summary="Listar perfis",
    description="Lista perfis disponíveis do usuário"
)
async def get_perfis(
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)]
):
    """
    Lista todos os perfis do usuário.

    Perfis são detectados automaticamente baseado em:
    - Cadastro direto na tabela perfis_usuario
    - Proprietário de usina
    - Gestor de usina
    - Beneficiário de GD
    - Parceiro do marketplace
    """
    perfis = await auth_service.get_user_perfis(current_user.id)

    # Detecta perfis adicionais
    perfis_detectados = await auth_service._detectar_perfis(current_user.id)

    # Mescla perfis (evita duplicatas)
    perfis_existentes = {p.perfil for p in perfis}
    for perfil in perfis_detectados:
        if perfil not in perfis_existentes:
            from backend.auth.schemas import PerfilResponse
            perfis.append(PerfilResponse(perfil=perfil, ativo=True))

    # Determina perfil ativo (prioridade: superadmin > proprietario > gestor > etc)
    prioridade = ["superadmin", "proprietario", "gestor", "beneficiario", "parceiro", "usuario"]
    perfil_ativo = None
    for p in prioridade:
        if any(pf.perfil == p and pf.ativo for pf in perfis):
            perfil_ativo = p
            break

    return PerfisResponse(
        perfis=perfis,
        perfil_ativo=perfil_ativo
    )
