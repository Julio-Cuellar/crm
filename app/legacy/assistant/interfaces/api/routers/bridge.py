import hashlib
import hmac
import json
import logging
import re
from collections.abc import Mapping
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.legacy.assistant.application.use_cases.dispatch_to_bot import DispatchToBotUseCase, load_tenant_agent_prompt
from app.legacy.assistant.application.use_cases.handle_bot_reply import HandleBotReplyUseCase
from app.platform.config import settings
from app.platform.security import decrypt_value
from app.modules.customers.domain.entities.customer import Customer
from app.modules.conversations.domain.entities.bot_session import BotSession as DomainBotSession
from app.modules.conversations.infrastructure.db.repositories.mongo_chat_history_repository import MongoChatHistoryRepository
from app.modules.customers.infrastructure.db.repositories.sqlalchemy_customer_repository import SQLAlchemyCustomerRepository
from app.modules.tenants.infrastructure.db.repositories.sqlalchemy_tenant_credential_repository import SQLAlchemyTenantCredentialRepository
from app.modules.tenants.infrastructure.db.repositories.sqlalchemy_tenant_repository import SQLAlchemyTenantRepository
from app.modules.conversations.infrastructure.db.repositories.sqlalchemy_bot_session_repository import SQLAlchemyBotSessionRepository
from app.modules.scheduling.infrastructure.db.repositories.sqlalchemy_appointment_repository import SQLAlchemyAppointmentRepository
from app.modules.catalog.infrastructure.db.repositories.sqlalchemy_service_repository import SQLAlchemyServiceRepository
from app.legacy.assistant.infrastructure.db.repositories.redis_conversation_memory_repository import RedisConversationMemoryRepository
from app.platform.db.session import get_db
from app.legacy.assistant.infrastructure.n8n.n8n_bot_gateway import N8nBotGateway
from app.platform.websocket.manager import ws_manager
from app.legacy.assistant.interfaces.api.schemas.bot import BotReplyRequest
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bridge", tags=["Bridge"])


def _canonical_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if digits:
        return f"+{digits}"
    return phone.strip()


def _phone_candidates(phone: str) -> list[str]:
    stripped = phone.strip()
    canonical = _canonical_phone(phone)
    candidates = [stripped]
    if canonical and canonical not in candidates:
        candidates.append(canonical)
    if stripped.startswith("+"):
        digits = re.sub(r"\D", "", stripped)
        if digits and digits not in candidates:
            candidates.append(digits)
    elif canonical.startswith("+"):
        digits = canonical.lstrip("+")
        if digits and digits not in candidates:
            candidates.append(digits)
    return candidates


def _extract_contact_name(contact: Mapping[str, Any] | None, fallback: str) -> str:
    if not contact:
        return fallback

    profile = contact.get("profile")
    if isinstance(profile, Mapping):
        name = str(profile.get("name") or "").strip()
        if name:
            return name

    name = str(contact.get("name") or "").strip()
    return name or fallback


def _extract_message_payload(message: Mapping[str, Any]) -> tuple[str, str, str | None]:
    message_type = str(message.get("type") or "TEXT").upper()

    if message_type == "TEXT":
        text = message.get("text")
        body = ""
        if isinstance(text, Mapping):
            body = str(text.get("body") or "").strip()
        return "TEXT", body, None

    if message_type == "IMAGE":
        image = message.get("image")
        caption = ""
        media_url = None
        if isinstance(image, Mapping):
            caption = str(image.get("caption") or "").strip()
            media_url = str(image.get("link") or image.get("id") or "").strip() or None
        return "IMAGE", caption or "[Imagen]", media_url

    if message_type == "AUDIO":
        audio = message.get("audio")
        media_url = None
        if isinstance(audio, Mapping):
            media_url = str(audio.get("link") or audio.get("id") or "").strip() or None
        return "AUDIO", "[Audio]", media_url

    if message_type == "DOCUMENT":
        document = message.get("document")
        media_url = None
        fallback = "[Documento]"
        if isinstance(document, Mapping):
            media_url = str(document.get("link") or document.get("id") or "").strip() or None
            fallback = str(document.get("filename") or document.get("caption") or fallback).strip() or fallback
        return "DOCUMENT", fallback, media_url

    if message_type == "LOCATION":
        location = message.get("location")
        if isinstance(location, Mapping):
            lat = location.get("latitude")
            lon = location.get("longitude")
            if lat is not None and lon is not None:
                return "LOCATION", f"{lat}, {lon}", None
        return "LOCATION", "[Ubicación]", None

    fallback_content = str(message.get("text", {}).get("body") if isinstance(message.get("text"), Mapping) else "").strip()
    return message_type, fallback_content or f"[{message_type.title()}]", None


