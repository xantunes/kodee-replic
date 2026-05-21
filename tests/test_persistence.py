"""Tests for persistence service (ConversationRepository and save_chat_turn)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.persistence import ConversationRepository, save_chat_turn


class TestConversationRepository:
    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Return a mocked AsyncSession."""
        session = MagicMock()
        session.execute = AsyncMock()
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.commit = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_or_create_conversation_creates_new(self, mock_session) -> None:
        """Test that get_or_create_conversation creates a new record when not found."""
        # Simulate no existing conversation
        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute.return_value = scalar_result

        repo = ConversationRepository(mock_session)
        conv = await repo.get_or_create_conversation("user-1", "session-1")

        assert conv.user_id == "user-1"
        assert conv.session_id == "session-1"
        assert isinstance(conv.id, uuid.UUID)
        mock_session.add.assert_called_once()
        mock_session.flush.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_or_create_conversation_returns_existing(self, mock_session) -> None:
        """Test that get_or_create_conversation returns existing record."""
        existing = MagicMock()
        existing.user_id = "user-1"
        existing.session_id = "session-1"

        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none = MagicMock(return_value=existing)
        mock_session.execute.return_value = scalar_result

        repo = ConversationRepository(mock_session)
        conv = await repo.get_or_create_conversation("user-1", "session-1")

        assert conv is existing
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_message(self, mock_session) -> None:
        """Test adding a message to a conversation."""
        repo = ConversationRepository(mock_session)
        conv_id = uuid.uuid4()
        msg = await repo.add_message(conv_id, "user", "Hello")

        assert msg.conversation_id == conv_id
        assert msg.role == "user"
        assert msg.content == "Hello"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_add_tool_execution(self, mock_session) -> None:
        """Test adding a tool execution."""
        repo = ConversationRepository(mock_session)
        conv_id = uuid.uuid4()
        exec_record = await repo.add_tool_execution(
            conversation_id=conv_id,
            tool_name="calculate",
            arguments={"expression": "2+2"},
            result={"output": "4"},
            success=True,
            duration_ms=150,
        )

        assert exec_record.conversation_id == conv_id
        assert exec_record.tool_name == "calculate"
        assert exec_record.success is True
        assert exec_record.duration_ms == 150
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_messages_returns_empty_when_not_found(self, mock_session) -> None:
        """Test get_messages returns empty list for unknown session."""
        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute.return_value = scalar_result

        repo = ConversationRepository(mock_session)
        messages = await repo.get_messages("nonexistent")
        assert messages == []


class TestSaveChatTurn:
    @pytest.mark.asyncio
    async def test_save_chat_turn_persists_data(self) -> None:
        """Test that save_chat_turn persists conversation, messages, and actions."""
        mock_session = MagicMock()
        mock_session.execute = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        mock_session.commit = AsyncMock()

        # Simulate no existing conversation
        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute.return_value = scalar_result

        async def _mock_gen():
            yield mock_session

        with patch(
            "app.services.persistence.get_db_session", _mock_gen
        ):
            conv_id = await save_chat_turn(
                user_id="user-1",
                session_id="session-1",
                user_message="Hello",
                assistant_message="Hi there",
                actions=[
                    {"tool": "calculate", "args": {"expression": "1+1"}, "result": "2"}
                ],
            )

        assert conv_id is not None
        assert isinstance(conv_id, uuid.UUID)
        assert mock_session.commit.await_count == 1

    @pytest.mark.asyncio
    async def test_save_chat_turn_graceful_on_failure(self) -> None:
        """Test that save_chat_turn returns None on failure without raising."""
        async def _failing_gen():
            raise Exception("DB down")
            yield  # noqa: unreachable

        with patch(
            "app.services.persistence.get_db_session", _failing_gen
        ):
            conv_id = await save_chat_turn(
                user_id="user-1",
                session_id="session-1",
                user_message="Hello",
                assistant_message="Hi",
            )

        assert conv_id is None
