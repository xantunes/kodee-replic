"""Tests for chat API endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    """Provide an async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_post_chat_returns_200(client: AsyncClient) -> None:
    """Test that POST /chat returns HTTP 200."""
    payload = {
        "user_id": "user-123",
        "message": "Hello, Kodee!",
    }
    response = await client.post("/chat", json=payload)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_post_chat_response_has_message_and_session_id(client: AsyncClient) -> None:
    """Test that POST /chat response contains message and session_id."""
    payload = {
        "user_id": "user-123",
        "message": "Hello, Kodee!",
    }
    response = await client.post("/chat", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert "session_id" in data
    assert isinstance(data["message"], str)
    assert isinstance(data["session_id"], str)
    assert len(data["session_id"]) > 0
