from app.modules.tenants.domain.entities.tenant import Tenant
from app.modules.tenants.domain.ports.tenant_repository import TenantRepository
from app.platform.messaging.event_bus import EventBus
from app.modules.tenants.domain.exceptions.tenant import TenantSlugAlreadyExistsException, EventBusUnavailableException


class CreateTenantUseCase:
    def __init__(
        self,
        tenant_repository: TenantRepository,
        event_bus: EventBus | None = None,
    ):
        self.tenant_repository = tenant_repository
        self.event_bus = event_bus

    async def execute(
        self,
        name: str,
        slug: str,
        phone_number_id: str | None = None,
        timezone: str = "America/Mexico_City",
        locale: str = "es",
        owner_name: str | None = None,
        owner_email: str | None = None,
        owner_password_hash: str | None = None
    ) -> Tenant:
        # Validar si ya existe un tenant con el mismo slug
        existing = await self.tenant_repository.get_by_slug(slug)
        if existing:
            raise TenantSlugAlreadyExistsException(f"El identificador '{slug}' ya está registrado.")

        tenant = Tenant(
            name=name,
            slug=slug,
            phone_number_id=phone_number_id,
            timezone=timezone,
            locale=locale
        )

        saved_tenant = await self.tenant_repository.save(tenant)

        # Si se envían los datos del propietario del negocio, publicar el evento para que
        # el módulo `identity` cree el usuario OWNER. Sin RabbitMQ no hay forma de crear el
        # OWNER sin tocar el repositorio de otro módulo, así que la operación falla explícito
        # en vez de degradar silenciosamente (ver plan de monolito modular).
        if owner_name and owner_email and owner_password_hash:
            if not self.event_bus:
                raise EventBusUnavailableException(
                    "No se pudo completar el registro: el bus de eventos no está disponible."
                )
            payload = {
                "tenantId": str(saved_tenant.id),
                "name": saved_tenant.name,
                "ownerName": owner_name,
                "ownerEmail": owner_email,
                "ownerPasswordHash": owner_password_hash
            }
            await self.event_bus.publish("tenant.created", payload)

        return saved_tenant
