import uuid
from app.domain.entities.user import User
from app.domain.ports.user_repository import UserRepository
from app.domain.exceptions.user import UserAlreadyExistsException
from app.core.security import get_password_hash


class CreateUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(
        self,
        tenant_id: uuid.UUID,
        email: str,
        password: str,
        name: str,
        role: str = "STAFF",
        is_hashed: bool = False
    ) -> User:
        # Validar si el email ya existe bajo el mismo tenant
        existing = await self.user_repository.get_by_email_and_tenant(email, tenant_id)
        if existing:
            raise UserAlreadyExistsException(f"El correo '{email}' ya se encuentra registrado en este negocio.")

        # Obtener el hash de la contraseña si no viene previamente hasheada
        if is_hashed:
            password_hash = password
        else:
            password_hash = get_password_hash(password)

        user = User(
            tenant_id=tenant_id,
            email=email,
            password_hash=password_hash,
            name=name,
            role=role
        )

        return await self.user_repository.save(user)
