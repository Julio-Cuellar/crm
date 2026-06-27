import uuid
from app.domain.entities.ticket import Ticket
from app.domain.ports.ticket_repository import TicketRepository
from app.domain.exceptions.tickets import TicketNotFoundException


class UpdateTicketUseCase:
    def __init__(self, ticket_repository: TicketRepository):
        self.ticket_repository = ticket_repository

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
        return await self.ticket_repository.save(ticket)
