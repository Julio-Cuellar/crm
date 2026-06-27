import uuid
from app.domain.entities.service import Service
from app.domain.ports.service_repository import ServiceRepository
from app.domain.exceptions.services import ServiceNotFoundException


class GetServiceUseCase:
    def __init__(self, service_repository: ServiceRepository):
        self.service_repository = service_repository

    async def execute(self, service_id: uuid.UUID, tenant_id: uuid.UUID) -> Service:
        service = await self.service_repository.get_by_id(service_id)
        
        # Validar existencia y scoping de tenant
        if not service or service.tenant_id != tenant_id:
            raise ServiceNotFoundException()
            
        return service
