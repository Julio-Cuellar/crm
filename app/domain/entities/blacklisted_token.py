import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BlacklistedToken:
    token: str
    expires_at: datetime
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.now)
