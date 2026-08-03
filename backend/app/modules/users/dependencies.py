from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.security import InvalidTokenError, decode_user_access_token

from .models import UserAccount

user_bearer_scheme = HTTPBearer(auto_error=False)


async def optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(user_bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserAccount | None:
    if credentials is None:
        return None
    try:
        payload = decode_user_access_token(credentials.credentials)
    except InvalidTokenError:
        return None
    return await session.scalar(
        select(UserAccount).where(
            UserAccount.public_id == payload["sub"], UserAccount.status == "active"
        )
    )


async def require_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(user_bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserAccount:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="User authentication required")
    try:
        payload = decode_user_access_token(credentials.credentials)
    except InvalidTokenError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    user = await session.scalar(
        select(UserAccount).where(
            UserAccount.public_id == payload["sub"], UserAccount.status == "active"
        )
    )
    if user is None:
        raise HTTPException(status_code=401, detail="User account is unavailable")
    return user
