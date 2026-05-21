"""Tests for monitoring, metrics, and request logging middleware."""

from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

from app.utils.monitoring import init_tracing


class TestMetricsEndpoint:
    """Tests for the /metrics endpoint."""

    @pytest.mark.asyncio
    async def test_metrics_returns_stats(self, client: AsyncClient) -> None:
        """Test that /metrics returns uptime, total_requests, and active_sessions."""
        response = await client.get("/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "uptime_seconds" in data
        assert "total_requests" in data
        assert "active_sessions" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert isinstance(data["total_requests"], int)
        assert isinstance(data["active_sessions"], int)
        assert data["uptime_seconds"] >= 0
        assert data["active_sessions"] >= 0

    @pytest.mark.asyncio
    async def test_metrics_increments_total_requests(self, client: AsyncClient) -> None:
        """Test that each request increments total_requests."""
        r1 = await client.get("/metrics")
        before = r1.json()["total_requests"]

        # Make an additional request
        await client.get("/health")

        r2 = await client.get("/metrics")
        after = r2.json()["total_requests"]

        assert after > before


class TestHealthEndpoint:
    """Tests to ensure /health continues to work."""

    @pytest.mark.asyncio
    async def test_health_still_works(self, client: AsyncClient) -> None:
        """Test that /health returns the expected healthy payload."""
        response = await client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "environment" in data
        assert "version" in data


class TestRequestLoggingMiddleware:
    """Tests for the request logging middleware."""

    @pytest.mark.asyncio
    async def test_request_logging_middleware(self, client: AsyncClient) -> None:
        """Test that the middleware logs request details via the logger."""
        mock_logger = MagicMock()

        with patch("app.utils.monitoring.get_logger", return_value=mock_logger):
            response = await client.get("/health")

        assert response.status_code == 200
        # The middleware calls logger.info with a formatted message template
        assert mock_logger.info.called
        call_args = mock_logger.info.call_args
        # The first positional argument is the log message template
        log_msg = call_args[0][0] if call_args[0] else ""
        assert "method" in log_msg or "path" in log_msg


class TestTracing:
    """Tests for OpenTelemetry tracing initialization."""

    def test_init_tracing_runs_without_error(self) -> None:
        """Test that init_tracing() can be called without raising an exception."""
        init_tracing()
