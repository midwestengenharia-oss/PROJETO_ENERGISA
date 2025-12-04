"""
Saques Service - Lógica de negócio para Saques/Comissões
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from ..core.database import get_supabase
from ..core.exceptions import NotFoundError, ValidationError, ForbiddenError
from .schemas import StatusSaque, TipoSaque


class SaquesService:
    """Serviço para gerenciamento de saques e comissões"""

    def __init__(self):
        self.supabase = get_supabase()
        self.taxa_transferencia = Decimal("0.00")  # Taxa de transferência (pode ser configurável)
        self.valor_minimo_saque = Decimal("50.00")  # Valor mínimo para saque

    async def listar(
        self,
        user_id: str,
        perfis: List[str],
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
        tipo: Optional[str] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None
    ) -> Dict[str, Any]:
        """Lista saques com filtros e paginação"""

        query = self.supabase.table("saques").select(
            "*, usuarios!saques_solicitante_id_fkey(id, nome_completo, email, cpf)",
            count="exact"
        )

        # Filtros de acesso por perfil
        if "superadmin" not in perfis and "proprietario" not in perfis:
            # Usuários comuns só veem seus próprios saques
            query = query.eq("solicitante_id", user_id)

        # Filtros opcionais
        if status:
            query = query.eq("status", status)
        if tipo:
            query = query.eq("tipo", tipo)
        if data_inicio:
            query = query.gte("data_solicitacao", str(data_inicio))
        if data_fim:
            query = query.lte("data_solicitacao", str(data_fim))

        # Paginação
        offset = (page - 1) * per_page
        query = query.order("data_solicitacao", desc=True)
        query = query.range(offset, offset + per_page - 1)

        result = query.execute()
        total = result.count or 0
        total_pages = (total + per_page - 1) // per_page

        return {
            "saques": result.data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }

    async def buscar(self, saque_id: int, user_id: str, perfis: List[str]) -> Dict[str, Any]:
        """Busca saque por ID"""

        result = self.supabase.table("saques").select(
            "*, usuarios!saques_solicitante_id_fkey(id, nome_completo, email, cpf)"
        ).eq("id", saque_id).single().execute()

        if not result.data:
            raise NotFoundError("Saque não encontrado")

        saque = result.data

        # Verificar permissão de acesso
        if "superadmin" not in perfis and "proprietario" not in perfis:
            if saque.get("solicitante_id") != user_id:
                raise ForbiddenError("Acesso negado a este saque")

        return saque

    async def obter_saldo(self, user_id: str) -> Dict[str, Any]:
        """Obtém saldo de comissões do usuário"""

        # Buscar comissões disponíveis
        comissoes = self.supabase.table("comissoes").select("*").eq(
            "usuario_id", user_id
        ).execute()

        saldo_disponivel = Decimal("0")
        saldo_pendente = Decimal("0")

        for c in comissoes.data:
            valor = Decimal(str(c.get("valor_comissao", 0)))
            if c.get("status") == "DISPONIVEL":
                saldo_disponivel += valor
            elif c.get("status") == "PENDENTE":
                saldo_pendente += valor

        # Buscar saques pagos
        saques_pagos = self.supabase.table("saques").select("valor").eq(
            "solicitante_id", user_id
        ).eq("status", StatusSaque.PAGO.value).execute()

        total_recebido = sum(Decimal(str(s.get("valor", 0))) for s in saques_pagos.data)

        # Último saque
        ultimo_saque = self.supabase.table("saques").select("data_pagamento").eq(
            "solicitante_id", user_id
        ).eq("status", StatusSaque.PAGO.value).order("data_pagamento", desc=True).limit(1).execute()

        return {
            "saldo_disponivel": float(saldo_disponivel),
            "saldo_pendente": float(saldo_pendente),
            "total_recebido": float(total_recebido),
            "ultimo_saque": ultimo_saque.data[0].get("data_pagamento") if ultimo_saque.data else None
        }

    async def listar_comissoes(self, user_id: str, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Lista comissões do usuário"""

        offset = (page - 1) * per_page

        result = self.supabase.table("comissoes").select(
            "*, usinas(id, nome)", count="exact"
        ).eq("usuario_id", user_id).order("criado_em", desc=True).range(
            offset, offset + per_page - 1
        ).execute()

        # Calcular saldo disponível
        saldo_result = self.supabase.table("comissoes").select("valor_comissao").eq(
            "usuario_id", user_id
        ).eq("status", "DISPONIVEL").execute()

        saldo_disponivel = sum(Decimal(str(c.get("valor_comissao", 0))) for c in saldo_result.data)

        return {
            "comissoes": result.data,
            "total": result.count or 0,
            "saldo_disponivel": float(saldo_disponivel)
        }

    async def solicitar(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Solicita novo saque"""

        valor = Decimal(str(data["valor"]))

        # Validar valor mínimo
        if valor < self.valor_minimo_saque:
            raise ValidationError(f"Valor mínimo para saque é R$ {self.valor_minimo_saque}")

        # Verificar saldo disponível
        saldo = await self.obter_saldo(user_id)
        if valor > Decimal(str(saldo["saldo_disponivel"])):
            raise ValidationError("Saldo insuficiente para este saque")

        # Verificar se há saque pendente
        saque_pendente = self.supabase.table("saques").select("id").eq(
            "solicitante_id", user_id
        ).in_("status", [StatusSaque.PENDENTE.value, StatusSaque.APROVADO.value, StatusSaque.PROCESSANDO.value]).execute()

        if saque_pendente.data:
            raise ValidationError("Você já possui um saque em processamento")

        # Calcular valor líquido
        taxa = valor * self.taxa_transferencia
        valor_liquido = valor - taxa

        dados_bancarios = data["dados_bancarios"]

        saque_data = {
            "tipo": data.get("tipo", TipoSaque.COMISSAO_GESTOR.value),
            "solicitante_id": user_id,
            "valor": float(valor),
            "taxa_transferencia": float(taxa),
            "valor_liquido": float(valor_liquido),
            "status": StatusSaque.PENDENTE.value,
            "data_solicitacao": datetime.now().isoformat(),
            "banco": dados_bancarios["banco"],
            "agencia": dados_bancarios["agencia"],
            "conta": dados_bancarios["conta"],
            "digito": dados_bancarios.get("digito"),
            "tipo_conta": dados_bancarios["tipo_conta"],
            "pix_chave": dados_bancarios.get("pix_chave"),
            "pix_tipo": dados_bancarios.get("pix_tipo"),
            "titular_nome": dados_bancarios["titular_nome"],
            "titular_cpf_cnpj": dados_bancarios["titular_cpf_cnpj"],
            "observacoes": data.get("observacoes")
        }

        result = self.supabase.table("saques").insert(saque_data).execute()

        # Marcar comissões como utilizadas
        comissoes_disponiveis = self.supabase.table("comissoes").select("id, valor_comissao").eq(
            "usuario_id", user_id
        ).eq("status", "DISPONIVEL").order("criado_em").execute()

        valor_restante = valor
        for comissao in comissoes_disponiveis.data:
            if valor_restante <= 0:
                break

            valor_comissao = Decimal(str(comissao["valor_comissao"]))
            if valor_comissao <= valor_restante:
                self.supabase.table("comissoes").update({
                    "status": "EM_SAQUE",
                    "saque_id": result.data[0]["id"]
                }).eq("id", comissao["id"]).execute()
                valor_restante -= valor_comissao

        return result.data[0]

    async def aprovar(self, saque_id: int, data: Dict[str, Any], user_id: str, perfis: List[str]) -> Dict[str, Any]:
        """Aprova saque"""

        if "superadmin" not in perfis and "proprietario" not in perfis:
            raise ForbiddenError("Apenas administradores podem aprovar saques")

        saque = await self.buscar(saque_id, user_id, perfis)

        if saque.get("status") != StatusSaque.PENDENTE.value:
            raise ValidationError("Apenas saques pendentes podem ser aprovados")

        update_data = {
            "status": StatusSaque.APROVADO.value,
            "data_aprovacao": datetime.now().isoformat(),
            "aprovado_por": user_id,
            "atualizado_em": datetime.now().isoformat()
        }

        if data.get("observacoes"):
            update_data["observacoes"] = f"{saque.get('observacoes') or ''}\n[Aprovação] {data['observacoes']}".strip()

        result = self.supabase.table("saques").update(update_data).eq("id", saque_id).execute()
        return result.data[0]

    async def rejeitar(self, saque_id: int, data: Dict[str, Any], user_id: str, perfis: List[str]) -> Dict[str, Any]:
        """Rejeita saque"""

        if "superadmin" not in perfis and "proprietario" not in perfis:
            raise ForbiddenError("Apenas administradores podem rejeitar saques")

        saque = await self.buscar(saque_id, user_id, perfis)

        if saque.get("status") not in [StatusSaque.PENDENTE.value, StatusSaque.APROVADO.value]:
            raise ValidationError("Este saque não pode ser rejeitado")

        update_data = {
            "status": StatusSaque.REJEITADO.value,
            "motivo_rejeicao": data["motivo"],
            "atualizado_em": datetime.now().isoformat()
        }

        result = self.supabase.table("saques").update(update_data).eq("id", saque_id).execute()

        # Liberar comissões vinculadas
        self.supabase.table("comissoes").update({
            "status": "DISPONIVEL",
            "saque_id": None
        }).eq("saque_id", saque_id).execute()

        return result.data[0]

    async def registrar_pagamento(self, saque_id: int, data: Dict[str, Any], user_id: str, perfis: List[str]) -> Dict[str, Any]:
        """Registra pagamento do saque"""

        if "superadmin" not in perfis and "proprietario" not in perfis:
            raise ForbiddenError("Apenas administradores podem registrar pagamentos")

        saque = await self.buscar(saque_id, user_id, perfis)

        if saque.get("status") != StatusSaque.APROVADO.value:
            raise ValidationError("Apenas saques aprovados podem ser pagos")

        update_data = {
            "status": StatusSaque.PAGO.value,
            "data_pagamento": str(data["data_pagamento"]),
            "comprovante_url": data.get("comprovante_url"),
            "numero_transacao": data.get("numero_transacao"),
            "atualizado_em": datetime.now().isoformat()
        }

        if data.get("observacoes"):
            update_data["observacoes"] = f"{saque.get('observacoes') or ''}\n[Pagamento] {data['observacoes']}".strip()

        result = self.supabase.table("saques").update(update_data).eq("id", saque_id).execute()

        # Marcar comissões como pagas
        self.supabase.table("comissoes").update({
            "status": "PAGO"
        }).eq("saque_id", saque_id).execute()

        return result.data[0]

    async def cancelar(self, saque_id: int, motivo: str, user_id: str, perfis: List[str]) -> Dict[str, Any]:
        """Cancela saque"""

        saque = await self.buscar(saque_id, user_id, perfis)

        # Usuário comum só pode cancelar seus próprios saques pendentes
        if "superadmin" not in perfis and "proprietario" not in perfis:
            if saque.get("solicitante_id") != user_id:
                raise ForbiddenError("Acesso negado")
            if saque.get("status") != StatusSaque.PENDENTE.value:
                raise ValidationError("Apenas saques pendentes podem ser cancelados")

        if saque.get("status") == StatusSaque.PAGO.value:
            raise ValidationError("Saques pagos não podem ser cancelados")

        update_data = {
            "status": StatusSaque.CANCELADO.value,
            "motivo_rejeicao": motivo,
            "atualizado_em": datetime.now().isoformat()
        }

        result = self.supabase.table("saques").update(update_data).eq("id", saque_id).execute()

        # Liberar comissões vinculadas
        self.supabase.table("comissoes").update({
            "status": "DISPONIVEL",
            "saque_id": None
        }).eq("saque_id", saque_id).execute()

        return result.data[0]

    async def estatisticas(self, user_id: str, perfis: List[str]) -> Dict[str, Any]:
        """Retorna estatísticas de saques"""

        query = self.supabase.table("saques").select("*")

        # Se não for admin, apenas seus saques
        if "superadmin" not in perfis and "proprietario" not in perfis:
            query = query.eq("solicitante_id", user_id)

        result = query.execute()
        saques = result.data

        total = len(saques)
        valor_solicitado = sum(Decimal(str(s.get("valor", 0))) for s in saques)
        valor_pago = sum(Decimal(str(s.get("valor", 0))) for s in saques if s.get("status") == StatusSaque.PAGO.value)

        pendentes = len([s for s in saques if s.get("status") == StatusSaque.PENDENTE.value])
        aprovados = len([s for s in saques if s.get("status") == StatusSaque.APROVADO.value])
        pagos = len([s for s in saques if s.get("status") == StatusSaque.PAGO.value])
        rejeitados = len([s for s in saques if s.get("status") == StatusSaque.REJEITADO.value])

        return {
            "total_saques": total,
            "valor_total_solicitado": float(valor_solicitado),
            "valor_total_pago": float(valor_pago),
            "saques_pendentes": pendentes,
            "saques_aprovados": aprovados,
            "saques_pagos": pagos,
            "saques_rejeitados": rejeitados
        }

    async def meus_saques(self, user_id: str) -> List[Dict[str, Any]]:
        """Lista saques do usuário logado"""

        result = self.supabase.table("saques").select("*").eq(
            "solicitante_id", user_id
        ).order("data_solicitacao", desc=True).execute()

        return result.data
