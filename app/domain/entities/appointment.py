import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Appointment:
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    start_at: datetime
    end_at: datetime
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    service_id: uuid.UUID | None = None
    status: str = "PENDING"  # PENDING | CONFIRMED | CANCELLED | COMPLETED | NO_SHOW
    notes: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update(
        self,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        service_id: uuid.UUID | None = None,
        status: str | None = None,
        notes: str | None = None,
    ) -> None:
        if start_at is not None:
            self.start_at = start_at
        if end_at is not None:
            self.end_at = end_at
        if service_id is not None:
            self.service_id = service_id
        if status is not None:
            self.status = status
        if notes is not None:
            self.notes = notes
        self.updated_at = datetime.now()
