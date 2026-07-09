import uuid
from app.modules.tickets.domain.entities.ticket import Ticket
from app.modules.tickets.domain.ports.ticket_repository import TicketRepository
from app.modules.tickets.domain.exceptions.tickets import TicketNotFoundException
from app.modules.tickets.infrastructure.messaging.publishers import publish_ticket_updated
from app.platform.messaging.event_bus import EventBus


class UpdateTicketUseCase:
    def __init__(self, ticket_repository: TicketRepository, event_bus: EventBus | None = None):
        self.ticket_repository = ticket_repository
        self.event_bus = event_bus

    async def execute(
        self,
        ticket_id: uuid.UUID,
        title: str | None = None,
        description: str | None = None,
        category: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        assigned_to: uuid.UUID | None = None,
    ) -> Ticket:
        ticket = await self.ticket_repository.get_by_id(ticket_id)
        if not ticket:
            raise TicketNotFoundException(f"No se encontró ningún ticket con el ID '{ticket_id}'.")

        ticket.update(
            title=title,
            description=description,
            category=category,
            status=status,
            priority=priority,
            assigned_to=assigned_to,
        )
        saved = await self.ticket_repository.save(ticket)
        await publish_ticket_updated(self.event_bus, saved)
        return saved
