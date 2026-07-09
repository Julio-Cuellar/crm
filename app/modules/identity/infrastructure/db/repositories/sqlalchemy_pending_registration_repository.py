import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.identity.domain.entities.pending_registration import PendingRegistration as DomainPendingRegistration
from app.modules.identity.domain.ports.pending_registration_repository import PendingRegistrationRepository
from app.modules.identity.infrastructure.db.models.pending_registration import PendingRegistration as DbPendingRegistration


class SQLAlchemyPendingRegistrationRepository(PendingRegistrationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, db_pending: DbPendingRegistration) -> DomainPendingRegistration:
        return DomainPendingRegistration(
            id=db_pending.id,
            email=db_pending.email,
            password_hash=db_pending.password_hash,
            name=db_pending.name,
            tenant_name=db_pending.tenant_name,
            verification_token=db_pending.verification_token,
            token_expires_at=db_pending.token_expires_at,
            created_at=db_pending.created_at
        )

    def _to_db(self, domain_pending: DomainPendingRegistration) -> DbPendingRegistration:
        return DbPendingRegistration(
            id=domain_pending.id,
            email=domain_pending.email,
            password_hash=domain_pending.password_hash,
            name=domain_pending.name,
            tenant_name=domain_pending.tenant_name,
            verification_token=domain_pending.verification_token,
            token_expires_at=domain_pending.token_expires_at,
            created_at=domain_pending.created_at
        )

    async def save(self, pending: DomainPendingRegistration) -> DomainPendingRegistration:
        db_pending = await self.session.get(DbPendingRegistration, pending.id)

        if db_pending:
            db_pending.email = pending.email
            db_pending.password_hash = pending.password_hash
            db_pending.name = pending.name
            db_pending.tenant_name = pending.tenant_name
            db_pending.verification_token = pending.verification_token
            db_pending.token_expires_at = pending.token_expires_at
        else:
            db_pending = self._to_db(pending)
            self.session.add(db_pending)

        await self.session.flush()
        return self._to_domain(db_pending)

    async def get_by_email(self, email: str) -> DomainPendingRegistration | None:
        stmt = select(DbPendingRegistration).where(DbPendingRegistration.email == email)
        result = await self.session.execute(stmt)
        db_pending = result.scalar_one_or_none()
        if not db_pending:
            return None
        return self._to_domain(db_pending)

    async def delete(self, email: str) -> None:
        stmt = delete(DbPendingRegistration).where(DbPendingRegistration.email == email)
        await self.session.execute(stmt)
        await self.session.flush()
