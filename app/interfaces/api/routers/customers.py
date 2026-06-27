import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from app.domain.entities.user import User as DomainUser
from app.domain.exceptions.base import AppException
from app.interfaces.api.dependencies.auth_bearer import get_current_user
from app.interfaces.api.schemas.customer import CustomerCreate, CustomerUpdate, CustomerUpsert, CustomerResponse
from app.interfaces.api.dependencies.customers import (
    get_create_customer_use_case,
    get_upsert_customer_use_case,
    get_update_customer_use_case,
    get_get_customer_use_case,
    get_list_customers_use_case,
    get_delete_customer_use_case
)
from app.application.use_cases.create_customer import CreateCustomerUseCase
from app.application.use_cases.upsert_customer import UpsertCustomerUseCase
from app.application.use_cases.update_customer import UpdateCustomerUseCase
from app.application.use_cases.get_customer import GetCustomerUseCase
from app.application.use_cases.list_customers import ListCustomersUseCase
from app.application.use_cases.delete_customer import DeleteCustomerUseCase

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_in: CustomerCreate,
    current_user: DomainUser = Depends(get_current_user),
    create_use_case: CreateCustomerUseCase = Depends(get_create_customer_use_case)
):
    """
    Crea un nuevo cliente bajo el Tenant del usuario autenticado.
    Permitido para cualquier rol del Tenant (OWNER, ADMIN, STAFF).
    """
    try:
        return await create_use_case.execute(
            tenant_id=current_user.tenant_id,
            phone=customer_in.phone,
            name=customer_in.name,
            email=customer_in.email
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


@router.post("/upsert", response_model=CustomerResponse, status_code=status.HTTP_200_OK)
async def upsert_customer(
    customer_in: CustomerUpsert,
    current_user: DomainUser = Depends(get_current_user),
    upsert_use_case: UpsertCustomerUseCase = Depends(get_upsert_customer_use_case)
):
    """
    Registra o actualiza de forma transparente a un cliente utilizando su número de teléfono.
    Muy útil para integraciones automatizadas (ej. n8n webhooks).
    """
    try:
        return await upsert_use_case.execute(
            tenant_id=current_user.tenant_id,
            phone=customer_in.phone,
            name=customer_in.name,
            email=customer_in.email
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


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: uuid.UUID,
    customer_in: CustomerUpdate,
    current_user: DomainUser = Depends(get_current_user),
    update_use_case: UpdateCustomerUseCase = Depends(get_update_customer_use_case)
):
    """
    Modifica la información básica o el estado de lead del cliente.
    """
    try:
        return await update_use_case.execute(
            customer_id=customer_id,
            tenant_id=current_user.tenant_id,
            name=customer_in.name,
            email=customer_in.email,
            lead_status=customer_in.lead_status
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


@router.get("/", response_model=list[CustomerResponse])
async def list_customers(
    current_user: DomainUser = Depends(get_current_user),
    list_use_case: ListCustomersUseCase = Depends(get_list_customers_use_case)
):
    """
    Lista todos los clientes registrados bajo el Tenant del usuario autenticado.
    """
    try:
        return await list_use_case.execute(tenant_id=current_user.tenant_id)
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"code": e.code, "message": e.message}
        )


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: uuid.UUID,
    current_user: DomainUser = Depends(get_current_user),
    get_use_case: GetCustomerUseCase = Depends(get_get_customer_use_case)
):
    """
    Consulta los detalles informativos de un cliente específico.
    """
    try:
        return await get_use_case.execute(
            customer_id=customer_id,
            tenant_id=current_user.tenant_id
        )
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"code": e.code, "message": e.message}
        )


@router.delete("/{customer_id}", status_code=status.HTTP_200_OK)
async def delete_customer(
    customer_id: uuid.UUID,
    current_user: DomainUser = Depends(get_current_user),
    delete_use_case: DeleteCustomerUseCase = Depends(get_delete_customer_use_case)
):
    """
    Elimina físicamente a un cliente.
    """
    try:
        success = await delete_use_case.execute(
            customer_id=customer_id,
            tenant_id=current_user.tenant_id
        )
        return {"success": success, "message": "Cliente eliminado correctamente."}
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"code": e.code, "message": e.message}
        )
