import uuid
from abc import ABC, abstractmethod
from app.domain.entities.tenant_credential import TenantCredential

class TenantCredentialRepository(ABC):
    @abstractmethod
    async def save(self, credential: TenantCredential) -> TenantCredential:
        """Guarda o actualiza una credencial de tenant."""
        pass

    @abstractmethod
    async def get_by_tenant_and_type(
        self, tenant_id: uuid.UUID, credential_type: str
    ) -> TenantCredential | None:
        """Busca una credencial específica de un tenant por tipo."""
        pass

    @abstractmethod
    async def delete(self, tenant_id: uuid.UUID, credential_type: str) -> None:
        """Elimina una credencial específica de un tenant."""
        pass
