import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.scheduling.infrastructure.db.models.customer_projection import CustomerProjection


class CustomerProjectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, customer_id: uuid.UUID) -> CustomerProjection | None:
        return await self.session.get(CustomerProjection, customer_id)

    async def upsert(
        self,
        customer_id: uuid.UUID,
        tenant_id: uuid.UUID,
        name: str,
        phone: str,
        email: str | None,
        source_updated_at: datetime | None,
    ) -> None:
        row = await self.session.get(CustomerProjection, customer_id)
        if row:
            if source_updated_at and row.source_updated_at and source_updated_at < row.source_updated_at:
                return  # evento desordenado/atrasado, no-op
            row.tenant_id = tenant_id
            row.name = name
            row.phone = phone
            row.email = email
            row.source_updated_at = source_updated_at
        else:
            row = CustomerProjection(
                id=customer_id, tenant_id=tenant_id, name=name, phone=phone,
                email=email, source_updated_at=source_updated_at,
            )
            self.session.add(row)
        await self.session.flush()

    async def delete(self, customer_id: uuid.UUID) -> None:
        row = await self.session.get(CustomerProjection, customer_id)
        if row:
            await self.session.delete(row)
            await self.session.flush()
