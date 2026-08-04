from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.dependencies import require_admin
from app.modules.platform_sync.schemas import SyncRunResponse, SyncSourceResponse, SyncSourceUpsert
from app.modules.platform_sync.service import PlatformSyncService

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/platform-sync/sources", response_model=list[SyncSourceResponse])
async def list_sync_sources(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[SyncSourceResponse]:
    return await PlatformSyncService(session).list_sources()


@router.put("/platform-sync/sources/{platform_code}", response_model=SyncSourceResponse)
async def configure_sync_source(
    platform_code: str,
    payload: SyncSourceUpsert,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SyncSourceResponse:
    try:
        return await PlatformSyncService(session).upsert(platform_code, payload)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/platform-sync/sources/{platform_code}/run", response_model=SyncRunResponse)
async def run_sync_source(
    platform_code: str, session: Annotated[AsyncSession, Depends(get_db_session)]
) -> SyncRunResponse:
    try:
        return await PlatformSyncService(session).run(platform_code)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
