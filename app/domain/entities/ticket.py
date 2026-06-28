import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Ticket:
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    title: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    description: str | None = None
    category: str = "INQUIRY"  # "TECHNICAL", "BILLING", "INQUIRY", "COMPLAINT"
    status: str = "OPEN"  # "OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"
    priority: str = "MEDIUM"  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    assigned_to: uuid.UUID | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update(
        self,
        title: str | None = None,
        description: str | None = None,
        category: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        assigned_to: uuid.UUID | None = None,
    ) -> None:
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if category is not None:
            self.category = category
        if status is not None:
            self.status = status
        if priority is not None:
            self.priority = priority
        if assigned_to is not None:
            self.assigned_to = assigned_to
        self.updated_at = datetime.now()
