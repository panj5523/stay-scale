from datetime import UTC, datetime

from app.core.config import settings


def freshness_status(captured_at: datetime, *, now: datetime | None = None) -> tuple[str, int]:
    reference = now or datetime.now(UTC).replace(tzinfo=None)
    captured = captured_at.replace(tzinfo=None)
    age_minutes = max(0, int((reference - captured).total_seconds() // 60))
    return ("fresh" if age_minutes <= settings.price_freshness_minutes else "stale", age_minutes)
