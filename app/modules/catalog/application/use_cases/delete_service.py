import uuid
from app.modules.catalog.domain.ports.service_repository import ServiceRepository
from app.modules.catalog.domain.exceptions.services import ServiceNotFoundException
from app.modules.catalog.infrastructure.messaging.publishers import publish_service_deleted
from app.platform.messaging.event_bus import EventBus


class DeleteServiceUseCase:
    def __init__(self, service_repository: ServiceRepository, event_bus: EventBus | None = None):
        self.service_repository = service_repository
        self.event_bus = event_bus

    async def execute(self, service_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        service = await self.service_repository.get_by_id(service_id)

        # Validar existencia y scoping de tenant
        if not service or service.tenant_id != tenant_id:
            raise ServiceNotFoundException()

        deleted = await self.service_repository.delete(service_id)
        if deleted:
            await publish_service_deleted(self.event_bus, service_id, tenant_id)
        return deleted
