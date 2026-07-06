import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.tenant import Tenant as DomainTenant
from app.domain.ports.tenant_repository import TenantRepository
from app.infrastructure.db.models.tenant import Tenant as DbTenant


class SQLAlchemyTenantRepository(TenantRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, db_tenant: DbTenant) -> DomainTenant:
        return DomainTenant(
            id=db_tenant.id,
            name=db_tenant.name,
            slug=db_tenant.slug,
            phone_number_id=db_tenant.phone_number_id,
            timezone=db_tenant.timezone,
            locale=db_tenant.locale,
            mode=db_tenant.mode,
            account_type=db_tenant.account_type,
            enabled_modules=db_tenant.enabled_modules or [db_tenant.mode],
            is_active=db_tenant.is_active,
            ai_system_prompt=db_tenant.ai_system_prompt,
            created_at=db_tenant.created_at,
            updated_at=db_tenant.updated_at
        )

    def _to_db(self, domain_tenant: DomainTenant) -> DbTenant:
        return DbTenant(
            id=domain_tenant.id,
            name=domain_tenant.name,
            slug=domain_tenant.slug,
            phone_number_id=domain_tenant.phone_number_id,
            timezone=domain_tenant.timezone,
            locale=domain_tenant.locale,
            mode=domain_tenant.mode,
            account_type=domain_tenant.account_type,
            enabled_modules=domain_tenant.enabled_modules,
            is_active=domain_tenant.is_active,
            ai_system_prompt=domain_tenant.ai_system_prompt,
            created_at=domain_tenant.created_at,
            updated_at=domain_tenant.updated_at
        )

    async def save(self, tenant: DomainTenant) -> DomainTenant:
        db_tenant = await self.session.get(DbTenant, tenant.id)

        if db_tenant:
            db_tenant.name = tenant.name
            db_tenant.slug = tenant.slug
            db_tenant.phone_number_id = tenant.phone_number_id
            db_tenant.timezone = tenant.timezone
            db_tenant.locale = tenant.locale
            db_tenant.mode = tenant.mode
            db_tenant.account_type = tenant.account_type
            db_tenant.enabled_modules = tenant.enabled_modules
            db_tenant.is_active = tenant.is_active
            db_tenant.ai_system_prompt = tenant.ai_system_prompt
            db_tenant.updated_at = tenant.updated_at
        else:
            db_tenant = self._to_db(tenant)
            self.session.add(db_tenant)

        await self.session.flush()
        await self.session.refresh(db_tenant)
        return self._to_domain(db_tenant)

    async def get_by_id(self, tenant_id: uuid.UUID) -> DomainTenant | None:
        db_tenant = await self.session.get(DbTenant, tenant_id)
        if not db_tenant:
            return None
        return self._to_domain(db_tenant)

    async def get_by_slug(self, slug: str) -> DomainTenant | None:
        stmt = select(DbTenant).where(DbTenant.slug == slug)
        result = await self.session.execute(stmt)
        db_tenant = result.scalar_one_or_none()
        if not db_tenant:
            return None
        return self._to_domain(db_tenant)

    async def get_by_phone_number_id(self, phone_number_id: str) -> DomainTenant | None:
        stmt = select(DbTenant).where(DbTenant.phone_number_id == phone_number_id)
        result = await self.session.execute(stmt)
        db_tenant = result.scalar_one_or_none()
        if not db_tenant:
            return None
        return self._to_domain(db_tenant)