def _verify_signature(raw_body: bytes, signature_header: str | None, app_secret: str | None) -> None:
    if not app_secret:
        return

    if not signature_header:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Webhook sin firma de validación.")

    prefix, _, provided_signature = signature_header.partition("=")
    if prefix != "sha256" or not provided_signature:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Firma de webhook inválida.")

    expected_signature = hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, provided_signature):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Firma de webhook inválida.")


def _extract_first_phone_number_id(payload: Mapping[str, Any]) -> str:
    for entry in payload.get("entry", []):
        if not isinstance(entry, Mapping):
            continue
        for change in entry.get("changes", []):
            if not isinstance(change, Mapping):
                continue
            value = change.get("value", {})
            if not isinstance(value, Mapping):
                continue
            metadata = value.get("metadata", {})
            if isinstance(metadata, Mapping):
                phone_id = str(metadata.get("phone_number_id") or "").strip()
                if phone_id:
                    return phone_id
            phone_id = str(value.get("phone_number_id") or "").strip()
            if phone_id:
                return phone_id
    return ""


class EscalateRequest(BaseModel):
    reason: str | None = None


async def _find_or_create_customer(
    customer_repo: SQLAlchemyCustomerRepository,
    *,
    tenant_id: UUID,
    phone: str,
    name: str,
) -> Customer:
    for candidate in _phone_candidates(phone):
        customer = await customer_repo.get_by_phone_and_tenant(candidate, tenant_id)
        if customer:
            if name.strip() and customer.name != name.strip():
                customer.update_info(name=name, email=customer.email)
                customer = await customer_repo.save(customer)
            return customer

    customer = Customer(
        tenant_id=tenant_id,
        phone=_canonical_phone(phone),
        name=name.strip() or _canonical_phone(phone),
        lead_status="NEW",
    )
    return await customer_repo.save(customer)


async def _handle_inbound_message(
    *,
    tenant_id: UUID,
    phone_number_id: str,
    customer_repo: SQLAlchemyCustomerRepository,
    mongo_repo: MongoChatHistoryRepository,
    message: Mapping[str, Any],
    contacts_by_wa_id: dict[str, Mapping[str, Any]],
    db: AsyncSession,
) -> None:
    from_number = str(message.get("from") or "").strip()
    if not from_number:
        logger.warning("Webhook de WhatsApp sin campo 'from' en message.")
        return

    contact = contacts_by_wa_id.get(from_number)
    customer_name = _extract_contact_name(contact, fallback=_canonical_phone(from_number))
    customer = await _find_or_create_customer(
        customer_repo,
        tenant_id=tenant_id,
        phone=from_number,
        name=customer_name,
    )

    # Buscar o crear la sesión de bot para el cliente
    bot_session_repo = SQLAlchemyBotSessionRepository(db)
    bot_session = await bot_session_repo.get_by_tenant_and_phone(tenant_id, customer.phone)
    if not bot_session:
        bot_session = DomainBotSession(
            tenant_id=tenant_id,
            customer_phone=customer.phone,
            automation_mode="AUTOMATED"
        )
        bot_session = await bot_session_repo.save(bot_session)

    # Actualizar estado de cliente nuevo a CONTACTED automáticamente
    if customer.lead_status == "NEW":
        try:
            customer.change_status("CONTACTED")
            await customer_repo.save(customer)
        except Exception as e:
            logger.warning("Error al actualizar lead_status de NEW a CONTACTED: %s", e)

    chat = await mongo_repo.get_or_create_chat(
        tenant_id,
        customer.id,
        platform="WHATSAPP",
    )

    message_type, content, media_url = _extract_message_payload(message)
    await mongo_repo.save_message(
        chat_id=chat["_id"],
        direction="INBOUND",
        message_type=message_type,
        content=content,
        external_id=str(message.get("id") or ""),
        media_url=media_url,
        status="DELIVERED",
    )

    # Notificar en tiempo real a los agentes conectados del tenant
    await ws_manager.broadcast(tenant_id, {
        "type": "new_message",
        "customerId": str(customer.id),
        "customerName": customer.name,
        "preview": content[:80],
        "lastMessageAt": chat.get("lastMessageAt", ""),
    })

    # Si la sesión del bot está pausada para humanos, omitimos n8n
    if bot_session.automation_mode == "HUMAN":
        logger.info("Conversación pausada para humanos. Omitiendo bot.")
        return

    # Despachar a n8n sin bloquear el webhook de Meta. La respuesta vuelve por
    # POST /bridge/n8n/reply, donde se envía WhatsApp y se ejecutan acciones.
    if settings.BOT_ENABLED_DEFAULT and content:
        try:
            tenant_repo = SQLAlchemyTenantRepository(db)
            tenant = await tenant_repo.get_by_id(tenant_id)
            if not tenant:
                logger.warning("No se pudo despachar bot: tenant no encontrado %s", tenant_id)
                return

            memory_repo = RedisConversationMemoryRepository()
            if bot_session.context_json:
                await memory_repo.merge_state(chat["_id"], bot_session.context_json)

            dispatch_uc = DispatchToBotUseCase(
                bot_gateway=N8nBotGateway(),
                memory_repo=memory_repo,
                mongo_repo=mongo_repo,
            )
            agent_prompt = await load_tenant_agent_prompt(db, tenant_id)
            await dispatch_uc.execute(
                tenant=tenant,
                customer=customer,
                chat=chat,
                content=content,
                message_type=message_type,
                media_url=media_url,
                external_id=str(message.get("id") or ""),
                agent_prompt=agent_prompt,
            )
        except Exception as exc:  # noqa: BLE001 - el bot no debe tumbar la recepcion
            logger.warning("No se pudo despachar el mensaje al bot: %s", exc)



