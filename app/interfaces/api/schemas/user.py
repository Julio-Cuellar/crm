import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, EmailStr
from pydantic.alias_generators import to_camel


class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    role: str = Field("STAFF", max_length=20)  # OWNER | ADMIN | STAFF

    # Forzar la serialización camelCase hacia el frontend
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
