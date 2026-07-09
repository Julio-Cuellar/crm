from typing import Any

from app.modules.tenants.domain.entities.tenant import Tenant
from app.platform.messaging.event_bus import EventBus


async def publish_tenant_updated(event_bus: EventBus | None, tenant: Tenant) -> None:
    if event_bus:
        payload: dict[str, Any] = {
            "tenantId": str(tenant.id),
            "name": tenant.name,
            "timezone": tenant.timezone,
            "locale": tenant.locale,
            "mode": tenant.mode,
        }
        await event_bus.publish("tenant.updated", payload)
