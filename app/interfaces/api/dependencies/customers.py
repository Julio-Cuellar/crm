from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repositories.sqlalchemy_customer_repository import SQLAlchemyCustomerRepository
from app.application.use_cases.create_customer import CreateCustomerUseCase
from app.application.use_cases.upsert_customer import UpsertCustomerUseCase
from app.application.use_cases.update_customer import UpdateCustomerUseCase
from app.application.use_cases.get_customer import GetCustomerUseCase
from app.application.use_cases.list_customers import ListCustomersUseCase
from app.application.use_cases.delete_customer import DeleteCustomerUseCase


async def get_customer_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyCustomerRepository:
    return SQLAlchemyCustomerRepository(db)


async def get_create_customer_use_case(
    repo: SQLAlchemyCustomerRepository = Depends(get_customer_repository)
) -> CreateCustomerUseCase:
    return CreateCustomerUseCase(repo)


async def get_upsert_customer_use_case(
    repo: SQLAlchemyCustomerRepository = Depends(get_customer_repository)
) -> UpsertCustomerUseCase:
    return UpsertCustomerUseCase(repo)


async def get_update_customer_use_case(
    repo: SQLAlchemyCustomerRepository = Depends(get_customer_repository)
) -> UpdateCustomerUseCase:
    return UpdateCustomerUseCase(repo)


async def get_get_customer_use_case(
    repo: SQLAlchemyCustomerRepository = Depends(get_customer_repository)
) -> GetCustomerUseCase:
    return GetCustomerUseCase(repo)


async def get_list_customers_use_case(
    repo: SQLAlchemyCustomerRepository = Depends(get_customer_repository)
) -> ListCustomersUseCase:
    return ListCustomersUseCase(repo)


async def get_delete_customer_use_case(
    repo: SQLAlchemyCustomerRepository = Depends(get_customer_repository)
) -> DeleteCustomerUseCase:
    return DeleteCustomerUseCase(repo)
