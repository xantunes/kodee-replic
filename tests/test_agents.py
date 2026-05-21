"""Tests for the multi-agent router and handoff system."""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.agents.base import BaseAgent
from app.agents.orchestrator import MAX_HISTORY, Orchestrator
from app.agents.router import AVAILABLE_AGENTS, AgentRouter
from app.agents.specialized import (
    CodeAgent,
    CreativeAgent,
    GeneralAgent,
    ResearchAgent,
)


class DummyAgent(BaseAgent):
    """Dummy agent for testing."""

    name = "dummy"
    system_prompt = "You are a dummy agent."

    async def run(
        self, message: str, history: list[BaseMessage]
    ) -> Dict[str, Any]:
        """Return a simple response."""
        return {"message": f"Dummy: {message}", "agent": self.name}


class TestAgentRouter:
    """Tests for AgentRouter."""

    @pytest.mark.asyncio
    async def test_route_returns_valid_agent_name(self) -> None:
        """Test that route returns a valid agent name."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat = AsyncMock(return_value="code")

        router = AgentRouter(llm_service=mock_llm_service)
        result = await router.route("How do I write a Python function?", [])

        assert result in AVAILABLE_AGENTS
        assert result == "code"

    @pytest.mark.asyncio
    async def test_route_fallback_to_general(self) -> None:
        """Test that invalid classification falls back to general."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat = AsyncMock(return_value="unknown_agent")

        router = AgentRouter(llm_service=mock_llm_service)
        result = await router.route("Hello", [])

        assert result == "general"

    @pytest.mark.asyncio
    async def test_route_strips_and_lowercases(self) -> None:
        """Test that route normalizes the LLM response."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat = AsyncMock(return_value="  RESEARCH  ")

        router = AgentRouter(llm_service=mock_llm_service)
        result = await router.route("What is the capital of France?", [])

        assert result == "research"

    @pytest.mark.asyncio
    async def test_route_uses_routing_prompt(self) -> None:
        """Test that route sends the routing prompt to the LLM."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat = AsyncMock(return_value="general")

        router = AgentRouter(llm_service=mock_llm_service)
        await router.route("Hello", [])

        call_args = mock_llm_service.chat.await_args
        messages = call_args[0][0]
        assert len(messages) == 2
        assert "classify" in messages[0].content.lower()


