import logging
import re
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decrypt_value
from app.domain.entities.appointment import Appointment as DomainAppointment
from app.domain.entities.bot_session import BotSession as DomainBotSession
from app.domain.entities.customer import Customer
from app.domain.ports.conversation_memory_repository import ConversationMemoryRepository
from app.infrastructure.db.repositories.mongo_chat_history_repository import MongoChatHistoryRepository
from app.infrastructure.db.repositories.sqlalchemy_appointment_repository import SQLAlchemyAppointmentRepository
from app.infrastructure.db.repositories.sqlalchemy_bot_session_repository import SQLAlchemyBotSessionRepository
from app.infrastructure.db.repositories.sqlalchemy_customer_repository import SQLAlchemyCustomerRepository
from app.infrastructure.db.repositories.sqlalchemy_service_repository import SQLAlchemyServiceRepository
from app.infrastructure.db.repositories.sqlalchemy_tenant_credential_repository import (
    SQLAlchemyTenantCredentialRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_tenant_repository import SQLAlchemyTenantRepository
from app.infrastructure.messaging.whatsapp_cloud_api import WhatsAppCloudAPIError, send_whatsapp_message
from app.infrastructure.websocket.manager import ws_manager
from app.interfaces.api.schemas.bot import BotReplyRequest

logger = logging.getLogger(__name__)


def _canonical_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    return f"+{digits}" if digits else phone.strip()


class HandleBotReplyUseCase:
    """Procesa la respuesta del bot (callback de n8n): persiste memoria, envía al
    cliente por el canal y notifica a los agentes por WebSocket.

    Idempotente por `correlationId`: un reintento de n8n no duplica el envío.
    """

    def __init__(
        self,
        memory_repo: ConversationMemoryRepository,
        mongo_repo: MongoChatHistoryRepository | None = None,
    ) -> None:
        self._memory = memory_repo
        self._mongo = mongo_repo or MongoChatHistoryRepository()

    async def execute(self, *, db: AsyncSession, reply: BotReplyRequest) -> dict[str, Any]:
        first_time = await self._memory.mark_processed(reply.correlation_id)
        if not first_time:
            return {"status": "duplicate", "correlationId": reply.correlation_id}

        customer_repo = SQLAlchemyCustomerRepository(db)
        customer = await customer_repo.get_by_id(reply.customer_id)
        if not customer or customer.tenant_id != reply.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado para el tenant indicado.",
            )

        # 1. Persistir memoria (resumen recompactado + patch de estado).
        if reply.memory.summary is not None:
            await self._memory.save_summary(
                reply.chat_id, reply.memory.summary.text, reply.memory.summary.version
            )
        if reply.memory.state_patch:
            await self._memory.merge_state(reply.chat_id, reply.memory.state_patch)

        bot_session_repo = SQLAlchemyBotSessionRepository(db)
        bot_session = await bot_session_repo.get_by_tenant_and_phone(reply.tenant_id, customer.phone)
        if not bot_session:
            bot_session = DomainBotSession(
                tenant_id=reply.tenant_id,
                customer_phone=customer.phone,
                automation_mode="AUTOMATED",
            )

        state_patch = reply.memory.state_patch or {}
        self._apply_state_to_session(bot_session, state_patch)
        await bot_session_repo.save(bot_session)

        chat = await self._mongo.get_or_create_chat(
            reply.tenant_id, reply.customer_id, platform=reply.channel
        )

        await self._execute_actions(
            db=db,
            tenant_id=reply.tenant_id,
            customer=customer,
            actions=reply.actions,
            state_patch=state_patch,
            bot_session=bot_session,
        )
        await bot_session_repo.save(bot_session)

        # 2. Handoff: el bot cede a un humano -> no auto-responder, solo avisar.
        if reply.handoff:
            await self._set_human_mode(
                tenant_id=reply.tenant_id,
                customer=customer,
                bot_session=bot_session,
                bot_session_repo=bot_session_repo,
            )
            return {"status": "handoff"}

        content = reply.reply.content.strip() or f"[{reply.reply.type.title()}]"

        # 3. Enviar al cliente por el canal (reusa la capa de canal del backend).
        external_id: str | None = None
        if reply.channel == "WHATSAPP" and not settings.N8N_BOT_STUB:
            external_id = await self._send_whatsapp(db, reply.tenant_id, customer.phone, content)

        # 4. Guardar OUTBOUND en el historial.
        msg = await self._mongo.save_message(
            chat_id=chat["_id"],
            direction="OUTBOUND",
            message_type=reply.reply.type,
            content=content,
            external_id=external_id,
            media_url=reply.reply.media_url,
            status="SENT",
        )

        # 5. Reflejar en la pantalla de chat de los agentes conectados.
        await ws_manager.broadcast(
            reply.tenant_id,
            {
                "type": "new_message",
                "customerId": str(reply.customer_id),
                "customerName": customer.name,
                "preview": content[:80],
                "lastMessageAt": str(msg.get("sentAt", "")),
            },
        )

        return {"status": "sent", "messageId": str(msg["_id"])}

    async def _send_whatsapp(
        self, db: AsyncSession, tenant_id: Any, customer_phone: str, body: str
    ) -> str | None:
        tenant_repo = SQLAlchemyTenantRepository(db)
        tenant = await tenant_repo.get_by_id(tenant_id)
        if not tenant or not tenant.phone_number_id:
            logger.warning("Bot reply para tenant sin phone_number_id: %s", tenant_id)
            return None

        credential_repo = SQLAlchemyTenantCredentialRepository(db)
        credential = await credential_repo.get_by_tenant_and_type(tenant_id, "whatsapp_api_token")
        if not credential:
            logger.warning("Bot reply sin token de WhatsApp configurado: %s", tenant_id)
            return None

        access_token = decrypt_value(credential.encrypted_value)
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": _canonical_phone(customer_phone),
            "type": "text",
            "text": {"body": body},
        }
        try:
            result = await send_whatsapp_message(
                phone_number_id=tenant.phone_number_id,
                access_token=access_token,
                payload=payload,
            )
            return result.message_id or None
        except WhatsAppCloudAPIError as exc:
            logger.warning("Envío del bot por WhatsApp falló: %s", exc.message)
            return None

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except Exception:
            return None

    def _apply_state_to_session(self, bot_session: DomainBotSession, state_patch: dict[str, Any]) -> None:
        if not state_patch:
            return

        bot_session.temp_name = state_patch.get("nombre") or bot_session.temp_name
        bot_session.temp_email = state_patch.get("correo") or bot_session.temp_email
        bot_session.temp_organization = state_patch.get("organizacion") or bot_session.temp_organization
        bot_session.temp_service = state_patch.get("servicio") or bot_session.temp_service
        bot_session.temp_description = state_patch.get("descripcion") or bot_session.temp_description

        parsed_date = self._parse_datetime(state_patch.get("fecha_hora"))
        if parsed_date:
            bot_session.temp_appointment_date = parsed_date

        bot_session.temp_folio = state_patch.get("folio") or bot_session.temp_folio
        bot_session.context_json = {**(bot_session.context_json or {}), **state_patch}

    async def _set_human_mode(
        self,
        *,
        tenant_id: Any,
        customer: Customer,
        bot_session: DomainBotSession,
        bot_session_repo: SQLAlchemyBotSessionRepository,
    ) -> None:
        bot_session.automation_mode = "HUMAN"
        await bot_session_repo.save(bot_session)
        await ws_manager.broadcast(
            tenant_id,
            {
                "type": "automation_mode_changed",
                "customerId": str(customer.id),
                "customerName": customer.name,
                "mode": "HUMAN",
                "changedBy": "workflow",
            },
        )
        await ws_manager.broadcast(
            tenant_id,
            {"type": "handoff", "customerId": str(customer.id), "customerName": customer.name},
        )

    async def _execute_actions(
        self,
        *,
        db: AsyncSession,
        tenant_id: Any,
        customer: Customer,
        actions: list[dict[str, Any]],
        state_patch: dict[str, Any],
        bot_session: DomainBotSession,
    ) -> None:
        if not actions:
            return

        appt_repo = SQLAlchemyAppointmentRepository(db)
        customer_repo = SQLAlchemyCustomerRepository(db)

        for action in actions:
            if not isinstance(action, dict):
                continue

            action_type = str(action.get("type", "")).upper()
            payload = action.get("payload", {}) or {}
            if not isinstance(payload, dict):
                payload = {}
            data = {**state_patch, **payload}

            if action_type == "BOOK_APPOINTMENT":
                await self._book_appointment(db, tenant_id, customer, data, bot_session, appt_repo, customer_repo)
            elif action_type in ("HUMAN_ESCALATION", "ESCALATE_TO_HUMAN"):
                bot_session.automation_mode = "HUMAN"
                await ws_manager.broadcast(
                    tenant_id,
                    {
                        "type": "automation_mode_changed",
                        "customerId": str(customer.id),
                        "customerName": customer.name,
                        "mode": "HUMAN",
                        "changedBy": "workflow",
                    },
                )
            elif action_type == "UPDATE_LEAD_STATUS":
                new_status = data.get("status")
                if new_status:
                    try:
                        customer.change_status(str(new_status))
                        await customer_repo.save(customer)
                    except Exception as exc:
                        logger.warning("Error al actualizar lead_status para customer %s: %s", customer.id, exc)
            elif action_type == "RESCHEDULE_APPOINTMENT":
                await self._reschedule_appointment(customer, data, appt_repo)
            elif action_type == "CANCEL_APPOINTMENT":
                latest_appt = await appt_repo.get_latest_by_customer(customer.id)
                if latest_appt:
                    latest_appt.update(status="CANCELLED")
                    await appt_repo.save(latest_appt)
            elif action_type == "RESEND_EMAIL":
                new_email = data.get("correo")
                if new_email and new_email != customer.email:
                    customer.update_info(name=customer.name, email=str(new_email))
                    await customer_repo.save(customer)

    async def _book_appointment(
        self,
        db: AsyncSession,
        tenant_id: Any,
        customer: Customer,
        data: dict[str, Any],
        bot_session: DomainBotSession,
        appt_repo: SQLAlchemyAppointmentRepository,
        customer_repo: SQLAlchemyCustomerRepository,
    ) -> None:
        start_at = self._parse_datetime(data.get("fecha_hora"))
        if not start_at:
            logger.warning("No se pudo parsear fecha_hora para BOOK_APPOINTMENT: %s", data.get("fecha_hora"))
            return

        duration = 60
        service_id = None
        service_name = data.get("servicio")
        if service_name:
            service_repo = SQLAlchemyServiceRepository(db)
            services = await service_repo.get_by_tenant(tenant_id)
            for service in services:
                if service.name.lower() == str(service_name).lower():
                    duration = service.duration_minutes
                    service_id = service.id
                    break

        appointment = DomainAppointment(
            tenant_id=tenant_id,
            customer_id=customer.id,
            service_id=service_id,
            start_at=start_at,
            end_at=start_at + timedelta(minutes=duration),
            status="CONFIRMED",
            notes=data.get("descripcion"),
        )
        await appt_repo.save(appointment)
        bot_session.clear_temp()

        new_name = data.get("nombre")
        new_email = data.get("correo")
        if (new_name and new_name != customer.name) or (new_email and new_email != customer.email):
            customer.update_info(
                name=str(new_name or customer.name),
                email=str(new_email or customer.email) if (new_email or customer.email) else None,
            )
            await customer_repo.save(customer)

    async def _reschedule_appointment(
        self,
        customer: Customer,
        data: dict[str, Any],
        appt_repo: SQLAlchemyAppointmentRepository,
    ) -> None:
        new_start = self._parse_datetime(data.get("nueva_fecha_hora") or data.get("fecha_hora"))
        if not new_start:
            return

        latest_appt = await appt_repo.get_latest_by_customer(customer.id)
        if latest_appt:
            duration = int((latest_appt.end_at - latest_appt.start_at).total_seconds() / 60)
            latest_appt.update(
                start_at=new_start,
                end_at=new_start + timedelta(minutes=duration),
                status="CONFIRMED",
            )
            await appt_repo.save(latest_appt)
