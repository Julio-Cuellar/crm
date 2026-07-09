from typing import Any

from app.modules.tickets.domain.entities.ticket import Ticket
from app.platform.messaging.event_bus import EventBus


def _ticket_payload(ticket: Ticket) -> dict[str, Any]:
    return {
        "ticketId": str(ticket.id),
        "tenantId": str(ticket.tenant_id),
        "customerId": str(ticket.customer_id),
        "status": ticket.status,
        "priority": ticket.priority,
    }


async def publish_ticket_created(event_bus: EventBus | None, ticket: Ticket) -> None:
    if event_bus:
        await event_bus.publish("ticket.created", _ticket_payload(ticket))


async def publish_ticket_updated(event_bus: EventBus | None, ticket: Ticket) -> None:
    if event_bus:
        await event_bus.publish("ticket.updated", _ticket_payload(ticket))
