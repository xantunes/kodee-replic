"""Tests for monitoring utilities."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from app.utils.monitoring import (
    JSONFormatter,
    RequestLoggingMiddleware,
    add_request_middleware,
    get_logger,
    init_logging,
)


class TestJSONFormatter:
    def test_basic_format(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Hello", args=(), exc_info=None,
        )
        output = formatter.format(record)
        assert '"message": "Hello"' in output
        assert '"level": "INFO"' in output

    def test_format_with_extra_fields(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Request", args=(), exc_info=None,
        )
        record.method = "GET"
        record.path = "/health"
        record.status_code = 200
        record.duration_ms = 42.5

        output = formatter.format(record)
        assert '"method": "GET"' in output
        assert '"path": "/health"' in output
        assert '"status_code": 200' in output
        assert '"duration_ms": 42.5' in output

    def test_format_with_exception(self) -> None:
        import sys
        formatter = JSONFormatter()
        try:
            raise ValueError("Boom")
        except ValueError:
            exc_info = sys.exc_info()
            record = logging.LogRecord(
                name="test", level=logging.ERROR, pathname="", lineno=0,
                msg="Error", args=(), exc_info=exc_info,
            )
        output = formatter.format(record)
        assert '"exception":' in output
        assert "Boom" in output


class TestGetLogger:
    def test_returns_logger(self) -> None:
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"


class TestInitLogging:
    def test_adds_handler(self) -> None:
        # Clear existing handlers first
        root = logging.getLogger()
        for h in list(root.handlers):
            root.removeHandler(h)

        with patch("app.utils.monitoring.settings.LOG_LEVEL", "DEBUG"):
            init_logging()

        assert any(isinstance(h, logging.StreamHandler) for h in root.handlers)

    def test_no_duplicate_handlers(self) -> None:
        root = logging.getLogger()
        for h in list(root.handlers):
            root.removeHandler(h)

        with patch("app.utils.monitoring.settings.LOG_LEVEL", "INFO"):
            init_logging()
            init_logging()

        stream_handlers = [
            h for h in root.handlers if isinstance(h, logging.StreamHandler)
        ]
        assert len(stream_handlers) == 1


class TestRequestLoggingMiddleware:
    @pytest.mark.asyncio
    async def test_increments_total_requests(self) -> None:
        from fastapi import FastAPI
        from httpx import AsyncClient
        import httpx

        app = FastAPI()
        add_request_middleware(app)

        @app.get("/test")
        async def test_endpoint() -> dict:
            return {"ok": True}

        async with AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            await client.get("/test")

        # total_requests should have been incremented
        from app.utils.monitoring import total_requests
        assert total_requests >= 1
