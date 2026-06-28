import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from app.domain.entities.user import User as DomainUser
from app.domain.exceptions.base import AppException
from app.interfaces.api.dependencies.auth_bearer import get_current_user
from app.interfaces.api.schemas.ticket import TicketCreate, TicketUpdate, TicketResponse
from app.interfaces.api.dependencies.tickets import (
    get_create_ticket_use_case,
    get_list_customer_tickets_use_case,
    get_update_ticket_use_case
)
from app.interfaces.api.dependencies.customers import get_customer_repository
from app.application.use_cases.create_ticket import CreateTicketUseCase
from app.application.use_cases.list_customer_tickets import ListCustomerTicketsUseCase
from app.application.use_cases.update_ticket import UpdateTicketUseCase

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_in: TicketCreate,
    current_user: DomainUser = Depends(get_current_user),
    customer_repo = Depends(get_customer_repository),
    create_use_case: CreateTicketUseCase = Depends(get_create_ticket_use_case)
):
    """
    Crea un nuevo ticket de soporte asociado a un cliente.
    """
    try:
        # Validar que el cliente pertenezca al tenant
        customer = await customer_repo.get_by_id(ticket_in.customer_id)
        if not customer or customer.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CUSTOMER_NOT_FOUND", "message": "El cliente especificado no existe."}
            )

        return await create_use_case.execute(
            tenant_id=current_user.tenant_id,
            customer_id=ticket_in.customer_id,
            title=ticket_in.title,
            description=ticket_in.description,
            category=ticket_in.category,
            priority=ticket_in.priority,
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


@router.get("/customer/{customer_id}", response_model=list[TicketResponse])
async def list_customer_tickets(
    customer_id: uuid.UUID,
    current_user: DomainUser = Depends(get_current_user),
    customer_repo = Depends(get_customer_repository),
    list_use_case: ListCustomerTicketsUseCase = Depends(get_list_customer_tickets_use_case)
):
    """
    Lista todos los tickets asociados a un cliente específico.
    """
    try:
        # Validar que el cliente pertenezca al tenant
        customer = await customer_repo.get_by_id(customer_id)
        if not customer or customer.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CUSTOMER_NOT_FOUND", "message": "El cliente especificado no existe."}
            )

        return await list_use_case.execute(customer_id=customer_id)
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"code": e.code, "message": e.message}
        )


@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: uuid.UUID,
    ticket_in: TicketUpdate,
    current_user: DomainUser = Depends(get_current_user),
    update_use_case: UpdateTicketUseCase = Depends(get_update_ticket_use_case)
):
    """
    Actualiza la información, el estado o la prioridad de un ticket existente.
    """
    try:
        return await update_use_case.execute(
            ticket_id=ticket_id,
            title=ticket_in.title,
            description=ticket_in.description,
            category=ticket_in.category,
            status=ticket_in.status,
            priority=ticket_in.priority,
            assigned_to=ticket_in.assigned_to,
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
