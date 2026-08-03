from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.dependencies import require_admin
from app.modules.auth.models import AdminUser
from app.modules.data_retention.archive import DataArchiveService
from app.modules.data_retention.schemas import (
    ArchiveFileInfo,
    ArchiveListResponse,
    ArchiveRequest,
    ArchiveResponse,
    DataRetentionReport,
    RestoreExecuteRequest,
    RestoreExecuteResponse,
    RestoreExecutionReadiness,
    RestorePlanResponse,
    RestorePreviewResponse,
    RestoreRequestCreate,
    RestoreRequestDecision,
    RestoreRequestResponse,
)
from app.modules.data_retention.service import DataRetentionService

router = APIRouter()


@router.get(
    "/data-retention/report",
    response_model=DataRetentionReport,
    dependencies=[Depends(require_admin)],
)
async def get_data_retention_report(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> DataRetentionReport:
    return await DataRetentionService(session).get_report()


@router.post(
    "/data-retention/archive", response_model=ArchiveResponse, dependencies=[Depends(require_admin)]
)
async def create_data_retention_archive(
    payload: ArchiveRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ArchiveResponse:
    try:
        return await DataArchiveService(session).create(confirmed=payload.confirm)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get(
    "/data-retention/archives",
    response_model=ArchiveListResponse,
    dependencies=[Depends(require_admin)],
)
async def list_data_retention_archives(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ArchiveListResponse:
    return await DataArchiveService(session).list_archives()


@router.post(
    "/data-retention/archives/{archive_id}/verify",
    response_model=ArchiveFileInfo,
    dependencies=[Depends(require_admin)],
)
async def verify_data_retention_archive(
    archive_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ArchiveFileInfo:
    try:
        return await DataArchiveService(session).verify(archive_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get(
    "/data-retention/archives/{archive_id}/download",
    response_class=FileResponse,
    dependencies=[Depends(require_admin)],
)
async def download_data_retention_archive(
    archive_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> FileResponse:
    try:
        path = DataArchiveService(session).resolve_path(archive_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return FileResponse(path, filename=path.name, media_type="application/zip")


@router.get(
    "/data-retention/archives/{archive_id}/restore-preview",
    response_model=RestorePreviewResponse,
    dependencies=[Depends(require_admin)],
)
async def preview_data_retention_restore(
    archive_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RestorePreviewResponse:
    try:
        return await DataArchiveService(session).restore_preview(archive_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get(
    "/data-retention/archives/{archive_id}/restore-plan",
    response_model=RestorePlanResponse,
    dependencies=[Depends(require_admin)],
)
async def plan_data_retention_restore(
    archive_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RestorePlanResponse:
    try:
        return await DataArchiveService(session).restore_plan(archive_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post(
    "/data-retention/restore-requests",
    response_model=RestoreRequestResponse,
    dependencies=[Depends(require_admin)],
)
async def create_restore_request(
    payload: RestoreRequestCreate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
) -> RestoreRequestResponse:
    try:
        request = await DataArchiveService(session).request_restore(payload.archive_id, admin.id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return RestoreRequestResponse.model_validate(request, from_attributes=True)


@router.get(
    "/data-retention/restore-requests",
    response_model=list[RestoreRequestResponse],
    dependencies=[Depends(require_admin)],
)
async def list_restore_requests(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[RestoreRequestResponse]:
    requests = await DataArchiveService(session).list_restore_requests()
    return [RestoreRequestResponse.model_validate(item, from_attributes=True) for item in requests]


@router.patch(
    "/data-retention/restore-requests/{public_id}",
    response_model=RestoreRequestResponse,
)
async def decide_restore_request(
    public_id: str,
    payload: RestoreRequestDecision,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
) -> RestoreRequestResponse:
    if admin.role != "super_admin":
        raise HTTPException(
            status_code=403, detail="Only super administrators can decide restore requests"
        )
    try:
        request = await DataArchiveService(session).decide_restore_request(
            public_id, admin.id, payload.action, payload.reason
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return RestoreRequestResponse.model_validate(request, from_attributes=True)


@router.get(
    "/data-retention/restore-requests/{public_id}/execution-readiness",
    response_model=RestoreExecutionReadiness,
)
async def get_restore_execution_readiness(
    public_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
) -> RestoreExecutionReadiness:
    if admin.role != "super_admin":
        raise HTTPException(
            status_code=403, detail="Only super administrators can check execution readiness"
        )
    try:
        return await DataArchiveService(session).execution_readiness(public_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post(
    "/data-retention/restore-requests/{public_id}/execute",
    response_model=RestoreExecuteResponse,
)
async def execute_restore_request(
    public_id: str,
    payload: RestoreExecuteRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    admin: Annotated[AdminUser, Depends(require_admin)],
) -> RestoreExecuteResponse:
    if admin.role != "super_admin":
        raise HTTPException(
            status_code=403, detail="Only super administrators can execute restores"
        )
    try:
        return await DataArchiveService(session).execute_restore(
            public_id, payload.confirmation, admin.id
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Restore transaction rolled back because database constraints failed",
        ) from error
