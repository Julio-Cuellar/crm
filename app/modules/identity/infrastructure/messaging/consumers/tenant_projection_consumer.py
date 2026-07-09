import uuid
from typing import Any

import aio_pika

from app.platform.db.session import async_session_factory
from app.platform.messaging.consumer_base import RabbitMQConsumer
from app.modules.identity.infrastructure.db.repositories.tenant_projection_repository import (
    TenantProjectionRepository,
)


class TenantProjectionConsumer:
    """Mantiene `identity_tenant_projection` (id, name) al día escuchando
    `tenant.created`/`tenant.updated` del módulo `tenants`, para que `identity`
    pueda mostrar el nombre del negocio en invitaciones sin leer la tabla de
    `tenants` directamente."""

    def __init__(self, connection: aio_pika.RobustConnection):
        self._consumer = RabbitMQConsumer(
            connection,
            queue_name="identity.tenant_projection",
            routing_key=["tenant.created", "tenant.updated"],
            handler=self._handle,
            label="identity.tenant_projection",
        )

    async def start(self) -> None:
        await self._consumer.start()

    async def stop(self) -> None:
        await self._consumer.stop()

    async def _handle(self, event_data: dict[str, Any]) -> None:
        payload = event_data.get("payload", {})
        tenant_id_str = payload.get("tenantId")
        name = payload.get("name")
        if not tenant_id_str or not name:
            return

        async with async_session_factory() as session:
            repo = TenantProjectionRepository(session)
            await repo.upsert(uuid.UUID(tenant_id_str), name, source_updated_at=None)
            await session.commit()
