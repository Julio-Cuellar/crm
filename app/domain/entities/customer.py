import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Customer:
    tenant_id: uuid.UUID
    phone: str
    name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    email: str | None = None
    lead_status: str = "NEW"  # NEW | CONTACTED | APPOINTMENT_SCHEDULED | APPOINTMENT_CONFIRMED | RECURRING_CLIENT | INACTIVE | BLOCKED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_info(self, name: str, email: str | None) -> None:
        """Actualiza la información básica de contacto del cliente."""
        if not name.strip():
            raise ValueError("El nombre del cliente no puede estar vacío.")
            
        self.name = name.strip()
        self.email = email.strip() if email else None
        self.updated_at = datetime.now()

    def change_status(self, status: str) -> None:
        """Modifica el estado de atención o seguimiento del cliente."""
        valid_statuses = [
            "NEW",
            "CONTACTED",
            "APPOINTMENT_SCHEDULED",
            "APPOINTMENT_CONFIRMED",
            "RECURRING_CLIENT",
            "INACTIVE",
            "BLOCKED",
        ]
        upper_status = status.upper()
        if upper_status not in valid_statuses:
            raise ValueError(f"Estado de cliente inválido. Debe ser uno de: {valid_statuses}")
            
        self.lead_status = upper_status
        self.updated_at = datetime.now()

    def block(self) -> None:
        """Bloquea al cliente para evitar futuras interacciones automáticas."""
        self.lead_status = "BLOCKED"
        self.updated_at = datetime.now()
