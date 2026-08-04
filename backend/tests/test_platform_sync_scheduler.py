from datetime import datetime, timedelta

from app.modules.platform_sync.scheduler import PlatformSyncScheduler


def test_never_run_source_is_due() -> None:
    now = datetime(2026, 8, 4, 10, 0)
    assert PlatformSyncScheduler.is_due(None, 60, "idle", now)


def test_source_is_due_after_interval() -> None:
    now = datetime(2026, 8, 4, 10, 0)
    assert PlatformSyncScheduler.is_due(now - timedelta(minutes=61), 60, "failed", now)
    assert not PlatformSyncScheduler.is_due(now - timedelta(minutes=59), 60, "idle", now)


def test_running_source_is_never_due() -> None:
    now = datetime(2026, 8, 4, 10, 0)
    assert not PlatformSyncScheduler.is_due(None, 60, "running", now)
