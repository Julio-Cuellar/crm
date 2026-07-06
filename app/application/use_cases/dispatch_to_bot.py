import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.domain.ports.bot_gateway import BotGateway
from app.domain.ports.conversation_memory_repository import ConversationMemoryRepository
from app.infrastructure.db.repositories.mongo_chat_history_repository import MongoChatHistoryRepository

logger = logging.getLogger(__name__)

# Mantener referencia fuerte a las tasks en background para que el GC no las cancele.
_background_tasks: set[asyncio.Task] = set()


class DispatchToBotUseCase:
    """Arma el payload de conversación y lo despacha al bot (n8n).

    Cambio clave vs. la versión anterior: NO se manda el historial plano de
    mensajes. Se envía un resumen compacto + estado estructurado (memoria) y solo
    una cola mínima de turnos recientes para coherencia inmediata. El backend
    lleva el contador de turnos y pide recompactar (`refreshSummary`) cada K.
    """

    def __init__(
        self,
        bot_gateway: BotGateway,
        memory_repo: ConversationMemoryRepository,
        mongo_repo: MongoChatHistoryRepository | None = None,
    ) -> None:
        self._bot = bot_gateway
        self._memory = memory_repo
        self._mongo = mongo_repo or MongoChatHistoryRepository()

    async def execute(
        self,
        *,
        tenant: Any,
        customer: Any,
        chat: dict,
        content: str,
        message_type: str = "TEXT",
        media_url: str | None = None,
        external_id: str | None = None,
        agent_prompt: str | None = None,
    ) -> dict[str, Any]:
        chat_id = chat["_id"]

        turns = await self._memory.bump_turn(chat_id)
        memory = await self._memory.get(chat_id)
        every = settings.BOT_SUMMARY_REFRESH_EVERY_TURNS
        refresh_summary = every > 0 and turns % every == 0

        recent_turns = await self._recent_turns(chat_id)

        payload = self._build_payload(
            tenant=tenant,
            customer=customer,
            chat_id=chat_id,
            content=content,
            message_type=message_type,
            media_url=media_url,
            external_id=external_id,
            memory=memory,
            recent_turns=recent_turns,
            refresh_summary=refresh_summary,
            agent_prompt=agent_prompt or build_default_agent_prompt(tenant),
        )

        # Fire-and-forget: no bloquear la respuesta del webhook (Meta exige 200 rápido).
        task = asyncio.create_task(self._bot.dispatch(payload))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)

        return payload

    async def _recent_turns(self, chat_id: Any) -> list[dict[str, Any]]:
        n = settings.BOT_RECENT_TURNS
        if n <= 0:
            return []
        messages = await self._mongo.get_messages_by_chat_id(chat_id)
        tail = messages[-n:]
        return [
            {
                "role": "customer" if msg.get("direction") == "INBOUND" else "bot",
                "type": msg.get("type", "TEXT"),
                "content": msg.get("content", ""),
                "sentAt": self._iso(msg.get("sentAt")),
            }
            for msg in tail
        ]

    def _build_payload(
        self,
        *,
        tenant: Any,
        customer: Any,
        chat_id: Any,
        content: str,
        message_type: str,
        media_url: str | None,
        external_id: str | None,
        memory: dict[str, Any],
        recent_turns: list[dict[str, Any]],
        refresh_summary: bool,
        agent_prompt: str,
    ) -> dict[str, Any]:
        summary = memory.get("summary") or {}
        state = memory.get("state") or {}
        callback_url = f"{settings.PUBLIC_BASE_URL.rstrip('/')}/api/v1/bridge/n8n/reply"

        return {
            "correlationId": str(uuid.uuid4()),
            "channel": "WHATSAPP",
            "receivedAt": datetime.now(timezone.utc).isoformat(),
            "callbackUrl": callback_url,
            "business": {
                "tenantId": str(tenant.id),
                "name": tenant.name,
                "vertical": getattr(tenant, "mode", "SERVICES"),
                "locale": tenant.locale,
                "timezone": tenant.timezone,
            },
            # Prompt del agente INDIVIDUAL por tenant/usuario (el workflow lo usa como systemMessage).
            "agent": {
                "prompt": agent_prompt,
                "config": {
                    "name": tenant.name,
                    "vertical": getattr(tenant, "mode", "SERVICES"),
                    "locale": tenant.locale,
                    "timezone": tenant.timezone,
                },
            },
            "conversation": {
                "chatId": str(chat_id),
                "customerId": str(customer.id),
                "customerName": customer.name,
                "customerPhone": customer.phone,
            },
            "message": {
                "externalId": external_id or "",
                "type": message_type,
                "content": content,
                "mediaUrl": media_url,
            },
            "context": {
                "summary": {
                    "text": summary.get("text", ""),
                    "version": summary.get("version", 0),
                    "updatedAt": summary.get("updatedAt"),
                    "turnsSinceRefresh": summary.get("turnsSinceRefresh", 0),
                },
                "state": state,
                "recentTurns": recent_turns,
                "refreshSummary": refresh_summary,
            },
        }

    @staticmethod
    def _iso(value: Any) -> str:
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value or "")


