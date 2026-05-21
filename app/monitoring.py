"""Monitoring, logging, and observability setup for the Kodee Replica."""

import json
import logging
import sys
import time
from typing import Any, Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

# Global stats for the /metrics endpoint
_start_time: float = time.time()
total_requests: int = 0
active_sessions: int = 0


class JSONFormatter(logging.Formatter):
    """Format log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "method"):
            log_obj["method"] = record.method
        if hasattr(record, "path"):
            log_obj["path"] = record.path
        if hasattr(record, "status_code"):
            log_obj["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = record.duration_ms
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def init_logging() -> None:
    """Configure structured JSON logging for the application."""
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    # Avoid adding duplicate handlers on reloads
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a logger with the configured JSON formatting."""
    return logging.getLogger(name)


def init_sentry() -> None:
    """Initialize Sentry SDK with FastAPI integration if SENTRY_DSN is set."""
    if settings.SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[FastApiIntegration()],
            traces_sample_rate=1.0,
            environment=settings.APP_ENV,
        )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs each HTTP request with timing and status."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        global total_requests
        total_requests += 1

        start = time.time()
        response = await call_next(request)
        duration = (time.time() - start) * 1000

        logger = get_logger("app.request")
        extra = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration, 2),
        }
        logger.info("%(method)s %(path)s %(status_code)s %(duration_ms)sms", extra)
        return response


def add_request_middleware(app: FastAPI) -> None:
    """Attach the request-logging middleware to the FastAPI application."""
    app.add_middleware(RequestLoggingMiddleware)
