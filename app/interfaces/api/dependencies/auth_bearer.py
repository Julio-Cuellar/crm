import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from app.infrastructure.db.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.infrastructure.db.repositories.sqlalchemy_blacklisted_token_repository import SQLAlchemyBlacklistedTokenRepository
from app.interfaces.api.dependencies.users import get_user_repository
from app.interfaces.api.dependencies.blacklisted_tokens import get_blacklisted_token_repository
from app.core.security import decode_token
from app.domain.entities.user import User

# Instancia del esquema HTTP Bearer
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repository),
    blacklist_repo: SQLAlchemyBlacklistedTokenRepository = Depends(get_blacklisted_token_repository)
) -> User:
    """
    Dependencia para obtener y validar el usuario actualmente autenticado mediante JWT.
    Valida también que el token no haya sido revocado en la lista negra (por cierre de sesión).
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token de acceso o ha expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 1. Verificar si el token está registrado en la lista negra (Logout)
    if await blacklist_repo.is_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión cerrada. El token de acceso ha sido invalidado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = decode_token(token)
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        # Validar que sea un token de acceso y contenga el sub
        if token_type != "access" or not user_id_str:
            raise credentials_exception
            
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    # Buscar usuario y validar estado
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta de este usuario está desactivada."
        )
        
    return user
