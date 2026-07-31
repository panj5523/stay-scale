from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.ingestion.queries import IngestionQueryService
from app.modules.ingestion.schemas import (
    BatchListParams,
    IngestionBatchDetail,
    IngestionBatchListResponse,
)

router = APIRouter()


@router.get("/batches", response_model=IngestionBatchListResponse)
async def list_ingestion_batches(
    params: Annotated[BatchListParams, Query()],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IngestionBatchListResponse:
    return await IngestionQueryService(session).list_batches(params)


@router.get("/batches/{batch_id}", response_model=IngestionBatchDetail)
async def get_ingestion_batch(
    batch_id: int,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> IngestionBatchDetail:
    batch = await IngestionQueryService(session).get_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Ingestion batch not found")
    return batch
