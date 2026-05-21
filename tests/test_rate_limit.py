"""Tests for rate limiting middleware."""

import httpx
import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.utils.rate_limit import RateLimitMiddleware, add_rate_limit_middleware


@pytest.fixture
def rate_limited_app() -> FastAPI:
    app = FastAPI()
    add_rate_limit_middleware(app)

    @app.get("/test")
    async def test_endpoint() -> dict:
        return {"ok": True}

    return app


@pytest.mark.asyncio
async def test_rate_limit_allows_requests(rate_limited_app: FastAPI) -> None:
    """Requests under the limit should succeed."""
    async with AsyncClient(transport=httpx.ASGITransport(app=rate_limited_app), base_url="http://test") as client:
        response = await client.get("/test")
        assert response.status_code == 200
        assert response.json() == {"ok": True}


@pytest.mark.asyncio
async def test_rate_limit_blocks_excess_requests(rate_limited_app: FastAPI) -> None:
    """Requests over the limit should return 429."""
    # The default rate limit is 10 RPS, so we need to exceed that.
    # We'll create a custom middleware with a very low limit for testing.
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, max_requests=1, window_seconds=60)

    @app.get("/test")
    async def test_endpoint() -> dict:
        return {"ok": True}

    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        r1 = await client.get("/test")
        assert r1.status_code == 200

        r2 = await client.get("/test")
        assert r2.status_code == 429
        assert "Rate limit exceeded" in r2.text
