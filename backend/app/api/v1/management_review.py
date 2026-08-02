from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.dependencies import require_admin
from app.modules.management_review.schemas import (
    ReviewDecisionRequest,
    ReviewDecisionResponse,
    ReviewQueueParams,
    ReviewQueueResponse,
)
from app.modules.management_review.service import (
    ManagementReviewService,
    ReviewConflictError,
    ReviewTargetNotFoundError,
)

router = APIRouter()


@router.get(
    "/reviews",
    response_model=ReviewQueueResponse,
    dependencies=[Depends(require_admin)],
)
async def list_review_tasks(
    params: Annotated[ReviewQueueParams, Query()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ReviewQueueResponse:
    return await ManagementReviewService(session).list_tasks(params)


@router.post(
    "/reviews/{record_id}/decision",
    response_model=ReviewDecisionResponse,
    dependencies=[Depends(require_admin)],
)
async def decide_review_task(
    record_id: int,
    request: ReviewDecisionRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ReviewDecisionResponse:
    try:
        result = await ManagementReviewService(session).decide(record_id, request)
    except ReviewConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ReviewTargetNotFoundError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    if result is None:
        raise HTTPException(status_code=404, detail="Review task not found")
    return result
