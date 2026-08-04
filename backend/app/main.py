import logging
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import engine
from app.infrastructure.redis import redis_client
from app.modules.platform_sync.scheduler import platform_sync_scheduler

request_logger = logging.getLogger("app.http")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def request_id_from_header(value: str | None) -> str:
    return value if value and REQUEST_ID_PATTERN.fullmatch(value) else uuid4().hex


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    await platform_sync_scheduler.start()
    yield
    await platform_sync_scheduler.stop()
    await redis_client.aclose()
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.app_debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request_id_from_header(request.headers.get("X-Request-ID"))
        started_at = perf_counter()
        common_fields = {
            "event": "http.request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
        }
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((perf_counter() - started_at) * 1000, 2)
            request_logger.exception(
                "request failed",
                extra={**common_fields, "status_code": 500, "duration_ms": duration_ms},
            )
            raise
        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        log_level = logging.INFO
        if response.status_code >= 500:
            log_level = logging.ERROR
        elif response.status_code >= 400 or duration_ms >= settings.slow_request_threshold_ms:
            log_level = logging.WARNING
        request_logger.log(
            log_level,
            "request completed",
            extra={
                **common_fields,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)

app.include_router(api_router, prefix=settings.api_v1_prefix)
