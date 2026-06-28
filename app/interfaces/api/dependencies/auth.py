from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repositories.sqlalchemy_pending_registration_repository import SQLAlchemyPendingRegistrationRepository
from app.infrastructure.db.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.interfaces.api.dependencies.users import get_user_repository
from app.interfaces.api.dependencies.tenants import get_create_tenant_use_case, get_event_bus
from app.application.use_cases.register_tenant import RegisterTenantUseCase
from app.application.use_cases.verify_registration import VerifyRegistrationUseCase
from app.application.use_cases.login import LoginUseCase
from app.application.use_cases.create_tenant import CreateTenantUseCase
from app.domain.ports.event_bus import EventBus


async def get_pending_registration_repository(
    db: AsyncSession = Depends(get_db)
) -> SQLAlchemyPendingRegistrationRepository:
    return SQLAlchemyPendingRegistrationRepository(db)


async def get_register_tenant_use_case(
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository),
    pending_repo: SQLAlchemyPendingRegistrationRepository = Depends(get_pending_registration_repository),
    event_bus: EventBus = Depends(get_event_bus)
) -> RegisterTenantUseCase:
    return RegisterTenantUseCase(user_repo, pending_repo, event_bus)


from app.application.use_cases.refresh_token import RefreshTokenUseCase

async def get_verify_registration_use_case(
    pending_repo: SQLAlchemyPendingRegistrationRepository = Depends(get_pending_registration_repository),
    create_tenant_use_case: CreateTenantUseCase = Depends(get_create_tenant_use_case)
) -> VerifyRegistrationUseCase:
    return VerifyRegistrationUseCase(pending_repo, create_tenant_use_case)


async def get_login_use_case(
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository)
) -> LoginUseCase:
    return LoginUseCase(user_repo)


async def get_refresh_token_use_case(
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository)
) -> RefreshTokenUseCase:
    return RefreshTokenUseCase(user_repo)