async def _handle_status_update(
    *,
    mongo_repo: MongoChatHistoryRepository,
    status_update: Mapping[str, Any],
) -> None:
    message_id = str(status_update.get("id") or "").strip()
    if not message_id:
        return

    status_value = str(status_update.get("status") or "").strip().upper()
    if not status_value:
        return

    await mongo_repo.update_message_status_by_external_id(message_id, status_value)

    # Notificar cambio de estado (delivered / read) a los agentes conectados.
    # No conocemos el tenant_id aquí, así que broadcast se hace en el caller con tenant_id.
    # Se pasa como retorno para que _receive_webhook pueda hacer el broadcast.
    return {"externalId": message_id, "status": status_value}


@router.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(request: Request):
    params = request.query_params
    hub_mode = params.get("hub.mode")
    hub_challenge = params.get("hub.challenge")
    hub_verify_token = params.get("hub.verify_token")

    if (
        hub_mode == "subscribe"
        and hub_verify_token == settings.META_WEBHOOK_VERIFY_TOKEN
        and hub_challenge is not None
    ):
        return PlainTextResponse(hub_challenge, status_code=status.HTTP_200_OK)

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification token mismatch.")


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
):
    raw_body = await request.body()

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payload de webhook inválido.") from exc

    # Verificar firma con el App Secret del tenant que envía el mensaje
    first_phone_number_id = _extract_first_phone_number_id(payload)
    app_secret: str | None = None
    if first_phone_number_id:
        tenant_repo_for_sig = SQLAlchemyTenantRepository(db)
        tenant_for_sig = await tenant_repo_for_sig.get_by_phone_number_id(first_phone_number_id)
        if tenant_for_sig:
            cred_repo_for_sig = SQLAlchemyTenantCredentialRepository(db)
            cred_for_sig = await cred_repo_for_sig.get_by_tenant_and_type(tenant_for_sig.id, "whatsapp_app_secret")
            app_secret = decrypt_value(cred_for_sig.encrypted_value) if cred_for_sig else None
    _verify_signature(raw_body, x_hub_signature_256, app_secret)

    if payload.get("object") != "whatsapp_business_account":
        return JSONResponse({"status": "ignored", "reason": "unsupported_object"}, status_code=status.HTTP_200_OK)

    tenant_repo = SQLAlchemyTenantRepository(db)
    customer_repo = SQLAlchemyCustomerRepository(db)
    mongo_repo = MongoChatHistoryRepository()

    processed_messages = 0
    processed_statuses = 0

    for entry in payload.get("entry", []):
        if not isinstance(entry, Mapping):
            continue

        for change in entry.get("changes", []):
            if not isinstance(change, Mapping):
                continue

            value = change.get("value", {})
            if not isinstance(value, Mapping):
                continue

            metadata = value.get("metadata", {})
            phone_number_id = ""
            if isinstance(metadata, Mapping):
                phone_number_id = str(metadata.get("phone_number_id") or "").strip()
            if not phone_number_id:
                phone_number_id = str(value.get("phone_number_id") or "").strip()
            if not phone_number_id:
                continue

            tenant = await tenant_repo.get_by_phone_number_id(phone_number_id)
            if not tenant:
                logger.warning("Webhook recibido para phone_number_id desconocido: %s", phone_number_id)
                continue

            contacts_by_wa_id: dict[str, Mapping[str, Any]] = {}
            for contact in value.get("contacts", []):
                if not isinstance(contact, Mapping):
                    continue
                wa_id = str(contact.get("wa_id") or "").strip()
                if wa_id:
                    contacts_by_wa_id[wa_id] = contact

            for message in value.get("messages", []):
                if not isinstance(message, Mapping):
                    continue
                await _handle_inbound_message(
                    tenant_id=tenant.id,
                    phone_number_id=phone_number_id,
                    customer_repo=customer_repo,
                    mongo_repo=mongo_repo,
                    message=message,
                    contacts_by_wa_id=contacts_by_wa_id,
                    db=db,
                )
                processed_messages += 1

            for status_update in value.get("statuses", []):
                if not isinstance(status_update, Mapping):
                    continue
                result = await _handle_status_update(mongo_repo=mongo_repo, status_update=status_update)
                if result and tenant:
                    await ws_manager.broadcast(tenant.id, {"type": "message_status", **result})
                processed_statuses += 1

    return {
        "status": "ok",
        "processedMessages": processed_messages,
        "processedStatuses": processed_statuses,
    }


