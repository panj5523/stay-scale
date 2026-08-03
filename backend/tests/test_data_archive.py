import zipfile

import pytest

from app.core.config import settings
from app.modules.data_retention.archive import DataArchiveService


@pytest.mark.asyncio
async def test_archive_list_and_integrity_verification(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "archive_output_dir", str(tmp_path))
    archive_id = "4c60a87b-3547-419e-a0e5-33ff5f0508c7"
    archive_path = tmp_path / f"stay-scale-{archive_id}.zip"
    with zipfile.ZipFile(archive_path, "w") as bundle:
        bundle.writestr("manifest.json", "{}")

    service = DataArchiveService(None)  # type: ignore[arg-type]
    listed = await service.list_archives()
    verified = await service.verify(archive_id)
    preview = await service.restore_preview(archive_id)
    plan = await service.restore_plan(archive_id)

    assert listed.total == 1
    assert listed.archives[0].archive_id == archive_id
    assert verified.integrity_status == "valid"
    assert len(verified.sha256 or "") == 64
    assert preview.restore_performed is False
    assert preview.total_records == 0
    assert preview.manifest_found is True
    assert plan.restore_performed is False
    assert plan.total_conflicts == 0
    assert plan.can_restore_safely is False


def test_archive_path_rejects_invalid_id(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "archive_output_dir", str(tmp_path))
    service = DataArchiveService(None)  # type: ignore[arg-type]

    with pytest.raises(FileNotFoundError):
        service.resolve_path("../../outside")
