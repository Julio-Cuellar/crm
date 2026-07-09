import uuid
from abc import ABC, abstractmethod
from app.modules.tickets.domain.entities.ticket import Ticket


class TicketRepository(ABC):
    @abstractmethod
    async def save(self, ticket: Ticket) -> Ticket:
        """Guarda o actualiza un ticket en el almacenamiento."""
        pass

    @abstractmethod
    async def get_by_id(self, ticket_id: uuid.UUID) -> Ticket | None:
        """Busca un ticket por su identificador único (UUID)."""
        pass

    @abstractmethod
    async def get_by_customer_id(self, customer_id: uuid.UUID) -> list[Ticket]:
        """Obtiene la lista de tickets asociados a un cliente específico."""
        pass

    @abstractmethod
    async def get_by_tenant_id(self, tenant_id: uuid.UUID) -> list[Ticket]:
        """Obtiene todos los tickets asociados a un tenant específico."""
        pass

    @abstractmethod
    async def delete(self, ticket_id: uuid.UUID) -> bool:
        """Elimina un ticket del almacenamiento."""
        pass
