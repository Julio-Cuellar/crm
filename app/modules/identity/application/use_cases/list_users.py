import uuid
from app.modules.identity.domain.entities.user import User
from app.modules.identity.domain.ports.user_repository import UserRepository


class ListUsersUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, tenant_id: uuid.UUID) -> list[User]:
        """Recupera la lista de todos los usuarios registrados bajo un tenant específico."""
        return await self.user_repository.get_by_tenant(tenant_id)
