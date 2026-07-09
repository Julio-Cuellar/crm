import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.scheduling.infrastructure.db.models.service_projection import ServiceProjection


class ServiceProjectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, service_id: uuid.UUID) -> ServiceProjection | None:
        return await self.session.get(ServiceProjection, service_id)

    async def upsert(
        self,
        service_id: uuid.UUID,
        tenant_id: uuid.UUID,
        name: str,
        duration_minutes: int,
        price: Decimal | None,
        currency: str,
        is_active: bool,
        source_updated_at: datetime | None,
    ) -> None:
        row = await self.session.get(ServiceProjection, service_id)
        if row:
            if source_updated_at and row.source_updated_at and source_updated_at < row.source_updated_at:
                return  # evento desordenado/atrasado, no-op
            row.tenant_id = tenant_id
            row.name = name
            row.duration_minutes = duration_minutes
            row.price = price
            row.currency = currency
            row.is_active = is_active
            row.source_updated_at = source_updated_at
        else:
            row = ServiceProjection(
                id=service_id, tenant_id=tenant_id, name=name, duration_minutes=duration_minutes,
                price=price, currency=currency, is_active=is_active, source_updated_at=source_updated_at,
            )
            self.session.add(row)
        await self.session.flush()

    async def delete(self, service_id: uuid.UUID) -> None:
        row = await self.session.get(ServiceProjection, service_id)
        if row:
            await self.session.delete(row)
            await self.session.flush()
