from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.platform.db.session import get_db
from app.platform.messaging.event_bus import EventBus
from app.modules.scheduling.infrastructure.db.repositories.sqlalchemy_appointment_repository import SQLAlchemyAppointmentRepository
from app.modules.scheduling.infrastructure.db.repositories.customer_projection_repository import (
    CustomerProjectionRepository,
)
from app.modules.scheduling.infrastructure.db.repositories.service_projection_repository import (
    ServiceProjectionRepository,
)
from app.modules.scheduling.infrastructure.gateways.customers_fallback_gateway import CustomersFallbackGateway
from app.modules.scheduling.infrastructure.gateways.catalog_fallback_gateway import CatalogFallbackGateway
from app.modules.scheduling.application.use_cases.create_appointment import CreateAppointmentUseCase
from app.modules.scheduling.application.use_cases.get_appointment import GetAppointmentUseCase
from app.modules.scheduling.application.use_cases.list_appointments import ListAppointmentsUseCase
from app.modules.scheduling.application.use_cases.update_appointment import UpdateAppointmentUseCase
from app.modules.scheduling.application.use_cases.delete_appointment import DeleteAppointmentUseCase

_security = HTTPBearer()


async def get_appointment_repository(
    db: AsyncSession = Depends(get_db)
) -> SQLAlchemyAppointmentRepository:
    return SQLAlchemyAppointmentRepository(db)


async def get_customer_projection_repository(
    db: AsyncSession = Depends(get_db)
) -> CustomerProjectionRepository:
    return CustomerProjectionRepository(db)


async def get_service_projection_repository(
    db: AsyncSession = Depends(get_db)
) -> ServiceProjectionRepository:
    return ServiceProjectionRepository(db)


async def get_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(_security)) -> str:
    return credentials.credentials


async def get_event_bus(request: Request) -> EventBus | None:
    return request.app.state.event_bus


async def get_customers_fallback_gateway(
    token: str = Depends(get_bearer_token)
) -> CustomersFallbackGateway:
    return CustomersFallbackGateway(token)


async def get_catalog_fallback_gateway(
    token: str = Depends(get_bearer_token)
) -> CatalogFallbackGateway:
    return CatalogFallbackGateway(token)


async def get_create_appointment_use_case(
    repo: SQLAlchemyAppointmentRepository = Depends(get_appointment_repository),
    customer_projection_repo: CustomerProjectionRepository = Depends(get_customer_projection_repository),
    service_projection_repo: ServiceProjectionRepository = Depends(get_service_projection_repository),
    customers_gateway: CustomersFallbackGateway = Depends(get_customers_fallback_gateway),
    catalog_gateway: CatalogFallbackGateway = Depends(get_catalog_fallback_gateway),
    event_bus: EventBus | None = Depends(get_event_bus),
) -> CreateAppointmentUseCase:
    return CreateAppointmentUseCase(
        repo, customer_projection_repo, service_projection_repo, customers_gateway, catalog_gateway, event_bus
    )


async def get_get_appointment_use_case(
    repo: SQLAlchemyAppointmentRepository = Depends(get_appointment_repository)
) -> GetAppointmentUseCase:
    return GetAppointmentUseCase(repo)


async def get_list_appointments_use_case(
    repo: SQLAlchemyAppointmentRepository = Depends(get_appointment_repository)
) -> ListAppointmentsUseCase:
    return ListAppointmentsUseCase(repo)


async def get_update_appointment_use_case(
    repo: SQLAlchemyAppointmentRepository = Depends(get_appointment_repository),
    service_projection_repo: ServiceProjectionRepository = Depends(get_service_projection_repository),
    catalog_gateway: CatalogFallbackGateway = Depends(get_catalog_fallback_gateway),
    event_bus: EventBus | None = Depends(get_event_bus),
) -> UpdateAppointmentUseCase:
    return UpdateAppointmentUseCase(repo, service_projection_repo, catalog_gateway, event_bus)


async def get_delete_appointment_use_case(
    repo: SQLAlchemyAppointmentRepository = Depends(get_appointment_repository)
) -> DeleteAppointmentUseCase:
    return DeleteAppointmentUseCase(repo)
