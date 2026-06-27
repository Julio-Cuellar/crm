import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    tenant_id: uuid.UUID
    email: str
    password_hash: str
    name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    role: str = "STAFF"  # OWNER | ADMIN | STAFF
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def deactivate(self) -> None:
        """Desactiva al usuario."""
        self.is_active = False
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """Reactiva al usuario."""
        self.is_active = True
        self.updated_at = datetime.now()

    def update_profile(self, name: str) -> None:
        """Actualiza la información personal del usuario."""
        self.name = name
        self.updated_at = datetime.now()

    def change_role(self, new_role: str) -> None:
        """Modifica el rol del usuario."""
        self.role = new_role
        self.updated_at = datetime.now()
