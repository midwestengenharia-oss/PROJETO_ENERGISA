"""
Leads Service - Lógica de negócio para Leads/Simulações
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from ..core.database import get_supabase
from ..core.exceptions import NotFoundError, ValidationError
from .schemas import StatusLead, OrigemLead


class LeadsService:
    """Serviço para gerenciamento de leads e simulações"""

    def __init__(self):
        self.supabase = get_supabase()
        self.desconto_padrao = Decimal("0.30")  # 30% de desconto

    async def listar(
        self,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
        origem: Optional[str] = None,
        responsavel_id: Optional[str] = None,
        busca: Optional[str] = None
    ) -> Dict[str, Any]:
        """Lista leads com filtros e paginação"""

        query = self.supabase.table("leads").select(
            "*, simulacoes(*), contatos(*)",
            count="exact"
        )

        if status:
            query = query.eq("status", status)
        if origem:
            query = query.eq("origem", origem)
        if responsavel_id:
            query = query.eq("responsavel_id", responsavel_id)
        if busca:
            query = query.or_(f"nome.ilike.%{busca}%,telefone.ilike.%{busca}%,email.ilike.%{busca}%")

        offset = (page - 1) * per_page
        query = query.order("criado_em", desc=True).range(offset, offset + per_page - 1)

        result = query.execute()
        total = result.count or 0
        total_pages = (total + per_page - 1) // per_page

        return {
            "leads": result.data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }

    async def buscar(self, lead_id: int) -> Dict[str, Any]:
        """Busca lead por ID"""

        result = self.supabase.table("leads").select(
            "*, simulacoes(*), contatos(*)"
        ).eq("id", lead_id).single().execute()

        if not result.data:
            raise NotFoundError("Lead não encontrado")

        return result.data

    async def criar(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria novo lead"""

        # Verificar se já existe lead com mesmo CPF
        cpf = data["cpf"]
        existente = self.supabase.table("leads").select("*").eq("cpf", cpf).execute()

        if existente.data:
            lead_existente = existente.data[0]
            # Se já foi convertido ou perdido, permite criar novo
            if lead_existente["status"] not in [StatusLead.CONVERTIDO.value, StatusLead.PERDIDO.value]:
                return lead_existente  # Retorna lead existente

        lead_data = {
            "nome": data["nome"],
            "email": data.get("email"),
            "telefone": data.get("telefone"),
            "cpf": cpf,
            "cidade": data.get("cidade"),
            "uf": data.get("uf"),
            "status": StatusLead.NOVO.value,
            "origem": data.get("origem", OrigemLead.LANDING_PAGE.value),
            "utm_source": data.get("utm_source"),
            "utm_medium": data.get("utm_medium"),
            "utm_campaign": data.get("utm_campaign")
        }

        result = self.supabase.table("leads").insert(lead_data).execute()
        return result.data[0]

    async def atualizar(self, lead_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza lead"""

        lead = await self.buscar(lead_id)

        if lead.get("status") == StatusLead.CONVERTIDO.value:
            raise ValidationError("Lead já convertido não pode ser alterado")

        update_data = {k: v for k, v in data.items() if v is not None}
        update_data["atualizado_em"] = datetime.now().isoformat()

        result = self.supabase.table("leads").update(update_data).eq("id", lead_id).execute()
        return result.data[0]

    async def simular(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria simulação para um lead"""

        lead_id = data["lead_id"]
        lead = await self.buscar(lead_id)

        valor_fatura = Decimal(str(data["valor_fatura_media"]))
        quantidade_ucs = data.get("quantidade_ucs", 1)

        # Calcular economia
        economia_mensal = valor_fatura * self.desconto_padrao * quantidade_ucs
        economia_anual = economia_mensal * 12
        percentual = self.desconto_padrao * 100

        simulacao_data = {
            "lead_id": lead_id,
            "valor_fatura_media": float(valor_fatura),
            "consumo_medio_kwh": data.get("consumo_medio_kwh"),
            "quantidade_ucs": quantidade_ucs,
            "desconto_aplicado": float(self.desconto_padrao),
            "economia_mensal": float(economia_mensal),
            "economia_anual": float(economia_anual),
            "percentual_economia": float(percentual)
        }

        result = self.supabase.table("simulacoes").insert(simulacao_data).execute()

        # Atualizar status do lead
        self.supabase.table("leads").update({
            "status": StatusLead.SIMULACAO.value,
            "atualizado_em": datetime.now().isoformat()
        }).eq("id", lead_id).execute()

        return result.data[0]

    async def registrar_contato(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Registra contato com lead"""

        lead_id = data["lead_id"]
        await self.buscar(lead_id)

        contato_data = {
            "lead_id": lead_id,
            "tipo_contato": data["tipo_contato"],
            "descricao": data["descricao"],
            "proximo_contato": str(data["proximo_contato"]) if data.get("proximo_contato") else None,
            "realizado_por": user_id
        }

        result = self.supabase.table("contatos").insert(contato_data).execute()

        # Atualizar status do lead para CONTATO se ainda não estiver
        self.supabase.table("leads").update({
            "status": StatusLead.CONTATO.value,
            "atualizado_em": datetime.now().isoformat()
        }).eq("id", lead_id).eq("status", StatusLead.SIMULACAO.value).execute()

        return result.data[0]

    async def converter(self, data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Converte lead em beneficiário"""

        lead_id = data["lead_id"]
        lead = await self.buscar(lead_id)

        if lead.get("status") == StatusLead.CONVERTIDO.value:
            raise ValidationError("Lead já foi convertido")

        usina_id = data["usina_id"]
        desconto = Decimal(str(data["desconto_percentual"]))

        # Verificar se usina existe
        usina = self.supabase.table("usinas").select("id").eq("id", usina_id).single().execute()
        if not usina.data:
            raise NotFoundError("Usina não encontrada")

        # Criar beneficiário
        beneficiario_data = {
            "usina_id": usina_id,
            "nome": lead["nome"],
            "email": lead.get("email"),
            "telefone": lead.get("telefone"),
            "cpf": lead["cpf"],
            "desconto": float(desconto),
            "percentual_rateio": float(data.get("percentual_rateio", 0)),
            "status": "PENDENTE",
            "origem": "LEAD",
            "lead_id": lead_id,
            "criado_por": user_id
        }

        beneficiario = self.supabase.table("beneficiarios").insert(beneficiario_data).execute()

        # Atualizar lead
        self.supabase.table("leads").update({
            "status": StatusLead.CONVERTIDO.value,
            "convertido_em": datetime.now().isoformat(),
            "beneficiario_id": beneficiario.data[0]["id"],
            "atualizado_em": datetime.now().isoformat()
        }).eq("id", lead_id).execute()

        return {
            "lead": lead,
            "beneficiario": beneficiario.data[0],
            "message": "Lead convertido com sucesso"
        }

    async def marcar_perdido(self, lead_id: int, motivo: str) -> Dict[str, Any]:
        """Marca lead como perdido"""

        lead = await self.buscar(lead_id)

        if lead.get("status") == StatusLead.CONVERTIDO.value:
            raise ValidationError("Lead já foi convertido")

        result = self.supabase.table("leads").update({
            "status": StatusLead.PERDIDO.value,
            "observacoes": f"{lead.get('observacoes') or ''}\n[Perdido] {motivo}".strip(),
            "atualizado_em": datetime.now().isoformat()
        }).eq("id", lead_id).execute()

        return result.data[0]

    async def atribuir_responsavel(self, lead_id: int, responsavel_id: str) -> Dict[str, Any]:
        """Atribui responsável ao lead"""

        await self.buscar(lead_id)

        # Verificar se responsável existe
        usuario = self.supabase.table("usuarios").select("id, nome_completo").eq("auth_id", responsavel_id).single().execute()
        if not usuario.data:
            raise NotFoundError("Usuário responsável não encontrado")

        result = self.supabase.table("leads").update({
            "responsavel_id": responsavel_id,
            "atualizado_em": datetime.now().isoformat()
        }).eq("id", lead_id).execute()

        return result.data[0]

    async def estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas de leads"""

        leads = self.supabase.table("leads").select("id, status, origem").execute()
        simulacoes = self.supabase.table("simulacoes").select("economia_anual").execute()

        total = len(leads.data)
        novos = len([l for l in leads.data if l["status"] == StatusLead.NOVO.value])
        em_contato = len([l for l in leads.data if l["status"] in [StatusLead.CONTATO.value, StatusLead.NEGOCIACAO.value]])
        convertidos = len([l for l in leads.data if l["status"] == StatusLead.CONVERTIDO.value])
        perdidos = len([l for l in leads.data if l["status"] == StatusLead.PERDIDO.value])

        taxa_conversao = Decimal(str(convertidos)) / Decimal(str(total)) * 100 if total > 0 else Decimal("0")
        economia_total = sum(Decimal(str(s.get("economia_anual", 0))) for s in simulacoes.data)

        # Por origem
        por_origem = {}
        for l in leads.data:
            origem = l.get("origem", "OUTROS")
            por_origem[origem] = por_origem.get(origem, 0) + 1

        # Por status
        por_status = {}
        for l in leads.data:
            status = l.get("status", "NOVO")
            por_status[status] = por_status.get(status, 0) + 1

        return {
            "total_leads": total,
            "leads_novos": novos,
            "leads_em_contato": em_contato,
            "leads_convertidos": convertidos,
            "leads_perdidos": perdidos,
            "taxa_conversao": float(taxa_conversao),
            "economia_total_simulada": float(economia_total),
            "por_origem": [{"origem": k, "quantidade": v} for k, v in por_origem.items()],
            "por_status": [{"status": k, "quantidade": v} for k, v in por_status.items()]
        }

    async def funil(self) -> Dict[str, Any]:
        """Retorna funil de vendas"""

        leads = self.supabase.table("leads").select("status").execute()

        etapas = [
            {"nome": "Novo", "status": StatusLead.NOVO.value, "quantidade": 0},
            {"nome": "Simulação", "status": StatusLead.SIMULACAO.value, "quantidade": 0},
            {"nome": "Contato", "status": StatusLead.CONTATO.value, "quantidade": 0},
            {"nome": "Negociação", "status": StatusLead.NEGOCIACAO.value, "quantidade": 0},
            {"nome": "Convertido", "status": StatusLead.CONVERTIDO.value, "quantidade": 0}
        ]

        for l in leads.data:
            status = l.get("status")
            for etapa in etapas:
                if etapa["status"] == status:
                    etapa["quantidade"] += 1
                    break

        total = len(leads.data)
        convertidos = etapas[-1]["quantidade"]
        taxa = Decimal(str(convertidos)) / Decimal(str(total)) * 100 if total > 0 else Decimal("0")

        return {
            "etapas": etapas,
            "total": total,
            "taxa_conversao_geral": float(taxa)
        }
