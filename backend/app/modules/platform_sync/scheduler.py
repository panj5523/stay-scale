import asyncio
import logging
from contextlib import suppress
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from app.core.config import settings
from app.db.session import async_session_factory
from app.modules.platform_sync.models import PlatformSyncSource
from app.modules.platform_sync.service import PlatformSyncService
from app.modules.platforms.models import Platform

logger = logging.getLogger(__name__)


class PlatformSyncScheduler:
    def __init__(self) -> None:
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        if not settings.platform_sync_scheduler_enabled or self._task is not None:
            return
        await self._recover_interrupted_runs()
        self._stop_event.clear()
        self._task = asyncio.create_task(self._loop(), name="platform-sync-scheduler")
        logger.info("Platform sync scheduler started")

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop_event.set()
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None
        logger.info("Platform sync scheduler stopped")

    async def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self.run_due_sources()
            except Exception:
                logger.exception("Platform sync scheduling cycle failed")
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=max(settings.platform_sync_poll_seconds, 5)
                )
            except TimeoutError:
                pass

    async def run_due_sources(self) -> None:
        now = datetime.now(UTC).replace(tzinfo=None)
        async with async_session_factory() as session:
            rows = (
                await session.execute(
                    select(PlatformSyncSource, Platform.code)
                    .join(Platform, Platform.id == PlatformSyncSource.platform_id)
                    .where(PlatformSyncSource.is_enabled.is_(True))
                )
            ).all()
        due_codes = [
            platform_code
            for source, platform_code in rows
            if self.is_due(source.last_run_at, source.interval_minutes, source.status, now)
        ]
        for platform_code in due_codes:
            await self._run_with_retry(platform_code)

    async def _run_with_retry(self, platform_code: str) -> None:
        attempts = max(settings.platform_sync_retry_attempts, 1)
        for attempt in range(1, attempts + 1):
            try:
                async with async_session_factory() as session:
                    await PlatformSyncService(session).run(platform_code)
                logger.info("Scheduled platform sync completed: %s", platform_code)
                return
            except ValueError as error:
                if "already running" in str(error):
                    logger.info(
                        "Scheduled platform sync skipped because it is running: %s",
                        platform_code,
                    )
                    return
                logger.warning(
                    "Scheduled platform sync attempt %s/%s failed for %s: %s",
                    attempt,
                    attempts,
                    platform_code,
                    error,
                )
            except Exception as error:
                logger.warning(
                    "Scheduled platform sync attempt %s/%s failed for %s: %s",
                    attempt,
                    attempts,
                    platform_code,
                    error,
                )
            if attempt < attempts:
                await asyncio.sleep(settings.platform_sync_retry_delay_seconds * attempt)

    async def _recover_interrupted_runs(self) -> None:
        async with async_session_factory() as session:
            await session.execute(
                update(PlatformSyncSource)
                .where(PlatformSyncSource.status == "running")
                .values(status="failed", last_error="Sync interrupted by application restart")
            )
            await session.commit()

    @staticmethod
    def is_due(
        last_run_at: datetime | None, interval_minutes: int, status: str, now: datetime
    ) -> bool:
        if status == "running":
            return False
        return last_run_at is None or last_run_at + timedelta(minutes=interval_minutes) <= now


platform_sync_scheduler = PlatformSyncScheduler()
