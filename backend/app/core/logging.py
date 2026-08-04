import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings

SENSITIVE_KEYS = ("password", "token", "authorization", "api_key", "secret", "cookie")
SENSITIVE_PATTERNS = (
    re.compile(r"(?i)(bearer\s+)[a-z0-9._~+\-/]+=*"),
    re.compile(r"(?i)(sk-[a-z0-9_-]{8,})"),
    re.compile(r"(?i)([a-z][a-z0-9+.-]*://[^:\s/]+:)([^@\s]+)(@)"),
)


def sanitize_log_value(value: Any, key: str = "") -> Any:
    if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {
            item_key: sanitize_log_value(item, str(item_key))
            for item_key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [sanitize_log_value(item) for item in value]
    if not isinstance(value, str):
        return value
    sanitized = value
    sanitized = SENSITIVE_PATTERNS[0].sub(r"\1[REDACTED]", sanitized)
    sanitized = SENSITIVE_PATTERNS[1].sub("[REDACTED]", sanitized)
    sanitized = SENSITIVE_PATTERNS[2].sub(r"\1[REDACTED]\3", sanitized)
    return sanitized


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitize_log_value(record.getMessage()),
        }
        for field in (
            "event",
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "client_ip",
        ):
            if hasattr(record, field):
                payload[field] = sanitize_log_value(getattr(record, field), field)
        if record.exc_info:
            payload["exception"] = sanitize_log_value(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    if settings.log_format.lower() == "json":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )
    logging.basicConfig(level=settings.log_level.upper(), handlers=[handler], force=True)
