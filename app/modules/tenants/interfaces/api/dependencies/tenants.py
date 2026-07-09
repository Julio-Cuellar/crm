from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.platform.db.session import get_db
from app.modules.tenants.infrastructure.db.repositories.sqlalchemy_tenant_repository import SQLAlchemyTenantRepository
from app.platform.messaging.event_bus import EventBus
from app.modules.tenants.application.use_cases.create_tenant import CreateTenantUseCase
from app.modules.tenants.application.use_cases.get_tenant import GetTenantUseCase
from app.modules.tenants.application.use_cases.update_tenant import UpdateTenantUseCase


async def get_tenant_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyTenantRepository:
    return SQLAlchemyTenantRepository(db)


async def get_event_bus(request: Request) -> EventBus | None:
    return request.app.state.event_bus


async def get_create_tenant_use_case(
    repo: SQLAlchemyTenantRepository = Depends(get_tenant_repository),
    event_bus: EventBus | None = Depends(get_event_bus),
) -> CreateTenantUseCase:
    return CreateTenantUseCase(repo, event_bus)


async def get_get_tenant_use_case(
    repo: SQLAlchemyTenantRepository = Depends(get_tenant_repository)
) -> GetTenantUseCase:
    return GetTenantUseCase(repo)


async def get_update_tenant_use_case(
    repo: SQLAlchemyTenantRepository = Depends(get_tenant_repository),
    event_bus: EventBus | None = Depends(get_event_bus),
) -> UpdateTenantUseCase:
    return UpdateTenantUseCase(repo, event_bus)
