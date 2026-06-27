import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class Service:
    tenant_id: uuid.UUID
    name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    description: str | None = None
    duration_minutes: int = 60
    price: Decimal | None = None
    currency: str = "MXN"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def deactivate(self) -> None:
        """Desactiva el servicio para que no se pueda agendar."""
        self.is_active = False
        self.updated_at = datetime.now()

    def activate(self) -> None:
        """Reactiva el servicio."""
        self.is_active = True
        self.updated_at = datetime.now()

    def update_details(
        self,
        name: str,
        description: str | None,
        duration_minutes: int,
        price: Decimal | None,
        currency: str
    ) -> None:
        """Actualiza los detalles informativos y de negocio del servicio."""
        if not name.strip():
            raise ValueError("El nombre del servicio no puede estar vacío.")
        if duration_minutes <= 0:
            raise ValueError("La duración del servicio debe ser mayor a 0 minutos.")
            
        self.name = name
        self.description = description
        self.duration_minutes = duration_minutes
        self.price = price
        self.currency = currency
        self.updated_at = datetime.now()
