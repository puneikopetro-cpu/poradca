"""
Centralized logging configuration.

Format:
  - DEV:  colored, human-readable
  - PROD: JSON-like structured (one line per record)

Usage:
    from backend.logger import get_logger
    logger = get_logger(__name__)
"""
import logging
import sys
from backend.config import settings


class _PlainFormatter(logging.Formatter):
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:
        self._style._fmt = self.fmt
        return super().format(record)


class _JsonFormatter(logging.Formatter):
    """Single-line JSON formatter for production / log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        import json
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Include any extra fields attached via logger.info("msg", extra={...})
        for key, val in record.__dict__.items():
            if key not in logging.LogRecord.__dict__ and not key.startswith("_"):
                payload[key] = val
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    is_prod = not settings.DATABASE_URL.startswith("sqlite")
    formatter: logging.Formatter = _JsonFormatter() if is_prod else _PlainFormatter()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)

    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "passlib", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
