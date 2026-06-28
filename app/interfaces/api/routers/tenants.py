import uuid
from fastapi import APIRouter, Depends, HTTPException
from app.application.use_cases.get_tenant import GetTenantUseCase
from app.application.use_cases.update_tenant import UpdateTenantUseCase
from app.domain.exceptions.base import AppException
from app.interfaces.api.dependencies.tenants import (
    get_get_tenant_use_case,
    get_update_tenant_use_case
)
from app.interfaces.api.schemas.tenant import TenantUpdate, TenantResponse

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: uuid.UUID,
    get_use_case: GetTenantUseCase = Depends(get_get_tenant_use_case)
):
    try:
        return await get_use_case.execute(tenant_id)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: uuid.UUID,
    tenant_in: TenantUpdate,
    update_use_case: UpdateTenantUseCase = Depends(get_update_tenant_use_case)
):
    try:
        tenant = await update_use_case.execute(
            tenant_id=tenant_id,
            name=tenant_in.name,
            slug=tenant_in.slug,
            phone_number_id=tenant_in.phone_number_id,
            timezone=tenant_in.timezone,
            locale=tenant_in.locale,
            mode=tenant_in.mode,
            account_type=tenant_in.account_type,
        )
        return tenant
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})


from app.interfaces.api.dependencies.auth_bearer import get_current_user
from app.domain.entities.user import User
from app.core.security import encrypt_value, decrypt_value
from app.infrastructure.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.repositories.sqlalchemy_tenant_credential_repository import SQLAlchemyTenantCredentialRepository
from app.infrastructure.db.repositories.sqlalchemy_tenant_repository import SQLAlchemyTenantRepository
from app.domain.entities.tenant_credential import TenantCredential
from app.interfaces.api.schemas.tenant import WhatsAppConfigRequest, WhatsAppConfigResponse

@router.get("/me/whatsapp", response_model=WhatsAppConfigResponse)
async def get_whatsapp_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tenant_id = current_user.tenant_id
    tenant_repo = SQLAlchemyTenantRepository(db)
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado.")

    cred_repo = SQLAlchemyTenantCredentialRepository(db)

    cred_token = await cred_repo.get_by_tenant_and_type(tenant_id, "whatsapp_api_token")
    decrypted_token = decrypt_value(cred_token.encrypted_value) if cred_token else None

    cred_secret = await cred_repo.get_by_tenant_and_type(tenant_id, "whatsapp_app_secret")
    decrypted_secret = decrypt_value(cred_secret.encrypted_value) if cred_secret else None

    return WhatsAppConfigResponse(
        phone_number_id=tenant.phone_number_id,
        whatsapp_api_token=decrypted_token,
        meta_app_secret=decrypted_secret,
    )

@router.put("/me/whatsapp", response_model=WhatsAppConfigResponse)
async def update_whatsapp_config(
    config_in: WhatsAppConfigRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tenant_id = current_user.tenant_id
    tenant_repo = SQLAlchemyTenantRepository(db)
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant no encontrado.")

    tenant.phone_number_id = config_in.phone_number_id
    await tenant_repo.save(tenant)

    cred_repo = SQLAlchemyTenantCredentialRepository(db)

    async def _upsert_credential(cred_type: str, value: str) -> None:
        encrypted = encrypt_value(value)
        cred = await cred_repo.get_by_tenant_and_type(tenant_id, cred_type)
        if cred:
            cred.encrypted_value = encrypted
        else:
            cred = TenantCredential(tenant_id=tenant_id, credential_type=cred_type, encrypted_value=encrypted)
        await cred_repo.save(cred)

    if config_in.whatsapp_api_token is not None:
        await _upsert_credential("whatsapp_api_token", config_in.whatsapp_api_token)

    if config_in.meta_app_secret is not None:
        await _upsert_credential("whatsapp_app_secret", config_in.meta_app_secret)

    cred_token = await cred_repo.get_by_tenant_and_type(tenant_id, "whatsapp_api_token")
    decrypted_token = decrypt_value(cred_token.encrypted_value) if cred_token else None

    cred_secret = await cred_repo.get_by_tenant_and_type(tenant_id, "whatsapp_app_secret")
    decrypted_secret = decrypt_value(cred_secret.encrypted_value) if cred_secret else None

    return WhatsAppConfigResponse(
        phone_number_id=tenant.phone_number_id,
        whatsapp_api_token=decrypted_token,
        meta_app_secret=decrypted_secret,
    )
