from datetime import datetime, timedelta, timezone
import base64
import hashlib
from typing import Any

import jwt
from cryptography.fernet import Fernet
from pwdlib import PasswordHash

from .config import get_settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_access_token(subject: str, email: str, name: str) -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    payload = {"sub": subject, "email": email, "name": name, "exp": expires}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def _fernet() -> Fernet:
    settings = get_settings()
    raw = settings.token_encryption_key.strip()
    if raw:
        key = raw.encode()
    else:
        digest = hashlib.sha256(settings.jwt_secret.encode()).digest()
        key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def seal_secret(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def unseal_secret(value: str) -> str:
    return _fernet().decrypt(value.encode()).decode()
