import uuid
from app.modules.tenants.domain.entities.tenant import Tenant
from app.modules.tenants.domain.ports.tenant_repository import TenantRepository
from app.modules.tenants.domain.exceptions.tenant import TenantNotFoundException


class GetTenantUseCase:
    def __init__(self, tenant_repository: TenantRepository):
        self.tenant_repository = tenant_repository

    async def execute(self, tenant_id: uuid.UUID) -> Tenant:
        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundException(f"No se encontró el negocio solicitado.")
        return tenant
