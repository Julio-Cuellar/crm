import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class TicketBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None)
    category: str = Field("INQUIRY", max_length=20)  # TECHNICAL, BILLING, INQUIRY, COMPLAINT
    priority: str = Field("MEDIUM", max_length=20)  # LOW, MEDIUM, HIGH, CRITICAL

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class TicketCreate(TicketBase):
    customer_id: uuid.UUID


class TicketUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None)
    category: str | None = Field(None, max_length=20)
    status: str | None = Field(None, max_length=20)  # OPEN, IN_PROGRESS, RESOLVED, CLOSED
    priority: str | None = Field(None, max_length=20)
    assigned_to: uuid.UUID | None = Field(None)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class TicketResponse(TicketBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    customer_id: uuid.UUID
    status: str
    assigned_to: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
