from app.domain.entities.tenant import Tenant
from app.domain.ports.tenant_repository import TenantRepository
from app.domain.ports.event_bus import EventBus
from app.domain.ports.user_repository import UserRepository
from app.domain.exceptions.tenant import TenantSlugAlreadyExistsException


class CreateTenantUseCase:
    def __init__(
        self,
        tenant_repository: TenantRepository,
        event_bus: EventBus | None = None,
        user_repository: UserRepository | None = None
    ):
        self.tenant_repository = tenant_repository
        self.event_bus = event_bus
        self.user_repository = user_repository

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

        # Si se envían los datos del propietario del negocio, publicar el evento o crearlo síncronamente
        if owner_name and owner_email and owner_password_hash:
            payload = {
                "tenantId": str(saved_tenant.id),
                "ownerName": owner_name,
                "ownerEmail": owner_email,
                "ownerPasswordHash": owner_password_hash
            }
            if self.event_bus:
                await self.event_bus.publish("tenant.created", payload)
            else:
                print("[CreateTenantUseCase] EventBus no disponible. Creando OWNER de forma síncrona...")
                if self.user_repository:
                    from app.application.use_cases.create_user import CreateUserUseCase
                    use_case = CreateUserUseCase(self.user_repository)
                    await use_case.execute(
                        tenant_id=saved_tenant.id,
                        email=owner_email,
                        password=owner_password_hash,
                        name=owner_name,
                        role="OWNER",
                        is_hashed=True
                    )
                    print(f"[CreateTenantUseCase] OWNER '{owner_email}' creado exitosamente de forma síncrona.")
                else:
                    print("[CreateTenantUseCase] Error: user_repository no disponible. No se pudo crear el OWNER.")

        return saved_tenant
