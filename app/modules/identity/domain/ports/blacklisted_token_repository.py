import abc
from app.modules.identity.domain.entities.blacklisted_token import BlacklistedToken


class BlacklistedTokenRepository(abc.ABC):
    @abc.abstractmethod
    async def save(self, blacklisted_token: BlacklistedToken) -> BlacklistedToken:
        """Guarda un token en la lista negra."""
        pass

    @abc.abstractmethod
    async def is_blacklisted(self, token: str) -> bool:
        """Verifica si un token ya está registrado en la lista negra."""
        pass

    @abc.abstractmethod
    async def clean_expired(self) -> None:
        """Elimina todos los tokens expirados de la base de datos."""
        pass
