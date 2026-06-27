import uuid
from decimal import Decimal
from app.domain.entities.service import Service
from app.domain.ports.service_repository import ServiceRepository


class CreateServiceUseCase:
    def __init__(self, service_repository: ServiceRepository):
        self.service_repository = service_repository

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
        return await self.service_repository.save(service)
