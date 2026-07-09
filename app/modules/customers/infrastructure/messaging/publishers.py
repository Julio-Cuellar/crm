from typing import Any

from app.modules.customers.domain.entities.customer import Customer
from app.platform.messaging.event_bus import EventBus


def _customer_payload(customer: Customer) -> dict[str, Any]:
    return {
        "customerId": str(customer.id),
        "tenantId": str(customer.tenant_id),
        "name": customer.name,
        "phone": customer.phone,
        "email": customer.email,
        "leadStatus": customer.lead_status,
        "updatedAt": customer.updated_at.isoformat(),
    }


async def publish_customer_created(event_bus: EventBus | None, customer: Customer) -> None:
    if event_bus:
        await event_bus.publish("customer.created", _customer_payload(customer))


async def publish_customer_updated(event_bus: EventBus | None, customer: Customer) -> None:
    if event_bus:
        await event_bus.publish("customer.updated", _customer_payload(customer))


async def publish_customer_deleted(event_bus: EventBus | None, customer_id, tenant_id) -> None:
    if event_bus:
        await event_bus.publish("customer.deleted", {"customerId": str(customer_id), "tenantId": str(tenant_id)})
