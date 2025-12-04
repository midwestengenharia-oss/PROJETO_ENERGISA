"""
Notificações Service - Lógica de negócio para Notificações
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from ..core.database import get_supabase
from ..core.exceptions import NotFoundError, ValidationError
from .schemas import TipoNotificacao, CanalNotificacao


class NotificacoesService:
    """Serviço para gerenciamento de notificações"""

    def __init__(self):
        self.supabase = get_supabase()

    async def listar(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 20,
        apenas_nao_lidas: bool = False,
        tipo: Optional[str] = None
    ) -> Dict[str, Any]:
        """Lista notificações do usuário"""

        query = self.supabase.table("notificacoes").select("*", count="exact").eq("usuario_id", user_id)

        if apenas_nao_lidas:
            query = query.eq("lida", False)
        if tipo:
            query = query.eq("tipo", tipo)

        offset = (page - 1) * per_page
        query = query.order("criado_em", desc=True).range(offset, offset + per_page - 1)

        result = query.execute()
        total = result.count or 0
        total_pages = (total + per_page - 1) // per_page

        # Contar não lidas
        nao_lidas_result = self.supabase.table("notificacoes").select("id", count="exact").eq(
            "usuario_id", user_id
        ).eq("lida", False).execute()

        return {
            "notificacoes": result.data,
            "total": total,
            "nao_lidas": nao_lidas_result.count or 0,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }

    async def buscar(self, notificacao_id: int, user_id: str) -> Dict[str, Any]:
        """Busca notificação por ID"""

        result = self.supabase.table("notificacoes").select("*").eq("id", notificacao_id).eq(
            "usuario_id", user_id
        ).single().execute()

        if not result.data:
            raise NotFoundError("Notificação não encontrada")

        return result.data

    async def contar_nao_lidas(self, user_id: str) -> int:
        """Conta notificações não lidas"""

        result = self.supabase.table("notificacoes").select("id", count="exact").eq(
            "usuario_id", user_id
        ).eq("lida", False).execute()

        return result.count or 0

    async def criar(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria nova notificação"""

        canais = data.get("canais", [CanalNotificacao.APP.value])
        if isinstance(canais, list) and len(canais) > 0 and hasattr(canais[0], 'value'):
            canais = [c.value for c in canais]

        notificacao_data = {
            "usuario_id": data["usuario_id"],
            "tipo": data.get("tipo", TipoNotificacao.INFO.value),
            "titulo": data["titulo"],
            "mensagem": data["mensagem"],
            "link": data.get("link"),
            "dados": data.get("dados"),
            "lida": False,
            "enviado_app": CanalNotificacao.APP.value in canais,
            "enviado_email": CanalNotificacao.EMAIL.value in canais,
            "enviado_sms": CanalNotificacao.SMS.value in canais,
            "enviado_whatsapp": CanalNotificacao.WHATSAPP.value in canais,
            "enviado_push": CanalNotificacao.PUSH.value in canais
        }

        result = self.supabase.table("notificacoes").insert(notificacao_data).execute()

        # TODO: Enviar notificação pelos canais selecionados
        # if CanalNotificacao.EMAIL.value in canais:
        #     await self._enviar_email(data["usuario_id"], data["titulo"], data["mensagem"])
        # if CanalNotificacao.SMS.value in canais:
        #     await self._enviar_sms(data["usuario_id"], data["mensagem"])

        return result.data[0]

    async def enviar_lote(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Envia notificação em lote"""

        usuario_ids = data.get("usuario_ids", [])

        # Se não especificou usuários, buscar por perfil ou usina
        if not usuario_ids:
            query = self.supabase.table("usuarios").select("auth_id")

            if data.get("perfis"):
                # Buscar usuários com os perfis especificados
                perfis_result = self.supabase.table("usuarios_perfis").select(
                    "usuario_id"
                ).in_("perfil", data["perfis"]).execute()
                usuario_ids = list(set([p["usuario_id"] for p in perfis_result.data]))

            elif data.get("usina_id"):
                # Buscar beneficiários da usina
                beneficiarios = self.supabase.table("beneficiarios").select(
                    "usuario_id"
                ).eq("usina_id", data["usina_id"]).execute()
                usuario_ids = [b["usuario_id"] for b in beneficiarios.data if b.get("usuario_id")]

        if not usuario_ids:
            raise ValidationError("Nenhum usuário encontrado para enviar notificação")

        enviadas = 0
        erros = []

        for usuario_id in usuario_ids:
            try:
                await self.criar({
                    "usuario_id": usuario_id,
                    "tipo": data.get("tipo", TipoNotificacao.INFO.value),
                    "titulo": data["titulo"],
                    "mensagem": data["mensagem"],
                    "link": data.get("link"),
                    "canais": data.get("canais", [CanalNotificacao.APP.value])
                })
                enviadas += 1
            except Exception as e:
                erros.append({"usuario_id": usuario_id, "erro": str(e)})

        return {
            "total_usuarios": len(usuario_ids),
            "enviadas": enviadas,
            "erros": erros
        }

    async def marcar_lida(self, notificacao_id: int, user_id: str) -> Dict[str, Any]:
        """Marca notificação como lida"""

        await self.buscar(notificacao_id, user_id)

        result = self.supabase.table("notificacoes").update({
            "lida": True,
            "lida_em": datetime.now().isoformat()
        }).eq("id", notificacao_id).execute()

        return result.data[0]

    async def marcar_todas_lidas(self, user_id: str) -> Dict[str, Any]:
        """Marca todas as notificações como lidas"""

        result = self.supabase.table("notificacoes").update({
            "lida": True,
            "lida_em": datetime.now().isoformat()
        }).eq("usuario_id", user_id).eq("lida", False).execute()

        return {"marcadas": len(result.data) if result.data else 0}

    async def excluir(self, notificacao_id: int, user_id: str) -> Dict[str, Any]:
        """Exclui notificação"""

        await self.buscar(notificacao_id, user_id)

        self.supabase.table("notificacoes").delete().eq("id", notificacao_id).execute()

        return {"message": "Notificação excluída"}

    async def obter_preferencias(self, user_id: str) -> Dict[str, Any]:
        """Obtém preferências de notificação do usuário"""

        result = self.supabase.table("preferencias_notificacao").select("*").eq(
            "usuario_id", user_id
        ).single().execute()

        if not result.data:
            # Criar preferências padrão
            preferencias = {
                "usuario_id": user_id,
                "email_cobrancas": True,
                "email_faturas": True,
                "email_contratos": True,
                "email_marketing": False,
                "sms_cobrancas": True,
                "sms_faturas": False,
                "whatsapp_cobrancas": True,
                "whatsapp_faturas": True,
                "push_habilitado": True
            }
            result = self.supabase.table("preferencias_notificacao").insert(preferencias).execute()
            return result.data[0]

        return result.data

    async def atualizar_preferencias(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Atualiza preferências de notificação"""

        # Verificar se existe
        existente = self.supabase.table("preferencias_notificacao").select("id").eq(
            "usuario_id", user_id
        ).single().execute()

        update_data = {k: v for k, v in data.items() if v is not None}

        if existente.data:
            result = self.supabase.table("preferencias_notificacao").update(
                update_data
            ).eq("usuario_id", user_id).execute()
        else:
            update_data["usuario_id"] = user_id
            result = self.supabase.table("preferencias_notificacao").insert(update_data).execute()

        return result.data[0]

    async def estatisticas(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Retorna estatísticas de notificações"""

        query = self.supabase.table("notificacoes").select("tipo, lida, enviado_email, enviado_sms, enviado_whatsapp")

        if user_id:
            query = query.eq("usuario_id", user_id)

        result = query.execute()
        notificacoes = result.data

        total = len(notificacoes)
        lidas = len([n for n in notificacoes if n.get("lida")])
        taxa_leitura = (lidas / total * 100) if total > 0 else 0

        # Por tipo
        por_tipo = {}
        for n in notificacoes:
            tipo = n.get("tipo", "INFO")
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

        # Por canal
        por_canal = {
            "APP": total,
            "EMAIL": len([n for n in notificacoes if n.get("enviado_email")]),
            "SMS": len([n for n in notificacoes if n.get("enviado_sms")]),
            "WHATSAPP": len([n for n in notificacoes if n.get("enviado_whatsapp")])
        }

        return {
            "total_enviadas": total,
            "total_lidas": lidas,
            "taxa_leitura": taxa_leitura,
            "por_tipo": [{"tipo": k, "quantidade": v} for k, v in por_tipo.items()],
            "por_canal": [{"canal": k, "quantidade": v} for k, v in por_canal.items()]
        }

    # ========================
    # Notificações automáticas
    # ========================

    async def notificar_nova_cobranca(self, beneficiario_id: int, cobranca_id: int, valor: float):
        """Notifica beneficiário sobre nova cobrança"""

        beneficiario = self.supabase.table("beneficiarios").select(
            "usuario_id, nome"
        ).eq("id", beneficiario_id).single().execute()

        if not beneficiario.data or not beneficiario.data.get("usuario_id"):
            return

        await self.criar({
            "usuario_id": beneficiario.data["usuario_id"],
            "tipo": TipoNotificacao.COBRANCA.value,
            "titulo": "Nova cobrança disponível",
            "mensagem": f"Você tem uma nova cobrança no valor de R$ {valor:.2f}. Acesse o sistema para mais detalhes.",
            "link": f"/cobrancas/{cobranca_id}",
            "dados": {"cobranca_id": cobranca_id, "valor": valor},
            "canais": [CanalNotificacao.APP.value, CanalNotificacao.EMAIL.value]
        })

    async def notificar_vencimento_proximo(self, beneficiario_id: int, cobranca_id: int, dias: int):
        """Notifica sobre cobrança próxima do vencimento"""

        beneficiario = self.supabase.table("beneficiarios").select(
            "usuario_id"
        ).eq("id", beneficiario_id).single().execute()

        if not beneficiario.data or not beneficiario.data.get("usuario_id"):
            return

        await self.criar({
            "usuario_id": beneficiario.data["usuario_id"],
            "tipo": TipoNotificacao.AVISO.value,
            "titulo": f"Cobrança vence em {dias} dia(s)",
            "mensagem": f"Sua cobrança vence em {dias} dia(s). Evite multas e encargos.",
            "link": f"/cobrancas/{cobranca_id}",
            "canais": [CanalNotificacao.APP.value, CanalNotificacao.WHATSAPP.value]
        })

    async def notificar_contrato_assinado(self, beneficiario_id: int, contrato_id: int):
        """Notifica sobre contrato assinado"""

        beneficiario = self.supabase.table("beneficiarios").select(
            "usuario_id"
        ).eq("id", beneficiario_id).single().execute()

        if not beneficiario.data or not beneficiario.data.get("usuario_id"):
            return

        await self.criar({
            "usuario_id": beneficiario.data["usuario_id"],
            "tipo": TipoNotificacao.SUCESSO.value,
            "titulo": "Contrato assinado com sucesso!",
            "mensagem": "Seu contrato foi assinado e está ativo. Bem-vindo à economia de energia!",
            "link": f"/contratos/{contrato_id}",
            "canais": [CanalNotificacao.APP.value, CanalNotificacao.EMAIL.value]
        })
