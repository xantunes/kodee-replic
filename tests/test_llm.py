"""Tests for LLM integration."""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.services.llm_service import LLMService
from app.llm.prompts import SYSTEM_PROMPT, build_messages
from app.llm.tool_registry import ToolRegistry
from app.services.chat_service import ChatService


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_register_tool(self) -> None:
        """Test registering a custom tool."""
        registry = ToolRegistry()

        def custom_tool(query: str) -> str:
            return f"Result for {query}"

        registry.register_tool(
            name="custom_tool",
            description="A custom tool for testing.",
            handler_fn=custom_tool,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The query string"}
                },
                "required": ["query"],
            },
        )

        tools = registry.get_tools()
        tool_names = [t["function"]["name"] for t in tools]
        assert "custom_tool" in tool_names

    def test_execute_tool(self) -> None:
        """Test executing a registered tool."""
        registry = ToolRegistry()

        def greet(name: str) -> str:
            return f"Hello, {name}!"

        registry.register_tool(
            name="greet",
            description="Greet someone by name.",
            handler_fn=greet,
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name to greet"}
                },
                "required": ["name"],
            },
        )

        result = registry.execute_tool("greet", {"name": "Alice"})
        assert result == "Hello, Alice!"

    def test_execute_tool_not_found(self) -> None:
        """Test executing a non-existent tool returns an error."""
        registry = ToolRegistry()
        result = registry.execute_tool("nonexistent", {})
        assert "not found" in result

    def test_default_tools_registered(self) -> None:
        """Test that default tools are pre-registered."""
        registry = ToolRegistry()
        tools = registry.get_tools()
        tool_names = {t["function"]["name"] for t in tools}
        assert "get_weather" in tool_names
        assert "calculate" in tool_names
        assert "get_time" in tool_names

    def test_execute_calculate_tool(self) -> None:
        """Test the pre-registered calculate tool."""
        registry = ToolRegistry()
        result = registry.execute_tool("calculate", {"expression": "2 + 3"})
        assert result == "5"

    def test_execute_weather_tool(self) -> None:
        """Test the pre-registered get_weather tool."""
        registry = ToolRegistry()
        result = registry.execute_tool("get_weather", {"location": "Lisbon"})
        assert "Lisbon" in result


class TestLLMService:
    """Tests for LLMService."""

    @pytest.mark.asyncio
    async def test_chat_returns_string(self) -> None:
        """Test that chat returns a string response."""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="Hello!"))

        with patch("app.services.llm_service._create_llm", return_value=mock_llm):
            service = LLMService()
            messages = [SystemMessage(content="System"), HumanMessage(content="Hi")]
            result = await service.chat(messages)
            assert result == "Hello!"
            mock_llm.ainvoke.assert_awaited_once_with(messages)

    @pytest.mark.asyncio
    async def test_chat_handles_api_error(self) -> None:
        """Test that chat handles API errors gracefully."""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("API Error"))

        with patch("app.services.llm_service._create_llm", return_value=mock_llm):
            service = LLMService()
            messages = [HumanMessage(content="Hi")]
            result = await service.chat(messages)
            assert "error" in result.lower() or "sorry" in result.lower()

    @pytest.mark.asyncio
    async def test_chat_with_tools_returns_aimessage(self) -> None:
        """Test that chat_with_tools returns an AIMessage."""
        mock_llm = MagicMock()
        mock_llm.bind_tools = MagicMock(return_value=mock_llm)
        mock_llm.ainvoke = AsyncMock(return_value=AIMessage(content="Response"))

        with patch("app.services.llm_service._create_llm", return_value=mock_llm):
            service = LLMService()
            messages = [HumanMessage(content="Hi")]
            tools: List[Dict[str, Any]] = []
            result = await service.chat_with_tools(messages, tools)
            assert isinstance(result, AIMessage)
            assert result.content == "Response"


class TestChatServiceWithLLM:
    """Tests for ChatService with mocked LLM."""

    @pytest.mark.asyncio
    async def test_process_message_with_mocked_llm(self) -> None:
        """Test process_message with a mocked orchestrator response."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process = AsyncMock(
            return_value={
                "message": "Mocked response",
                "actions": [],
                "session_id": "test-session",
            }
        )

        chat_service = ChatService(orchestrator=mock_orchestrator)

        with patch.object(chat_service.settings, "OPENAI_API_KEY", "test-key"):
            result = await chat_service.process_message(
                user_id="user-123",
                message="Hello",
            )

        assert result["message"] == "Mocked response"
        assert result["actions"] == []
        assert "session_id" in result

    @pytest.mark.asyncio
    async def test_process_message_with_tool_call(self) -> None:
        """Test process_message returns actions from orchestrator."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.process = AsyncMock(
            return_value={
                "message": "The result is 4.",
                "actions": [
                    {
                        "tool": "calculate",
                        "args": {"expression": "2 + 2"},
                        "result": "4",
                        "source": "local",
                    }
                ],
                "session_id": "test-session",
            }
        )

        chat_service = ChatService(orchestrator=mock_orchestrator)

        with patch.object(chat_service.settings, "OPENAI_API_KEY", "test-key"):
            result = await chat_service.process_message(
                user_id="user-123",
                message="What is 2 + 2?",
            )

        assert result["message"] == "The result is 4."
        assert len(result["actions"]) == 1
        assert result["actions"][0]["tool"] == "calculate"
        assert result["actions"][0]["result"] == "4"

    @pytest.mark.asyncio
    async def test_process_message_fallback_when_no_api_key(self) -> None:
        """Test that process_message falls back to echo when OPENAI_API_KEY is empty."""
        chat_service = ChatService()

        with patch.object(chat_service.settings, "OPENAI_API_KEY", ""):
            result = await chat_service.process_message(
                user_id="user-123",
                message="Hello",
            )

        assert result["message"] == "Echo: Hello"
        assert result["actions"] == []


class TestPrompts:
    """Tests for prompt building."""

    def test_build_messages(self) -> None:
        """Test that build_messages constructs the correct message list."""
        messages = build_messages(user_message="Hello", history=[])
        assert len(messages) == 2
        assert isinstance(messages[0], SystemMessage)
        assert messages[0].content == SYSTEM_PROMPT
        assert isinstance(messages[1], HumanMessage)
        assert messages[1].content == "Hello"

    def test_build_messages_with_history(self) -> None:
        """Test that build_messages includes history."""
        history = [AIMessage(content="Previous response")]
        messages = build_messages(user_message="Follow-up", history=history)
        assert len(messages) == 3
        assert isinstance(messages[0], SystemMessage)
        assert isinstance(messages[1], AIMessage)
        assert isinstance(messages[2], HumanMessage)
