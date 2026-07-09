from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import bcrypt
from app.platform.config import settings

ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña en texto plano coincide con el hash almacenado."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Genera el hash bcrypt de una contraseña."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Crea un Access Token JWT firmado."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Crea un Refresh Token JWT firmado."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decodifica y valida un token JWT. Lanza JWTError si el token es inválido o expiró."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])


import base64
import hashlib
from cryptography.fernet import Fernet

def _get_fernet_key() -> bytes:
    # Generar un hash SHA-256 de la clave secreta y codificar en base64
    key_hash = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key_hash)

def encrypt_value(plain_text: str) -> str:
    """Cifra un texto plano utilizando AES-128/256 (Fernet) de forma reversible."""
    if not plain_text:
        return ""
    key = _get_fernet_key()
    f = Fernet(key)
    return f.encrypt(plain_text.encode("utf-8")).decode("utf-8")

def decrypt_value(encrypted_text: str) -> str:
    """Descifra un texto cifrado utilizando AES-128/256 (Fernet)."""
    if not encrypted_text:
        return ""
    key = _get_fernet_key()
    f = Fernet(key)
    return f.decrypt(encrypted_text.encode("utf-8")).decode("utf-8")
