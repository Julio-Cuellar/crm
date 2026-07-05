import uuid
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_value
from app.domain.entities.user import User
from app.infrastructure.db.repositories.mongo_chat_history_repository import MongoChatHistoryRepository
from app.infrastructure.db.repositories.sqlalchemy_customer_repository import SQLAlchemyCustomerRepository
from app.infrastructure.db.repositories.sqlalchemy_tenant_credential_repository import (
    SQLAlchemyTenantCredentialRepository,
)
from app.infrastructure.db.repositories.sqlalchemy_tenant_repository import SQLAlchemyTenantRepository
from app.infrastructure.db.session import get_db
from app.infrastructure.messaging.whatsapp_cloud_api import (
    WhatsAppCloudAPIError,
    send_whatsapp_message,
)
from app.interfaces.api.dependencies.auth_bearer import get_current_user
from app.interfaces.api.schemas.chat import ChatResponse, MessageResponse, SendMessageRequest, ChatModeUpdateRequest
from app.infrastructure.db.repositories.sqlalchemy_bot_session_repository import SQLAlchemyBotSessionRepository
from app.infrastructure.websocket.manager import ws_manager

router = APIRouter(prefix="/chats", tags=["Chats"])


def _canonical_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if digits:
        return f"+{digits}"
    return phone.strip()


async def _load_whatsapp_config(db: AsyncSession, tenant_id: uuid.UUID) -> tuple[str, str]:
    tenant_repo = SQLAlchemyTenantRepository(db)
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado.")

    if not tenant.phone_number_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El tenant no tiene configurado un Phone Number ID de WhatsApp.",
        )

    credential_repo = SQLAlchemyTenantCredentialRepository(db)
    credential = await credential_repo.get_by_tenant_and_type(tenant_id, "whatsapp_api_token")
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El tenant no tiene configurado un token de acceso de WhatsApp.",
        )

    access_token = decrypt_value(credential.encrypted_value)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token de acceso de WhatsApp está vacío.",
        )

    return tenant.phone_number_id, access_token


def _build_outbound_payload(message_in: SendMessageRequest, customer_phone: str) -> dict[str, object]:
    message_type = message_in.type.upper()

    if message_type == "TEXT":
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": customer_phone,
            "type": "text",
            "text": {
                "body": message_in.content,
            },
        }

    if message_type == "IMAGE":
        if not message_in.media_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para enviar una imagen se requiere mediaUrl.",
            )
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": customer_phone,
            "type": "image",
        }
        image_payload = {"link": message_in.media_url}
        if message_in.content.strip():
            image_payload["caption"] = message_in.content.strip()
        payload["image"] = image_payload
        return payload

    if message_type == "DOCUMENT":
        if not message_in.media_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para enviar un documento se requiere mediaUrl.",
            )
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": customer_phone,
            "type": "document",
        }
        document_payload = {"link": message_in.media_url}
        if message_in.content.strip():
            document_payload["caption"] = message_in.content.strip()
        payload["document"] = document_payload
        return payload

    if message_type == "AUDIO":
        if not message_in.media_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para enviar un audio se requiere mediaUrl.",
            )
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": customer_phone,
            "type": "audio",
            "audio": {
                "link": message_in.media_url,
            },
        }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Tipo de mensaje no soportado: {message_in.type}",
    )


