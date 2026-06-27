from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import get_db
from app.infrastructure.db.repositories.sqlalchemy_ticket_repository import SQLAlchemyTicketRepository
from app.application.use_cases.create_ticket import CreateTicketUseCase
from app.application.use_cases.list_customer_tickets import ListCustomerTicketsUseCase
from app.application.use_cases.update_ticket import UpdateTicketUseCase


async def get_ticket_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyTicketRepository:
    return SQLAlchemyTicketRepository(db)


async def get_create_ticket_use_case(
    repo: SQLAlchemyTicketRepository = Depends(get_ticket_repository)
) -> CreateTicketUseCase:
    return CreateTicketUseCase(repo)


async def get_list_customer_tickets_use_case(
    repo: SQLAlchemyTicketRepository = Depends(get_ticket_repository)
) -> ListCustomerTicketsUseCase:
    return ListCustomerTicketsUseCase(repo)


async def get_update_ticket_use_case(
    repo: SQLAlchemyTicketRepository = Depends(get_ticket_repository)
) -> UpdateTicketUseCase:
    return UpdateTicketUseCase(repo)
