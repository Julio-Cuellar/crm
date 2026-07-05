from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repositories.sqlalchemy_appointment_repository import SQLAlchemyAppointmentRepository
from app.infrastructure.db.repositories.sqlalchemy_customer_repository import SQLAlchemyCustomerRepository
from app.infrastructure.db.repositories.sqlalchemy_service_repository import SQLAlchemyServiceRepository
from app.application.use_cases.create_appointment import CreateAppointmentUseCase
from app.application.use_cases.get_appointment import GetAppointmentUseCase
from app.application.use_cases.list_appointments import ListAppointmentsUseCase
from app.application.use_cases.update_appointment import UpdateAppointmentUseCase
from app.application.use_cases.delete_appointment import DeleteAppointmentUseCase


async def get_appointment_repository(
    db: AsyncSession = Depends(get_db)
) -> SQLAlchemyAppointmentRepository:
    return SQLAlchemyAppointmentRepository(db)


async def get_customer_repository(
    db: AsyncSession = Depends(get_db)
) -> SQLAlchemyCustomerRepository:
    return SQLAlchemyCustomerRepository(db)


async def get_service_repository(
    db: AsyncSession = Depends(get_db)
) -> SQLAlchemyServiceRepository:
    return SQLAlchemyServiceRepository(db)


async def get_create_appointment_use_case(
    repo: SQLAlchemyAppointmentRepository = Depends(get_appointment_repository),
    customer_repo: SQLAlchemyCustomerRepository = Depends(get_customer_repository),
    service_repo: SQLAlchemyServiceRepository = Depends(get_service_repository),
) -> CreateAppointmentUseCase:
    return CreateAppointmentUseCase(repo, customer_repo, service_repo)


async def get_get_appointment_use_case(
    repo: SQLAlchemyAppointmentRepository = Depends(get_appointment_repository)
) -> GetAppointmentUseCase:
    return GetAppointmentUseCase(repo)


async def get_list_appointments_use_case(
    repo: SQLAlchemyAppointmentRepository = Depends(get_appointment_repository)
) -> ListAppointmentsUseCase:
    return ListAppointmentsUseCase(repo)


async def get_update_appointment_use_case(
    repo: SQLAlchemyAppointmentRepository = Depends(get_appointment_repository),
    service_repo: SQLAlchemyServiceRepository = Depends(get_service_repository),
) -> UpdateAppointmentUseCase:
    return UpdateAppointmentUseCase(repo, service_repo)


async def get_delete_appointment_use_case(
    repo: SQLAlchemyAppointmentRepository = Depends(get_appointment_repository)
) -> DeleteAppointmentUseCase:
    return DeleteAppointmentUseCase(repo)
