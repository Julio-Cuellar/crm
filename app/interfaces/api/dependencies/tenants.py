from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repositories.sqlalchemy_tenant_repository import SQLAlchemyTenantRepository
from app.domain.ports.event_bus import EventBus
from app.application.use_cases.create_tenant import CreateTenantUseCase
from app.application.use_cases.get_tenant import GetTenantUseCase
from app.application.use_cases.update_tenant import UpdateTenantUseCase


from app.interfaces.api.dependencies.users import get_user_repository
from app.infrastructure.db.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository

async def get_tenant_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyTenantRepository:
    return SQLAlchemyTenantRepository(db)


async def get_event_bus(request: Request) -> EventBus:
    return request.app.state.event_bus


async def get_create_tenant_use_case(
    repo: SQLAlchemyTenantRepository = Depends(get_tenant_repository),
    event_bus: EventBus = Depends(get_event_bus),
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository)
) -> CreateTenantUseCase:
    return CreateTenantUseCase(repo, event_bus, user_repo)


async def get_get_tenant_use_case(
    repo: SQLAlchemyTenantRepository = Depends(get_tenant_repository)
) -> GetTenantUseCase:
    return GetTenantUseCase(repo)


async def get_update_tenant_use_case(
    repo: SQLAlchemyTenantRepository = Depends(get_tenant_repository)
) -> UpdateTenantUseCase:
    return UpdateTenantUseCase(repo)
