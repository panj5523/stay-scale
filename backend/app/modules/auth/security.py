from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()
ALGORITHM = "HS256"


class InvalidTokenError(ValueError):
    pass


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    return password_hash.verify(password, encoded)


def create_access_token(*, subject: str, role: str) -> tuple[str, int]:
    expires_in = settings.auth_token_expire_minutes * 60
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "role": role,
        "type": "admin_access",
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    return jwt.encode(payload, settings.auth_secret_key, algorithm=ALGORITHM), expires_in


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.auth_secret_key, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Invalid or expired access token") from exc
    if payload.get("type") != "admin_access" or not payload.get("sub"):
        raise InvalidTokenError("Invalid access token type")
    return payload
