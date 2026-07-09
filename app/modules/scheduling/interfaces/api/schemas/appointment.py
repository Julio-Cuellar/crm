import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CustomerNestedResponse(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    email: str | None = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class ServiceNestedResponse(BaseModel):
    id: uuid.UUID
    name: str
    duration_minutes: int
    price: float | None = None
    currency: str = "MXN"

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class AppointmentBase(BaseModel):
    customer_id: uuid.UUID
    service_id: uuid.UUID | None = None
    start_at: datetime
    end_at: datetime
    status: str = "PENDING"
    notes: str | None = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class AppointmentCreate(AppointmentBase):
    pass


class AppointmentUpdate(BaseModel):
    service_id: uuid.UUID | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None
    status: str | None = None
    notes: str | None = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class AppointmentResponse(AppointmentBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    customer: CustomerNestedResponse | None = None
    service: ServiceNestedResponse | None = None
