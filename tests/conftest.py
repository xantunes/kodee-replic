"""Shared pytest fixtures for the Kodee Replica test suite."""

from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.services.llm_service import LLMService
from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    import asyncio

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_settings() -> Settings:
    """Return a Settings instance with a test API key."""
    return Settings(
        OPENAI_API_KEY="test-api-key",
        OPENAI_MODEL="gpt-4o-mini",
        DATABASE_URL="postgresql+asyncpg://test:test@localhost/test",
        REDIS_URL="redis://localhost:6379/0",
        QDRANT_URL="http://localhost:6333",
    )


@pytest.fixture
def mock_llm_service() -> MagicMock:
    """Return a mocked LLMService with async chat methods."""
    mock = MagicMock(spec=LLMService)
    mock.chat = AsyncMock(return_value="Mocked LLM response")
    mock.chat_with_tools = AsyncMock(
        return_value=MagicMock(content="Mocked tool response")
    )
    mock.chat_with_tools_react = AsyncMock(
        return_value=MagicMock(content="Mocked tool response")
    )
    return mock
