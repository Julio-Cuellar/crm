import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

class ChatResponse(BaseModel):
    id: str = Field(..., alias="id")
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: str
    customer_phone: str
    platform: str
    external_thread_id: str | None = None
    status: str
    created_at: datetime
    last_message_at: datetime

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

class MessageResponse(BaseModel):
    id: str = Field(..., alias="id")
    history_chat_id: str
    direction: str
    type: str
    content: str
    media_url: str | None = None
    external_id: str | None = None
    sent_at: datetime
    status: str

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )

class SendMessageRequest(BaseModel):
    content: str
    type: str = "TEXT"
    media_url: str | None = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
