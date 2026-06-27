import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.service import Service as DomainService
from app.domain.ports.service_repository import ServiceRepository
from app.infrastructure.db.models.service import Service as DbService


class SQLAlchemyServiceRepository(ServiceRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, db_service: DbService) -> DomainService:
        return DomainService(
            id=db_service.id,
            tenant_id=db_service.tenant_id,
            name=db_service.name,
            description=db_service.description,
            duration_minutes=db_service.duration_minutes,
            price=db_service.price,
            currency=db_service.currency,
            is_active=db_service.is_active,
            created_at=db_service.created_at,
            updated_at=db_service.updated_at
        )

    def _to_db(self, domain_service: DomainService) -> DbService:
        return DbService(
            id=domain_service.id,
            tenant_id=domain_service.tenant_id,
            name=domain_service.name,
            description=domain_service.description,
            duration_minutes=domain_service.duration_minutes,
            price=domain_service.price,
            currency=domain_service.currency,
            is_active=domain_service.is_active,
            created_at=domain_service.created_at,
            updated_at=domain_service.updated_at
        )

    async def save(self, service: DomainService) -> DomainService:
        db_service = await self.session.get(DbService, service.id)

        if db_service:
            db_service.name = service.name
            db_service.description = service.description
            db_service.duration_minutes = service.duration_minutes
            db_service.price = service.price
            db_service.currency = service.currency
            db_service.is_active = service.is_active
            db_service.updated_at = service.updated_at
        else:
            db_service = self._to_db(service)
            self.session.add(db_service)

        await self.session.flush()
        return self._to_domain(db_service)

    async def get_by_id(self, service_id: uuid.UUID) -> DomainService | None:
        db_service = await self.session.get(DbService, service_id)
        if not db_service:
            return None
        return self._to_domain(db_service)

    async def get_by_tenant(self, tenant_id: uuid.UUID) -> list[DomainService]:
        stmt = select(DbService).where(DbService.tenant_id == tenant_id).order_by(DbService.name.asc())
        result = await self.session.execute(stmt)
        db_services = result.scalars().all()
        return [self._to_domain(s) for s in db_services]

    async def delete(self, service_id: uuid.UUID) -> bool:
        db_service = await self.session.get(DbService, service_id)
        if not db_service:
            return False
        await self.session.delete(db_service)
        await self.session.flush()
        return True
