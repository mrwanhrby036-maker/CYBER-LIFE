"""JSON logging with request correlation and explicit secret redaction."""
import json
import logging
import sys
from datetime import datetime, timezone
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
SENSITIVE_KEYS = {"authorization", "password", "id_token", "access_token", "refresh_token",
                  "credentials", "private_key", "secret", "cookie", "token"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {"timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname, "logger": record.name,
                "request_id": request_id_var.get(), "message": record.getMessage()}
        if hasattr(record, "event"):
            data["event"] = record.event
        if hasattr(record, "fields"):
            data["fields"] = redact(record.fields)
        if record.exc_info:
            data["exception_type"] = record.exc_info[0].__name__
        return json.dumps(data, ensure_ascii=False)


def redact(value):
    if isinstance(value, dict):
        return {k: "[REDACTED]" if any(s in k.lower() for s in SENSITIVE_KEYS)
                else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
