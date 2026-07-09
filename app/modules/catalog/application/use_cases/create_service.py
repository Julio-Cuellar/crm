import uuid
from decimal import Decimal
from app.modules.catalog.domain.entities.service import Service
from app.modules.catalog.domain.ports.service_repository import ServiceRepository
from app.modules.catalog.infrastructure.messaging.publishers import publish_service_created
from app.platform.messaging.event_bus import EventBus


class CreateServiceUseCase:
    def __init__(self, service_repository: ServiceRepository, event_bus: EventBus | None = None):
        self.service_repository = service_repository
        self.event_bus = event_bus

    async def execute(
        self,
        tenant_id: uuid.UUID,
        name: str,
        description: str | None,
        duration_minutes: int,
        price: Decimal | None,
        currency: str = "MXN"
    ) -> Service:
        if not name.strip():
            raise ValueError("El nombre del servicio no puede estar vacío.")
        if duration_minutes <= 0:
            raise ValueError("La duración del servicio debe ser mayor a 0 minutos.")

        service = Service(
            tenant_id=tenant_id,
            name=name.strip(),
            description=description.strip() if description else None,
            duration_minutes=duration_minutes,
            price=price,
            currency=currency.strip() if currency else "MXN"
        )
        saved = await self.service_repository.save(service)
        await publish_service_created(self.event_bus, saved)
        return saved
