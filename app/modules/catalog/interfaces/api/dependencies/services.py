from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.platform.db.session import get_db
from app.platform.messaging.event_bus import EventBus
from app.modules.catalog.infrastructure.db.repositories.sqlalchemy_service_repository import SQLAlchemyServiceRepository
from app.modules.catalog.application.use_cases.create_service import CreateServiceUseCase
from app.modules.catalog.application.use_cases.update_service import UpdateServiceUseCase
from app.modules.catalog.application.use_cases.get_service import GetServiceUseCase
from app.modules.catalog.application.use_cases.list_services import ListServicesUseCase
from app.modules.catalog.application.use_cases.delete_service import DeleteServiceUseCase


async def get_service_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyServiceRepository:
    return SQLAlchemyServiceRepository(db)


async def get_event_bus(request: Request) -> EventBus | None:
    return request.app.state.event_bus


async def get_create_service_use_case(
    repo: SQLAlchemyServiceRepository = Depends(get_service_repository),
    event_bus: EventBus | None = Depends(get_event_bus),
) -> CreateServiceUseCase:
    return CreateServiceUseCase(repo, event_bus)


async def get_update_service_use_case(
    repo: SQLAlchemyServiceRepository = Depends(get_service_repository),
    event_bus: EventBus | None = Depends(get_event_bus),
) -> UpdateServiceUseCase:
    return UpdateServiceUseCase(repo, event_bus)


async def get_get_service_use_case(
    repo: SQLAlchemyServiceRepository = Depends(get_service_repository)
) -> GetServiceUseCase:
    return GetServiceUseCase(repo)


async def get_list_services_use_case(
    repo: SQLAlchemyServiceRepository = Depends(get_service_repository)
) -> ListServicesUseCase:
    return ListServicesUseCase(repo)


async def get_delete_service_use_case(
    repo: SQLAlchemyServiceRepository = Depends(get_service_repository),
    event_bus: EventBus | None = Depends(get_event_bus),
) -> DeleteServiceUseCase:
    return DeleteServiceUseCase(repo, event_bus)
