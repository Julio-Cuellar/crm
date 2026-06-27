import uuid
from app.domain.entities.ticket import Ticket
from app.domain.ports.ticket_repository import TicketRepository


class CreateTicketUseCase:
    def __init__(self, ticket_repository: TicketRepository):
        self.ticket_repository = ticket_repository

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
        return await self.ticket_repository.save(ticket)
