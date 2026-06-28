import uuid
from app.domain.entities.ticket import Ticket
from app.domain.ports.ticket_repository import TicketRepository


class ListCustomerTicketsUseCase:
    def __init__(self, ticket_repository: TicketRepository):
        self.ticket_repository = ticket_repository

    async def execute(self, customer_id: uuid.UUID) -> list[Ticket]:
        return await self.ticket_repository.get_by_customer_id(customer_id)
