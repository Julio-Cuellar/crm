import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BotSession:
    tenant_id: uuid.UUID
    customer_phone: str
    automation_mode: str = "AUTOMATED"
    temp_name: str | None = None
    temp_email: str | None = None
    temp_organization: str | None = None
    temp_service: str | None = None
    temp_description: str | None = None
    temp_appointment_date: datetime | None = None
    temp_folio: str | None = None
    context_json: dict | None = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update(
        self,
        automation_mode: str | None = None,
        temp_name: str | None = None,
        temp_email: str | None = None,
        temp_organization: str | None = None,
        temp_service: str | None = None,
        temp_description: str | None = None,
        temp_appointment_date: datetime | None = None,
        temp_folio: str | None = None,
        context_json: dict | None = None,
    ) -> None:
        if automation_mode is not None:
            self.automation_mode = automation_mode
        if temp_name is not None:
            self.temp_name = temp_name
        if temp_email is not None:
            self.temp_email = temp_email
        if temp_organization is not None:
            self.temp_organization = temp_organization
        if temp_service is not None:
            self.temp_service = temp_service
        if temp_description is not None:
            self.temp_description = temp_description
        if temp_appointment_date is not None:
            self.temp_appointment_date = temp_appointment_date
        if temp_folio is not None:
            self.temp_folio = temp_folio
        if context_json is not None:
            self.context_json = context_json
        self.updated_at = datetime.now()

    def clear_temp(self) -> None:
        self.temp_name = None
        self.temp_email = None
        self.temp_organization = None
        self.temp_service = None
        self.temp_description = None
        self.temp_appointment_date = None
        self.temp_folio = None
        self.updated_at = datetime.now()
