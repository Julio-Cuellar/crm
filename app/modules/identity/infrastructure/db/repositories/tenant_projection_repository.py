import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity.infrastructure.db.models.tenant_projection import TenantProjection


class TenantProjectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_name(self, tenant_id: uuid.UUID) -> str | None:
        row = await self.session.get(TenantProjection, tenant_id)
        return row.name if row else None

    async def upsert(self, tenant_id: uuid.UUID, name: str, source_updated_at: datetime | None) -> None:
        row = await self.session.get(TenantProjection, tenant_id)
        if row:
            if source_updated_at and row.source_updated_at and source_updated_at < row.source_updated_at:
                return  # evento desordenado/atrasado, no-op
            row.name = name
            row.source_updated_at = source_updated_at
        else:
            row = TenantProjection(id=tenant_id, name=name, source_updated_at=source_updated_at)
            self.session.add(row)
        await self.session.flush()
