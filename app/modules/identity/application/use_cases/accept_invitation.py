from app.modules.identity.domain.ports.invitation_repository import InvitationRepository
from app.modules.identity.application.use_cases.create_user import CreateUserUseCase
from app.modules.identity.domain.entities.user import User
from app.modules.identity.domain.exceptions.auth import InvitationNotFoundException, InvitationExpiredException


class AcceptInvitationUseCase:
    def __init__(
        self,
        invitation_repo: InvitationRepository,
        create_user_use_case: CreateUserUseCase
    ):
        self.invitation_repo = invitation_repo
        self.create_user_use_case = create_user_use_case

    async def execute(self, token: str, name: str, password: str) -> User:
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
                "Esta invitación ha expirado. Solicite una nueva invitación al administrador."
            )

        # 3. Crear el usuario definitivo en la base de datos
        created_user = await self.create_user_use_case.execute(
            tenant_id=invitation.tenant_id,
            email=invitation.email,
            password=password,
            name=name,
            role=invitation.role
        )

        # 4. Eliminar la invitación para evitar doble uso
        await self.invitation_repo.delete_by_token(token)

        return created_user