@router.post("/n8n/reply")
async def receive_bot_reply(
    reply: BotReplyRequest,
    db: AsyncSession = Depends(get_db),
    x_callback_secret: str | None = Header(default=None, alias="X-Callback-Secret"),
):
    """Callback de n8n: entrega la respuesta del bot para enviarla al cliente."""
    if settings.N8N_CALLBACK_SECRET:
        if not x_callback_secret or not hmac.compare_digest(
            x_callback_secret, settings.N8N_CALLBACK_SECRET
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Callback no autorizado.")

    use_case = HandleBotReplyUseCase(memory_repo=RedisConversationMemoryRepository())
    return await use_case.execute(db=db, reply=reply)


@router.get("/tenants/{tenant_id}/availability")
async def get_tenant_availability(
    tenant_id: UUID,
    start_date: str | None = None,
    db: AsyncSession = Depends(get_db),
    x_bridge_token: str | None = Header(default=None, alias="X-Bridge-Token"),
):
    """
    Endpoint seguro para que n8n consulte la disponibilidad de citas y servicios de un tenant.
    Requiere cabecera 'X-Bridge-Token' coincidente con el SECRET_KEY del sistema.
    """
    expected_token = settings.SECRET_KEY
    if expected_token and x_bridge_token != expected_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado.")

    now = datetime.now()
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usar YYYY-MM-DD")
    else:
        start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Consultamos disponibilidad para los próximos 7 días
    end_dt = start_dt + timedelta(days=7)

    appt_repo = SQLAlchemyAppointmentRepository(db)
    appointments = await appt_repo.list_by_tenant_and_range(tenant_id, start_dt, end_dt)

    service_repo = SQLAlchemyServiceRepository(db)
    services = await service_repo.get_by_tenant(tenant_id)

    busy_slots = []
    for appt in appointments:
        if appt.status != "CANCELLED":
            busy_slots.append({
                "start": appt.start_at.isoformat(),
                "end": appt.end_at.isoformat(),
                "status": appt.status
            })

    services_list = []
    for s in services:
        if s.is_active:
            services_list.append({
                "id": str(s.id),
                "name": s.name,
                "duration_minutes": s.duration_minutes,
                "price": float(s.price) if s.price else None,
                "currency": s.currency
            })

    return {
        "tenant_id": str(tenant_id),
        "busy_slots": busy_slots,
        "services": services_list
    }


@router.post("/chats/{customer_id}/escalate")
async def escalate_chat_to_human(
    customer_id: UUID,
    payload: EscalateRequest,
    db: AsyncSession = Depends(get_db),
    x_bridge_token: str | None = Header(default=None, alias="X-Bridge-Token"),
):
    expected_token = settings.SECRET_KEY
    if expected_token and x_bridge_token != expected_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado.")

    customer_repo = SQLAlchemyCustomerRepository(db)
    customer = await customer_repo.get_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado.")

    bot_session_repo = SQLAlchemyBotSessionRepository(db)
    bot_session = await bot_session_repo.get_by_tenant_and_phone(customer.tenant_id, customer.phone)
    if not bot_session:
        from app.modules.conversations.domain.entities.bot_session import BotSession as DomainBotSession
        bot_session = DomainBotSession(
            tenant_id=customer.tenant_id,
            customer_phone=customer.phone,
            automation_mode="HUMAN"
        )
    else:
        bot_session.automation_mode = "HUMAN"

    await bot_session_repo.save(bot_session)

    # Notificar a los agentes conectados vía WebSocket
    await ws_manager.broadcast(customer.tenant_id, {
        "type": "automation_mode_changed",
        "customerId": str(customer.id),
        "customerName": customer.name,
        "mode": "HUMAN",
        "changedBy": "workflow"
    })

    return {
        "customer_id": str(customer.id),
        "automation_mode": "HUMAN"
    }
