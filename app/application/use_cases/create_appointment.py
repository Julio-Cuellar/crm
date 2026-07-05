import uuid
from datetime import datetime
from app.domain.entities.appointment import Appointment
from app.domain.ports.appointment_repository import AppointmentRepository
from app.domain.ports.customer_repository import CustomerRepository
from app.domain.ports.service_repository import ServiceRepository
from app.domain.exceptions.customers import CustomerNotFoundException
from app.domain.exceptions.services import ServiceNotFoundException


class CreateAppointmentUseCase:
    def __init__(
        self,
        appointment_repository: AppointmentRepository,
        customer_repository: CustomerRepository,
        service_repository: ServiceRepository,
    ):
        self.appointment_repository = appointment_repository
        self.customer_repository = customer_repository
        self.service_repository = service_repository

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
        # 1. Validar que el cliente exista y pertenezca al mismo tenant
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer or customer.tenant_id != tenant_id:
            raise CustomerNotFoundException()

        # 2. Validar que el servicio exista y pertenezca al mismo tenant, si se proporciona
        if service_id:
            service = await self.service_repository.get_by_id(service_id)
            if not service or service.tenant_id != tenant_id:
                raise ServiceNotFoundException()

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
        return await self.appointment_repository.save(appointment)
