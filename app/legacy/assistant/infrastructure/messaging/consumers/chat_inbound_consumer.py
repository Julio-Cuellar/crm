import uuid
from typing import Any

import aio_pika

from app.platform.db.session import async_session_factory
from app.platform.messaging.consumer_base import RabbitMQConsumer
from app.modules.customers.infrastructure.db.repositories.sqlalchemy_customer_repository import SQLAlchemyCustomerRepository
from app.modules.tenants.infrastructure.db.repositories.sqlalchemy_tenant_repository import SQLAlchemyTenantRepository
from app.modules.conversations.infrastructure.db.repositories.sqlalchemy_bot_session_repository import SQLAlchemyBotSessionRepository
from app.legacy.assistant.application.use_cases.dispatch_to_bot import DispatchToBotUseCase, load_tenant_agent_prompt
from app.legacy.assistant.infrastructure.n8n.n8n_bot_gateway import N8nBotGateway
from app.legacy.assistant.infrastructure.db.repositories.redis_conversation_memory_repository import (
    RedisConversationMemoryRepository,
)


class ChatInboundConsumer:
    """Reproduce el dispatch al bot para mensajes entrantes simulados desde
    `conversations` (`POST /chats/{id}/incoming`). `conversations` no puede llamar a
    `DispatchToBotUseCase` directamente (vive en `assistant`, todavía en app/legacy/),
    así que publica `chat.inbound_simulated` y este consumer reproduce exactamente el
    mismo flujo que antes vivía inline en el router de chats."""

    def __init__(self, connection: aio_pika.RobustConnection):
        self._consumer = RabbitMQConsumer(
            connection,
            queue_name="assistant.chat_inbound_simulated",
            routing_key="chat.inbound_simulated",
            handler=self._handle,
            label="assistant.chat_inbound_simulated",
        )

    async def start(self) -> None:
        await self._consumer.start()

    async def stop(self) -> None:
        await self._consumer.stop()

    async def _handle(self, event_data: dict[str, Any]) -> None:
        payload = event_data.get("payload", {})
        tenant_id = uuid.UUID(payload["tenantId"])
        customer_id = uuid.UUID(payload["customerId"])
        chat_id = payload["chatId"]
        content = payload.get("content")
        message_type = payload.get("messageType", "TEXT")
        media_url = payload.get("mediaUrl")

        async with async_session_factory() as db:
            customer_repo = SQLAlchemyCustomerRepository(db)
            customer = await customer_repo.get_by_id(customer_id)
            if not customer:
                return

            tenant_repo = SQLAlchemyTenantRepository(db)
            tenant = await tenant_repo.get_by_id(tenant_id)
            if not tenant:
                return

            bot_session_repo = SQLAlchemyBotSessionRepository(db)
            bot_session = await bot_session_repo.get_by_tenant_and_phone(tenant_id, customer.phone)

            memory_repo = RedisConversationMemoryRepository()
            if bot_session and bot_session.context_json:
                await memory_repo.merge_state(chat_id, bot_session.context_json)

            dispatch_uc = DispatchToBotUseCase(
                bot_gateway=N8nBotGateway(),
                memory_repo=memory_repo,
            )
            agent_prompt = await load_tenant_agent_prompt(db, tenant_id)
            await dispatch_uc.execute(
                tenant=tenant,
                customer=customer,
                chat={"_id": chat_id},
                content=content,
                message_type=message_type,
                media_url=media_url,
                agent_prompt=agent_prompt,
            )
