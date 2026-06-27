import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.invitation import Invitation as DomainInvitation
from app.domain.ports.invitation_repository import InvitationRepository
from app.infrastructure.db.models.invitation import Invitation as DbInvitation


class SQLAlchemyInvitationRepository(InvitationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, db_invite: DbInvitation) -> DomainInvitation:
        return DomainInvitation(
            id=db_invite.id,
            tenant_id=db_invite.tenant_id,
            email=db_invite.email,
            role=db_invite.role,
            token=db_invite.token,
            expires_at=db_invite.expires_at,
            created_at=db_invite.created_at
        )

    def _to_db(self, domain_invite: DomainInvitation) -> DbInvitation:
        return DbInvitation(
            id=domain_invite.id,
            tenant_id=domain_invite.tenant_id,
            email=domain_invite.email,
            role=domain_invite.role,
            token=domain_invite.token,
            expires_at=domain_invite.expires_at,
            created_at=domain_invite.created_at
        )

    async def save(self, invitation: DomainInvitation) -> DomainInvitation:
        db_invite = await self.session.get(DbInvitation, invitation.id)

        if db_invite:
            db_invite.email = invitation.email
            db_invite.role = invitation.role
            db_invite.token = invitation.token
            db_invite.expires_at = invitation.expires_at
        else:
            db_invite = self._to_db(invitation)
            self.session.add(db_invite)

        await self.session.flush()
        return self._to_domain(db_invite)

    async def get_by_token(self, token: str) -> DomainInvitation | None:
        stmt = select(DbInvitation).where(DbInvitation.token == token)
        result = await self.session.execute(stmt)
        db_invite = result.scalar_one_or_none()
        if not db_invite:
            return None
        return self._to_domain(db_invite)

    async def delete_by_token(self, token: str) -> None:
        stmt = delete(DbInvitation).where(DbInvitation.token == token)
        await self.session.execute(stmt)
        await self.session.flush()
