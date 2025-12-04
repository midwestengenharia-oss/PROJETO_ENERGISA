"""
Usinas Router - Endpoints de Usinas de Geração Distribuída
"""

from fastapi import APIRouter, Depends, Query, status
from typing import Annotated, Optional
import math

from backend.usinas.schemas import (
    UsinaCreateRequest,
    UsinaUpdateRequest,
    GestorUsinaRequest,
    UsinaResponse,
    UsinaListResponse,
    UsinaFiltros,
    UsinaStatus,
    TipoGeracao,
    GestorUsinaResponse,
    BeneficiarioResumoResponse,
    MessageResponse,
)
from backend.usinas.service import usinas_service
from backend.core.security import (
    CurrentUser,
    get_current_active_user,
    require_perfil,
)

router = APIRouter()


@router.get(
    "",
    response_model=UsinaListResponse,
    summary="Listar usinas",
    description="Lista usinas com filtros e paginação"
)
async def listar_usinas(
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
    nome: Optional[str] = Query(None, description="Filtrar por nome"),
    empresa_id: Optional[int] = Query(None, description="Filtrar por empresa"),
    status: Optional[UsinaStatus] = Query(None, description="Filtrar por status"),
    tipo_geracao: Optional[TipoGeracao] = Query(None, description="Filtrar por tipo"),
    page: int = Query(1, ge=1, description="Página"),
    per_page: int = Query(20, ge=1, le=100, description="Itens por página"),
):
    """
    Lista usinas da plataforma.

    - Superadmins veem todas
    - Gestores veem apenas as usinas que gerenciam
    - Proprietários veem suas usinas
    """
    filtros = UsinaFiltros(
        nome=nome,
        empresa_id=empresa_id,
        status=status,
        tipo_geracao=tipo_geracao
    )

    # Gestores só veem suas usinas
    if not current_user.is_superadmin:
        if "gestor" in current_user.perfis:
            filtros.gestor_id = str(current_user.id)

    usinas, total = await usinas_service.listar(
        filtros=filtros,
        page=page,
        per_page=per_page
    )

    total_pages = math.ceil(total / per_page) if total > 0 else 1

    return UsinaListResponse(
        usinas=usinas,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get(
    "/minhas",
    response_model=list[UsinaResponse],
    summary="Minhas usinas",
    description="Lista usinas que o usuário gerencia"
)
async def listar_minhas_usinas(
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Lista as usinas gerenciadas pelo usuário logado.
    """
    return await usinas_service.listar_por_gestor(str(current_user.id))


@router.post(
    "",
    response_model=UsinaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar usina",
    description="Cria nova usina de GD",
    dependencies=[Depends(require_perfil("superadmin", "proprietario"))]
)
async def criar_usina(
    data: UsinaCreateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Cria uma nova usina de Geração Distribuída.

    A UC geradora será automaticamente marcada como geradora.
    """
    return await usinas_service.criar(data)


@router.get(
    "/{usina_id}",
    response_model=UsinaResponse,
    summary="Buscar usina",
    description="Busca usina por ID"
)
async def buscar_usina(
    usina_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Busca dados completos de uma usina.

    Inclui gestores e beneficiários.
    """
    return await usinas_service.buscar_por_id(usina_id)


@router.put(
    "/{usina_id}",
    response_model=UsinaResponse,
    summary="Atualizar usina",
    description="Atualiza dados da usina",
    dependencies=[Depends(require_perfil("superadmin", "proprietario", "gestor"))]
)
async def atualizar_usina(
    usina_id: int,
    data: UsinaUpdateRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Atualiza dados de uma usina.
    """
    return await usinas_service.atualizar(usina_id, data)


@router.get(
    "/{usina_id}/gestores",
    response_model=list[GestorUsinaResponse],
    summary="Listar gestores",
    description="Lista gestores da usina"
)
async def listar_gestores(
    usina_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Lista os gestores de uma usina.
    """
    return await usinas_service.listar_gestores(usina_id)


@router.post(
    "/{usina_id}/gestores",
    response_model=GestorUsinaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar gestor",
    description="Adiciona gestor à usina",
    dependencies=[Depends(require_perfil("superadmin", "proprietario"))]
)
async def adicionar_gestor(
    usina_id: int,
    data: GestorUsinaRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Adiciona um usuário como gestor da usina.
    """
    return await usinas_service.adicionar_gestor(usina_id, data)


@router.delete(
    "/{usina_id}/gestores/{gestor_id}",
    response_model=MessageResponse,
    summary="Remover gestor",
    description="Remove gestor da usina",
    dependencies=[Depends(require_perfil("superadmin", "proprietario"))]
)
async def remover_gestor(
    usina_id: int,
    gestor_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Remove (desativa) um gestor da usina.
    """
    await usinas_service.remover_gestor(usina_id, gestor_id)
    return MessageResponse(
        message="Gestor removido com sucesso",
        success=True
    )


@router.get(
    "/{usina_id}/beneficiarios",
    response_model=list[BeneficiarioResumoResponse],
    summary="Listar beneficiários",
    description="Lista beneficiários da usina"
)
async def listar_beneficiarios(
    usina_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Lista os beneficiários de uma usina.
    """
    return await usinas_service.listar_beneficiarios(usina_id)
