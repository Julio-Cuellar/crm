import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.identity.domain.entities.blacklisted_token import BlacklistedToken as DomainToken
from app.modules.identity.domain.ports.blacklisted_token_repository import BlacklistedTokenRepository
from app.modules.identity.infrastructure.db.models.blacklisted_token import BlacklistedToken as DbToken


class SQLAlchemyBlacklistedTokenRepository(BlacklistedTokenRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, db_token: DbToken) -> DomainToken:
        return DomainToken(
            id=db_token.id,
            token=db_token.token,
            expires_at=db_token.expires_at,
            created_at=db_token.created_at
        )

    def _to_db(self, domain_token: DomainToken) -> DbToken:
        return DbToken(
            id=domain_token.id,
            token=domain_token.token,
            expires_at=domain_token.expires_at,
            created_at=domain_token.created_at
        )

    async def save(self, blacklisted_token: DomainToken) -> DomainToken:
        db_token = await self.session.get(DbToken, blacklisted_token.id)

        if db_token:
            db_token.token = blacklisted_token.token
            db_token.expires_at = blacklisted_token.expires_at
        else:
            db_token = self._to_db(blacklisted_token)
            self.session.add(db_token)

        await self.session.flush()
        return self._to_domain(db_token)

    async def is_blacklisted(self, token: str) -> bool:
        stmt = select(DbToken).where(DbToken.token == token)
        result = await self.session.execute(stmt)
        db_token = result.scalar_one_or_none()
        return db_token is not None

    async def clean_expired(self) -> None:
        now = datetime.datetime.now(datetime.timezone.utc)
        stmt = delete(DbToken).where(DbToken.expires_at < now)
        await self.session.execute(stmt)
        await self.session.flush()
