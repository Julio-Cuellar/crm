import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PendingRegistration:
    email: str
    password_hash: str
    name: str
    tenant_name: str
    verification_token: str
    token_expires_at: datetime
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.now)

    def is_expired(self) -> bool:
        """Verifica si el token de verificación ha expirado."""
        if self.token_expires_at.tzinfo is not None:
            return datetime.now(self.token_expires_at.tzinfo) > self.token_expires_at
        return datetime.now() > self.token_expires_at
