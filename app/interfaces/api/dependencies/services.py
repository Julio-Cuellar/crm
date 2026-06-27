from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repositories.sqlalchemy_service_repository import SQLAlchemyServiceRepository
from app.application.use_cases.create_service import CreateServiceUseCase
from app.application.use_cases.update_service import UpdateServiceUseCase
from app.application.use_cases.get_service import GetServiceUseCase
from app.application.use_cases.list_services import ListServicesUseCase
from app.application.use_cases.delete_service import DeleteServiceUseCase


async def get_service_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyServiceRepository:
    return SQLAlchemyServiceRepository(db)


async def get_create_service_use_case(
    repo: SQLAlchemyServiceRepository = Depends(get_service_repository)
) -> CreateServiceUseCase:
    return CreateServiceUseCase(repo)


async def get_update_service_use_case(
    repo: SQLAlchemyServiceRepository = Depends(get_service_repository)
) -> UpdateServiceUseCase:
    return UpdateServiceUseCase(repo)


async def get_get_service_use_case(
    repo: SQLAlchemyServiceRepository = Depends(get_service_repository)
) -> GetServiceUseCase:
    return GetServiceUseCase(repo)


async def get_list_services_use_case(
    repo: SQLAlchemyServiceRepository = Depends(get_service_repository)
) -> ListServicesUseCase:
    return ListServicesUseCase(repo)


async def get_delete_service_use_case(
    repo: SQLAlchemyServiceRepository = Depends(get_service_repository)
) -> DeleteServiceUseCase:
    return DeleteServiceUseCase(repo)
