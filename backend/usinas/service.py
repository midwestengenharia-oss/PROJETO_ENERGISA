"""
Usinas Service - Lógica de negócio para Usinas de Geração Distribuída
"""

from typing import Optional, List, Tuple
from decimal import Decimal
import logging
import math

from backend.core.database import db_admin
from backend.core.exceptions import NotFoundError, ConflictError, ValidationError
from backend.usinas.schemas import (
    UsinaCreateRequest,
    UsinaUpdateRequest,
    GestorUsinaRequest,
    UsinaResponse,
    UsinaFiltros,
    EmpresaResumoResponse,
    UCResumoResponse,
    GestorUsinaResponse,
    BeneficiarioResumoResponse,
)

logger = logging.getLogger(__name__)


class UsinasService:
    """Serviço de gestão de Usinas"""

    def __init__(self):
        self.db = db_admin

    def _formatar_uc(self, cod_empresa: int, cdc: int, digito: int) -> str:
        """Formata UC para exibição"""
        return f"{cod_empresa}/{cdc}-{digito}"

    async def listar(
        self,
        filtros: Optional[UsinaFiltros] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[UsinaResponse], int]:
        """
        Lista usinas com filtros e paginação.

        Args:
            filtros: Filtros de busca
            page: Página atual
            per_page: Itens por página

        Returns:
            Tupla (lista de usinas, total)
        """
        query = self.db.usinas().select(
            "*",
            "empresas(id, cnpj, razao_social, nome_fantasia)",
            "unidades_consumidoras!usinas_uc_geradora_id_fkey(id, cod_empresa, cdc, digito_verificador, nome_titular, cidade, uf, saldo_acumulado)",
            count="exact"
        )

        # Aplicar filtros
        if filtros:
            if filtros.nome:
                query = query.ilike("nome", f"%{filtros.nome}%")
            if filtros.empresa_id:
                query = query.eq("empresa_id", filtros.empresa_id)
            if filtros.status:
                query = query.eq("status", filtros.status.value)
            if filtros.tipo_geracao:
                query = query.eq("tipo_geracao", filtros.tipo_geracao.value)

        # Paginação
        offset = (page - 1) * per_page
        query = query.range(offset, offset + per_page - 1)

        # Ordenação
        query = query.order("criado_em", desc=True)

        result = query.execute()

        usinas = []
        for usina in result.data or []:
            usina_response = await self._build_usina_response(usina)
            usinas.append(usina_response)

        total = result.count if result.count else len(usinas)

        # Filtrar por gestor_id requer query adicional
        if filtros and filtros.gestor_id:
            gestores_result = self.db.table("gestores_usina").select(
                "usina_id"
            ).eq("gestor_id", filtros.gestor_id).eq("ativo", True).execute()

            usina_ids = {g["usina_id"] for g in gestores_result.data or []}
            usinas = [u for u in usinas if u.id in usina_ids]
            total = len(usinas)

        return usinas, total

    async def _build_usina_response(self, usina: dict) -> UsinaResponse:
        """Constrói resposta completa da usina"""
        # Empresa
        empresa = None
        if usina.get("empresas"):
            emp = usina["empresas"]
            empresa = EmpresaResumoResponse(
                id=emp["id"],
                cnpj=emp.get("cnpj"),
                razao_social=emp.get("razao_social"),
                nome_fantasia=emp.get("nome_fantasia")
            )

        # UC Geradora
        uc_geradora = None
        if usina.get("unidades_consumidoras"):
            uc = usina["unidades_consumidoras"]
            uc_geradora = UCResumoResponse(
                id=uc["id"],
                uc_formatada=self._formatar_uc(
                    uc["cod_empresa"], uc["cdc"], uc["digito_verificador"]
                ),
                nome_titular=uc.get("nome_titular"),
                cidade=uc.get("cidade"),
                uf=uc.get("uf"),
                saldo_acumulado=uc.get("saldo_acumulado", 0)
            )

        # Gestores
        gestores_result = self.db.table("gestores_usina").select(
            "*",
            "usuarios!gestores_usina_gestor_id_fkey(nome_completo, email)"
        ).eq("usina_id", usina["id"]).execute()

        gestores = []
        for g in gestores_result.data or []:
            usuario = g.get("usuarios", {})
            gestores.append(GestorUsinaResponse(
                id=g["id"],
                gestor_id=g["gestor_id"],
                nome_gestor=usuario.get("nome_completo") if usuario else None,
                email_gestor=usuario.get("email") if usuario else None,
                comissao_percentual=Decimal(str(g.get("comissao_percentual", 0))),
                ativo=g.get("ativo", True),
                criado_em=g.get("criado_em")
            ))

        # Beneficiários
        beneficiarios_result = self.db.beneficiarios().select(
            "*",
            "unidades_consumidoras!beneficiarios_uc_id_fkey(cod_empresa, cdc, digito_verificador)"
        ).eq("usina_id", usina["id"]).execute()

        beneficiarios = []
        percentual_alocado = Decimal("0")
        for b in beneficiarios_result.data or []:
            uc_benef = b.get("unidades_consumidoras", {})
            uc_formatada = None
            if uc_benef:
                uc_formatada = self._formatar_uc(
                    uc_benef["cod_empresa"], uc_benef["cdc"], uc_benef["digito_verificador"]
                )

            percentual = Decimal(str(b.get("percentual_rateio", 0)))
            percentual_alocado += percentual

            beneficiarios.append(BeneficiarioResumoResponse(
                id=b["id"],
                cpf=b["cpf"],
                nome=b.get("nome"),
                email=b.get("email"),
                percentual_rateio=percentual,
                desconto=Decimal(str(b.get("desconto", 0))),
                status=b.get("status", "PENDENTE"),
                uc_formatada=uc_formatada
            ))

        return UsinaResponse(
            id=usina["id"],
            nome=usina["nome"],
            empresa_id=usina.get("empresa_id"),
            uc_geradora_id=usina["uc_geradora_id"],
            capacidade_kwp=Decimal(str(usina["capacidade_kwp"])) if usina.get("capacidade_kwp") else None,
            tipo_geracao=usina.get("tipo_geracao", "SOLAR"),
            data_conexao=usina.get("data_conexao"),
            desconto_padrao=Decimal(str(usina.get("desconto_padrao", 0.30))),
            status=usina.get("status", "ATIVA"),
            endereco=usina.get("endereco"),
            latitude=Decimal(str(usina["latitude"])) if usina.get("latitude") else None,
            longitude=Decimal(str(usina["longitude"])) if usina.get("longitude") else None,
            criado_em=usina.get("criado_em"),
            atualizado_em=usina.get("atualizado_em"),
            empresa=empresa,
            uc_geradora=uc_geradora,
            gestores=gestores,
            beneficiarios=beneficiarios,
            total_beneficiarios=len(beneficiarios),
            total_gestores=len([g for g in gestores if g.ativo]),
            percentual_rateio_alocado=percentual_alocado
        )

    async def buscar_por_id(self, usina_id: int) -> UsinaResponse:
        """
        Busca usina por ID.

        Args:
            usina_id: ID da usina

        Returns:
            UsinaResponse

        Raises:
            NotFoundError: Se usina não encontrada
        """
        result = self.db.usinas().select(
            "*",
            "empresas(id, cnpj, razao_social, nome_fantasia)",
            "unidades_consumidoras!usinas_uc_geradora_id_fkey(id, cod_empresa, cdc, digito_verificador, nome_titular, cidade, uf, saldo_acumulado)"
        ).eq("id", usina_id).single().execute()

        if not result.data:
            raise NotFoundError("Usina")

        return await self._build_usina_response(result.data)

    async def criar(self, data: UsinaCreateRequest) -> UsinaResponse:
        """
        Cria nova usina.

        Args:
            data: Dados da usina

        Returns:
            UsinaResponse

        Raises:
            ValidationError: Se UC não é geradora
            ConflictError: Se UC já vinculada a outra usina
        """
        # Verifica se UC existe e é geradora
        uc_result = self.db.unidades_consumidoras().select(
            "id", "is_geradora"
        ).eq("id", data.uc_geradora_id).single().execute()

        if not uc_result.data:
            raise NotFoundError("Unidade Consumidora")

        # Marca UC como geradora se ainda não for
        if not uc_result.data.get("is_geradora"):
            self.db.unidades_consumidoras().update({
                "is_geradora": True
            }).eq("id", data.uc_geradora_id).execute()

        # Verifica se UC já está vinculada a outra usina
        existing = self.db.usinas().select("id").eq(
            "uc_geradora_id", data.uc_geradora_id
        ).execute()

        if existing.data:
            raise ConflictError("UC já vinculada a outra usina")

        # Cria usina
        usina_data = {
            "nome": data.nome,
            "uc_geradora_id": data.uc_geradora_id,
            "empresa_id": data.empresa_id,
            "capacidade_kwp": float(data.capacidade_kwp) if data.capacidade_kwp else None,
            "tipo_geracao": data.tipo_geracao.value,
            "data_conexao": data.data_conexao.isoformat() if data.data_conexao else None,
            "desconto_padrao": float(data.desconto_padrao),
            "status": "ATIVA",
            "endereco": data.endereco,
            "latitude": float(data.latitude) if data.latitude else None,
            "longitude": float(data.longitude) if data.longitude else None
        }

        result = self.db.usinas().insert(usina_data).execute()

        if not result.data:
            raise ValidationError("Erro ao criar usina")

        return await self.buscar_por_id(result.data[0]["id"])

    async def atualizar(
        self,
        usina_id: int,
        data: UsinaUpdateRequest
    ) -> UsinaResponse:
        """
        Atualiza dados da usina.

        Args:
            usina_id: ID da usina
            data: Dados para atualizar

        Returns:
            UsinaResponse atualizada
        """
        # Verifica se existe
        await self.buscar_por_id(usina_id)

        # Monta dados para atualização
        update_data = {}
        if data.nome is not None:
            update_data["nome"] = data.nome
        if data.capacidade_kwp is not None:
            update_data["capacidade_kwp"] = float(data.capacidade_kwp)
        if data.tipo_geracao is not None:
            update_data["tipo_geracao"] = data.tipo_geracao.value
        if data.data_conexao is not None:
            update_data["data_conexao"] = data.data_conexao.isoformat()
        if data.desconto_padrao is not None:
            update_data["desconto_padrao"] = float(data.desconto_padrao)
        if data.status is not None:
            update_data["status"] = data.status.value
        if data.endereco is not None:
            update_data["endereco"] = data.endereco
        if data.latitude is not None:
            update_data["latitude"] = float(data.latitude)
        if data.longitude is not None:
            update_data["longitude"] = float(data.longitude)

        if not update_data:
            return await self.buscar_por_id(usina_id)

        self.db.usinas().update(update_data).eq("id", usina_id).execute()

        return await self.buscar_por_id(usina_id)

    async def adicionar_gestor(
        self,
        usina_id: int,
        data: GestorUsinaRequest
    ) -> GestorUsinaResponse:
        """
        Adiciona gestor à usina.

        Args:
            usina_id: ID da usina
            data: Dados do gestor

        Returns:
            GestorUsinaResponse
        """
        # Verifica se usina existe
        await self.buscar_por_id(usina_id)

        # Verifica se já é gestor
        existing = self.db.table("gestores_usina").select("id", "ativo").eq(
            "usina_id", usina_id
        ).eq("gestor_id", data.gestor_id).execute()

        if existing.data:
            # Reativa se existir
            self.db.table("gestores_usina").update({
                "ativo": True,
                "comissao_percentual": float(data.comissao_percentual)
            }).eq("usina_id", usina_id).eq("gestor_id", data.gestor_id).execute()
        else:
            # Cria novo
            self.db.table("gestores_usina").insert({
                "usina_id": usina_id,
                "gestor_id": data.gestor_id,
                "comissao_percentual": float(data.comissao_percentual),
                "ativo": True
            }).execute()

        # Busca dados do gestor
        result = self.db.table("gestores_usina").select(
            "*",
            "usuarios!gestores_usina_gestor_id_fkey(nome_completo, email)"
        ).eq("usina_id", usina_id).eq("gestor_id", data.gestor_id).single().execute()

        g = result.data
        usuario = g.get("usuarios", {})

        return GestorUsinaResponse(
            id=g["id"],
            gestor_id=g["gestor_id"],
            nome_gestor=usuario.get("nome_completo") if usuario else None,
            email_gestor=usuario.get("email") if usuario else None,
            comissao_percentual=Decimal(str(g.get("comissao_percentual", 0))),
            ativo=g.get("ativo", True),
            criado_em=g.get("criado_em")
        )

    async def remover_gestor(
        self,
        usina_id: int,
        gestor_id: str
    ) -> bool:
        """
        Remove (desativa) gestor da usina.

        Args:
            usina_id: ID da usina
            gestor_id: ID do gestor

        Returns:
            True se sucesso
        """
        from datetime import datetime, timezone

        self.db.table("gestores_usina").update({
            "ativo": False,
            "desativado_em": datetime.now(timezone.utc).isoformat()
        }).eq("usina_id", usina_id).eq("gestor_id", gestor_id).execute()

        return True

    async def listar_gestores(self, usina_id: int) -> List[GestorUsinaResponse]:
        """
        Lista gestores de uma usina.

        Args:
            usina_id: ID da usina

        Returns:
            Lista de gestores
        """
        result = self.db.table("gestores_usina").select(
            "*",
            "usuarios!gestores_usina_gestor_id_fkey(nome_completo, email)"
        ).eq("usina_id", usina_id).execute()

        gestores = []
        for g in result.data or []:
            usuario = g.get("usuarios", {})
            gestores.append(GestorUsinaResponse(
                id=g["id"],
                gestor_id=g["gestor_id"],
                nome_gestor=usuario.get("nome_completo") if usuario else None,
                email_gestor=usuario.get("email") if usuario else None,
                comissao_percentual=Decimal(str(g.get("comissao_percentual", 0))),
                ativo=g.get("ativo", True),
                criado_em=g.get("criado_em")
            ))

        return gestores

    async def listar_beneficiarios(
        self,
        usina_id: int
    ) -> List[BeneficiarioResumoResponse]:
        """
        Lista beneficiários de uma usina.

        Args:
            usina_id: ID da usina

        Returns:
            Lista de beneficiários
        """
        result = self.db.beneficiarios().select(
            "*",
            "unidades_consumidoras!beneficiarios_uc_id_fkey(cod_empresa, cdc, digito_verificador)"
        ).eq("usina_id", usina_id).execute()

        beneficiarios = []
        for b in result.data or []:
            uc = b.get("unidades_consumidoras", {})
            uc_formatada = None
            if uc:
                uc_formatada = self._formatar_uc(
                    uc["cod_empresa"], uc["cdc"], uc["digito_verificador"]
                )

            beneficiarios.append(BeneficiarioResumoResponse(
                id=b["id"],
                cpf=b["cpf"],
                nome=b.get("nome"),
                email=b.get("email"),
                percentual_rateio=Decimal(str(b.get("percentual_rateio", 0))),
                desconto=Decimal(str(b.get("desconto", 0))),
                status=b.get("status", "PENDENTE"),
                uc_formatada=uc_formatada
            ))

        return beneficiarios

    async def listar_por_gestor(self, gestor_id: str) -> List[UsinaResponse]:
        """
        Lista usinas gerenciadas por um gestor.

        Args:
            gestor_id: ID do gestor

        Returns:
            Lista de usinas
        """
        filtros = UsinaFiltros(gestor_id=gestor_id)
        usinas, _ = await self.listar(filtros=filtros, per_page=1000)
        return usinas


# Instância global do serviço
usinas_service = UsinasService()
