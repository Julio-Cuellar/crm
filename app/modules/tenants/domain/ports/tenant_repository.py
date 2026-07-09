import uuid
from abc import ABC, abstractmethod
from app.modules.tenants.domain.entities.tenant import Tenant


class TenantRepository(ABC):
    @abstractmethod
    async def save(self, tenant: Tenant) -> Tenant:
        """Guarda o actualiza un tenant en el medio de almacenamiento."""
        pass

    @abstractmethod
    async def get_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        """Busca un tenant por su identificador único (UUID)."""
        pass

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Tenant | None:
        """Busca un tenant por su slug URL-friendly único."""
        pass

    @abstractmethod
    async def get_by_phone_number_id(self, phone_number_id: str) -> Tenant | None:
        """Busca un tenant por el identificador de su línea de WhatsApp de Meta."""
        pass