@router.get("", response_model=list[ChatResponse])
async def list_chats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = current_user.tenant_id

    mongo_repo = MongoChatHistoryRepository()
    raw_chats = await mongo_repo.list_chats_by_tenant(tenant_id)

    # 1. Obtener los IDs de cliente únicos
    customer_ids = []
    for rc in raw_chats:
        cid = rc.get("customerId")
        if cid:
            try:
                customer_ids.append(uuid.UUID(str(cid)))
            except ValueError:
                continue

    # 2. Cargar Customers en bloque
    from app.infrastructure.db.models.customer import Customer as DbCustomer
    from app.infrastructure.db.models.bot_session import BotSession as DbBotSession
    from sqlalchemy import select

    customers_map = {}
    if customer_ids:
        stmt_cust = select(DbCustomer).where(DbCustomer.id.in_(customer_ids))
        res_cust = await db.execute(stmt_cust)
        customers_map = {c.id: c for c in res_cust.scalars().all()}

    # 3. Cargar BotSessions en bloque
    phones = [c.phone for c in customers_map.values()]
    bot_sessions_map = {}
    if phones:
        stmt_bot = select(DbBotSession).where(
            DbBotSession.tenant_id == tenant_id, 
            DbBotSession.customer_phone.in_(phones)
        )
        res_bot = await db.execute(stmt_bot)
        bot_sessions_map = {b.customer_phone: b for b in res_bot.scalars().all()}

    # 4. Obtener último mensaje para preview
    from app.infrastructure.db.mongo.mongo_client import mongo_client
    from datetime import datetime

    chat_ids = [str(rc["_id"]) for rc in raw_chats]
    last_messages_map = {}
    if chat_ids:
        db_mongo = mongo_client.db
        pipeline = [
            {"$match": {"historyChatId": {"$in": chat_ids}}},
            {"$sort": {"sentAt": -1}},
            {"$group": {
                "_id": "$historyChatId",
                "content": {"$first": "$content"},
                "type": {"$first": "$type"},
                "sentAt": {"$first": "$sentAt"}
            }}
        ]
        cursor = db_mongo.messages.aggregate(pipeline)
        agg_res = await cursor.to_list(length=len(chat_ids))
        last_messages_map = {r["_id"]: r for r in agg_res}

    chats_list = []
    for raw_chat in raw_chats:
        customer_id_str = raw_chat.get("customerId")
        if not customer_id_str:
            continue

        try:
            customer_id = uuid.UUID(str(customer_id_str))
        except ValueError:
            continue

        customer = customers_map.get(customer_id)
        if not customer:
            customer_name = "Cliente Desconocido"
            customer_phone = "Desconocido"
            customer_email = None
            lead_status = "NEW"
            automation_mode = "AUTOMATED"
        else:
            customer_name = customer.name
            customer_phone = customer.phone
            customer_email = customer.email
            lead_status = customer.lead_status
            
            # Obtener el modo de la sesión
            bot_session = bot_sessions_map.get(customer.phone)
            automation_mode = bot_session.automation_mode if bot_session else "AUTOMATED"

        chat_id_str = str(raw_chat["_id"])
        last_msg = last_messages_map.get(chat_id_str)
        last_message_preview = last_msg.get("content")[:80] if last_msg and last_msg.get("content") else None
        last_message_type = last_msg.get("type") if last_msg else None

        chats_list.append(
            ChatResponse(
                id=chat_id_str,
                tenant_id=tenant_id,
                customer_id=customer_id,
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email,
                lead_status=lead_status,
                automation_mode=automation_mode,
                last_message_preview=last_message_preview,
                last_message_type=last_message_type,
                platform=raw_chat.get("platform", "WHATSAPP"),
                external_thread_id=raw_chat.get("externalThreadId"),
                status=raw_chat.get("status", "ACTIVE"),
                created_at=raw_chat["createdAt"],
                last_message_at=raw_chat["lastMessageAt"],
            )
        )

    chats_list.sort(key=lambda x: x.last_message_at, reverse=True)
    return chats_list


