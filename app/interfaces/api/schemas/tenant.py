import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

TENANT_MODES = {"SERVICES", "SALES"}
TENANT_ACCOUNT_TYPES = {"INDIVIDUAL", "BUSINESS", "TEAM"}


class TenantBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., min_length=2, max_length=200)
    phone_number_id: str | None = Field(None, max_length=50)
    timezone: str = Field("America/Mexico_City", max_length=100)
    locale: str = Field("es", max_length=10)
    mode: str = Field("SERVICES", pattern="^(SERVICES|SALES)$")
    account_type: str = Field("INDIVIDUAL", pattern="^(INDIVIDUAL|BUSINESS|TEAM)$")
    # None = "no modificar los módulos habilitados actuales" (ver UpdateTenantUseCase/Tenant.update_settings)
    enabled_modules: list[str] | None = Field(None)

    @field_validator("enabled_modules")
    @classmethod
    def _validate_enabled_modules(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        if not value:
            raise ValueError("enabled_modules no puede estar vacío")
        invalid = set(value) - TENANT_MODES
        if invalid:
            raise ValueError(f"Módulos inválidos: {invalid}. Valores permitidos: {TENANT_MODES}")
        return value

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
    ai_system_prompt: str | None = None
    created_at: datetime
    updated_at: datetime


class TenantAIConfigUpdate(BaseModel):
    system_prompt: str | None = Field(None, description="System prompt for the Gemini AI assistant")

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class TenantAIConfigResponse(BaseModel):
    tenant_id: uuid.UUID
    system_prompt: str | None = None
    updated_at: datetime

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class WhatsAppConfigResponse(BaseModel):
    phone_number_id: str | None = None
    whatsapp_api_token: str | None = None
    meta_app_secret: str | None = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )


class WhatsAppConfigRequest(BaseModel):
    phone_number_id: str | None = Field(None, max_length=50)
    whatsapp_api_token: str | None = None
    meta_app_secret: str | None = None

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True
    )
