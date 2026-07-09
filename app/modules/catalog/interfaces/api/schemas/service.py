import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    duration_minutes: int = Field(60, gt=0)
    price: Decimal | None = Field(None, ge=0)
    currency: str = Field("MXN", min_length=1, max_length=10)

    # Forzar la serialización camelCase hacia el frontend
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(ServiceBase):
    is_active: bool = True


class ServiceResponse(ServiceBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
