from datetime import datetime, timezone
from jose import JWTError
from app.core.security import decode_token
from app.domain.entities.blacklisted_token import BlacklistedToken
from app.domain.ports.blacklisted_token_repository import BlacklistedTokenRepository
from app.domain.exceptions.auth import InvalidCredentialsException


class LogoutUseCase:
    def __init__(self, blacklist_repo: BlacklistedTokenRepository):
        self.blacklist_repo = blacklist_repo

    async def execute(self, token: str) -> None:
        try:
            # 1. Decodificar el token para validar firma y obtener expiración (exp)
            payload = decode_token(token)
            exp: int = payload.get("exp")
            
            if not exp:
                raise InvalidCredentialsException("El token no posee fecha de expiración.")

            # Convertir timestamp exp (segundos) a datetime timezone-aware (UTC)
            expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)

            # 2. Crear y persistir el token en la lista negra
            blacklisted = BlacklistedToken(
                token=token,
                expires_at=expires_at
            )
            
            await self.blacklist_repo.save(blacklisted)
            
        except JWTError:
            # Si el token es inválido o ya expiró, no es necesario hacer nada ya que no podrá volver a usarse
            pass
