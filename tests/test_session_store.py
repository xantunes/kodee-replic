"""Tests for session store implementations."""

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.utils.session_store import InMemorySessionStore


class TestInMemorySessionStore:
    @pytest.fixture
    def store(self) -> InMemorySessionStore:
        return InMemorySessionStore()

    @pytest.mark.asyncio
    async def test_get_history_empty(self, store: InMemorySessionStore) -> None:
        history = await store.get_history("session-1")
        assert history == []

    @pytest.mark.asyncio
    async def test_set_and_get_history(self, store: InMemorySessionStore) -> None:
        messages = [HumanMessage(content="Hello"), AIMessage(content="Hi there")]
        await store.set_history("session-1", messages)

        history = await store.get_history("session-1")
        assert len(history) == 2
        assert isinstance(history[0], HumanMessage)
        assert history[0].content == "Hello"
        assert isinstance(history[1], AIMessage)
        assert history[1].content == "Hi there"

    @pytest.mark.asyncio
    async def test_get_history_returns_copy(self, store: InMemorySessionStore) -> None:
        messages = [HumanMessage(content="Hello")]
        await store.set_history("session-1", messages)

        h1 = await store.get_history("session-1")
        h2 = await store.get_history("session-1")
        assert h1 is not h2

    @pytest.mark.asyncio
    async def test_clear_history(self, store: InMemorySessionStore) -> None:
        await store.set_history("session-1", [HumanMessage(content="Hello")])
        await store.clear_history("session-1")

        history = await store.get_history("session-1")
        assert history == []

    @pytest.mark.asyncio
    async def test_clear_nonexistent_session(self, store: InMemorySessionStore) -> None:
        # Should not raise
        await store.clear_history("nonexistent")
