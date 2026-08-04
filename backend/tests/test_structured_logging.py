import json
import logging

from app.core.logging import JsonLogFormatter, sanitize_log_value
from app.main import request_id_from_header


def test_sensitive_values_are_redacted_recursively() -> None:
    sanitized = sanitize_log_value(
        {
            "username": "demo",
            "password": "12345678",
            "nested": {"deepseek_api_key": "sk-secret-value"},
            "authorization": "Bearer abc.def.ghi",
        }
    )

    assert sanitized == {
        "username": "demo",
        "password": "[REDACTED]",
        "nested": {"deepseek_api_key": "[REDACTED]"},
        "authorization": "[REDACTED]",
    }


def test_json_formatter_emits_request_fields_without_credentials() -> None:
    record = logging.LogRecord(
        name="app.http",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="database mysql://user:secret@mysql:3306/stay_scale",
        args=(),
        exc_info=None,
    )
    record.request_id = "request-123"
    record.method = "GET"
    record.path = "/api/v1/health/live"
    record.status_code = 200
    record.duration_ms = 12.5

    payload = json.loads(JsonLogFormatter().format(record))

    assert payload["request_id"] == "request-123"
    assert payload["duration_ms"] == 12.5
    assert "secret" not in payload["message"]


def test_untrusted_request_id_is_replaced() -> None:
    assert request_id_from_header("safe-request_123") == "safe-request_123"
    generated = request_id_from_header("bad\nrequest")
    assert generated != "bad\nrequest"
    assert len(generated) == 32
