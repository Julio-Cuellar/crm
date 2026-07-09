import abc
from app.modules.identity.domain.entities.invitation import Invitation


class InvitationRepository(abc.ABC):
    @abc.abstractmethod
    async def save(self, invitation: Invitation) -> Invitation:
        """Guarda o actualiza una invitación."""
        pass

    @abc.abstractmethod
    async def get_by_token(self, token: str) -> Invitation | None:
        """Busca una invitación por su token único."""
        pass

    @abc.abstractmethod
    async def delete_by_token(self, token: str) -> None:
        """Elimina una invitación por su token."""
        pass
