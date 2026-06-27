import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.user import User as DomainUser
from app.domain.ports.user_repository import UserRepository
from app.infrastructure.db.models.user import User as DbUser


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, db_user: DbUser) -> DomainUser:
        return DomainUser(
            id=db_user.id,
            tenant_id=db_user.tenant_id,
            email=db_user.email,
            password_hash=db_user.password_hash,
            name=db_user.name,
            role=db_user.role,
            is_active=db_user.is_active,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )

    def _to_db(self, domain_user: DomainUser) -> DbUser:
        return DbUser(
            id=domain_user.id,
            tenant_id=domain_user.tenant_id,
            email=domain_user.email,
            password_hash=domain_user.password_hash,
            name=domain_user.name,
            role=domain_user.role,
            is_active=domain_user.is_active,
            created_at=domain_user.created_at,
            updated_at=domain_user.updated_at
        )

    async def save(self, user: DomainUser) -> DomainUser:
        db_user = await self.session.get(DbUser, user.id)

        if db_user:
            db_user.name = user.name
            db_user.password_hash = user.password_hash
            db_user.role = user.role
            db_user.is_active = user.is_active
            db_user.updated_at = user.updated_at
        else:
            db_user = self._to_db(user)
            self.session.add(db_user)

        await self.session.flush()
        return self._to_domain(db_user)

    async def get_by_id(self, user_id: uuid.UUID) -> DomainUser | None:
        db_user = await self.session.get(DbUser, user_id)
        if not db_user:
            return None
        return self._to_domain(db_user)

    async def get_by_email_and_tenant(self, email: str, tenant_id: uuid.UUID) -> DomainUser | None:
        stmt = select(DbUser).where(DbUser.email == email, DbUser.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        db_user = result.scalar_one_or_none()
        if not db_user:
            return None
        return self._to_domain(db_user)

    async def get_by_email(self, email: str) -> DomainUser | None:
        stmt = select(DbUser).where(DbUser.email == email)
        result = await self.session.execute(stmt)
        db_user = result.scalars().first()
        if not db_user:
            return None
        return self._to_domain(db_user)

    async def get_by_tenant(self, tenant_id: uuid.UUID) -> list[DomainUser]:
        stmt = select(DbUser).where(DbUser.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        db_users = result.scalars().all()
        return [self._to_domain(db_user) for db_user in db_users]
