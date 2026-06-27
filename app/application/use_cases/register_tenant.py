import random
import string
from datetime import datetime, timedelta
from app.domain.entities.pending_registration import PendingRegistration
from app.domain.ports.pending_registration_repository import PendingRegistrationRepository
from app.domain.ports.user_repository import UserRepository
from app.domain.ports.event_bus import EventBus
from app.domain.exceptions.auth import EmailAlreadyRegisteredException
from app.core.security import get_password_hash


class RegisterTenantUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        pending_repo: PendingRegistrationRepository,
        event_bus: EventBus | None = None
    ):
        self.user_repo = user_repo
        self.pending_repo = pending_repo
        self.event_bus = event_bus

    async def execute(
        self,
        email: str,
        password: str,
        name: str,
        tenant_name: str
    ) -> PendingRegistration:
        # 1. Validar si el email ya está tomado por un usuario activo en el sistema
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise EmailAlreadyRegisteredException(
                f"El correo electrónico '{email}' ya está registrado con una cuenta activa."
            )

        # 2. Si ya hay una solicitud de pre-registro existente para ese correo, la limpiamos
        existing_pending = await self.pending_repo.get_by_email(email)
        if existing_pending:
            await self.pending_repo.delete(email)

        # 3. Encriptar contraseña y generar token de verificación (6 dígitos numéricos)
        password_hash = get_password_hash(password)
        verification_token = "".join(random.choices(string.digits, k=6))
        token_expires_at = datetime.now() + timedelta(hours=24)

        # 4. Crear y guardar el registro de pre-registro
        pending = PendingRegistration(
            email=email,
            password_hash=password_hash,
            name=name,
            tenant_name=tenant_name,
            verification_token=verification_token,
            token_expires_at=token_expires_at
        )

        saved_pending = await self.pending_repo.save(pending)

        # Siempre imprimir el token en la consola para facilitar el desarrollo/pruebas
        print(f"\n[RegisterTenantUseCase] Token de verificación generado para {email}: {verification_token}\n")

        # 5. Publicar evento para enviar el correo de verificación (ej. vía n8n)
        if self.event_bus:
            payload = {
                "email": saved_pending.email,
                "name": saved_pending.name,
                "tenantName": saved_pending.tenant_name,
                "verificationToken": saved_pending.verification_token,
                "expiresAt": saved_pending.token_expires_at.isoformat()
            }
            await self.event_bus.publish("registration.verification_requested", payload)

        return saved_pending
