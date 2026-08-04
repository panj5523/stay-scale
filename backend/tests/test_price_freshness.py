from datetime import datetime, timedelta

from app.modules.pricing.freshness import freshness_status


def test_price_freshness_marks_old_snapshot_stale():
    now = datetime(2026, 8, 4, 12, 0)
    assert freshness_status(now - timedelta(minutes=30), now=now) == ("fresh", 30)
    assert freshness_status(now - timedelta(hours=4), now=now) == ("stale", 240)
