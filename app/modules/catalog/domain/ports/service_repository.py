import uuid
from abc import ABC, abstractmethod
from app.modules.catalog.domain.entities.service import Service


class ServiceRepository(ABC):
    @abstractmethod
    async def save(self, service: Service) -> Service:
        """Guarda o actualiza un servicio en el almacenamiento."""
        pass

    @abstractmethod
    async def get_by_id(self, service_id: uuid.UUID) -> Service | None:
        """Busca un servicio por su identificador único (UUID)."""
        pass

    @abstractmethod
    async def get_by_tenant(self, tenant_id: uuid.UUID) -> list[Service]:
        """Obtiene la lista de todos los servicios registrados bajo un tenant específico."""
        pass

    @abstractmethod
    async def delete(self, service_id: uuid.UUID) -> bool:
        """Elimina físicamente un servicio del almacenamiento."""
        pass
