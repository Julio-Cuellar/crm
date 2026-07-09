import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CustomerBase(BaseModel):
    phone: str = Field(..., min_length=5, max_length=20, pattern=r"^\+?[0-9]+$")
    name: str = Field(..., min_length=1, max_length=200)
    email: str | None = Field(None, max_length=200)

    # Forzar camelCase en JSON para el frontend e integraciones
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class CustomerCreate(CustomerBase):
    pass


class CustomerUpsert(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str | None = Field(None, max_length=200)
    lead_status: str = Field(..., max_length=20)  # NEW | ACTIVE | INACTIVE | BLOCKED

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class CustomerResponse(CustomerBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    lead_status: str
    pipeline_stage: str
    deal_value: float | None = None
    created_at: datetime
    updated_at: datetime


class CustomerPipelineUpdate(BaseModel):
    pipeline_stage: str = Field(..., pattern="^(NEW|CONTACTED|PROPOSAL|WON|LOST)$")
    deal_value: float | None = Field(None, ge=0)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
