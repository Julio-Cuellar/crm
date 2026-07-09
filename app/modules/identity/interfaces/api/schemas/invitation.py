import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from pydantic.alias_generators import to_camel


class InvitationBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class InviteRequest(InvitationBase):
    email: EmailStr
    role: str = Field("STAFF", max_length=20)  # ADMIN | STAFF


class InvitationResponse(InvitationBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    email: EmailStr
    role: str
    token: str
    expires_at: datetime
    created_at: datetime


class InvitationDetailsResponse(InvitationBase):
    email: EmailStr
    tenant_name: str
    role: str
    token: str


class AcceptInvitationRequest(InvitationBase):
    token: str
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)
