import uuid
from app.modules.scheduling.domain.entities.appointment import Appointment
from app.modules.scheduling.domain.ports.appointment_repository import AppointmentRepository
from app.modules.scheduling.domain.exceptions.appointments import AppointmentNotFoundException


class GetAppointmentUseCase:
    def __init__(self, appointment_repository: AppointmentRepository):
        self.appointment_repository = appointment_repository

    async def execute(self, appointment_id: uuid.UUID, tenant_id: uuid.UUID) -> Appointment:
        appointment = await self.appointment_repository.get_by_id(appointment_id)
        if not appointment or appointment.tenant_id != tenant_id:
            raise AppointmentNotFoundException()
        return appointment
