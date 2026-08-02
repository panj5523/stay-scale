from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.modules.auth.dependencies import require_admin
from app.modules.operations.schemas import OperationsDashboardResponse
from app.modules.operations.service import OperationsDashboardService

router = APIRouter()


@router.get(
    "/dashboard",
    response_model=OperationsDashboardResponse,
    dependencies=[Depends(require_admin)],
)
async def get_operations_dashboard(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OperationsDashboardResponse:
    return await OperationsDashboardService(session).get()
