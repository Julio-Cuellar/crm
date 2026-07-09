import uuid
from app.modules.tenants.domain.entities.tenant import Tenant
from app.modules.tenants.domain.ports.tenant_repository import TenantRepository
from app.modules.tenants.domain.exceptions.tenant import TenantNotFoundException, TenantSlugAlreadyExistsException
from app.modules.tenants.infrastructure.messaging.publishers import publish_tenant_updated
from app.platform.messaging.event_bus import EventBus


class UpdateTenantUseCase:
    def __init__(self, tenant_repository: TenantRepository, event_bus: EventBus | None = None):
        self.tenant_repository = tenant_repository
        self.event_bus = event_bus

    async def execute(
        self,
        tenant_id: uuid.UUID,
        name: str,
        slug: str,
        phone_number_id: str | None = None,
        timezone: str = "America/Mexico_City",
        locale: str = "es",
        mode: str = "SERVICES",
        account_type: str = "INDIVIDUAL",
        enabled_modules: list[str] | None = None,
    ) -> Tenant:
        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundException(f"No se encontró el negocio solicitado.")

        if tenant.slug != slug:
            existing = await self.tenant_repository.get_by_slug(slug)
            if existing:
                raise TenantSlugAlreadyExistsException(f"El identificador '{slug}' ya está registrado.")

        tenant.update_settings(
            name=name,
            timezone=timezone,
            locale=locale,
            mode=mode,
            account_type=account_type,
            enabled_modules=enabled_modules,
        )
        tenant.slug = slug
        tenant.phone_number_id = phone_number_id

        saved = await self.tenant_repository.save(tenant)
        await publish_tenant_updated(self.event_bus, saved)
        return saved
