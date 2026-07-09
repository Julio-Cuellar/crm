import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tickets.infrastructure.db.models.customer_projection import CustomerProjection


class CustomerProjectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, customer_id: uuid.UUID) -> CustomerProjection | None:
        return await self.session.get(CustomerProjection, customer_id)

    async def upsert(self, customer_id: uuid.UUID, tenant_id: uuid.UUID, name: str) -> None:
        row = await self.session.get(CustomerProjection, customer_id)
        if row:
            row.tenant_id = tenant_id
            row.name = name
        else:
            row = CustomerProjection(id=customer_id, tenant_id=tenant_id, name=name)
            self.session.add(row)
        await self.session.flush()

    async def delete(self, customer_id: uuid.UUID) -> None:
        row = await self.session.get(CustomerProjection, customer_id)
        if row:
            await self.session.delete(row)
            await self.session.flush()
