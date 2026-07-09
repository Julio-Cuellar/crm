import uuid
from typing import Any

import aio_pika

from app.platform.db.session import async_session_factory
from app.platform.messaging.consumer_base import RabbitMQConsumer
from app.modules.tickets.infrastructure.db.repositories.customer_projection_repository import (
    CustomerProjectionRepository,
)


class CustomerEventsConsumer:
    """Mantiene `tickets_customer_projection` al día escuchando
    `customer.created`/`customer.updated`/`customer.deleted` del módulo `customers`."""

    def __init__(self, connection: aio_pika.RobustConnection):
        self._consumer = RabbitMQConsumer(
            connection,
            queue_name="tickets.customer_events",
            routing_key=["customer.created", "customer.updated", "customer.deleted"],
            handler=self._handle,
            label="tickets.customer_events",
        )

    async def start(self) -> None:
        await self._consumer.start()

    async def stop(self) -> None:
        await self._consumer.stop()

    async def _handle(self, event_data: dict[str, Any]) -> None:
        event_name = event_data.get("event")
        payload = event_data.get("payload", {})
        customer_id_str = payload.get("customerId")
        if not customer_id_str:
            return
        customer_id = uuid.UUID(customer_id_str)

        async with async_session_factory() as session:
            repo = CustomerProjectionRepository(session)
            if event_name == "customer.deleted":
                await repo.delete(customer_id)
            else:
                await repo.upsert(
                    customer_id=customer_id,
                    tenant_id=uuid.UUID(payload["tenantId"]),
                    name=payload.get("name", ""),
                )
            await session.commit()
