from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.platform.db.session import get_db
from app.platform.messaging.event_bus import EventBus
from app.modules.tickets.infrastructure.db.repositories.sqlalchemy_ticket_repository import SQLAlchemyTicketRepository
from app.modules.tickets.infrastructure.db.repositories.customer_projection_repository import (
    CustomerProjectionRepository,
)
from app.modules.tickets.application.use_cases.create_ticket import CreateTicketUseCase
from app.modules.tickets.application.use_cases.list_customer_tickets import ListCustomerTicketsUseCase
from app.modules.tickets.application.use_cases.update_ticket import UpdateTicketUseCase


async def get_ticket_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyTicketRepository:
    return SQLAlchemyTicketRepository(db)


async def get_customer_projection_repository(
    db: AsyncSession = Depends(get_db)
) -> CustomerProjectionRepository:
    return CustomerProjectionRepository(db)


async def get_event_bus(request: Request) -> EventBus | None:
    return request.app.state.event_bus


async def get_create_ticket_use_case(
    repo: SQLAlchemyTicketRepository = Depends(get_ticket_repository),
    event_bus: EventBus | None = Depends(get_event_bus),
) -> CreateTicketUseCase:
    return CreateTicketUseCase(repo, event_bus)


async def get_list_customer_tickets_use_case(
    repo: SQLAlchemyTicketRepository = Depends(get_ticket_repository)
) -> ListCustomerTicketsUseCase:
    return ListCustomerTicketsUseCase(repo)


async def get_update_ticket_use_case(
    repo: SQLAlchemyTicketRepository = Depends(get_ticket_repository),
    event_bus: EventBus | None = Depends(get_event_bus),
) -> UpdateTicketUseCase:
    return UpdateTicketUseCase(repo, event_bus)
