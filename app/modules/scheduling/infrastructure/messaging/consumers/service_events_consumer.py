import uuid
from decimal import Decimal
from typing import Any

import aio_pika

from app.platform.db.session import async_session_factory
from app.platform.messaging.consumer_base import RabbitMQConsumer
from app.modules.scheduling.infrastructure.db.repositories.service_projection_repository import (
    ServiceProjectionRepository,
)


class ServiceEventsConsumer:
    """Mantiene `scheduling_service_projection` al día escuchando
    `service.created`/`service.updated`/`service.deleted` del módulo `catalog`."""

    def __init__(self, connection: aio_pika.RobustConnection):
        self._consumer = RabbitMQConsumer(
            connection,
            queue_name="scheduling.service_events",
            routing_key=["service.created", "service.updated", "service.deleted"],
            handler=self._handle,
            label="scheduling.service_events",
        )

    async def start(self) -> None:
        await self._consumer.start()

    async def stop(self) -> None:
        await self._consumer.stop()

    async def _handle(self, event_data: dict[str, Any]) -> None:
        event_name = event_data.get("event")
        payload = event_data.get("payload", {})
        service_id_str = payload.get("serviceId")
        if not service_id_str:
            return
        service_id = uuid.UUID(service_id_str)

        async with async_session_factory() as session:
            repo = ServiceProjectionRepository(session)
            if event_name == "service.deleted":
                await repo.delete(service_id)
            else:
                price = payload.get("price")
                await repo.upsert(
                    service_id=service_id,
                    tenant_id=uuid.UUID(payload["tenantId"]),
                    name=payload.get("name", ""),
                    duration_minutes=payload.get("durationMinutes", 60),
                    price=Decimal(str(price)) if price is not None else None,
                    currency=payload.get("currency", "MXN"),
                    is_active=payload.get("isActive", True),
                    source_updated_at=None,
                )
            await session.commit()
