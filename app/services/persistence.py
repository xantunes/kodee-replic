"""Persistence service for conversations, messages, and tool executions."""

import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Conversation, Message, ToolExecution, get_db_session

logger = logging.getLogger(__name__)


class ConversationRepository:
    """Repository for persisting chat data to PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with an async SQLAlchemy session.

        Args:
            session: Async database session.
        """
        self._session = session

    async def get_or_create_conversation(
        self, user_id: str, session_id: str
    ) -> Conversation:
        """Get an existing conversation by session_id or create a new one.

        Args:
            user_id: Unique user identifier.
            session_id: Unique session identifier.

        Returns:
            The existing or newly created Conversation.
        """
        result = await self._session.execute(
            select(Conversation).where(Conversation.session_id == session_id)
        )
        conversation = result.scalar_one_or_none()

        if conversation is None:
            conversation = Conversation(
                id=uuid.uuid4(),
                user_id=user_id,
                session_id=session_id,
            )
            self._session.add(conversation)
            await self._session.flush()
            await self._session.refresh(conversation)

        return conversation

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        tool_calls: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """Add a message to a conversation.

        Args:
            conversation_id: UUID of the parent conversation.
            role: Message role (user, assistant, system, tool).
            content: Message text.
            tool_calls: Optional tool call data.

        Returns:
            The created Message.
        """
        message = Message(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
        )
        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)
        return message

    async def get_messages(self, session_id: str) -> List[Message]:
        """Retrieve all messages for a session, ordered by creation time.

        Args:
            session_id: Session identifier.

        Returns:
            List of Message objects.
        """
        result = await self._session.execute(
            select(Conversation)
            .where(Conversation.session_id == session_id)
            .join(Conversation.messages)
        )
        conversation = result.scalar_one_or_none()
        if conversation is None:
            return []
        return list(conversation.messages)

    async def add_tool_execution(
        self,
        conversation_id: uuid.UUID,
        tool_name: str,
        arguments: Optional[Dict[str, Any]],
        result: Optional[Dict[str, Any]],
        success: bool,
        duration_ms: Optional[int] = None,
    ) -> ToolExecution:
        """Log a tool execution associated with a conversation.

        Args:
            conversation_id: UUID of the parent conversation.
            tool_name: Name of the executed tool.
            arguments: Tool arguments.
            result: Tool result.
            success: Whether the execution succeeded.
            duration_ms: Execution duration in milliseconds.

        Returns:
            The created ToolExecution.
        """
        execution = ToolExecution(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            success=success,
            duration_ms=duration_ms,
        )
        self._session.add(execution)
        await self._session.flush()
        await self._session.refresh(execution)
        return execution


async def get_conversation_id_by_session(session_id: str) -> Optional[uuid.UUID]:
    """Get the conversation UUID for a given session_id.

    Args:
        session_id: Session identifier.

    Returns:
        Conversation UUID or None if not found.
    """
    try:
        async for db_session in get_db_session():
            repo = ConversationRepository(db_session)
            conv = await repo.get_or_create_conversation(
                user_id="unknown", session_id=session_id
            )
            return conv.id
    except Exception:
        return None


async def persist_tool_execution(
    conversation_id: uuid.UUID,
    tool_name: str,
    arguments: Optional[Dict[str, Any]],
    result: Optional[Dict[str, Any]],
    success: bool,
    duration_ms: Optional[int] = None,
) -> Optional[uuid.UUID]:
    """Persist a single tool execution to PostgreSQL in real time.

    Best-effort: failures are logged but not raised.

    Args:
        conversation_id: UUID of the parent conversation.
        tool_name: Name of the executed tool.
        arguments: Tool arguments.
        result: Tool result.
        success: Whether the execution succeeded.
        duration_ms: Execution duration in milliseconds.

    Returns:
        The ToolExecution UUID if persisted, None otherwise.
    """
    try:
        async for db_session in get_db_session():
            repo = ConversationRepository(db_session)
            exec_record = await repo.add_tool_execution(
                conversation_id=conversation_id,
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                success=success,
                duration_ms=duration_ms,
            )
            await db_session.commit()
            return exec_record.id
    except Exception as e:
        logger.warning("Failed to persist tool execution: %s", e)
        return None


async def save_chat_turn(
    user_id: str,
    session_id: str,
    user_message: str,
    assistant_message: str,
    actions: Optional[List[Dict[str, Any]]] = None,
) -> Optional[uuid.UUID]:
    """Persist a single chat turn (user message + assistant response) to PostgreSQL.

    This is a best-effort operation — failures are logged but not raised,
    so chat flow is never blocked by database issues.

    Args:
        user_id: Unique user identifier.
        session_id: Session identifier.
        user_message: The user's input message.
        assistant_message: The assistant's response text.
        actions: Optional list of tool actions performed during the turn.

    Returns:
        The conversation UUID if persisted, None otherwise.
    """
    try:
        async for db_session in get_db_session():
            repo = ConversationRepository(db_session)
            conversation = await repo.get_or_create_conversation(user_id, session_id)

            await repo.add_message(
                conversation_id=conversation.id,
                role="user",
                content=user_message,
            )
            await repo.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=assistant_message,
            )

            if actions:
                for action in actions:
                    await repo.add_tool_execution(
                        conversation_id=conversation.id,
                        tool_name=action.get("tool", "unknown"),
                        arguments=action.get("args"),
                        result={"output": action.get("result")},
                        success=action.get("error") is None,
                        duration_ms=action.get("duration_ms"),
                    )

            await db_session.commit()
            return conversation.id
    except Exception as e:
        logger.warning("Failed to persist chat turn: %s", e)
        return None
