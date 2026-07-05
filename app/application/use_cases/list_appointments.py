import uuid
from datetime import datetime
from app.domain.entities.appointment import Appointment
from app.domain.ports.appointment_repository import AppointmentRepository


class ListAppointmentsUseCase:
    def __init__(self, appointment_repository: AppointmentRepository):
        self.appointment_repository = appointment_repository

    async def execute(
        self, tenant_id: uuid.UUID, start_range: datetime, end_range: datetime
    ) -> list[Appointment]:
        return await self.appointment_repository.list_by_tenant_and_range(
            tenant_id, start_range, end_range
        )