class TestSpecializedAgents:
    """Tests for specialized agents."""

    def test_general_agent_system_prompt(self) -> None:
        """Test GeneralAgent has the correct system prompt."""
        agent = GeneralAgent()
        assert "general-purpose" in agent.system_prompt.lower()
        assert agent.name == "general"

    def test_code_agent_system_prompt(self) -> None:
        """Test CodeAgent has the correct system prompt."""
        agent = CodeAgent()
        assert "programming" in agent.system_prompt.lower()
        assert agent.name == "code"

    def test_research_agent_system_prompt(self) -> None:
        """Test ResearchAgent has the correct system prompt."""
        agent = ResearchAgent()
        assert "research" in agent.system_prompt.lower()
        assert agent.name == "research"

    def test_creative_agent_system_prompt(self) -> None:
        """Test CreativeAgent has the correct system prompt."""
        agent = CreativeAgent()
        assert "creative" in agent.system_prompt.lower()
        assert agent.name == "creative"

    @pytest.mark.asyncio
    async def test_general_agent_run(self) -> None:
        """Test GeneralAgent run method."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat_with_tools = AsyncMock(
            return_value=AIMessage(content="General response")
        )

        with patch(
            "app.agents.specialized.MCPClient"
        ) as mock_mcp_client, patch(
            "app.agents.specialized.ToolRegistry"
        ) as mock_tool_registry:
            mock_mcp_client.return_value.list_tools = AsyncMock(return_value=[])
            mock_tool_registry.return_value.get_tools = MagicMock(return_value=[])

            agent = GeneralAgent(llm_service=mock_llm_service)
            result = await agent.run("Hello", [])

        assert result["message"] == "General response"
        assert result["agent"] == "general"

    @pytest.mark.asyncio
    async def test_code_agent_run(self) -> None:
        """Test CodeAgent run method."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat_with_tools = AsyncMock(
            return_value=AIMessage(content="Code response")
        )

        with patch(
            "app.agents.specialized.MCPClient"
        ) as mock_mcp_client, patch(
            "app.agents.specialized.ToolRegistry"
        ) as mock_tool_registry:
            mock_mcp_client.return_value.list_tools = AsyncMock(return_value=[])
            mock_tool_registry.return_value.get_tools = MagicMock(return_value=[])

            agent = CodeAgent(llm_service=mock_llm_service)
            result = await agent.run("Write a function", [])

        assert result["message"] == "Code response"
        assert result["agent"] == "code"

    @pytest.mark.asyncio
    async def test_research_agent_run(self) -> None:
        """Test ResearchAgent run method."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat_with_tools = AsyncMock(
            return_value=AIMessage(content="Research response")
        )

        with patch(
            "app.agents.specialized.MCPClient"
        ) as mock_mcp_client, patch(
            "app.agents.specialized.ToolRegistry"
        ) as mock_tool_registry:
            mock_mcp_client.return_value.list_tools = AsyncMock(return_value=[])
            mock_tool_registry.return_value.get_tools = MagicMock(return_value=[])

            agent = ResearchAgent(llm_service=mock_llm_service)
            result = await agent.run("What is quantum computing?", [])

        assert result["message"] == "Research response"
        assert result["agent"] == "research"

    @pytest.mark.asyncio
    async def test_creative_agent_run(self) -> None:
        """Test CreativeAgent run method."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat = AsyncMock(return_value="Creative response")

        agent = CreativeAgent(llm_service=mock_llm_service)
        result = await agent.run("Write a poem", [])

        assert result["message"] == "Creative response"
        assert result["agent"] == "creative"

    @pytest.mark.asyncio
    async def test_code_agent_filters_tools(self) -> None:
        """Test CodeAgent filters to code-relevant tools."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat_with_tools = AsyncMock(
            return_value=AIMessage(content="Code response")
        )

        all_tools = [
            {"function": {"name": "read_file"}},
            {"function": {"name": "write_file"}},
            {"function": {"name": "run_command"}},
            {"function": {"name": "get_weather"}},
            {"function": {"name": "search_web"}},
        ]

        with patch(
            "app.agents.specialized.MCPClient"
        ) as mock_mcp_client, patch(
            "app.agents.specialized.ToolRegistry"
        ) as mock_tool_registry:
            mock_mcp_client.return_value.list_tools = AsyncMock(return_value=all_tools)
            mock_tool_registry.return_value.get_tools = MagicMock(return_value=[])

            agent = CodeAgent(llm_service=mock_llm_service)
            await agent.run("Fix my bug", [])

            tool_names = {
                t["function"]["name"] for t in agent.tools
            }
            assert "read_file" in tool_names
            assert "write_file" in tool_names
            assert "run_command" in tool_names
            assert "get_weather" not in tool_names
            assert "search_web" not in tool_names

    @pytest.mark.asyncio
    async def test_research_agent_filters_tools(self) -> None:
        """Test ResearchAgent filters to research-relevant tools."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat_with_tools = AsyncMock(
            return_value=AIMessage(content="Research response")
        )

        all_tools = [
            {"function": {"name": "search_web"}},
            {"function": {"name": "fetch_url"}},
            {"function": {"name": "get_weather"}},
            {"function": {"name": "read_file"}},
        ]

        with patch(
            "app.agents.specialized.MCPClient"
        ) as mock_mcp_client, patch(
            "app.agents.specialized.ToolRegistry"
        ) as mock_tool_registry:
            mock_mcp_client.return_value.list_tools = AsyncMock(return_value=all_tools)
            mock_tool_registry.return_value.get_tools = MagicMock(return_value=[])

            agent = ResearchAgent(llm_service=mock_llm_service)
            await agent.run("Research topic", [])

            tool_names = {
                t["function"]["name"] for t in agent.tools
            }
            assert "search_web" in tool_names
            assert "fetch_url" in tool_names
            assert "get_weather" in tool_names
            assert "read_file" not in tool_names


