import asyncio
import logging
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import settings
from app.db.session import engine
from app.infrastructure.redis import redis_client

logger = logging.getLogger(__name__)
router = APIRouter()


class ComponentCheck(BaseModel):
    status: Literal["up", "down"]
    message: str


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    service: str
    version: str
    checks: dict[str, ComponentCheck]
    timestamp: datetime


async def check_database(database_engine: AsyncEngine = engine) -> ComponentCheck:
    try:
        async with database_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return ComponentCheck(status="up", message="MySQL 连接正常")
    except Exception:
        logger.exception("MySQL readiness check failed")
        return ComponentCheck(status="down", message="MySQL 连接失败")


async def check_redis(client: Redis = redis_client) -> ComponentCheck:
    try:
        await client.ping()
        return ComponentCheck(status="up", message="Redis 连接正常")
    except Exception:
        logger.exception("Redis readiness check failed")
        return ComponentCheck(status="down", message="Redis 连接失败")


@router.get("/live")
async def liveness() -> dict[str, str]:
    return {
        "status": "alive",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/ready", response_model=ReadinessResponse)
async def readiness() -> ReadinessResponse | JSONResponse:
    database_check, redis_check = await asyncio.gather(
        check_database(),
        check_redis(),
    )
    is_ready = database_check.status == "up" and redis_check.status == "up"
    payload = ReadinessResponse(
        status="ready" if is_ready else "not_ready",
        service=settings.app_name,
        version=settings.app_version,
        checks={"database": database_check, "redis": redis_check},
        timestamp=datetime.now(UTC),
    )

    if not is_ready:
        return JSONResponse(status_code=503, content=payload.model_dump(mode="json"))
    return payload
