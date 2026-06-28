import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Tenant:
    name: str
    slug: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    phone_number_id: str | None = None
    timezone: str = "America/Mexico_City"
    locale: str = "es"
    mode: str = "SERVICES"
    account_type: str = "INDIVIDUAL"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now()

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = datetime.now()

    def update_settings(self, name: str, timezone: str, locale: str, mode: str, account_type: str = "INDIVIDUAL") -> None:
        self.name = name
        self.timezone = timezone
        self.locale = locale
        self.mode = mode
        self.account_type = account_type
        self.updated_at = datetime.now()
