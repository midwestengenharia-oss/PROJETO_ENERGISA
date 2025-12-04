"""
Usuarios Service - Lógica de negócio para gestão de usuários
"""

from typing import Optional, List, Tuple
import logging
import math

from backend.core.database import db_admin
from backend.core.exceptions import NotFoundError, ConflictError, ValidationError
from backend.usuarios.schemas import (
    UsuarioCreateRequest,
    UsuarioUpdateRequest,
    UsuarioResponse,
    UsuarioFiltros,
    PerfilUsuarioResponse,
    PerfilTipo,
)

logger = logging.getLogger(__name__)


class UsuariosService:
    """Serviço de gestão de usuários"""

    def __init__(self):
        self.db = db_admin

    async def listar(
        self,
        filtros: Optional[UsuarioFiltros] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[UsuarioResponse], int]:
        """
        Lista usuários com filtros e paginação.

        Args:
            filtros: Filtros de busca
            page: Página atual
            per_page: Itens por página

        Returns:
            Tupla (lista de usuários, total)
        """
        query = self.db.usuarios().select(
            "*",
            "perfis_usuario(perfil, ativo)",
            count="exact"
        )

        # Aplicar filtros
        if filtros:
            if filtros.nome:
                query = query.ilike("nome_completo", f"%{filtros.nome}%")
            if filtros.email:
                query = query.ilike("email", f"%{filtros.email}%")
            if filtros.cpf:
                query = query.eq("cpf", filtros.cpf)
            if filtros.ativo is not None:
                query = query.eq("ativo", filtros.ativo)
            if filtros.is_superadmin is not None:
                query = query.eq("is_superadmin", filtros.is_superadmin)

        # Paginação
        offset = (page - 1) * per_page
        query = query.range(offset, offset + per_page - 1)

        # Ordenação
        query = query.order("criado_em", desc=True)

        result = query.execute()

        usuarios = []
        for user in result.data or []:
            perfis = []
            if user.get("perfis_usuario"):
                perfis = [
                    p["perfil"] for p in user["perfis_usuario"]
                    if p.get("ativo", True)
                ]

            usuarios.append(UsuarioResponse(
                id=user["id"],
                auth_id=user.get("auth_id"),
                nome_completo=user["nome_completo"],
                email=user["email"],
                cpf=user.get("cpf"),
                telefone=user.get("telefone"),
                avatar_url=user.get("avatar_url"),
                is_superadmin=user.get("is_superadmin", False),
                ativo=user.get("ativo", True),
                email_verificado=user.get("email_verificado", False),
                perfis=perfis,
                criado_em=user.get("criado_em"),
                atualizado_em=user.get("atualizado_em"),
                ultimo_acesso=user.get("ultimo_acesso")
            ))

        total = result.count if result.count else len(usuarios)
        return usuarios, total

    async def buscar_por_id(self, usuario_id: str) -> UsuarioResponse:
        """
        Busca usuário por ID.

        Args:
            usuario_id: ID do usuário (UUID)

        Returns:
            UsuarioResponse

        Raises:
            NotFoundError: Se usuário não encontrado
        """
        result = self.db.usuarios().select(
            "*",
            "perfis_usuario(perfil, ativo)"
        ).eq("id", usuario_id).single().execute()

        if not result.data:
            raise NotFoundError("Usuário")

        user = result.data
        perfis = []
        if user.get("perfis_usuario"):
            perfis = [
                p["perfil"] for p in user["perfis_usuario"]
                if p.get("ativo", True)
            ]

        return UsuarioResponse(
            id=user["id"],
            auth_id=user.get("auth_id"),
            nome_completo=user["nome_completo"],
            email=user["email"],
            cpf=user.get("cpf"),
            telefone=user.get("telefone"),
            avatar_url=user.get("avatar_url"),
            is_superadmin=user.get("is_superadmin", False),
            ativo=user.get("ativo", True),
            email_verificado=user.get("email_verificado", False),
            perfis=perfis,
            criado_em=user.get("criado_em"),
            atualizado_em=user.get("atualizado_em"),
            ultimo_acesso=user.get("ultimo_acesso")
        )

    async def buscar_por_cpf(self, cpf: str) -> Optional[UsuarioResponse]:
        """
        Busca usuário por CPF.

        Args:
            cpf: CPF do usuário

        Returns:
            UsuarioResponse ou None
        """
        result = self.db.usuarios().select(
            "*",
            "perfis_usuario(perfil, ativo)"
        ).eq("cpf", cpf).single().execute()

        if not result.data:
            return None

        user = result.data
        perfis = []
        if user.get("perfis_usuario"):
            perfis = [
                p["perfil"] for p in user["perfis_usuario"]
                if p.get("ativo", True)
            ]

        return UsuarioResponse(
            id=user["id"],
            auth_id=user.get("auth_id"),
            nome_completo=user["nome_completo"],
            email=user["email"],
            cpf=user.get("cpf"),
            telefone=user.get("telefone"),
            avatar_url=user.get("avatar_url"),
            is_superadmin=user.get("is_superadmin", False),
            ativo=user.get("ativo", True),
            email_verificado=user.get("email_verificado", False),
            perfis=perfis,
            criado_em=user.get("criado_em"),
            atualizado_em=user.get("atualizado_em"),
            ultimo_acesso=user.get("ultimo_acesso")
        )

    async def buscar_por_email(self, email: str) -> Optional[UsuarioResponse]:
        """
        Busca usuário por email.

        Args:
            email: Email do usuário

        Returns:
            UsuarioResponse ou None
        """
        result = self.db.usuarios().select(
            "*",
            "perfis_usuario(perfil, ativo)"
        ).eq("email", email).single().execute()

        if not result.data:
            return None

        user = result.data
        perfis = []
        if user.get("perfis_usuario"):
            perfis = [
                p["perfil"] for p in user["perfis_usuario"]
                if p.get("ativo", True)
            ]

        return UsuarioResponse(
            id=user["id"],
            auth_id=user.get("auth_id"),
            nome_completo=user["nome_completo"],
            email=user["email"],
            cpf=user.get("cpf"),
            telefone=user.get("telefone"),
            avatar_url=user.get("avatar_url"),
            is_superadmin=user.get("is_superadmin", False),
            ativo=user.get("ativo", True),
            email_verificado=user.get("email_verificado", False),
            perfis=perfis,
            criado_em=user.get("criado_em"),
            atualizado_em=user.get("atualizado_em"),
            ultimo_acesso=user.get("ultimo_acesso")
        )

    async def criar(self, data: UsuarioCreateRequest) -> UsuarioResponse:
        """
        Cria novo usuário (sem Supabase Auth - apenas tabela usuarios).

        Args:
            data: Dados do usuário

        Returns:
            UsuarioResponse

        Raises:
            ConflictError: Se CPF ou email já existem
        """
        # Verifica duplicatas
        existing_cpf = self.db.usuarios().select("id").eq("cpf", data.cpf).execute()
        if existing_cpf.data:
            raise ConflictError("CPF já cadastrado")

        existing_email = self.db.usuarios().select("id").eq("email", data.email).execute()
        if existing_email.data:
            raise ConflictError("Email já cadastrado")

        # Cria usuário
        user_data = {
            "nome_completo": data.nome_completo,
            "email": data.email,
            "cpf": data.cpf,
            "telefone": data.telefone,
            "is_superadmin": data.is_superadmin,
            "ativo": True,
            "email_verificado": False
        }

        result = self.db.usuarios().insert(user_data).execute()

        if not result.data:
            raise ValidationError("Erro ao criar usuário")

        user = result.data[0]
        user_id = user["id"]

        # Adiciona perfis
        for perfil in data.perfis:
            self.db.perfis_usuario().insert({
                "usuario_id": user_id,
                "perfil": perfil.value,
                "ativo": True
            }).execute()

        return await self.buscar_por_id(user_id)

    async def atualizar(
        self,
        usuario_id: str,
        data: UsuarioUpdateRequest
    ) -> UsuarioResponse:
        """
        Atualiza dados do usuário.

        Args:
            usuario_id: ID do usuário
            data: Dados para atualizar

        Returns:
            UsuarioResponse atualizado

        Raises:
            NotFoundError: Se usuário não encontrado
        """
        # Verifica se existe
        existing = self.db.usuarios().select("id").eq("id", usuario_id).execute()
        if not existing.data:
            raise NotFoundError("Usuário")

        # Monta dados para atualização
        update_data = {}
        if data.nome_completo is not None:
            update_data["nome_completo"] = data.nome_completo
        if data.telefone is not None:
            update_data["telefone"] = data.telefone
        if data.avatar_url is not None:
            update_data["avatar_url"] = data.avatar_url
        if data.preferencias is not None:
            update_data["preferencias"] = data.preferencias
        if data.ativo is not None:
            update_data["ativo"] = data.ativo

        if not update_data:
            return await self.buscar_por_id(usuario_id)

        self.db.usuarios().update(update_data).eq("id", usuario_id).execute()

        return await self.buscar_por_id(usuario_id)

    async def desativar(self, usuario_id: str) -> UsuarioResponse:
        """
        Desativa um usuário.

        Args:
            usuario_id: ID do usuário

        Returns:
            UsuarioResponse atualizado
        """
        return await self.atualizar(
            usuario_id,
            UsuarioUpdateRequest(ativo=False)
        )

    async def ativar(self, usuario_id: str) -> UsuarioResponse:
        """
        Ativa um usuário.

        Args:
            usuario_id: ID do usuário

        Returns:
            UsuarioResponse atualizado
        """
        return await self.atualizar(
            usuario_id,
            UsuarioUpdateRequest(ativo=True)
        )

    async def listar_perfis(self, usuario_id: str) -> List[PerfilUsuarioResponse]:
        """
        Lista perfis de um usuário.

        Args:
            usuario_id: ID do usuário

        Returns:
            Lista de perfis
        """
        result = self.db.perfis_usuario().select("*").eq(
            "usuario_id", usuario_id
        ).execute()

        return [
            PerfilUsuarioResponse(
                id=p["id"],
                perfil=p["perfil"],
                ativo=p.get("ativo", True),
                dados_perfil=p.get("dados_perfil"),
                criado_em=p.get("criado_em")
            )
            for p in result.data or []
        ]

    async def atribuir_perfil(
        self,
        usuario_id: str,
        perfil: PerfilTipo,
        dados_perfil: Optional[dict] = None
    ) -> PerfilUsuarioResponse:
        """
        Atribui perfil a um usuário.

        Args:
            usuario_id: ID do usuário
            perfil: Tipo de perfil
            dados_perfil: Dados adicionais do perfil

        Returns:
            PerfilUsuarioResponse

        Raises:
            ConflictError: Se perfil já existe
        """
        # Verifica se já tem o perfil
        existing = self.db.perfis_usuario().select("id").eq(
            "usuario_id", usuario_id
        ).eq("perfil", perfil.value).execute()

        if existing.data:
            # Atualiza para ativo
            self.db.perfis_usuario().update({
                "ativo": True,
                "dados_perfil": dados_perfil or {}
            }).eq("usuario_id", usuario_id).eq("perfil", perfil.value).execute()

            result = self.db.perfis_usuario().select("*").eq(
                "usuario_id", usuario_id
            ).eq("perfil", perfil.value).single().execute()
        else:
            # Cria novo
            result = self.db.perfis_usuario().insert({
                "usuario_id": usuario_id,
                "perfil": perfil.value,
                "ativo": True,
                "dados_perfil": dados_perfil or {}
            }).execute()

        p = result.data[0] if isinstance(result.data, list) else result.data
        return PerfilUsuarioResponse(
            id=p["id"],
            perfil=p["perfil"],
            ativo=p.get("ativo", True),
            dados_perfil=p.get("dados_perfil"),
            criado_em=p.get("criado_em")
        )

    async def remover_perfil(self, usuario_id: str, perfil: PerfilTipo) -> bool:
        """
        Remove (desativa) perfil de um usuário.

        Args:
            usuario_id: ID do usuário
            perfil: Tipo de perfil

        Returns:
            True se sucesso
        """
        self.db.perfis_usuario().update({
            "ativo": False
        }).eq("usuario_id", usuario_id).eq("perfil", perfil.value).execute()

        return True

    async def registrar_acesso(self, usuario_id: str) -> None:
        """
        Registra último acesso do usuário.

        Args:
            usuario_id: ID do usuário
        """
        from datetime import datetime, timezone

        self.db.usuarios().update({
            "ultimo_acesso": datetime.now(timezone.utc).isoformat()
        }).eq("id", usuario_id).execute()

    async def buscar_por_perfil(
        self,
        perfil: PerfilTipo,
        apenas_ativos: bool = True
    ) -> List[UsuarioResponse]:
        """
        Busca usuários por perfil.

        Args:
            perfil: Tipo de perfil
            apenas_ativos: Se deve filtrar apenas ativos

        Returns:
            Lista de usuários com o perfil
        """
        query = self.db.perfis_usuario().select(
            "usuario_id"
        ).eq("perfil", perfil.value)

        if apenas_ativos:
            query = query.eq("ativo", True)

        result = query.execute()

        if not result.data:
            return []

        usuario_ids = [p["usuario_id"] for p in result.data]
        usuarios = []

        for uid in usuario_ids:
            try:
                usuario = await self.buscar_por_id(uid)
                if apenas_ativos and not usuario.ativo:
                    continue
                usuarios.append(usuario)
            except NotFoundError:
                continue

        return usuarios


# Instância global do serviço
usuarios_service = UsuariosService()
