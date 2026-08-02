from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.dependencies import require_admin
from app.modules.auth.models import AdminUser
from app.modules.auth.schemas import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminUserResponse,
)
from app.modules.auth.service import AdminAuthService

router = APIRouter()


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    request: AdminLoginRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdminLoginResponse:
    result = await AdminAuthService(session).login(request.username, request.password)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid administrator credentials")
    return result


@router.get("/me", response_model=AdminUserResponse)
async def get_current_admin(
    user: Annotated[AdminUser, Depends(require_admin)],
) -> AdminUserResponse:
    return AdminAuthService._response(user)
