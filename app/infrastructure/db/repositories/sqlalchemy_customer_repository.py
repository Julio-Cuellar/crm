import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.customer import Customer as DomainCustomer
from app.domain.ports.customer_repository import CustomerRepository
from app.infrastructure.db.models.customer import Customer as DbCustomer


class SQLAlchemyCustomerRepository(CustomerRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, db_customer: DbCustomer) -> DomainCustomer:
        return DomainCustomer(
            id=db_customer.id,
            tenant_id=db_customer.tenant_id,
            phone=db_customer.phone,
            name=db_customer.name,
            email=db_customer.email,
            lead_status=db_customer.lead_status,
            pipeline_stage=db_customer.pipeline_stage,
            deal_value=db_customer.deal_value,
            created_at=db_customer.created_at,
            updated_at=db_customer.updated_at
        )

    def _to_db(self, domain_customer: DomainCustomer) -> DbCustomer:
        return DbCustomer(
            id=domain_customer.id,
            tenant_id=domain_customer.tenant_id,
            phone=domain_customer.phone,
            name=domain_customer.name,
            email=domain_customer.email,
            lead_status=domain_customer.lead_status,
            pipeline_stage=domain_customer.pipeline_stage,
            deal_value=domain_customer.deal_value,
            created_at=domain_customer.created_at,
            updated_at=domain_customer.updated_at
        )

    async def save(self, customer: DomainCustomer) -> DomainCustomer:
        db_customer = await self.session.get(DbCustomer, customer.id)

        if db_customer:
            db_customer.name = customer.name
            db_customer.email = customer.email
            db_customer.lead_status = customer.lead_status
            db_customer.pipeline_stage = customer.pipeline_stage
            db_customer.deal_value = customer.deal_value
            db_customer.updated_at = customer.updated_at
        else:
            db_customer = self._to_db(customer)
            self.session.add(db_customer)

        await self.session.flush()
        return self._to_domain(db_customer)

    async def get_by_id(self, customer_id: uuid.UUID) -> DomainCustomer | None:
        db_customer = await self.session.get(DbCustomer, customer_id)
        if not db_customer:
            return None
        return self._to_domain(db_customer)

    async def get_by_phone_and_tenant(self, phone: str, tenant_id: uuid.UUID) -> DomainCustomer | None:
        stmt = select(DbCustomer).where(DbCustomer.tenant_id == tenant_id, DbCustomer.phone == phone)
        result = await self.session.execute(stmt)
        db_customer = result.scalars().first()
        if not db_customer:
            return None
        return self._to_domain(db_customer)

    async def get_by_tenant(self, tenant_id: uuid.UUID) -> list[DomainCustomer]:
        stmt = select(DbCustomer).where(DbCustomer.tenant_id == tenant_id).order_by(DbCustomer.name.asc())
        result = await self.session.execute(stmt)
        db_customers = result.scalars().all()
        return [self._to_domain(c) for c in db_customers]

    async def delete(self, customer_id: uuid.UUID) -> bool:
        db_customer = await self.session.get(DbCustomer, customer_id)
        if not db_customer:
            return False
        await self.session.delete(db_customer)
        await self.session.flush()
        return True
