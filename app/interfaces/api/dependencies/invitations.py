from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repositories.sqlalchemy_invitation_repository import SQLAlchemyInvitationRepository
from app.infrastructure.db.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.infrastructure.db.repositories.sqlalchemy_tenant_repository import SQLAlchemyTenantRepository
from app.interfaces.api.dependencies.users import get_user_repository, get_create_user_use_case
from app.interfaces.api.dependencies.tenants import get_tenant_repository, get_event_bus
from app.application.use_cases.invite_user import InviteUserUseCase
from app.application.use_cases.get_invitation_by_token import GetInvitationByTokenUseCase
from app.application.use_cases.accept_invitation import AcceptInvitationUseCase
from app.application.use_cases.create_user import CreateUserUseCase
from app.domain.ports.event_bus import EventBus


async def get_invitation_repository(
    db: AsyncSession = Depends(get_db)
) -> SQLAlchemyInvitationRepository:
    return SQLAlchemyInvitationRepository(db)


async def get_invite_user_use_case(
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository),
    invitation_repo: SQLAlchemyInvitationRepository = Depends(get_invitation_repository),
    tenant_repo: SQLAlchemyTenantRepository = Depends(get_tenant_repository),
    event_bus: EventBus = Depends(get_event_bus)
) -> InviteUserUseCase:
    return InviteUserUseCase(user_repo, invitation_repo, tenant_repo, event_bus)


async def get_get_invitation_by_token_use_case(
    invitation_repo: SQLAlchemyInvitationRepository = Depends(get_invitation_repository),
    tenant_repo: SQLAlchemyTenantRepository = Depends(get_tenant_repository)
) -> GetInvitationByTokenUseCase:
    return GetInvitationByTokenUseCase(invitation_repo, tenant_repo)


async def get_accept_invitation_use_case(
    invitation_repo: SQLAlchemyInvitationRepository = Depends(get_invitation_repository),
    create_user_use_case: CreateUserUseCase = Depends(get_create_user_use_case)
) -> AcceptInvitationUseCase:
    return AcceptInvitationUseCase(invitation_repo, create_user_use_case)
