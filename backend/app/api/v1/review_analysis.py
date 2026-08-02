from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.review_analysis.schemas import ReviewAnalysisRequest, ReviewAnalysisResponse
from app.modules.review_analysis.service import ReviewAnalysisService

router = APIRouter()


@router.get(
    "/listings/{listing_id}/review-analysis/latest",
    response_model=ReviewAnalysisResponse,
)
async def get_latest_listing_review_analysis(
    listing_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ReviewAnalysisResponse:
    result = await ReviewAnalysisService(session).get_latest(listing_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Review analysis not found")
    return result


@router.post(
    "/listings/{listing_id}/review-analysis",
    response_model=ReviewAnalysisResponse,
    status_code=201,
)
async def analyze_listing_reviews(
    listing_id: str,
    request: ReviewAnalysisRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ReviewAnalysisResponse:
    result = await ReviewAnalysisService(session).analyze(listing_id, request)
    if result is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return result
