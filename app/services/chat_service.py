"""Chat service for processing messages."""

import uuid
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, ToolMessage

from app.config import settings
from app.llm.llm_service import LLMService
from app.llm.prompts import build_messages
from app.llm.tool_registry import ToolRegistry
from app.mcp.client import MCPClient


class ChatService:
    """Service for handling chat interactions."""

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        tool_registry: Optional[ToolRegistry] = None,
        mcp_client: Optional[MCPClient] = None,
    ) -> None:
        """Initialize the chat service."""
        self.settings = settings
        self.llm_service = llm_service or LLMService()
        self.tool_registry = tool_registry or ToolRegistry()
        self.mcp_client = mcp_client or MCPClient()

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

        # Fallback to echo if OPENAI_API_KEY is not configured
        if not self.settings.OPENAI_API_KEY:
            return {
                "message": f"Echo: {message}",
                "actions": [],
                "session_id": session_id,
            }

        # Build conversation messages
        messages = build_messages(user_message=message, history=[])

        # Get available tools from both local registry and MCP server
        local_tools = self.tool_registry.get_tools()
        mcp_tools = await self.mcp_client.list_tools()
        tools = local_tools + mcp_tools

        # Call LLM with combined tools
        response = await self.llm_service.chat_with_tools(messages, tools)

        actions: List[Dict[str, Any]] = []

        # Handle tool calls if present
        if isinstance(response, AIMessage) and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})

                # Route tool call: local first, then MCP
                local_tool_names = {
                    t["function"]["name"] for t in local_tools
                }
                if tool_name in local_tool_names:
                    tool_result = self.tool_registry.execute_tool(
                        tool_name, tool_args
                    )
                    source = "local"
                else:
                    tool_result = await self.mcp_client.call_tool(
                        tool_name, tool_args
                    )
                    source = "mcp"

                actions.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": tool_result,
                    "source": source,
                })
                # Append tool call and result to conversation
                messages.append(AIMessage(content="", tool_calls=[tool_call]))
                messages.append(
                    ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call.get("id", ""),
                    )
                )

            # Get final response after tool results
            final_response = await self.llm_service.chat_with_tools(messages, tools)
            return {
                "message": str(final_response.content),
                "actions": actions,
                "session_id": session_id,
            }

        return {
            "message": str(response.content),
            "actions": actions,
            "session_id": session_id,
        }
