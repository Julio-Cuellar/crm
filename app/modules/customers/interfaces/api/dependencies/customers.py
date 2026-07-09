from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.platform.db.session import get_db
from app.platform.messaging.event_bus import EventBus
from app.modules.customers.infrastructure.db.repositories.sqlalchemy_customer_repository import SQLAlchemyCustomerRepository
from app.modules.customers.application.use_cases.create_customer import CreateCustomerUseCase
from app.modules.customers.application.use_cases.upsert_customer import UpsertCustomerUseCase
from app.modules.customers.application.use_cases.update_customer import UpdateCustomerUseCase
from app.modules.customers.application.use_cases.update_customer_pipeline import UpdateCustomerPipelineUseCase
from app.modules.customers.application.use_cases.get_customer import GetCustomerUseCase
from app.modules.customers.application.use_cases.list_customers import ListCustomersUseCase
from app.modules.customers.application.use_cases.delete_customer import DeleteCustomerUseCase


async def get_customer_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyCustomerRepository:
    return SQLAlchemyCustomerRepository(db)


async def get_event_bus(request: Request) -> EventBus | None:
    return request.app.state.event_bus


async def get_create_customer_use_case(
    repo: SQLAlchemyCustomerRepository = Depends(get_customer_repository),
    event_bus: EventBus | None = Depends(get_event_bus),
) -> CreateCustomerUseCase:
    return CreateCustomerUseCase(repo, event_bus)


async def get_upsert_customer_use_case(
    repo: SQLAlchemyCustomerRepository = Depends(get_customer_repository),
    event_bus: EventBus | None = Depends(get_event_bus),
) -> UpsertCustomerUseCase:
    return UpsertCustomerUseCase(repo, event_bus)


async def get_update_customer_use_case(
    repo: SQLAlchemyCustomerRepository = Depends(get_customer_repository),
    event_bus: EventBus | None = Depends(get_event_bus),
) -> UpdateCustomerUseCase:
    return UpdateCustomerUseCase(repo, event_bus)


async def get_update_customer_pipeline_use_case(
    repo: SQLAlchemyCustomerRepository = Depends(get_customer_repository),
    event_bus: EventBus | None = Depends(get_event_bus),
) -> UpdateCustomerPipelineUseCase:
    return UpdateCustomerPipelineUseCase(repo, event_bus)


async def get_get_customer_use_case(
    repo: SQLAlchemyCustomerRepository = Depends(get_customer_repository)
) -> GetCustomerUseCase:
    return GetCustomerUseCase(repo)


async def get_list_customers_use_case(
    repo: SQLAlchemyCustomerRepository = Depends(get_customer_repository)
) -> ListCustomersUseCase:
    return ListCustomersUseCase(repo)


async def get_delete_customer_use_case(
    repo: SQLAlchemyCustomerRepository = Depends(get_customer_repository),
    event_bus: EventBus | None = Depends(get_event_bus),
) -> DeleteCustomerUseCase:
    return DeleteCustomerUseCase(repo, event_bus)
