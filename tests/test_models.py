"""Tests for SQLAlchemy database models."""

import uuid

from app.models.database import Conversation, Message, ToolExecution, now_utc


class TestToolExecution:
    """Tests for the ToolExecution model."""

    def test_can_instantiate_with_all_fields(self) -> None:
        """Test that ToolExecution can be created with all required fields."""
        conv_id = uuid.uuid4()
        te_id = uuid.uuid4()
        created = now_utc()
        te = ToolExecution(
            id=te_id,
            conversation_id=conv_id,
            tool_name="calculate",
            arguments={"expression": "2 + 2"},
            result={"output": "4"},
            success=True,
            duration_ms=42,
            created_at=created,
        )
        assert te.id == te_id
        assert te.tool_name == "calculate"
        assert te.arguments == {"expression": "2 + 2"}
        assert te.result == {"output": "4"}
        assert te.success is True
        assert te.duration_ms == 42
        assert te.conversation_id == conv_id
        assert te.created_at == created

    def test_can_instantiate_with_minimal_fields(self) -> None:
        """Test that ToolExecution can be created with only required fields."""
        te_id = uuid.uuid4()
        te = ToolExecution(
            id=te_id,
            tool_name="get_weather",
            success=False,
        )
        assert te.id == te_id
        assert te.tool_name == "get_weather"
        assert te.arguments is None
        assert te.result is None
        assert te.success is False
        assert te.duration_ms is None
        assert te.conversation_id is None
        assert te.created_at is None

    def test_table_name(self) -> None:
        """Test that the table name is correct."""
        assert ToolExecution.__tablename__ == "tool_executions"

    def test_column_attributes_exist(self) -> None:
        """Test that all expected columns are mapped on ToolExecution."""
        cols = {c.name for c in ToolExecution.__table__.columns}
        assert "id" in cols
        assert "conversation_id" in cols
        assert "tool_name" in cols
        assert "arguments" in cols
        assert "result" in cols
        assert "success" in cols
        assert "duration_ms" in cols
        assert "created_at" in cols


class TestConversation:
    """Tests for the Conversation model."""

    def test_can_instantiate(self) -> None:
        """Test that Conversation can be created."""
        conv = Conversation(
            id=uuid.uuid4(),
            user_id="user-1",
            session_id="sess-1",
            created_at=now_utc(),
        )
        assert conv.user_id == "user-1"
        assert conv.session_id == "sess-1"
        assert isinstance(conv.id, uuid.UUID)

    def test_table_name(self) -> None:
        """Test that the table name is correct."""
        assert Conversation.__tablename__ == "conversations"


class TestMessage:
    """Tests for the Message model."""

    def test_can_instantiate(self) -> None:
        """Test that Message can be created."""
        conv_id = uuid.uuid4()
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=conv_id,
            role="user",
            content="Hello",
            created_at=now_utc(),
        )
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.conversation_id == conv_id
        assert msg.tool_calls is None

    def test_table_name(self) -> None:
        """Test that the table name is correct."""
        assert Message.__tablename__ == "messages"