class TestOrchestrator:
    """Tests for Orchestrator."""

    @pytest.mark.asyncio
    async def test_orchestrator_process(self) -> None:
        """Test that orchestrator processes a message."""
        mock_router = MagicMock()
        mock_router.route = AsyncMock(return_value="general")

        mock_general_agent = MagicMock()
        mock_general_agent.run = AsyncMock(
            return_value={"message": "Hello!", "agent": "general"}
        )

        orchestrator = Orchestrator(
            router=mock_router,
            general_agent=mock_general_agent,
        )

        result = await orchestrator.process(
            user_id="user-1", message="Hi", session_id="session-1"
        )

        assert result["message"] == "Hello!"
        assert result["agent_used"] == "general"
        assert result["session_id"] == "session-1"

    @pytest.mark.asyncio
    async def test_orchestrator_maintains_history(self) -> None:
        """Test that orchestrator maintains conversation history across turns."""
        mock_router = MagicMock()
        mock_router.route = AsyncMock(return_value="general")

        mock_general_agent = MagicMock()
        mock_general_agent.run = AsyncMock(
            side_effect=[
                {"message": "Response 1", "agent": "general"},
                {"message": "Response 2", "agent": "general"},
            ]
        )

        orchestrator = Orchestrator(
            router=mock_router,
            general_agent=mock_general_agent,
        )

        await orchestrator.process(
            user_id="user-1", message="Message 1", session_id="session-1"
        )
        await orchestrator.process(
            user_id="user-1", message="Message 2", session_id="session-1"
        )

        history = orchestrator.get_history("session-1")
        assert len(history) == 4  # 2 HumanMessages + 2 AIMessages
        assert isinstance(history[0], HumanMessage)
        assert history[0].content == "Message 1"
        assert isinstance(history[1], AIMessage)
        assert history[1].content == "Response 1"
        assert isinstance(history[2], HumanMessage)
        assert history[2].content == "Message 2"
        assert isinstance(history[3], AIMessage)
        assert history[3].content == "Response 2"

    @pytest.mark.asyncio
    async def test_orchestrator_history_limit(self) -> None:
        """Test that orchestrator keeps only the last N messages."""
        mock_router = MagicMock()
        mock_router.route = AsyncMock(return_value="general")

        mock_general_agent = MagicMock()
        mock_general_agent.run = AsyncMock(
            side_effect=[
                {"message": f"Response {i}", "agent": "general"}
                for i in range(MAX_HISTORY + 2)
            ]
        )

        orchestrator = Orchestrator(
            router=mock_router,
            general_agent=mock_general_agent,
        )

        for i in range(MAX_HISTORY + 2):
            await orchestrator.process(
                user_id="user-1",
                message=f"Message {i}",
                session_id="session-1",
            )

        history = orchestrator.get_history("session-1")
        assert len(history) == MAX_HISTORY
        # Each turn adds 2 messages. With MAX_HISTORY + 2 turns (24 messages),
        # the last MAX_HISTORY (10) are kept. First 14 messages (7 turns) dropped.
        assert history[0].content == "Message 7"
        assert history[-1].content == f"Response {MAX_HISTORY + 1}"

    @pytest.mark.asyncio
    async def test_orchestrator_tracks_agent_usage(self) -> None:
        """Test that orchestrator tracks which agent handled each turn."""
        mock_router = MagicMock()
        mock_router.route = AsyncMock(
            side_effect=["general", "code", "research"]
        )

        mock_general_agent = MagicMock()
        mock_general_agent.run = AsyncMock(
            return_value={"message": "General!", "agent": "general"}
        )

        mock_code_agent = MagicMock()
        mock_code_agent.run = AsyncMock(
            return_value={"message": "Code!", "agent": "code"}
        )

        mock_research_agent = MagicMock()
        mock_research_agent.run = AsyncMock(
            return_value={"message": "Research!", "agent": "research"}
        )

        orchestrator = Orchestrator(
            router=mock_router,
            general_agent=mock_general_agent,
            code_agent=mock_code_agent,
            research_agent=mock_research_agent,
        )

        await orchestrator.process(
            user_id="user-1", message="Hi", session_id="session-1"
        )
        await orchestrator.process(
            user_id="user-1", message="Fix bug", session_id="session-1"
        )
        await orchestrator.process(
            user_id="user-1", message="Lookup fact", session_id="session-1"
        )

        usage = orchestrator.get_agent_usage("session-1")
        assert usage == ["general", "code", "research"]

    @pytest.mark.asyncio
    async def test_orchestrator_generates_session_id(self) -> None:
        """Test that orchestrator generates a session_id if not provided."""
        mock_router = MagicMock()
        mock_router.route = AsyncMock(return_value="general")

        mock_general_agent = MagicMock()
        mock_general_agent.run = AsyncMock(
            return_value={"message": "Hello!", "agent": "general"}
        )

        orchestrator = Orchestrator(
            router=mock_router,
            general_agent=mock_general_agent,
        )

        result = await orchestrator.process(
            user_id="user-1", message="Hi", session_id=None
        )

        assert result["session_id"] is not None
        assert len(result["session_id"]) > 0


class TestOrchestratorHandoff:
    """Tests for agent handoff behavior."""

    @pytest.mark.asyncio
    async def test_two_messages_routed_to_different_agents(self) -> None:
        """Test that two messages can be routed to different agents."""
        mock_router = MagicMock()
        mock_router.route = AsyncMock(
            side_effect=["creative", "code"]
        )

        mock_creative_agent = MagicMock()
        mock_creative_agent.run = AsyncMock(
            return_value={"message": "A poem", "agent": "creative"}
        )

        mock_code_agent = MagicMock()
        mock_code_agent.run = AsyncMock(
            return_value={"message": "def hello(): pass", "agent": "code"}
        )

        orchestrator = Orchestrator(
            router=mock_router,
            creative_agent=mock_creative_agent,
            code_agent=mock_code_agent,
        )

        result1 = await orchestrator.process(
            user_id="user-1", message="Write a poem", session_id="session-1"
        )
        result2 = await orchestrator.process(
            user_id="user-1", message="Write a function", session_id="session-1"
        )

        assert result1["agent_used"] == "creative"
        assert result2["agent_used"] == "code"
        assert mock_creative_agent.run.await_count == 1
        assert mock_code_agent.run.await_count == 1

        # Verify history contains both interactions
        history = orchestrator.get_history("session-1")
        assert len(history) == 4
