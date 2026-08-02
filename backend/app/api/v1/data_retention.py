from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.dependencies import require_admin
from app.modules.data_retention.schemas import DataRetentionReport
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
