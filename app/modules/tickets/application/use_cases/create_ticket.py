import uuid
from app.modules.tickets.domain.entities.ticket import Ticket
from app.modules.tickets.domain.ports.ticket_repository import TicketRepository
from app.modules.tickets.infrastructure.messaging.publishers import publish_ticket_created
from app.platform.messaging.event_bus import EventBus


class CreateTicketUseCase:
    def __init__(self, ticket_repository: TicketRepository, event_bus: EventBus | None = None):
        self.ticket_repository = ticket_repository
        self.event_bus = event_bus

    async def execute(
        self,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        title: str,
        description: str | None = None,
        category: str = "INQUIRY",
        priority: str = "MEDIUM",
        assigned_to: uuid.UUID | None = None,
    ) -> Ticket:
        ticket = Ticket(
            tenant_id=tenant_id,
            customer_id=customer_id,
            title=title.strip(),
            description=description.strip() if description else None,
            category=category,
            priority=priority,
            assigned_to=assigned_to,
        )
        saved = await self.ticket_repository.save(ticket)
        await publish_ticket_created(self.event_bus, saved)
        return saved
