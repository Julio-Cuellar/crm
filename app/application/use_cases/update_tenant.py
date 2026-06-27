import uuid
from app.domain.entities.tenant import Tenant
from app.domain.ports.tenant_repository import TenantRepository
from app.domain.exceptions.tenant import TenantNotFoundException, TenantSlugAlreadyExistsException


class UpdateTenantUseCase:
    def __init__(self, tenant_repository: TenantRepository):
        self.tenant_repository = tenant_repository

    async def execute(
        self,
        tenant_id: uuid.UUID,
        name: str,
        slug: str,
        phone_number_id: str | None = None,
        timezone: str = "America/Mexico_City",
        locale: str = "es",
        mode: str = "SERVICES",
    ) -> Tenant:
        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundException(f"No se encontró el negocio solicitado.")

        if tenant.slug != slug:
            existing = await self.tenant_repository.get_by_slug(slug)
            if existing:
                raise TenantSlugAlreadyExistsException(f"El identificador '{slug}' ya está registrado.")

        tenant.update_settings(name=name, timezone=timezone, locale=locale, mode=mode)
        tenant.slug = slug
        tenant.phone_number_id = phone_number_id

        return await self.tenant_repository.save(tenant)