@router.get("/{customer_id}/messages", response_model=list[MessageResponse])
async def get_chat_messages(
    customer_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = current_user.tenant_id

    customer_repo = SQLAlchemyCustomerRepository(db)
    customer = await customer_repo.get_by_id(customer_id)
    if not customer or customer.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Cliente no encontrado en este Tenant.")

    mongo_repo = MongoChatHistoryRepository()
    chat = await mongo_repo.get_or_create_chat(tenant_id, customer_id, platform="WHATSAPP")

    chat_id = chat["_id"]
    raw_messages = await mongo_repo.get_messages_by_chat_id(chat_id)

    return [
        MessageResponse(
            id=str(msg["_id"]),
            history_chat_id=str(msg["historyChatId"]),
            direction=msg["direction"],
            type=msg["type"],
            content=msg["content"],
            media_url=msg.get("mediaUrl"),
            external_id=msg.get("externalId"),
            sent_at=msg["sentAt"],
            status=msg.get("status", "SENT"),
        )
        for msg in raw_messages
    ]


@router.post("/{customer_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_chat_message(
    customer_id: uuid.UUID,
    message_in: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = current_user.tenant_id

    customer_repo = SQLAlchemyCustomerRepository(db)
    customer = await customer_repo.get_by_id(customer_id)
    if not customer or customer.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Cliente no encontrado en este Tenant.")

    phone_number_id, access_token = await _load_whatsapp_config(db, tenant_id)
    customer_phone = _canonical_phone(customer.phone)
    outbound_payload = _build_outbound_payload(message_in, customer_phone)

    try:
        send_result = await send_whatsapp_message(
            phone_number_id=phone_number_id,
            access_token=access_token,
            payload=outbound_payload,
        )
    except WhatsAppCloudAPIError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "code": "WHATSAPP_SEND_FAILED",
                "message": exc.message,
                "details": exc.details,
            },
        ) from exc

    mongo_repo = MongoChatHistoryRepository()
    chat = await mongo_repo.get_or_create_chat(tenant_id, customer_id, platform="WHATSAPP")
    chat_id = chat["_id"]

    outbound_type = message_in.type.upper()
    outbound_content = message_in.content.strip() if message_in.content else ""
    if not outbound_content:
        outbound_content = f"[{outbound_type.title()}]"

    msg = await mongo_repo.save_message(
        chat_id=chat_id,
        direction="OUTBOUND",
        message_type=outbound_type,
        content=outbound_content,
        external_id=send_result.message_id or None,
        media_url=message_in.media_url,
        status="SENT",
    )

    return MessageResponse(
        id=str(msg["_id"]),
        history_chat_id=str(msg["historyChatId"]),
        direction=msg["direction"],
        type=msg["type"],
        content=msg["content"],
        media_url=msg.get("mediaUrl"),
        external_id=msg.get("externalId"),
        sent_at=msg["sentAt"],
        status=msg["status"],
    )


@router.post("/{customer_id}/incoming", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def receive_incoming_message_sim(
    customer_id: uuid.UUID,
    message_in: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tenant_id = current_user.tenant_id

    customer_repo = SQLAlchemyCustomerRepository(db)
    customer = await customer_repo.get_by_id(customer_id)
    if not customer or customer.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Cliente no encontrado en este Tenant.")

    mongo_repo = MongoChatHistoryRepository()
    chat = await mongo_repo.get_or_create_chat(tenant_id, customer_id, platform="WHATSAPP")
    chat_id = chat["_id"]

    msg = await mongo_repo.save_message(
        chat_id=chat_id,
        direction="INBOUND",
        message_type=message_in.type,
        content=message_in.content,
        media_url=message_in.media_url,
        status="DELIVERED",
    )

    return MessageResponse(
        id=str(msg["_id"]),
        history_chat_id=str(msg["historyChatId"]),
        direction=msg["direction"],
        type=msg["type"],
        content=msg["content"],
        media_url=msg.get("mediaUrl"),
        external_id=msg.get("externalId"),
        sent_at=msg["sentAt"],
        status=msg["status"],
    )


@router.patch("/{customer_id}/mode", response_model=dict)
async def update_chat_automation_mode(
    customer_id: uuid.UUID,
    payload: ChatModeUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tenant_id = current_user.tenant_id

    customer_repo = SQLAlchemyCustomerRepository(db)
    customer = await customer_repo.get_by_id(customer_id)
    if not customer or customer.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Cliente no encontrado en este Tenant.")

    bot_session_repo = SQLAlchemyBotSessionRepository(db)
    bot_session = await bot_session_repo.get_by_tenant_and_phone(tenant_id, customer.phone)
    if not bot_session:
        from app.domain.entities.bot_session import BotSession as DomainBotSession
        bot_session = DomainBotSession(
            tenant_id=tenant_id,
            customer_phone=customer.phone,
            automation_mode=payload.mode
        )
    else:
        bot_session.automation_mode = payload.mode
        
    await bot_session_repo.save(bot_session)

    # Notificar cambio por WebSocket
    await ws_manager.broadcast(tenant_id, {
        "type": "automation_mode_changed",
        "customerId": str(customer.id),
        "customerName": customer.name,
        "mode": payload.mode,
        "changedBy": "staff"
    })

    from datetime import datetime
    return {
        "customer_id": str(customer.id),
        "automation_mode": payload.mode,
        "updated_at": datetime.now().isoformat()
    }
