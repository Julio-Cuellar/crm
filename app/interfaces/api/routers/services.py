import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from app.domain.entities.user import User as DomainUser
from app.domain.exceptions.base import AppException
from app.interfaces.api.dependencies.auth_bearer import get_current_user
from app.interfaces.api.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse
from app.interfaces.api.dependencies.services import (
    get_create_service_use_case,
    get_update_service_use_case,
    get_get_service_use_case,
    get_list_services_use_case,
    get_delete_service_use_case
)
from app.application.use_cases.create_service import CreateServiceUseCase
from app.application.use_cases.update_service import UpdateServiceUseCase
from app.application.use_cases.get_service import GetServiceUseCase
from app.application.use_cases.list_services import ListServicesUseCase
from app.application.use_cases.delete_service import DeleteServiceUseCase

router = APIRouter(prefix="/services", tags=["Services"])


@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    service_in: ServiceCreate,
    current_user: DomainUser = Depends(get_current_user),
    create_use_case: CreateServiceUseCase = Depends(get_create_service_use_case)
):
    """
    Crea un nuevo servicio en el catálogo del Tenant del usuario actual.
    Solo permitido para roles OWNER o ADMIN.
    """
    if current_user.role not in ["OWNER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para administrar el catálogo de servicios."
        )
    try:
        return await create_use_case.execute(
            tenant_id=current_user.tenant_id,
            name=service_in.name,
            description=service_in.description,
            duration_minutes=service_in.duration_minutes,
            price=service_in.price,
            currency=service_in.currency
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"code": e.code, "message": e.message}
        )


@router.put("/{service_id}", response_model=ServiceResponse)
async def update_service(
    service_id: uuid.UUID,
    service_in: ServiceUpdate,
    current_user: DomainUser = Depends(get_current_user),
    update_use_case: UpdateServiceUseCase = Depends(get_update_service_use_case)
):
    """
    Modifica la información de un servicio del catálogo.
    Solo permitido para roles OWNER o ADMIN.
    """
    if current_user.role not in ["OWNER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para administrar el catálogo de servicios."
        )
    try:
        return await update_use_case.execute(
            service_id=service_id,
            tenant_id=current_user.tenant_id,
            name=service_in.name,
            description=service_in.description,
            duration_minutes=service_in.duration_minutes,
            price=service_in.price,
            currency=service_in.currency,
            is_active=service_in.is_active
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VALIDATION_ERROR", "message": str(e)}
        )
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"code": e.code, "message": e.message}
        )


@router.get("/", response_model=list[ServiceResponse])
async def list_services(
    only_active: bool = False,
    current_user: DomainUser = Depends(get_current_user),
    list_use_case: ListServicesUseCase = Depends(get_list_services_use_case)
):
    """
    Lista todos los servicios pertenecientes al Tenant del usuario autenticado.
    Permitido para cualquier rol del Tenant (OWNER, ADMIN, STAFF).
    """
    try:
        return await list_use_case.execute(
            tenant_id=current_user.tenant_id,
            only_active=only_active
        )
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"code": e.code, "message": e.message}
        )


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service(
    service_id: uuid.UUID,
    current_user: DomainUser = Depends(get_current_user),
    get_use_case: GetServiceUseCase = Depends(get_get_service_use_case)
):
    """
    Obtiene los detalles de un servicio específico.
    Permitido para cualquier rol del Tenant (OWNER, ADMIN, STAFF).
    """
    try:
        return await get_use_case.execute(
            service_id=service_id,
            tenant_id=current_user.tenant_id
        )
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"code": e.code, "message": e.message}
        )


@router.delete("/{service_id}", status_code=status.HTTP_200_OK)
async def delete_service(
    service_id: uuid.UUID,
    current_user: DomainUser = Depends(get_current_user),
    delete_use_case: DeleteServiceUseCase = Depends(get_delete_service_use_case)
):
    """
    Elimina físicamente un servicio del catálogo.
    Solo permitido para roles OWNER o ADMIN.
    """
    if current_user.role not in ["OWNER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para administrar el catálogo de servicios."
        )
    try:
        success = await delete_use_case.execute(
            service_id=service_id,
            tenant_id=current_user.tenant_id
        )
        return {"success": success, "message": "Servicio eliminado correctamente del catálogo."}
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"code": e.code, "message": e.message}
        )
