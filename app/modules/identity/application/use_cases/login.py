from app.modules.identity.domain.ports.user_repository import UserRepository
from app.modules.identity.domain.exceptions.auth import InvalidCredentialsException
from app.platform.security import verify_password, create_access_token, create_refresh_token
from app.modules.identity.domain.entities.user import User


class LoginUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, email: str, password: str) -> tuple[User, str, str]:
        # 1. Buscar al usuario de manera global por email
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise InvalidCredentialsException()

        # 2. Validar que el usuario esté activo
        if not user.is_active:
            raise InvalidCredentialsException("La cuenta de usuario está desactivada.")

        # 3. Verificar contraseña
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsException()

        # 4. Generar tokens JWT
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "tenantId": str(user.tenant_id)
        }

        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return user, access_token, refresh_token
