import asyncio
import hashlib
import json
import uuid
import zipfile
from datetime import UTC, datetime
from datetime import date as date_type
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect

from app.core.config import settings
from app.modules.ingestion.models import IngestionBatch, IngestionRecord
from app.modules.preference_parsing.models import PreferenceParseSession
from app.modules.recommendations.models import RecommendationAdjustment, RecommendationSession
from app.modules.review_analysis.models import ListingReview, ReviewAnalysisSnapshot
from app.modules.travel_planning.models import TravelPlanDraft

from .models import ArchiveRestoreRequest
from .schemas import (
    ArchiveFileInfo,
    ArchiveListResponse,
    ArchiveResponse,
    RestoreExecuteResponse,
    RestoreExecutionReadiness,
    RestorePlanResponse,
    RestorePreviewResponse,
    RestoreTablePlan,
)


class DataArchiveService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, *, confirmed: bool) -> ArchiveResponse:
        if not confirmed:
            raise ValueError("Archive requires explicit confirmation")
        models = (
            RecommendationSession,
            RecommendationAdjustment,
            ListingReview,
            ReviewAnalysisSnapshot,
            PreferenceParseSession,
            TravelPlanDraft,
            IngestionBatch,
            IngestionRecord,
        )
        archive_id = str(uuid.uuid4())
        generated_at = datetime.now(UTC).replace(tzinfo=None)
        output_dir = Path(settings.archive_output_dir)
        await asyncio.to_thread(output_dir.mkdir, parents=True, exist_ok=True)
        path = output_dir / f"stay-scale-{archive_id}.zip"
        counts: dict[str, int] = {}
        manifest: dict[str, Any] = {
            "archive_id": archive_id,
            "generated_at": generated_at.isoformat(),
            "deletion_performed": False,
            "truncated_tables": [],
        }
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for model in models:
                rows = (
                    (
                        await self.session.execute(
                            select(model).limit(settings.archive_max_records_per_table)
                        )
                    )
                    .scalars()
                    .all()
                )
                records = [
                    {
                        column.key: _json_value(getattr(row, column.key))
                        for column in inspect(model).mapper.column_attrs
                    }
                    for row in rows
                ]
                table = model.__tablename__
                counts[table] = len(records)
                if len(records) == settings.archive_max_records_per_table:
                    manifest["truncated_tables"].append(table)
                bundle.writestr(
                    f"data/{table}.jsonl",
                    "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records),
                )
            manifest["counts"] = counts
            bundle.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        digest = hashlib.sha256(await asyncio.to_thread(path.read_bytes)).hexdigest()
        return ArchiveResponse(
            archive_id=archive_id,
            file_name=path.name,
            file_path=str(path),
            sha256=digest,
            counts=counts,
            generated_at=generated_at,
            deletion_performed=False,
            warnings=["归档包已生成，热表数据未删除。"],
        )

    async def list_archives(self) -> ArchiveListResponse:
        output_dir = Path(settings.archive_output_dir)
        if not await asyncio.to_thread(output_dir.exists):
            return ArchiveListResponse(archives=[], total=0)
        paths = await asyncio.to_thread(lambda: list(output_dir.glob("stay-scale-*.zip")))
        archives = []
        for path in paths:
            stat = await asyncio.to_thread(path.stat)
            archives.append(
                ArchiveFileInfo(
                    archive_id=path.stem.removeprefix("stay-scale-"),
                    file_name=path.name,
                    size_bytes=stat.st_size,
                    created_at=datetime.fromtimestamp(stat.st_mtime, UTC).replace(tzinfo=None),
                )
            )
        archives.sort(key=lambda item: item.created_at, reverse=True)
        return ArchiveListResponse(archives=archives, total=len(archives))

    async def verify(self, archive_id: str) -> ArchiveFileInfo:
        path = self.resolve_path(archive_id)
        stat = await asyncio.to_thread(path.stat)
        digest = hashlib.sha256(await asyncio.to_thread(path.read_bytes)).hexdigest()
        integrity_status = (
            "valid" if await asyncio.to_thread(self._zip_is_valid, path) else "invalid"
        )
        return ArchiveFileInfo(
            archive_id=archive_id,
            file_name=path.name,
            size_bytes=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_mtime, UTC).replace(tzinfo=None),
            sha256=digest,
            integrity_status=integrity_status,
        )

    async def restore_preview(self, archive_id: str) -> RestorePreviewResponse:
        path = self.resolve_path(archive_id)
        expected_tables = {
            "recommendation_sessions",
            "recommendation_adjustments",
            "listing_reviews",
            "review_analysis_snapshots",
            "preference_parse_sessions",
            "travel_plan_drafts",
            "ingestion_batches",
            "ingestion_records",
        }

        def read_bundle() -> tuple[bool, list[str], dict[str, int], bool]:
            with zipfile.ZipFile(path) as bundle:
                names = set(bundle.namelist())
                manifest_found = "manifest.json" in names
                tables = sorted(
                    name.removeprefix("data/").removesuffix(".jsonl")
                    for name in names
                    if name.startswith("data/") and name.endswith(".jsonl")
                )
                counts = {
                    table: sum(1 for _ in bundle.open(f"data/{table}.jsonl")) for table in tables
                }
                valid = bundle.testzip() is None and manifest_found
                return manifest_found, tables, counts, valid

        try:
            manifest_found, tables, counts, valid = await asyncio.to_thread(read_bundle)
        except (OSError, zipfile.BadZipFile) as error:
            raise FileNotFoundError("Archive is not a readable ZIP") from error
        missing = sorted(expected_tables - set(tables))
        warnings = ["这是恢复预览，不会向 MySQL 写入或覆盖任何数据。"]
        if missing:
            warnings.append(f"归档包缺少 {len(missing)} 个预期数据表。")
        if not valid:
            warnings.append("归档包完整性校验未通过。")
        return RestorePreviewResponse(
            archive_id=archive_id,
            file_name=path.name,
            integrity_status="valid" if valid else "invalid",
            manifest_found=manifest_found,
            tables_found=tables,
            missing_tables=missing,
            record_counts=counts,
            total_records=sum(counts.values()),
            warnings=warnings,
        )

    async def restore_plan(self, archive_id: str) -> RestorePlanResponse:
        path = self.resolve_path(archive_id)
        model_order = (
            IngestionBatch,
            IngestionRecord,
            RecommendationSession,
            RecommendationAdjustment,
            ListingReview,
            ReviewAnalysisSnapshot,
            PreferenceParseSession,
            TravelPlanDraft,
        )

        def read_records() -> tuple[dict[str, list[dict[str, Any]]], list[str]]:
            result: dict[str, list[dict[str, Any]]] = {}
            missing_tables: list[str] = []
            with zipfile.ZipFile(path) as bundle:
                for model in model_order:
                    table = model.__tablename__
                    name = f"data/{table}.jsonl"
                    if name not in bundle.namelist():
                        result[table] = []
                        missing_tables.append(table)
                        continue
                    records = []
                    for raw_line in bundle.read(name).decode("utf-8").splitlines():
                        if raw_line.strip():
                            try:
                                records.append(json.loads(raw_line))
                            except json.JSONDecodeError:
                                records.append({})
                    result[table] = records
            return result, missing_tables

        try:
            records_by_table, missing_tables = await asyncio.to_thread(read_records)
        except (OSError, UnicodeDecodeError, zipfile.BadZipFile) as error:
            raise FileNotFoundError("Archive data cannot be read") from error
        plans = []
        for model in model_order:
            table = model.__tablename__
            records = records_by_table[table]
            ids = [record.get("id") for record in records if isinstance(record.get("id"), int)]
            existing_ids = (
                set(
                    (await self.session.execute(select(model.id).where(model.id.in_(ids))))
                    .scalars()
                    .all()
                )
                if ids
                else set()
            )
            invalid = len(records) - len(ids)
            conflicts = sum(record_id in existing_ids for record_id in ids)
            plans.append(
                RestoreTablePlan(
                    table=table,
                    archive_records=len(records),
                    insert_candidates=len(ids) - conflicts,
                    existing_conflicts=conflicts,
                    invalid_records=invalid,
                )
            )
        total_candidates = sum(item.insert_candidates for item in plans)
        total_conflicts = sum(item.existing_conflicts for item in plans)
        blockers = []
        if missing_tables:
            blockers.append(f"归档包缺少 {len(missing_tables)} 个预期数据表。")
        if total_conflicts:
            blockers.append("存在主键冲突，必须先选择跳过、重映射或覆盖策略。")
        if any(item.invalid_records for item in plans):
            blockers.append("归档中存在缺少有效主键的记录。")
        return RestorePlanResponse(
            archive_id=archive_id,
            execution_order=[model.__tablename__ for model in model_order],
            tables=plans,
            total_insert_candidates=total_candidates,
            total_conflicts=total_conflicts,
            can_restore_safely=not blockers,
            blockers=blockers,
        )

    async def request_restore(self, archive_id: str, requester_id: int) -> ArchiveRestoreRequest:
        plan = await self.restore_plan(archive_id)
        verification = await self.verify(archive_id)
        snapshot = plan.model_dump(mode="json")
        snapshot["archive_sha256"] = verification.sha256
        request = ArchiveRestoreRequest(
            public_id=str(uuid.uuid4()),
            archive_id=archive_id,
            requested_by=requester_id,
            status="pending",
            plan_snapshot=snapshot,
        )
        self.session.add(request)
        await self.session.commit()
        await self.session.refresh(request)
        return request

    async def list_restore_requests(self) -> list[ArchiveRestoreRequest]:
        result = await self.session.execute(
            select(ArchiveRestoreRequest).order_by(ArchiveRestoreRequest.created_at.desc())
        )
        return list(result.scalars().all())

    async def decide_restore_request(
        self, public_id: str, reviewer_id: int, action: str, reason: str
    ) -> ArchiveRestoreRequest:
        if action not in {"approved", "rejected"}:
            raise ValueError("Action must be approved or rejected")
        request = await self.session.scalar(
            select(ArchiveRestoreRequest).where(ArchiveRestoreRequest.public_id == public_id)
        )
        if request is None:
            raise FileNotFoundError("Restore request not found")
        if request.status != "pending":
            raise ValueError("Restore request has already been decided")
        if request.requested_by == reviewer_id:
            raise ValueError("Requester cannot approve or reject their own restore request")
        request.status = action
        request.reviewed_by = reviewer_id
        request.decision_reason = reason.strip() or None
        await self.session.commit()
        await self.session.refresh(request)
        return request

    async def execution_readiness(self, public_id: str) -> RestoreExecutionReadiness:
        request = await self.session.scalar(
            select(ArchiveRestoreRequest).where(ArchiveRestoreRequest.public_id == public_id)
        )
        if request is None:
            raise FileNotFoundError("Restore request not found")
        verification = await self.verify(request.archive_id)
        current_plan = await self.restore_plan(request.archive_id)
        snapshot = request.plan_snapshot
        approved = request.status == "approved"
        integrity_valid = verification.integrity_status == "valid"
        archive_unchanged = (
            bool(snapshot.get("archive_sha256"))
            and snapshot.get("archive_sha256") == verification.sha256
        )
        plan_unchanged = (
            snapshot.get("total_insert_candidates") == current_plan.total_insert_candidates
            and snapshot.get("total_conflicts") == current_plan.total_conflicts
            and snapshot.get("blockers") == current_plan.blockers
        )
        no_conflicts = current_plan.can_restore_safely
        blockers = []
        if not approved:
            blockers.append("恢复申请尚未批准。")
        if not integrity_valid:
            blockers.append("归档包完整性校验未通过。")
        if not archive_unchanged:
            blockers.append("归档包哈希与申请时不一致。")
        if not plan_unchanged:
            blockers.append("当前数据库状态与申请时的恢复计划不一致。")
        if not no_conflicts:
            blockers.extend(current_plan.blockers)
        return RestoreExecutionReadiness(
            request_public_id=public_id,
            archive_id=request.archive_id,
            approved=approved,
            archive_integrity_valid=integrity_valid,
            archive_unchanged=archive_unchanged,
            plan_unchanged=plan_unchanged,
            no_conflicts=no_conflicts,
            ready_to_execute=not blockers,
            blockers=list(dict.fromkeys(blockers)),
        )

    async def execute_restore(
        self, public_id: str, confirmation: str, executor_id: int
    ) -> RestoreExecuteResponse:
        if confirmation != "RESTORE INSERT ONLY":
            raise ValueError("Confirmation phrase is incorrect")
        readiness = await self.execution_readiness(public_id)
        if not readiness.ready_to_execute:
            raise ValueError("Restore execution gate did not pass")
        request = await self.session.scalar(
            select(ArchiveRestoreRequest).where(ArchiveRestoreRequest.public_id == public_id)
        )
        if request is None:
            raise FileNotFoundError("Restore request not found")
        path = self.resolve_path(request.archive_id)
        model_order = (
            IngestionBatch,
            IngestionRecord,
            RecommendationSession,
            RecommendationAdjustment,
            ListingReview,
            ReviewAnalysisSnapshot,
            PreferenceParseSession,
            TravelPlanDraft,
        )

        def read_records() -> dict[str, list[dict[str, Any]]]:
            with zipfile.ZipFile(path) as bundle:
                return {
                    model.__tablename__: [
                        json.loads(line)
                        for line in bundle.read(f"data/{model.__tablename__}.jsonl")
                        .decode("utf-8")
                        .splitlines()
                        if line.strip()
                    ]
                    for model in model_order
                }

        records_by_table = await asyncio.to_thread(read_records)
        inserted_counts: dict[str, int] = {}
        try:
            for model in model_order:
                table = model.__tablename__
                records = records_by_table[table]
                columns = {column.key: column for column in inspect(model).columns}
                instances = []
                for record in records:
                    values = {
                        key: _restore_value(columns[key].type.python_type, value)
                        for key, value in record.items()
                        if key in columns
                    }
                    instances.append(model(**values))
                self.session.add_all(instances)
                inserted_counts[table] = len(instances)
            request.status = "executed"
            request.executed_by = executor_id
            request.executed_at = datetime.now(UTC).replace(tzinfo=None)
            request.execution_summary = {
                "archive_sha256": (await self.verify(request.archive_id)).sha256,
                "inserted_counts": inserted_counts,
                "total_inserted": sum(inserted_counts.values()),
                "overwrite_performed": False,
                "deletion_performed": False,
            }
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return RestoreExecuteResponse(
            request_public_id=public_id,
            archive_id=request.archive_id,
            status="executed",
            inserted_counts=inserted_counts,
            total_inserted=sum(inserted_counts.values()),
        )

    def resolve_path(self, archive_id: str) -> Path:
        try:
            normalized_id = str(uuid.UUID(archive_id))
        except ValueError as error:
            raise FileNotFoundError("Archive not found") from error
        output_dir = Path(settings.archive_output_dir).resolve()
        path = (output_dir / f"stay-scale-{normalized_id}.zip").resolve()
        if path.parent != output_dir or not path.is_file():
            raise FileNotFoundError("Archive not found")
        return path

    @staticmethod
    def _zip_is_valid(path: Path) -> bool:
        try:
            with zipfile.ZipFile(path) as bundle:
                return bundle.testzip() is None and "manifest.json" in bundle.namelist()
        except zipfile.BadZipFile:
            return False


def _json_value(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _restore_value(python_type: type, value: Any) -> Any:
    if value is None:
        return None
    if python_type is datetime and isinstance(value, str):
        return datetime.fromisoformat(value)
    if python_type is date_type and isinstance(value, str):
        return date_type.fromisoformat(value)
    if python_type is Decimal:
        return Decimal(str(value))
    return value
