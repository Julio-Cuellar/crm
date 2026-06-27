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
        )
        return tenant
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail={"code": e.code, "message": e.message})
