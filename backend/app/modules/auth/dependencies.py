from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.models import AdminUser
from app.modules.auth.security import InvalidTokenError, decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


async def require_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdminUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Administrator authentication required")
    try:
        payload = decode_access_token(credentials.credentials)
    except InvalidTokenError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    user = await session.scalar(
        select(AdminUser).where(
            AdminUser.public_id == payload["sub"],
            AdminUser.status == "active",
        )
    )
    if user is None or user.role not in {"review_admin", "super_admin"}:
        raise HTTPException(status_code=403, detail="Administrator permission denied")
    return user
