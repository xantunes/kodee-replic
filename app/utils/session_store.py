"""Session store implementations for conversation history.

Supports in-memory (default) and Redis backends.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.config import settings

logger = logging.getLogger(__name__)


def _message_to_dict(msg: BaseMessage) -> dict:
    """Serialize a LangChain message to a dict."""
    return {"type": msg.__class__.__name__, "content": msg.content}


def _message_from_dict(data: dict) -> BaseMessage:
    """Deserialize a dict to a LangChain message."""
    msg_type = data.get("type", "")
    content = data.get("content", "")
    if msg_type == "HumanMessage":
        return HumanMessage(content=content)
    if msg_type == "AIMessage":
        return AIMessage(content=content)
    if msg_type == "SystemMessage":
        return SystemMessage(content=content)
    return BaseMessage(content=content)


class SessionStore(ABC):
    """Abstract session store for conversation history."""

    @abstractmethod
    async def get_history(self, session_id: str) -> List[BaseMessage]:
        """Retrieve history for a session."""
        ...

    @abstractmethod
    async def set_history(self, session_id: str, history: List[BaseMessage]) -> None:
        """Store history for a session."""
        ...

    @abstractmethod
    async def clear_history(self, session_id: str) -> None:
        """Clear history for a session."""
        ...


class InMemorySessionStore(SessionStore):
    """In-memory session store (resets on app restart)."""

    def __init__(self) -> None:
        self._data: dict[str, List[BaseMessage]] = {}

    async def get_history(self, session_id: str) -> List[BaseMessage]:
        return list(self._data.get(session_id, []))

    async def set_history(self, session_id: str, history: List[BaseMessage]) -> None:
        self._data[session_id] = list(history)

    async def clear_history(self, session_id: str) -> None:
        self._data.pop(session_id, None)


class RedisSessionStore(SessionStore):
    """Redis-backed session store with TTL."""

    def __init__(self, redis_url: str | None = None, ttl_seconds: int = 3600) -> None:
        import redis.asyncio as aioredis

        self._redis = aioredis.from_url(redis_url or settings.REDIS_URL)
        self._ttl = ttl_seconds

    async def get_history(self, session_id: str) -> List[BaseMessage]:
        try:
            data = await self._redis.get(f"session:{session_id}")
            if data is None:
                return []
            items = json.loads(data)
            return [_message_from_dict(item) for item in items]
        except Exception as e:
            logger.warning("Redis get_history failed, returning empty: %s", e)
            return []

    async def set_history(self, session_id: str, history: List[BaseMessage]) -> None:
        try:
            items = [_message_to_dict(msg) for msg in history]
            await self._redis.setex(
                f"session:{session_id}", self._ttl, json.dumps(items)
            )
        except Exception as e:
            logger.warning("Redis set_history failed: %s", e)

    async def clear_history(self, session_id: str) -> None:
        try:
            await self._redis.delete(f"session:{session_id}")
        except Exception as e:
            logger.warning("Redis clear_history failed: %s", e)


def get_session_store() -> SessionStore:
    """Return a session store based on configuration.

    Uses Redis if REDIS_URL is available and non-empty, otherwise falls back
    to in-memory storage.
    """
    if settings.REDIS_URL and settings.REDIS_URL != "redis://localhost:6379/0":
        try:
            return RedisSessionStore()
        except Exception as e:
            logger.warning("Failed to create Redis session store: %s", e)
    return InMemorySessionStore()
