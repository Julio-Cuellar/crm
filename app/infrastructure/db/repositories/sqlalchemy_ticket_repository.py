import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.ticket import Ticket as DomainTicket
from app.domain.ports.ticket_repository import TicketRepository
from app.infrastructure.db.models.ticket import Ticket as DbTicket


class SQLAlchemyTicketRepository(TicketRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, db_ticket: DbTicket) -> DomainTicket:
        return DomainTicket(
            id=db_ticket.id,
            tenant_id=db_ticket.tenant_id,
            customer_id=db_ticket.customer_id,
            title=db_ticket.title,
            description=db_ticket.description,
            category=db_ticket.category,
            status=db_ticket.status,
            priority=db_ticket.priority,
            assigned_to=db_ticket.assigned_to,
            created_at=db_ticket.created_at,
            updated_at=db_ticket.updated_at
        )

    def _to_db(self, domain_ticket: DomainTicket) -> DbTicket:
        return DbTicket(
            id=domain_ticket.id,
            tenant_id=domain_ticket.tenant_id,
            customer_id=domain_ticket.customer_id,
            title=domain_ticket.title,
            description=domain_ticket.description,
            category=domain_ticket.category,
            status=domain_ticket.status,
            priority=domain_ticket.priority,
            assigned_to=domain_ticket.assigned_to,
            created_at=domain_ticket.created_at,
            updated_at=domain_ticket.updated_at
        )

    async def save(self, ticket: DomainTicket) -> DomainTicket:
        db_ticket = await self.session.get(DbTicket, ticket.id)

        if db_ticket:
            db_ticket.title = ticket.title
            db_ticket.description = ticket.description
            db_ticket.category = ticket.category
            db_ticket.status = ticket.status
            db_ticket.priority = ticket.priority
            db_ticket.assigned_to = ticket.assigned_to
            db_ticket.updated_at = ticket.updated_at
        else:
            db_ticket = self._to_db(ticket)
            self.session.add(db_ticket)

        await self.session.flush()
        return self._to_domain(db_ticket)

    async def get_by_id(self, ticket_id: uuid.UUID) -> DomainTicket | None:
        db_ticket = await self.session.get(DbTicket, ticket_id)
        if not db_ticket:
            return None
        return self._to_domain(db_ticket)

    async def get_by_customer_id(self, customer_id: uuid.UUID) -> list[DomainTicket]:
        stmt = select(DbTicket).where(DbTicket.customer_id == customer_id).order_by(DbTicket.created_at.desc())
        result = await self.session.execute(stmt)
        db_tickets = result.scalars().all()
        return [self._to_domain(t) for t in db_tickets]

    async def get_by_tenant_id(self, tenant_id: uuid.UUID) -> list[DomainTicket]:
        stmt = select(DbTicket).where(DbTicket.tenant_id == tenant_id).order_by(DbTicket.created_at.desc())
        result = await self.session.execute(stmt)
        db_tickets = result.scalars().all()
        return [self._to_domain(t) for t in db_tickets]

    async def delete(self, ticket_id: uuid.UUID) -> bool:
        db_ticket = await self.session.get(DbTicket, ticket_id)
        if not db_ticket:
            return False
        await self.session.delete(db_ticket)
        await self.session.flush()
        return True