def build_default_agent_prompt(tenant: Any) -> str:
    """Genera el system prompt INDIVIDUAL por tenant.

    Es per-user porque incrusta la identidad del negocio (nombre, vertical, zona).
    Un tenant puede sobreescribirlo por completo (ver load_tenant_agent_prompt);
    si no, se usa esta plantilla de consultorio con el contrato de salida JSON.
    """
    name = getattr(tenant, "name", "el negocio")
    vertical = getattr(tenant, "mode", "SERVICES")
    timezone = getattr(tenant, "timezone", "America/Mexico_City")
    return (
        f"Eres el Asistente Virtual de \"{name}\" (vertical: {vertical}). "
        f"Atiendes pacientes/clientes por chat con tuteo, de forma empática y clara. "
        f"Zona horaria: {timezone}. "
        "Tu objetivo: agendar citas, resolver dudas básicas y registrar el motivo de consulta. "
        "NO des diagnósticos ni indicaciones clínicas; ante quejas o dudas clínicas complejas, "
        "escala a humano (intent='human_escalation'). NUNCA generes folio (lo genera el backend). "
        "Usa el resumen y el estado de la conversación que te entrega el sistema; no inventes datos.\n\n"
        "Responde SIEMPRE en JSON válido con esta estructura, sin texto fuera del bloque:\n"
        "{\n"
        '  "intent": "triage|show_services|schedule|confirm_booking|ask_corrections|resend_email|reschedule|cancel|human_escalation",\n'
        '  "reply": "respuesta conversacional para el cliente",\n'
        '  "nombre": "", "correo": "", "servicio": "", "descripcion": "",\n'
        '  "fecha_hora": "ISO 8601 o vacío", "folio": "", "ticket_correcto": null\n'
        "}"
    )


async def load_tenant_agent_prompt(db: Any, tenant_id: Any) -> str | None:
    """Carga un prompt personalizado por tenant.

    En este repo el prompt vive en tenant.ai_system_prompt. Se conserva el fallback
    por credencial para compatibilidad con el repo de referencia.
    """
    from app.core.security import decrypt_value
    from app.infrastructure.db.repositories.sqlalchemy_tenant_repository import SQLAlchemyTenantRepository
    from app.infrastructure.db.repositories.sqlalchemy_tenant_credential_repository import (
        SQLAlchemyTenantCredentialRepository,
    )

    tenant_repo = SQLAlchemyTenantRepository(db)
    tenant = await tenant_repo.get_by_id(tenant_id)
    if tenant and tenant.ai_system_prompt:
        return tenant.ai_system_prompt

    repo = SQLAlchemyTenantCredentialRepository(db)
    cred = await repo.get_by_tenant_and_type(tenant_id, "ai_system_prompt")
    if not cred:
        return None
    try:
        value = decrypt_value(cred.encrypted_value)
    except Exception:
        return None
    return value or None
