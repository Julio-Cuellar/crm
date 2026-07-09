import uuid
from datetime import datetime, timedelta
from app.modules.identity.domain.entities.invitation import Invitation
from app.modules.identity.domain.ports.invitation_repository import InvitationRepository
from app.modules.identity.domain.ports.user_repository import UserRepository
from app.modules.identity.infrastructure.db.repositories.tenant_projection_repository import (
    TenantProjectionRepository,
)
from app.platform.messaging.event_bus import EventBus
from app.modules.identity.domain.exceptions.auth import EmailAlreadyRegisteredException
from app.platform.config import settings


class InviteUserUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        invitation_repo: InvitationRepository,
        tenant_projection_repo: TenantProjectionRepository,
        event_bus: EventBus | None = None
    ):
        self.user_repo = user_repo
        self.invitation_repo = invitation_repo
        self.tenant_projection_repo = tenant_projection_repo
        self.event_bus = event_bus

    async def execute(
        self,
        tenant_id: uuid.UUID,
        email: str,
        role: str = "STAFF"
    ) -> Invitation:
        # 1. Validar que el correo no esté registrado como usuario activo
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise EmailAlreadyRegisteredException(
                f"El correo electrónico '{email}' ya se encuentra registrado con una cuenta activa en el sistema."
            )

        # 2. Generar token único (UUIDv4) y expiración de 48 horas (u otra según config)
        token = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(hours=settings.INVITATION_EXPIRE_HOURS)

        # 3. Crear y guardar la invitación
        invitation = Invitation(
            tenant_id=tenant_id,
            email=email,
            role=role,
            token=token,
            expires_at=expires_at
        )

        saved_invitation = await self.invitation_repo.save(invitation)

        # 4. Obtener el nombre del Tenant desde la proyección local (poblada por eventos)
        tenant_name = await self.tenant_projection_repo.get_name(tenant_id) or "JChat CRM Tenant"

        # Siempre imprimir en consola el token y URL de aceptación para desarrollo local
        invitation_url = f"http://localhost:5173/invite/{token}"
        print(f"\n[InviteUserUseCase] Invitación generada para {email} (Rol: {role})")
        print(f"-> Enlace de Aceptación: {invitation_url}\n")

        # 5. Publicar evento para enviar la invitación (ej. vía n8n/SMTP)
        if self.event_bus:
            payload = {
                "email": saved_invitation.email,
                "role": saved_invitation.role,
                "token": saved_invitation.token,
                "tenantId": str(saved_invitation.tenant_id),
                "tenantName": tenant_name,
                "expiresAt": saved_invitation.expires_at.isoformat()
            }
            await self.event_bus.publish("user.invitation_requested", payload)

        return saved_invitation
