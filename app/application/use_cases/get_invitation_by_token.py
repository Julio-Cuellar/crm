from app.domain.entities.invitation import Invitation
from app.domain.ports.invitation_repository import InvitationRepository
from app.domain.ports.tenant_repository import TenantRepository
from app.domain.exceptions.auth import InvitationNotFoundException, InvitationExpiredException


class GetInvitationByTokenUseCase:
    def __init__(
        self,
        invitation_repo: InvitationRepository,
        tenant_repo: TenantRepository
    ):
        self.invitation_repo = invitation_repo
        self.tenant_repo = tenant_repo

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

        # 3. Obtener el nombre del Tenant
        tenant = await self.tenant_repo.get_by_id(invitation.tenant_id)
        tenant_name = tenant.name if tenant else "JChat CRM Tenant"

        return invitation, tenant_name
