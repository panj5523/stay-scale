from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ingestion.adapters import FixturePlatformAdapter
from app.modules.ingestion.service import IngestionService
from app.modules.platforms.models import Platform

from .models import PlatformSyncSource
from .schemas import SyncRunResponse, SyncSourceResponse, SyncSourceUpsert


class PlatformSyncService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_sources(self) -> list[SyncSourceResponse]:
        rows = (
            await self.session.execute(
                select(PlatformSyncSource, Platform)
                .join(Platform, Platform.id == PlatformSyncSource.platform_id)
                .order_by(Platform.code)
            )
        ).all()
        return [self._response(source, platform) for source, platform in rows]

    async def upsert(self, platform_code: str, payload: SyncSourceUpsert) -> SyncSourceResponse:
        platform = await self.session.scalar(
            select(Platform).where(Platform.code == platform_code, Platform.is_active.is_(True))
        )
        if platform is None:
            raise FileNotFoundError("Active platform not found")
        source = await self.session.scalar(
            select(PlatformSyncSource).where(PlatformSyncSource.platform_id == platform.id)
        )
        if source is None:
            source = PlatformSyncSource(
                public_id=str(uuid4()),
                platform_id=platform.id,
                connector_type=payload.connector_type,
                source_config={},
                interval_minutes=payload.interval_minutes,
            )
            self.session.add(source)
        source.connector_type = payload.connector_type
        source.source_config = {"source_label": payload.source_label}
        source.interval_minutes = payload.interval_minutes
        source.is_enabled = payload.is_enabled
        await self.session.commit()
        await self.session.refresh(source)
        return self._response(source, platform)

    async def run(self, platform_code: str) -> SyncRunResponse:
        row = (
            await self.session.execute(
                select(PlatformSyncSource, Platform)
                .join(Platform, Platform.id == PlatformSyncSource.platform_id)
                .where(Platform.code == platform_code)
            )
        ).first()
        if row is None:
            raise FileNotFoundError("Sync source not configured")
        source, platform = row
        if source.connector_type != "fixture":
            raise ValueError("Authorized API credentials and adapter are not configured yet")
        fixture = self._fixture_path(str(source.source_config.get("source_label", "")))
        started_at = datetime.now(UTC).replace(tzinfo=None)
        claimed = await self.session.execute(
            update(PlatformSyncSource)
            .where(PlatformSyncSource.id == source.id, PlatformSyncSource.status != "running")
            .values(status="running", last_run_at=started_at, last_error=None)
        )
        if claimed.rowcount != 1:
            await self.session.rollback()
            raise ValueError("Sync source is already running")
        await self.session.commit()
        source.status = "running"
        source.last_run_at = started_at
        source.last_error = None
        try:
            summary = await IngestionService(self.session).import_from(
                FixturePlatformAdapter(platform.code, fixture)
            )
        except Exception as error:
            source.status = "failed"
            source.last_error = str(error)[:500]
            await self.session.commit()
            raise
        source.status = "idle"
        source.last_success_at = datetime.now(UTC).replace(tzinfo=None)
        await self.session.commit()
        return SyncRunResponse(
            platform_code=platform.code,
            batch_id=summary.batch_id,
            status=summary.status,
            received_count=summary.received_count,
            imported_count=summary.imported_count,
            failed_count=summary.failed_count,
        )

    @staticmethod
    def _fixture_path(source_label: str) -> Path:
        fixture_root = (Path(__file__).parents[3] / "fixtures" / "ingestion").resolve()
        candidate = (fixture_root / source_label).resolve()
        if (
            candidate.parent != fixture_root
            or candidate.suffix.lower() != ".json"
            or not candidate.is_file()
        ):
            raise FileNotFoundError("Fixture source is not an allowed ingestion JSON file")
        return candidate

    @staticmethod
    def _response(source: PlatformSyncSource, platform: Platform) -> SyncSourceResponse:
        next_run = (
            source.last_run_at + timedelta(minutes=source.interval_minutes)
            if source.is_enabled and source.last_run_at
            else None
        )
        return SyncSourceResponse(
            public_id=source.public_id,
            platform_code=platform.code,
            platform_name=platform.name,
            connector_type=source.connector_type,
            source_label=str(source.source_config.get("source_label", "")),
            interval_minutes=source.interval_minutes,
            status=source.status,
            is_enabled=source.is_enabled,
            last_run_at=source.last_run_at,
            last_success_at=source.last_success_at,
            last_error=source.last_error,
            next_run_at=next_run,
        )
