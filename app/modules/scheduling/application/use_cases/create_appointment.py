import uuid
from datetime import datetime

from app.modules.scheduling.domain.entities.appointment import Appointment
from app.modules.scheduling.domain.ports.appointment_repository import AppointmentRepository
from app.modules.scheduling.infrastructure.db.repositories.customer_projection_repository import (
    CustomerProjectionRepository,
)
from app.modules.scheduling.infrastructure.db.repositories.service_projection_repository import (
    ServiceProjectionRepository,
)
from app.modules.scheduling.infrastructure.gateways.customers_fallback_gateway import CustomersFallbackGateway
from app.modules.scheduling.infrastructure.gateways.catalog_fallback_gateway import CatalogFallbackGateway
from app.modules.scheduling.application.use_cases._projection_resolvers import (
    ensure_customer_projected,
    ensure_service_projected,
)
from app.modules.scheduling.infrastructure.messaging.publishers import publish_appointment_created
from app.platform.messaging.event_bus import EventBus


class CreateAppointmentUseCase:
    def __init__(
        self,
        appointment_repository: AppointmentRepository,
        customer_projection_repository: CustomerProjectionRepository,
        service_projection_repository: ServiceProjectionRepository,
        customers_fallback_gateway: CustomersFallbackGateway,
        catalog_fallback_gateway: CatalogFallbackGateway,
        event_bus: EventBus | None = None,
    ):
        self.appointment_repository = appointment_repository
        self.customer_projection_repository = customer_projection_repository
        self.service_projection_repository = service_projection_repository
        self.customers_fallback_gateway = customers_fallback_gateway
        self.catalog_fallback_gateway = catalog_fallback_gateway
        self.event_bus = event_bus

    async def execute(
        self,
        tenant_id: uuid.UUID,
        customer_id: uuid.UUID,
        service_id: uuid.UUID | None,
        start_at: datetime,
        end_at: datetime,
        notes: str | None = None,
        status: str = "PENDING",
    ) -> Appointment:
        # 1. Validar que el cliente exista y pertenezca al mismo tenant (proyección + fallback)
        await ensure_customer_projected(
            self.customer_projection_repository, self.customers_fallback_gateway, customer_id, tenant_id
        )

        # 2. Validar que el servicio exista y pertenezca al mismo tenant, si se proporciona
        if service_id:
            await ensure_service_projected(
                self.service_projection_repository, self.catalog_fallback_gateway, service_id, tenant_id
            )

        # 3. Validar rango de fechas
        if start_at >= end_at:
            raise ValueError("La hora de inicio debe ser anterior a la hora de fin.")

        # 4. Crear y guardar la cita
        appointment = Appointment(
            tenant_id=tenant_id,
            customer_id=customer_id,
            service_id=service_id,
            start_at=start_at,
            end_at=end_at,
            status=status,
            notes=notes.strip() if notes else None,
        )
        saved = await self.appointment_repository.save(appointment)
        await publish_appointment_created(self.event_bus, saved)
        return saved
