from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.platform.db.session import get_db
from app.modules.identity.infrastructure.db.repositories.sqlalchemy_blacklisted_token_repository import SQLAlchemyBlacklistedTokenRepository
from app.modules.identity.application.use_cases.logout import LogoutUseCase


async def get_blacklisted_token_repository(
    db: AsyncSession = Depends(get_db)
) -> SQLAlchemyBlacklistedTokenRepository:
    return SQLAlchemyBlacklistedTokenRepository(db)


async def get_logout_use_case(
    blacklist_repo: SQLAlchemyBlacklistedTokenRepository = Depends(get_blacklisted_token_repository)
) -> LogoutUseCase:
    return LogoutUseCase(blacklist_repo)
