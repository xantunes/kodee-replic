"""SQLAlchemy models for database."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Conversation(Base):
    """Represents a conversation session."""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False, index=True)
    session_id = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)

    messages: list["Message"] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    """Represents a single message in a conversation."""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String, nullable=False)  # e.g., "user", "assistant", "system"
    content = Column(String, nullable=False)
    tool_calls = Column(JSON, nullable=True, default=None)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)

    conversation: "Conversation" = relationship("Conversation", back_populates="messages")
