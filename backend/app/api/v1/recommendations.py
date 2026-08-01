from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.recommendations.schemas import RecommendationRequest, RecommendationResponse
from app.modules.recommendations.service import RecommendationService

router = APIRouter()


@router.post("", response_model=RecommendationResponse, status_code=201)
async def create_recommendation(
    request: RecommendationRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RecommendationResponse:
    return await RecommendationService(session).recommend(request)


@router.get("/{session_id}", response_model=RecommendationResponse)
async def get_recommendation(
    session_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RecommendationResponse:
    recommendation = await RecommendationService(session).get(session_id)
    if recommendation is None:
        raise HTTPException(status_code=404, detail="Recommendation session not found")
    return recommendation
