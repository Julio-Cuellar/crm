import uuid
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class TenantCredential:
    tenant_id: uuid.UUID
    credential_type: str  # e.g., "whatsapp_api_token", "google_calendar_id"
    encrypted_value: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
