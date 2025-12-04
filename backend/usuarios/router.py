"""
Usuarios Router - Endpoints de gestão de usuários
"""

from fastapi import APIRouter, Depends, Query, status
from typing import Annotated, Optional
import math

from backend.usuarios.schemas import (
    UsuarioCreateRequest,
    UsuarioUpdateRequest,
    UsuarioResponse,
    UsuarioListResponse,
    UsuarioFiltros,
    PerfilUsuarioResponse,
    AtribuirPerfilRequest,
    PerfilTipo,
    MessageResponse,
)
from backend.usuarios.service import usuarios_service
from backend.core.security import (
    CurrentUser,
    get_current_active_user,
    require_perfil,
    require_superadmin,
)

router = APIRouter()


@router.get(
    "",
    response_model=UsuarioListResponse,
    summary="Listar usuários",
    description="Lista todos os usuários com filtros e paginação (admin)",
    dependencies=[Depends(require_perfil("superadmin", "gestor"))]
)
async def listar_usuarios(
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    nome: Optional[str] = Query(None, description="Filtrar por nome"),
    email: Optional[str] = Query(None, description="Filtrar por email"),
    cpf: Optional[str] = Query(None, description="Filtrar por CPF"),
    perfil: Optional[PerfilTipo] = Query(None, description="Filtrar por perfil"),
    ativo: Optional[bool] = Query(None, description="Filtrar por status ativo"),
    page: int = Query(1, ge=1, description="Página"),
    per_page: int = Query(20, ge=1, le=100, description="Itens por página"),
):
    """
    Lista usuários da plataforma.

    Acesso restrito a superadmins e gestores.
    """
    filtros = UsuarioFiltros(
        nome=nome,
        email=email,
        cpf=cpf,
        perfil=perfil,
        ativo=ativo
    )

    usuarios, total = await usuarios_service.listar(
        filtros=filtros,
        page=page,
        per_page=per_page
    )

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return UsuarioListResponse(
        usuarios=usuarios,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.post(
    "",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar usuário",
    description="Cria novo usuário (admin)",
    dependencies=[Depends(require_superadmin())]
)
async def criar_usuario(
    data: UsuarioCreateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Cria novo usuário na plataforma.

    Acesso restrito a superadmins.
    O usuário é criado sem autenticação (sem Supabase Auth).
    Para criar usuário com login, use o endpoint de signup.
    """
    return await usuarios_service.criar(data)


@router.get(
    "/perfil/{perfil}",
    response_model=list[UsuarioResponse],
    summary="Buscar por perfil",
    description="Lista usuários com determinado perfil",
    dependencies=[Depends(require_perfil("superadmin", "gestor"))]
)
async def buscar_por_perfil(
    perfil: PerfilTipo,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    apenas_ativos: bool = Query(True, description="Apenas usuários ativos"),
):
    """
    Busca usuários por tipo de perfil.

    Útil para listar todos os gestores, beneficiários, etc.
    """
    return await usuarios_service.buscar_por_perfil(
        perfil=perfil,
        apenas_ativos=apenas_ativos
    )


@router.get(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Buscar usuário",
    description="Busca usuário por ID",
    dependencies=[Depends(require_perfil("superadmin", "gestor"))]
)
async def buscar_usuario(
    usuario_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Busca dados completos de um usuário.
    """
    return await usuarios_service.buscar_por_id(usuario_id)


@router.put(
    "/{usuario_id}",
    response_model=UsuarioResponse,
    summary="Atualizar usuário",
    description="Atualiza dados do usuário",
    dependencies=[Depends(require_superadmin())]
)
async def atualizar_usuario(
    usuario_id: str,
    data: UsuarioUpdateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Atualiza dados de um usuário.

    Acesso restrito a superadmins.
    """
    return await usuarios_service.atualizar(usuario_id, data)


@router.post(
    "/{usuario_id}/desativar",
    response_model=UsuarioResponse,
    summary="Desativar usuário",
    description="Desativa um usuário",
    dependencies=[Depends(require_superadmin())]
)
async def desativar_usuario(
    usuario_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Desativa um usuário.

    O usuário não poderá mais acessar a plataforma.
    """
    return await usuarios_service.desativar(usuario_id)


@router.post(
    "/{usuario_id}/ativar",
    response_model=UsuarioResponse,
    summary="Ativar usuário",
    description="Ativa um usuário desativado",
    dependencies=[Depends(require_superadmin())]
)
async def ativar_usuario(
    usuario_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Ativa um usuário previamente desativado.
    """
    return await usuarios_service.ativar(usuario_id)


@router.get(
    "/{usuario_id}/perfis",
    response_model=list[PerfilUsuarioResponse],
    summary="Listar perfis do usuário",
    description="Lista todos os perfis de um usuário",
    dependencies=[Depends(require_perfil("superadmin", "gestor"))]
)
async def listar_perfis_usuario(
    usuario_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Lista todos os perfis atribuídos a um usuário.
    """
    return await usuarios_service.listar_perfis(usuario_id)


@router.post(
    "/{usuario_id}/perfis",
    response_model=PerfilUsuarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Atribuir perfil",
    description="Atribui um perfil ao usuário",
    dependencies=[Depends(require_superadmin())]
)
async def atribuir_perfil(
    usuario_id: str,
    data: AtribuirPerfilRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Atribui um novo perfil ao usuário.

    Se o perfil já existe (desativado), será reativado.
    """
    return await usuarios_service.atribuir_perfil(
        usuario_id=usuario_id,
        perfil=data.perfil,
        dados_perfil=data.dados_perfil
    )


@router.delete(
    "/{usuario_id}/perfis/{perfil}",
    response_model=MessageResponse,
    summary="Remover perfil",
    description="Remove (desativa) um perfil do usuário",
    dependencies=[Depends(require_superadmin())]
)
async def remover_perfil(
    usuario_id: str,
    perfil: PerfilTipo,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Remove (desativa) um perfil do usuário.

    O perfil não é deletado, apenas desativado.
    """
    await usuarios_service.remover_perfil(usuario_id, perfil)
    return MessageResponse(
        message=f"Perfil {perfil.value} removido com sucesso",
        success=True
    )
