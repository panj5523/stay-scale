from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import rate_limit
from app.db.session import get_db_session
from app.modules.travel_planning.schemas import TravelPlanResponse
from app.modules.travel_planning.service import TravelPlanService
from app.modules.users.dependencies import require_user
from app.modules.users.models import UserAccount
from app.modules.users.schemas import (
    FavoriteResponse,
    UserLoginRequest,
    UserLoginResponse,
    UserRegisterRequest,
    UserResponse,
)
from app.modules.users.service import UserService

router = APIRouter()


@router.post(
    "/auth/register",
    response_model=UserLoginResponse,
    status_code=201,
    dependencies=[Depends(rate_limit("user-register", 5))],
)
async def register_user(
    payload: UserRegisterRequest, session: Annotated[AsyncSession, Depends(get_db_session)]
) -> UserLoginResponse:
    try:
        return await UserService(session).register(
            payload.email, payload.password, payload.display_name
        )
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post(
    "/auth/login",
    response_model=UserLoginResponse,
    dependencies=[Depends(rate_limit("user-login", 10))],
)
async def login_user(
    payload: UserLoginRequest, session: Annotated[AsyncSession, Depends(get_db_session)]
) -> UserLoginResponse:
    result = await UserService(session).login(payload.email, payload.password)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid user credentials")
    return result


@router.get("/me", response_model=UserResponse)
async def get_user_profile(user: Annotated[UserAccount, Depends(require_user)]) -> UserResponse:
    return UserService.response(user)


@router.get("/me/favorites", response_model=list[FavoriteResponse])
async def list_user_favorites(
    user: Annotated[UserAccount, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[FavoriteResponse]:
    return await UserService(session).list_favorites(user)


@router.put("/me/favorites/{listing_public_id}", response_model=FavoriteResponse)
async def add_user_favorite(
    listing_public_id: str,
    user: Annotated[UserAccount, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> FavoriteResponse:
    try:
        return await UserService(session).add_favorite(user, listing_public_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.delete("/me/favorites/{listing_public_id}", status_code=204)
async def remove_user_favorite(
    listing_public_id: str,
    user: Annotated[UserAccount, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    await UserService(session).remove_favorite(user, listing_public_id)
    return Response(status_code=204)


@router.get("/me/travel-plans", response_model=list[TravelPlanResponse])
async def list_user_travel_plans(
    user: Annotated[UserAccount, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[TravelPlanResponse]:
    return await TravelPlanService(session).history(user.id)
