import uuid
from datetime import datetime

from app.modules.scheduling.domain.entities.appointment import Appointment
from app.modules.scheduling.domain.ports.appointment_repository import AppointmentRepository
from app.modules.scheduling.infrastructure.db.repositories.service_projection_repository import (
    ServiceProjectionRepository,
)
from app.modules.scheduling.infrastructure.gateways.catalog_fallback_gateway import CatalogFallbackGateway
from app.modules.scheduling.application.use_cases._projection_resolvers import ensure_service_projected
from app.modules.scheduling.domain.exceptions.appointments import AppointmentNotFoundException
from app.modules.scheduling.infrastructure.messaging.publishers import publish_appointment_updated
from app.platform.messaging.event_bus import EventBus


class UpdateAppointmentUseCase:
    def __init__(
        self,
        appointment_repository: AppointmentRepository,
        service_projection_repository: ServiceProjectionRepository,
        catalog_fallback_gateway: CatalogFallbackGateway,
        event_bus: EventBus | None = None,
    ):
        self.appointment_repository = appointment_repository
        self.service_projection_repository = service_projection_repository
        self.catalog_fallback_gateway = catalog_fallback_gateway
        self.event_bus = event_bus

    async def execute(
        self,
        appointment_id: uuid.UUID,
        tenant_id: uuid.UUID,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        service_id: uuid.UUID | None = None,
        status: str | None = None,
        notes: str | None = None,
    ) -> Appointment:
        appointment = await self.appointment_repository.get_by_id(appointment_id)
        if not appointment or appointment.tenant_id != tenant_id:
            raise AppointmentNotFoundException()

        # Validar el servicio si se actualiza
        if service_id is not None:
            if service_id:
                await ensure_service_projected(
                    self.service_projection_repository, self.catalog_fallback_gateway, service_id, tenant_id
                )
            appointment.service_id = service_id

        # Validar fechas si se actualizan
        new_start = start_at if start_at is not None else appointment.start_at
        new_end = end_at if end_at is not None else appointment.end_at
        if new_start >= new_end:
            raise ValueError("La hora de inicio debe ser anterior a la hora de fin.")

        appointment.update(
            start_at=start_at,
            end_at=end_at,
            status=status,
            notes=notes.strip() if notes is not None else None,
        )
        saved = await self.appointment_repository.save(appointment)
        await publish_appointment_updated(self.event_bus, saved)
        return saved
