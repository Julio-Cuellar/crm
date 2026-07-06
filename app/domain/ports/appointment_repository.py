import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from app.domain.entities.appointment import Appointment


class AppointmentRepository(ABC):
    @abstractmethod
    async def save(self, appointment: Appointment) -> Appointment:
        pass

    @abstractmethod
    async def get_by_id(self, appointment_id: uuid.UUID) -> Appointment | None:
        pass

    @abstractmethod
    async def get_latest_by_customer(self, customer_id: uuid.UUID) -> Appointment | None:
        pass

    @abstractmethod
    async def list_by_tenant_and_range(
        self, tenant_id: uuid.UUID, start_range: datetime, end_range: datetime
    ) -> list[Appointment]:
        pass

    @abstractmethod
    async def delete(self, appointment_id: uuid.UUID) -> bool:
        pass
