import uuid
from app.domain.entities.service import Service
from app.domain.ports.service_repository import ServiceRepository


class ListServicesUseCase:
    def __init__(self, service_repository: ServiceRepository):
        self.service_repository = service_repository

    async def execute(self, tenant_id: uuid.UUID, only_active: bool = False) -> list[Service]:
        services = await self.service_repository.get_by_tenant(tenant_id)
        if only_active:
            return [s for s in services if s.is_active]
        return services
