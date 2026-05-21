"""Chat service for processing messages."""

import uuid
from typing import Any, Dict, List, Optional

from app.agents.orchestrator import Orchestrator
from app.config import settings
from app.services.llm_service import LLMService
from app.llm.tool_registry import ToolRegistry
from app.mcp.client import MCPClient
from app.services.persistence import save_chat_turn
from app.utils.security import validate_chat_input


class ChatService:
    """Service for handling chat interactions."""

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        tool_registry: Optional[ToolRegistry] = None,
        mcp_client: Optional[MCPClient] = None,
        orchestrator: Optional[Orchestrator] = None,
    ) -> None:
        """Initialize the chat service."""
        self.settings = settings
        self.llm_service = llm_service or LLMService()
        self.tool_registry = tool_registry or ToolRegistry()
        self.mcp_client = mcp_client or MCPClient()
        self.orchestrator = orchestrator or Orchestrator()

    async def process_message(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process a user message and return a response.

        Args:
            user_id: Unique identifier for the user.
            message: Message content from the user.
            session_id: Optional session identifier for conversation continuity.

        Returns:
            Dictionary containing the response message, actions, and session_id.
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        # Security: validate and sanitize user input
        validation = validate_chat_input(message)
        if not validation["safe"]:
            return {
                "message": (
                    "I can't process that request because it contains "
                    f"potentially harmful content ({', '.join(validation['issues'])}). "
                    "Please rephrase your question."
                ),
                "actions": [],
                "session_id": session_id,
            }
        message = validation["sanitized"]

        # Fallback to echo if OPENAI_API_KEY is not configured
        if not self.settings.OPENAI_API_KEY:
            return {
                "message": f"Echo: {message}",
                "actions": [],
                "session_id": session_id,
            }

        result = await self.orchestrator.process(
            user_id=user_id,
            message=message,
            session_id=session_id,
        )

        # Best-effort persistence to PostgreSQL
        await save_chat_turn(
            user_id=user_id,
            session_id=result["session_id"],
            user_message=message,
            assistant_message=result["message"],
            actions=result.get("actions", []),
        )

        return {
            "message": result["message"],
            "actions": result.get("actions", []),
            "session_id": result["session_id"],
        }
