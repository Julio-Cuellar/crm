import re
import unicodedata
from app.modules.identity.domain.ports.pending_registration_repository import PendingRegistrationRepository
from app.modules.tenants.application.use_cases.create_tenant import CreateTenantUseCase
from app.modules.tenants.domain.entities.tenant import Tenant
from app.modules.identity.domain.exceptions.auth import (
    PendingRegistrationNotFoundException,
    InvalidVerificationTokenException,
    TokenExpiredException
)


def slugify(text: str) -> str:
    """Genera un slug React-friendly y URL-friendly a partir de un texto."""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)


class VerifyRegistrationUseCase:
    def __init__(
        self,
        pending_repo: PendingRegistrationRepository,
        create_tenant_use_case: CreateTenantUseCase
    ):
        self.pending_repo = pending_repo
        self.create_tenant_use_case = create_tenant_use_case

    async def execute(self, email: str, token: str) -> Tenant:
        # 1. Buscar pre-registro
        pending = await self.pending_repo.get_by_email(email)
        if not pending:
            raise PendingRegistrationNotFoundException(
                f"No hay solicitudes de registro pendientes para el correo '{email}'."
            )

        # 2. Validar token
        if pending.verification_token != token:
            raise InvalidVerificationTokenException(
                "El código de verificación ingresado no es válido."
            )

        # 3. Validar expiración
        if pending.is_expired():
            await self.pending_repo.delete(email)
            raise TokenExpiredException(
                "El código de verificación ha expirado. Por favor, regístrese nuevamente."
            )

        # 4. Materializar el Tenant usando el caso de uso existente
        # Esto disparará el evento 'tenant.created' que dará de alta al usuario OWNER asíncronamente
        tenant_slug = slugify(pending.tenant_name)
        
        created_tenant = await self.create_tenant_use_case.execute(
            name=pending.tenant_name,
            slug=tenant_slug,
            owner_name=pending.name,
            owner_email=pending.email,
            owner_password_hash=pending.password_hash
        )

        # 5. Eliminar el pre-registro
        await self.pending_repo.delete(email)

        return created_tenant
