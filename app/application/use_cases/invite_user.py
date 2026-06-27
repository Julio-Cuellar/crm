import uuid
from datetime import datetime, timedelta
from app.domain.entities.invitation import Invitation
from app.domain.ports.invitation_repository import InvitationRepository
from app.domain.ports.user_repository import UserRepository
from app.domain.ports.tenant_repository import TenantRepository
from app.domain.ports.event_bus import EventBus
from app.domain.exceptions.auth import EmailAlreadyRegisteredException
from app.core.config import settings


class InviteUserUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        invitation_repo: InvitationRepository,
        tenant_repo: TenantRepository,
        event_bus: EventBus | None = None
    ):
        self.user_repo = user_repo
        self.invitation_repo = invitation_repo
        self.tenant_repo = tenant_repo
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

        # 4. Obtener el nombre del Tenant
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        tenant_name = tenant.name if tenant else "JChat CRM Tenant"

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
        else:
            print(f"[InviteUserUseCase] EventBus no disponible. Invitación creada para {email} con Token: {token}")

        return saved_invitation
