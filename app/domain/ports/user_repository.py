import uuid
from abc import ABC, abstractmethod
from app.domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> User:
        """Guarda o actualiza un usuario en el medio de almacenamiento."""
        pass

    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Busca un usuario por su identificador único (UUID)."""
        pass

    @abstractmethod
    async def get_by_email_and_tenant(self, email: str, tenant_id: uuid.UUID) -> User | None:
        """Busca un usuario por su correo electrónico dentro de un tenant específico."""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        """Busca un usuario de manera global por su correo electrónico (búsqueda entre tenants)."""
        pass

    @abstractmethod
    async def get_by_tenant(self, tenant_id: uuid.UUID) -> list[User]:
        """Obtiene la lista de todos los usuarios registrados bajo un tenant específico."""
        pass
