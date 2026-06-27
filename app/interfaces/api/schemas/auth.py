from pydantic import BaseModel, ConfigDict, Field, EmailStr
from pydantic.alias_generators import to_camel


class AuthBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True
    )


class RegisterRequest(AuthBase):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2, max_length=100)
    tenant_name: str = Field(..., min_length=2, max_length=200)


class VerifyRequest(AuthBase):
    email: EmailStr
    token: str = Field(..., min_length=6, max_length=6)


class LoginRequest(AuthBase):
    email: EmailStr
    password: str


class TokenResponse(AuthBase):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
