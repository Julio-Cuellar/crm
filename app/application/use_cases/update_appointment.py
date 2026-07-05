import uuid
from datetime import datetime
from app.domain.entities.appointment import Appointment
from app.domain.ports.appointment_repository import AppointmentRepository
from app.domain.ports.service_repository import ServiceRepository
from app.domain.exceptions.appointments import AppointmentNotFoundException
from app.domain.exceptions.services import ServiceNotFoundException


class UpdateAppointmentUseCase:
    def __init__(
        self,
        appointment_repository: AppointmentRepository,
        service_repository: ServiceRepository,
    ):
        self.appointment_repository = appointment_repository
        self.service_repository = service_repository

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
                service = await self.service_repository.get_by_id(service_id)
                if not service or service.tenant_id != tenant_id:
                    raise ServiceNotFoundException()
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
        return await self.appointment_repository.save(appointment)
