from app.modules.identity.domain.entities.invitation import Invitation
from app.modules.identity.domain.ports.invitation_repository import InvitationRepository
from app.modules.identity.infrastructure.db.repositories.tenant_projection_repository import (
    TenantProjectionRepository,
)
from app.modules.identity.domain.exceptions.auth import InvitationNotFoundException, InvitationExpiredException


class GetInvitationByTokenUseCase:
    def __init__(
        self,
        invitation_repo: InvitationRepository,
        tenant_projection_repo: TenantProjectionRepository
    ):
        self.invitation_repo = invitation_repo
        self.tenant_projection_repo = tenant_projection_repo

    async def execute(self, token: str) -> tuple[Invitation, str]:
        # 1. Buscar la invitación por token
        invitation = await self.invitation_repo.get_by_token(token)
        if not invitation:
            raise InvitationNotFoundException(
                "La invitación solicitada no existe o ya fue utilizada."
            )

        # 2. Validar expiración
        if invitation.is_expired():
            await self.invitation_repo.delete_by_token(token)
            raise InvitationExpiredException(
                "Esta invitación ha expirado. Por favor, solicita una nueva al administrador."
            )

        # 3. Obtener el nombre del Tenant desde la proyección local (poblada por eventos)
        tenant_name = await self.tenant_projection_repo.get_name(invitation.tenant_id) or "JChat CRM Tenant"

        return invitation, tenant_name
