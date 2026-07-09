from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.platform.db.session import get_db
from app.modules.identity.infrastructure.db.repositories.sqlalchemy_invitation_repository import SQLAlchemyInvitationRepository
from app.modules.identity.infrastructure.db.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.modules.identity.infrastructure.db.repositories.tenant_projection_repository import (
    TenantProjectionRepository,
)
from app.modules.identity.interfaces.api.dependencies.users import get_user_repository, get_create_user_use_case
from app.modules.identity.application.use_cases.invite_user import InviteUserUseCase
from app.modules.identity.application.use_cases.get_invitation_by_token import GetInvitationByTokenUseCase
from app.modules.identity.application.use_cases.accept_invitation import AcceptInvitationUseCase
from app.modules.identity.application.use_cases.create_user import CreateUserUseCase
from app.platform.messaging.event_bus import EventBus


async def get_invitation_repository(
    db: AsyncSession = Depends(get_db)
) -> SQLAlchemyInvitationRepository:
    return SQLAlchemyInvitationRepository(db)


async def get_tenant_projection_repository(
    db: AsyncSession = Depends(get_db)
) -> TenantProjectionRepository:
    return TenantProjectionRepository(db)


async def get_event_bus(request: Request) -> EventBus | None:
    return request.app.state.event_bus


async def get_invite_user_use_case(
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository),
    invitation_repo: SQLAlchemyInvitationRepository = Depends(get_invitation_repository),
    tenant_projection_repo: TenantProjectionRepository = Depends(get_tenant_projection_repository),
    event_bus: EventBus | None = Depends(get_event_bus)
) -> InviteUserUseCase:
    return InviteUserUseCase(user_repo, invitation_repo, tenant_projection_repo, event_bus)


async def get_get_invitation_by_token_use_case(
    invitation_repo: SQLAlchemyInvitationRepository = Depends(get_invitation_repository),
    tenant_projection_repo: TenantProjectionRepository = Depends(get_tenant_projection_repository)
) -> GetInvitationByTokenUseCase:
    return GetInvitationByTokenUseCase(invitation_repo, tenant_projection_repo)


async def get_accept_invitation_use_case(
    invitation_repo: SQLAlchemyInvitationRepository = Depends(get_invitation_repository),
    create_user_use_case: CreateUserUseCase = Depends(get_create_user_use_case)
) -> AcceptInvitationUseCase:
    return AcceptInvitationUseCase(invitation_repo, create_user_use_case)
