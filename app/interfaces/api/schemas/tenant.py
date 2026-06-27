import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class TenantBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., min_length=2, max_length=200)
    phone_number_id: str | None = Field(None, max_length=50)
    timezone: str = Field("America/Mexico_City", max_length=100)
    locale: str = Field("es", max_length=10)

    # Configuración de Pydantic v2 para forzar alias camelCase en JSON
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class TenantCreate(TenantBase):
    owner_name: str | None = Field(None, min_length=2, max_length=100)
    owner_email: str | None = None
    owner_password_hash: str | None = None


class TenantUpdate(TenantBase):
    pass


class TenantResponse(TenantBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
