import uuid
from app.modules.identity.domain.entities.user import User
from app.modules.identity.domain.ports.user_repository import UserRepository
from app.modules.identity.domain.exceptions.user import UserNotFoundException


class GetUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: uuid.UUID) -> User:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"No se encontró el usuario solicitado.")
        return user
