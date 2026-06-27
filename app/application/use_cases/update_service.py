import uuid
from decimal import Decimal
from app.domain.entities.service import Service
from app.domain.ports.service_repository import ServiceRepository
from app.domain.exceptions.services import ServiceNotFoundException


class UpdateServiceUseCase:
    def __init__(self, service_repository: ServiceRepository):
        self.service_repository = service_repository

    async def execute(
        self,
        service_id: uuid.UUID,
        tenant_id: uuid.UUID,
        name: str,
        description: str | None,
        duration_minutes: int,
        price: Decimal | None,
        currency: str,
        is_active: bool
    ) -> Service:
        service = await self.service_repository.get_by_id(service_id)
        
        # Validar existencia y pertenencia al tenant (multi-tenancy scoping)
        if not service or service.tenant_id != tenant_id:
            raise ServiceNotFoundException()

        # Actualizar detalles e invocar métodos informativos del dominio
        service.update_details(
            name=name.strip(),
            description=description.strip() if description else None,
            duration_minutes=duration_minutes,
            price=price,
            currency=currency.strip() if currency else "MXN"
        )
        
        if is_active:
            service.activate()
        else:
            service.deactivate()

        return await self.service_repository.save(service)
