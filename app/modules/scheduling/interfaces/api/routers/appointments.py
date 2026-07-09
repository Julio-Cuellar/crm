import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.modules.identity.domain.entities.user import User as DomainUser
from app.platform.exceptions import AppException
from app.platform.db.session import get_db
from app.modules.scheduling.infrastructure.db.models.customer_projection import CustomerProjection
from app.modules.scheduling.infrastructure.db.models.service_projection import ServiceProjection
from app.modules.identity.interfaces.api.dependencies.auth_bearer import get_current_user

from app.modules.scheduling.interfaces.api.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    CustomerNestedResponse,
    ServiceNestedResponse
)
from app.modules.scheduling.interfaces.api.dependencies.appointments import (
    get_create_appointment_use_case,
    get_get_appointment_use_case,
    get_list_appointments_use_case,
    get_update_appointment_use_case,
    get_delete_appointment_use_case
)
from app.modules.scheduling.application.use_cases.create_appointment import CreateAppointmentUseCase
from app.modules.scheduling.application.use_cases.get_appointment import GetAppointmentUseCase
from app.modules.scheduling.application.use_cases.list_appointments import ListAppointmentsUseCase
from app.modules.scheduling.application.use_cases.update_appointment import UpdateAppointmentUseCase
from app.modules.scheduling.application.use_cases.delete_appointment import DeleteAppointmentUseCase

router = APIRouter(prefix="/appointments", tags=["Appointments"])


async def _enrich_appointments(db: AsyncSession, appointments: list) -> list[AppointmentResponse]:
    if not appointments:
        return []

    # 1. Recopilar IDs
    customer_ids = {a.customer_id for a in appointments if a.customer_id}
    service_ids = {a.service_id for a in appointments if a.service_id}

    # 2. Cargar clientes en bloque (desde la proyección local, no la tabla de `customers`)
    customers_map = {}
    if customer_ids:
        res_cust = await db.execute(select(CustomerProjection).where(CustomerProjection.id.in_(list(customer_ids))))
        customers_map = {c.id: c for c in res_cust.scalars().all()}

    # 3. Cargar servicios en bloque (desde la proyección local, no la tabla de `services`)
    services_map = {}
    if service_ids:
        res_serv = await db.execute(select(ServiceProjection).where(ServiceProjection.id.in_(list(service_ids))))
        services_map = {s.id: s for s in res_serv.scalars().all()}

    # 4. Construir respuestas estructuradas
    enriched = []
    for appt in appointments:
        cust = customers_map.get(appt.customer_id)
        serv = services_map.get(appt.service_id) if appt.service_id else None

        cust_res = CustomerNestedResponse.model_validate(cust) if cust else None
        serv_res = ServiceNestedResponse.model_validate(serv) if serv else None

        enriched.append(
            AppointmentResponse(
                id=appt.id,
                tenant_id=appt.tenant_id,
                customer_id=appt.customer_id,
                service_id=appt.service_id,
                start_at=appt.start_at,
                end_at=appt.end_at,
                status=appt.status,
                notes=appt.notes,
                created_at=appt.created_at,
                updated_at=appt.updated_at,
                customer=cust_res,
                service=serv_res
            )
        )
    return enriched


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appt_in: AppointmentCreate,
    current_user: DomainUser = Depends(get_current_user),
    create_use_case: CreateAppointmentUseCase = Depends(get_create_appointment_use_case),
    db: AsyncSession = Depends(get_db)
):
    """
    Crea una nueva cita (Appointment) vinculada a un cliente y servicio del tenant actual.
    """
    try:
        appointment = await create_use_case.execute(
            tenant_id=current_user.tenant_id,
            customer_id=appt_in.customer_id,
            service_id=appt_in.service_id,
            start_at=appt_in.start_at,
            end_at=appt_in.end_at,
            notes=appt_in.notes,
            status=appt_in.status
        )
        enriched = await _enrich_appointments(db, [appointment])
        return enriched[0]
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


@router.get("/", response_model=list[AppointmentResponse])
async def list_appointments(
    start_range: datetime = Query(..., description="Fecha y hora de inicio del rango (ISO8601)"),
    end_range: datetime = Query(..., description="Fecha y hora de fin del rango (ISO8601)"),
    current_user: DomainUser = Depends(get_current_user),
    list_use_case: ListAppointmentsUseCase = Depends(get_list_appointments_use_case),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista las citas del tenant del usuario actual dentro de un rango de fechas.
    """
    try:
        appointments = await list_use_case.execute(
            tenant_id=current_user.tenant_id,
            start_range=start_range,
            end_range=end_range
        )
        return await _enrich_appointments(db, appointments)
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"code": e.code, "message": e.message}
        )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: uuid.UUID,
    current_user: DomainUser = Depends(get_current_user),
    get_use_case: GetAppointmentUseCase = Depends(get_get_appointment_use_case),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene los detalles de una cita específica.
    """
    try:
        appointment = await get_use_case.execute(
            appointment_id=appointment_id,
            tenant_id=current_user.tenant_id
        )
        enriched = await _enrich_appointments(db, [appointment])
        return enriched[0]
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"code": e.code, "message": e.message}
        )


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: uuid.UUID,
    appt_in: AppointmentUpdate,
    current_user: DomainUser = Depends(get_current_user),
    update_use_case: UpdateAppointmentUseCase = Depends(get_update_appointment_use_case),
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza la información de una cita (reprogramación, cambio de servicio, estado o notas).
    """
    try:
        appointment = await update_use_case.execute(
            appointment_id=appointment_id,
            tenant_id=current_user.tenant_id,
            start_at=appt_in.start_at,
            end_at=appt_in.end_at,
            service_id=appt_in.service_id,
            status=appt_in.status,
            notes=appt_in.notes
        )
        enriched = await _enrich_appointments(db, [appointment])
        return enriched[0]
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


@router.delete("/{appointment_id}", status_code=status.HTTP_200_OK)
async def delete_appointment(
    appointment_id: uuid.UUID,
    current_user: DomainUser = Depends(get_current_user),
    delete_use_case: DeleteAppointmentUseCase = Depends(get_delete_appointment_use_case)
):
    """
    Elimina físicamente una cita.
    """
    try:
        success = await delete_use_case.execute(
            appointment_id=appointment_id,
            tenant_id=current_user.tenant_id
        )
        return {"success": success, "message": "Cita eliminada correctamente de la agenda."}
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"code": e.code, "message": e.message}
        )
