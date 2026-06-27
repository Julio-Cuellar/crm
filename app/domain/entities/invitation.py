import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Invitation:
    tenant_id: uuid.UUID
    email: str
    role: str
    token: str
    expires_at: datetime
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        """Verifica si la invitación ha expirado."""
        if self.expires_at.tzinfo is not None:
            return datetime.now(self.expires_at.tzinfo) > self.expires_at
        return datetime.now() > self.expires_at
