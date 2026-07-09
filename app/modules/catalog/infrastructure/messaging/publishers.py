from typing import Any

from app.modules.catalog.domain.entities.service import Service
from app.platform.messaging.event_bus import EventBus


def _service_payload(service: Service) -> dict[str, Any]:
    return {
        "serviceId": str(service.id),
        "tenantId": str(service.tenant_id),
        "name": service.name,
        "durationMinutes": service.duration_minutes,
        "price": float(service.price) if service.price is not None else None,
        "currency": service.currency,
        "isActive": service.is_active,
        "updatedAt": service.updated_at.isoformat(),
    }


async def publish_service_created(event_bus: EventBus | None, service: Service) -> None:
    if event_bus:
        await event_bus.publish("service.created", _service_payload(service))


async def publish_service_updated(event_bus: EventBus | None, service: Service) -> None:
    if event_bus:
        await event_bus.publish("service.updated", _service_payload(service))


async def publish_service_deleted(event_bus: EventBus | None, service_id, tenant_id) -> None:
    if event_bus:
        await event_bus.publish("service.deleted", {"serviceId": str(service_id), "tenantId": str(tenant_id)})
