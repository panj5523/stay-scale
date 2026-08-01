from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.travel_planning.schemas import TravelPlanResponse
from app.modules.travel_planning.service import TravelPlanRangeError, TravelPlanService

router = APIRouter()


@router.post("/recommendations/{session_id}/travel-plan", response_model=TravelPlanResponse)
async def create_travel_plan(
    session_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TravelPlanResponse:
    try:
        plan = await TravelPlanService(session).create(session_id)
    except TravelPlanRangeError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if plan is None:
        raise HTTPException(status_code=404, detail="Recommendation session not found")
    return plan
