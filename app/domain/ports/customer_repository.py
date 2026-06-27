import uuid
from abc import ABC, abstractmethod
from app.domain.entities.customer import Customer


class CustomerRepository(ABC):
    @abstractmethod
    async def save(self, customer: Customer) -> Customer:
        """Guarda o actualiza un cliente en el almacenamiento."""
        pass

    @abstractmethod
    async def get_by_id(self, customer_id: uuid.UUID) -> Customer | None:
        """Busca un cliente por su identificador único (UUID)."""
        pass

    @abstractmethod
    async def get_by_phone_and_tenant(self, phone: str, tenant_id: uuid.UUID) -> Customer | None:
        """Busca un cliente por su número de teléfono dentro de un tenant específico."""
        pass

    @abstractmethod
    async def get_by_tenant(self, tenant_id: uuid.UUID) -> list[Customer]:
        """Obtiene la lista de todos los clientes registrados bajo un tenant específico."""
        pass

    @abstractmethod
    async def delete(self, customer_id: uuid.UUID) -> bool:
        """Elimina físicamente un cliente del almacenamiento."""
        pass
