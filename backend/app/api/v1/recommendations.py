from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.recommendations.schemas import (
    RecommendationAdjustmentRequest,
    RecommendationAdjustmentResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from app.modules.recommendations.service import RecommendationService
from app.modules.users.dependencies import optional_user, require_user
from app.modules.users.models import UserAccount

router = APIRouter()


@router.post("", response_model=RecommendationResponse, status_code=201)
async def create_recommendation(
    request: RecommendationRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user: Annotated[UserAccount | None, Depends(optional_user)],
) -> RecommendationResponse:
    service = RecommendationService(session)
    if user is None:
        return await service.recommend(request)
    return await service.recommend(request, user.id)


@router.get("/history", response_model=list[RecommendationResponse])
async def get_recommendation_history(
    user: Annotated[UserAccount, Depends(require_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[RecommendationResponse]:
    return await RecommendationService(session).history(user.id)


@router.get("/{session_id}", response_model=RecommendationResponse)
async def get_recommendation(
    session_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RecommendationResponse:
    recommendation = await RecommendationService(session).get(session_id)
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommendation session not found")
    return recommendation


@router.post("/{session_id}/explanations", response_model=RecommendationResponse)
async def explain_recommendation(
    session_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RecommendationResponse:
    recommendation = await RecommendationService(session).explain(session_id)
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommendation session not found")
    return recommendation


@router.post(
    "/{session_id}/adjust",
    response_model=RecommendationAdjustmentResponse,
)
async def adjust_recommendation(
    session_id: str,
    request: RecommendationAdjustmentRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RecommendationAdjustmentResponse:
    adjustment = await RecommendationService(session).adjust(session_id, request)
    if adjustment is None:
        raise HTTPException(status_code=404, detail="Recommendation session not found")
    return adjustment
