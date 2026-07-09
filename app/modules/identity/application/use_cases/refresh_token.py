import uuid
from app.modules.identity.domain.ports.user_repository import UserRepository
from app.modules.identity.domain.exceptions.auth import InvalidCredentialsException
from app.platform.security import decode_token, create_access_token, create_refresh_token
from jose import JWTError


class RefreshTokenUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def execute(self, refresh_token: str) -> tuple[str, str]:
        credentials_exception = InvalidCredentialsException("Token de refresco inválido o expirado.")
        
        try:
            payload = decode_token(refresh_token)
            user_id_str: str = payload.get("sub")
            token_type: str = payload.get("type")
            
            if token_type != "refresh" or not user_id_str:
                raise credentials_exception
                
            user_id = uuid.UUID(user_id_str)
        except (JWTError, ValueError):
            raise credentials_exception

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise credentials_exception

        # Generar nuevos tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "tenantId": str(user.tenant_id)
        }

        new_access_token = create_access_token(data=token_data)
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return new_access_token, new_refresh_token
