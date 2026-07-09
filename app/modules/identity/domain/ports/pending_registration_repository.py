import abc
from app.modules.identity.domain.entities.pending_registration import PendingRegistration


class PendingRegistrationRepository(abc.ABC):
    @abc.abstractmethod
    async def save(self, pending: PendingRegistration) -> PendingRegistration:
        """Guarda o actualiza un registro de pre-registro."""
        pass

    @abc.abstractmethod
    async def get_by_email(self, email: str) -> PendingRegistration | None:
        """Busca un registro de pre-registro por correo electrónico."""
        pass

    @abc.abstractmethod
    async def delete(self, email: str) -> None:
        """Elimina un pre-registro una vez completado o expirado."""
        pass
