"""
Sync Router - Endpoints de sincronização
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from pydantic import BaseModel

from backend.core.security import CurrentUser, get_current_active_user, require_perfil
from backend.sync.service import sync_service
from backend.sync.scheduler import sync_scheduler

router = APIRouter()


class SyncResponse(BaseModel):
    """Resposta de sincronização"""
    success: bool
    message: str
    stats: dict = {}


class SyncStatusResponse(BaseModel):
    """Status do scheduler"""
    running: bool
    interval_minutes: int
    last_sync: str | None
    last_stats: dict | None


@router.get(
    "/status",
    response_model=SyncStatusResponse,
    summary="Status do Scheduler",
    description="Retorna o status do scheduler de sincronização"
)
async def get_sync_status(
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """Retorna status do scheduler de sincronização."""
    return sync_scheduler.get_status()


@router.post(
    "/executar",
    response_model=SyncResponse,
    summary="Executar Sincronização",
    description="Executa sincronização manual de todas as UCs",
    dependencies=[Depends(require_perfil("superadmin", "gestor"))]
)
async def executar_sync(
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Executa sincronização manual de todas as UCs.

    Requer perfil superadmin ou gestor.
    """
    try:
        stats = await sync_service.sincronizar_todas_ucs()
        return SyncResponse(
            success=True,
            message="Sincronização executada com sucesso",
            stats=stats
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na sincronização: {str(e)}"
        )


@router.post(
    "/uc/{uc_id}",
    response_model=SyncResponse,
    summary="Sincronizar UC Específica",
    description="Sincroniza uma UC específica"
)
async def sincronizar_uc(
    uc_id: int,
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Sincroniza uma UC específica.

    Requer que o usuário tenha sessão ativa na Energisa.
    """
    from backend.ucs.service import ucs_service
    from backend.usuarios.service import usuarios_service

    # Busca a UC
    uc = await ucs_service.buscar_por_id(uc_id)

    # Verifica permissão
    if not current_user.is_superadmin and "gestor" not in current_user.perfis:
        if uc.usuario_id != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão para sincronizar esta UC"
            )

    # Busca CPF do usuário
    usuario = await usuarios_service.buscar_por_id(str(current_user.id))
    cpf = usuario.cpf

    # Executa sincronização
    result = await sync_service.sincronizar_uc_especifica(uc_id, cpf)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Erro na sincronização")
        )

    return SyncResponse(
        success=True,
        message="UC sincronizada com sucesso",
        stats={
            "uc_atualizada": result.get("uc_atualizada"),
            "faturas_sincronizadas": result.get("faturas_sincronizadas")
        }
    )


@router.post(
    "/gd/minhas-ucs",
    response_model=SyncResponse,
    summary="Sincronizar GD das minhas UCs",
    description="Sincroniza dados de GD de todas as UCs do usuário logado"
)
async def sincronizar_gd_minhas_ucs(
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """
    Sincroniza dados de Geração Distribuída de todas as UCs do usuário.

    Requer sessão ativa na Energisa.
    """
    from backend.usuarios.service import usuarios_service

    # Busca CPF do usuário
    usuario = await usuarios_service.buscar_por_id(str(current_user.id))
    cpf = usuario.cpf

    if not cpf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF não cadastrado no perfil"
        )

    # Executa sincronização de GD
    result = await sync_service.sincronizar_gd_usuario(str(current_user.id), cpf)

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Erro na sincronização de GD")
        )

    return SyncResponse(
        success=True,
        message=f"GD sincronizado: {result.get('gd_sincronizados', 0)} registros em {result.get('ucs_processadas', 0)} UCs",
        stats=result
    )


@router.post(
    "/scheduler/start",
    response_model=SyncResponse,
    summary="Iniciar Scheduler",
    description="Inicia o scheduler de sincronização",
    dependencies=[Depends(require_perfil("superadmin"))]
)
async def start_scheduler(
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """Inicia o scheduler de sincronização."""
    sync_scheduler.start()
    return SyncResponse(
        success=True,
        message="Scheduler iniciado",
        stats=sync_scheduler.get_status()
    )


@router.post(
    "/scheduler/stop",
    response_model=SyncResponse,
    summary="Parar Scheduler",
    description="Para o scheduler de sincronização",
    dependencies=[Depends(require_perfil("superadmin"))]
)
async def stop_scheduler(
    current_user: Annotated[CurrentUser, Depends(get_current_active_user)],
):
    """Para o scheduler de sincronização."""
    sync_scheduler.stop()
    return SyncResponse(
        success=True,
        message="Scheduler parado",
        stats=sync_scheduler.get_status()
    )
