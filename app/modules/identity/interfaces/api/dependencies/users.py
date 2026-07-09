from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.platform.db.session import get_db
from app.modules.identity.infrastructure.db.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.modules.identity.application.use_cases.create_user import CreateUserUseCase
from app.modules.identity.application.use_cases.get_user import GetUserUseCase
from app.modules.identity.application.use_cases.list_users import ListUsersUseCase


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyUserRepository:
    return SQLAlchemyUserRepository(db)


async def get_create_user_use_case(
    repo: SQLAlchemyUserRepository = Depends(get_user_repository)
) -> CreateUserUseCase:
    return CreateUserUseCase(repo)


async def get_get_user_use_case(
    repo: SQLAlchemyUserRepository = Depends(get_user_repository)
) -> GetUserUseCase:
    return GetUserUseCase(repo)


async def get_list_users_use_case(
    repo: SQLAlchemyUserRepository = Depends(get_user_repository)
) -> ListUsersUseCase:
    return ListUsersUseCase(repo)
