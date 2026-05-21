"""Tests for the multi-agent router and handoff system."""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.agents.base_agent import BaseAgent
from app.agents.handoff import HandoffClassifier
from app.agents.orchestrator import MAX_HISTORY, Orchestrator
from app.agents.router import AVAILABLE_AGENTS, AgentRouter
from app.agents.specialized import BackupAgent, DNSAgent, GeneralAgent, MonitoringAgent


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
        mock_llm_service.chat = AsyncMock(return_value="dns")

        router = AgentRouter(llm_service=mock_llm_service)
        result = await router.route("Create an A record for example.com", [])

        assert result in AVAILABLE_AGENTS
        assert result == "dns"

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
        mock_llm_service.chat = AsyncMock(return_value="  MONITORING  ")

        router = AgentRouter(llm_service=mock_llm_service)
        result = await router.route("Is my server down?", [])

        assert result == "monitoring"

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

    def test_dns_agent_system_prompt(self) -> None:
        """Test DNSAgent has the correct system prompt."""
        agent = DNSAgent()
        assert "dns" in agent.system_prompt.lower()
        assert agent.name == "dns"

    def test_backup_agent_system_prompt(self) -> None:
        """Test BackupAgent has the correct system prompt."""
        agent = BackupAgent()
        assert "backup" in agent.system_prompt.lower()
        assert agent.name == "backup"

    def test_monitoring_agent_system_prompt(self) -> None:
        """Test MonitoringAgent has the correct system prompt."""
        agent = MonitoringAgent()
        assert "monitoring" in agent.system_prompt.lower()
        assert agent.name == "monitoring"

    @pytest.mark.asyncio
    async def test_general_agent_run(self) -> None:
        """Test GeneralAgent run method."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat_with_tools_react = AsyncMock(
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
    async def test_dns_agent_run(self) -> None:
        """Test DNSAgent run method."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat_with_tools_react = AsyncMock(
            return_value=AIMessage(content="DNS response")
        )

        with patch(
            "app.agents.specialized.MCPClient"
        ) as mock_mcp_client, patch(
            "app.agents.specialized.ToolRegistry"
        ) as mock_tool_registry:
            mock_mcp_client.return_value.list_tools = AsyncMock(return_value=[])
            mock_tool_registry.return_value.get_tools = MagicMock(return_value=[])

            agent = DNSAgent(llm_service=mock_llm_service)
            result = await agent.run("Create an A record", [])

        assert result["message"] == "DNS response"
        assert result["agent"] == "dns"

    @pytest.mark.asyncio
    async def test_backup_agent_run(self) -> None:
        """Test BackupAgent run method."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat_with_tools_react = AsyncMock(
            return_value=AIMessage(content="Backup response")
        )

        with patch(
            "app.agents.specialized.MCPClient"
        ) as mock_mcp_client, patch(
            "app.agents.specialized.ToolRegistry"
        ) as mock_tool_registry:
            mock_mcp_client.return_value.list_tools = AsyncMock(return_value=[])
            mock_tool_registry.return_value.get_tools = MagicMock(return_value=[])

            agent = BackupAgent(llm_service=mock_llm_service)
            result = await agent.run("Create a backup", [])

        assert result["message"] == "Backup response"
        assert result["agent"] == "backup"

    @pytest.mark.asyncio
    async def test_monitoring_agent_run(self) -> None:
        """Test MonitoringAgent run method."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat_with_tools_react = AsyncMock(
            return_value=AIMessage(content="Monitoring response")
        )

        with patch(
            "app.agents.specialized.MCPClient"
        ) as mock_mcp_client, patch(
            "app.agents.specialized.ToolRegistry"
        ) as mock_tool_registry:
            mock_mcp_client.return_value.list_tools = AsyncMock(return_value=[])
            mock_tool_registry.return_value.get_tools = MagicMock(return_value=[])

            agent = MonitoringAgent(llm_service=mock_llm_service)
            result = await agent.run("Check server health", [])

        assert result["message"] == "Monitoring response"
        assert result["agent"] == "monitoring"

    @pytest.mark.asyncio
    async def test_dns_agent_filters_tools(self) -> None:
        """Test DNSAgent filters to DNS-relevant tools."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat_with_tools_react = AsyncMock(
            return_value=AIMessage(content="DNS response")
        )

        all_tools = [
            {"function": {"name": "create_record"}},
            {"function": {"name": "list_records"}},
            {"function": {"name": "delete_record"}},
            {"function": {"name": "get_weather"}},
            {"function": {"name": "create_backup"}},
        ]

        with patch(
            "app.agents.specialized.MCPClient"
        ) as mock_mcp_client, patch(
            "app.agents.specialized.ToolRegistry"
        ) as mock_tool_registry:
            mock_mcp_client.return_value.list_tools = AsyncMock(return_value=all_tools)
            mock_tool_registry.return_value.get_tools = MagicMock(return_value=[])

            agent = DNSAgent(llm_service=mock_llm_service)
            await agent.run("Create a record", [])

            tool_names = {
                t["function"]["name"] for t in agent.tools
            }
            assert "create_record" in tool_names
            assert "list_records" in tool_names
            assert "delete_record" in tool_names
            assert "get_weather" not in tool_names
            assert "create_backup" not in tool_names

    @pytest.mark.asyncio
    async def test_backup_agent_filters_tools(self) -> None:
        """Test BackupAgent filters to backup-relevant tools."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat_with_tools_react = AsyncMock(
            return_value=AIMessage(content="Backup response")
        )

        all_tools = [
            {"function": {"name": "create_backup"}},
            {"function": {"name": "restore_backup"}},
            {"function": {"name": "list_backups"}},
            {"function": {"name": "create_record"}},
        ]

        with patch(
            "app.agents.specialized.MCPClient"
        ) as mock_mcp_client, patch(
            "app.agents.specialized.ToolRegistry"
        ) as mock_tool_registry:
            mock_mcp_client.return_value.list_tools = AsyncMock(return_value=all_tools)
            mock_tool_registry.return_value.get_tools = MagicMock(return_value=[])

            agent = BackupAgent(llm_service=mock_llm_service)
            await agent.run("Restore backup", [])

            tool_names = {
                t["function"]["name"] for t in agent.tools
            }
            assert "create_backup" in tool_names
            assert "restore_backup" in tool_names
            assert "list_backups" in tool_names
            assert "create_record" not in tool_names

    @pytest.mark.asyncio
    async def test_monitoring_agent_filters_tools(self) -> None:
        """Test MonitoringAgent filters to monitoring-relevant tools."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat_with_tools_react = AsyncMock(
            return_value=AIMessage(content="Monitoring response")
        )

        all_tools = [
            {"function": {"name": "check_server_health"}},
            {"function": {"name": "get_website_status"}},
            {"function": {"name": "check_server_health"}},
            {"function": {"name": "create_backup"}},
        ]

        with patch(
            "app.agents.specialized.MCPClient"
        ) as mock_mcp_client, patch(
            "app.agents.specialized.ToolRegistry"
        ) as mock_tool_registry:
            mock_mcp_client.return_value.list_tools = AsyncMock(return_value=all_tools)
            mock_tool_registry.return_value.get_tools = MagicMock(return_value=[])

            agent = MonitoringAgent(llm_service=mock_llm_service)
            await agent.run("Is my site up?", [])

            tool_names = {
                t["function"]["name"] for t in agent.tools
            }
            assert "check_server_health" in tool_names
            assert "get_website_status" in tool_names
            assert "check_server_health" in tool_names
            assert "create_backup" not in tool_names


class TestHandoffClassifier:
    """Tests for HandoffClassifier."""

    @pytest.mark.asyncio
    async def test_detects_human_escalation_yes(self) -> None:
        """Test that handoff classifier returns True when LLM says yes."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat = AsyncMock(return_value="yes")

        classifier = HandoffClassifier(llm_service=mock_llm_service)
        result = await classifier.is_seeking_human("I want to speak to a human")

        assert result is True

    @pytest.mark.asyncio
    async def test_detects_human_escalation_no(self) -> None:
        """Test that handoff classifier returns False when LLM says no."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat = AsyncMock(return_value="no")

        classifier = HandoffClassifier(llm_service=mock_llm_service)
        result = await classifier.is_seeking_human("What is the weather?")

        assert result is False

    @pytest.mark.asyncio
    async def test_uses_handoff_prompt(self) -> None:
        """Test that handoff sends the correct prompt to the LLM."""
        mock_llm_service = MagicMock()
        mock_llm_service.chat = AsyncMock(return_value="no")

        classifier = HandoffClassifier(llm_service=mock_llm_service)
        await classifier.is_seeking_human("Hello")

        call_args = mock_llm_service.chat.await_args
        messages = call_args[0][0]
        assert len(messages) == 2
        assert "human" in messages[0].content.lower()
        assert "yes" in messages[0].content.lower()
        assert "no" in messages[0].content.lower()


class TestOrchestrator:
    """Tests for Orchestrator."""

    @pytest.mark.asyncio
    async def test_orchestrator_process(self) -> None:
        """Test that orchestrator processes a message."""
        mock_router = MagicMock()
        mock_router.route = AsyncMock(return_value="general")

        mock_handoff = MagicMock()
        mock_handoff.is_seeking_human = AsyncMock(return_value=False)

        mock_general_agent = MagicMock()
        mock_general_agent.run = AsyncMock(
            return_value={"message": "Hello!", "agent": "general"}
        )

        orchestrator = Orchestrator(
            router=mock_router,
            handoff_classifier=mock_handoff,
            general_agent=mock_general_agent,
        )

        result = await orchestrator.process(
            user_id="user-1", message="Hi", session_id="session-1"
        )

        assert result["message"] == "Hello!"
        assert result["agent_used"] == "general"
        assert result["session_id"] == "session-1"

    @pytest.mark.asyncio
    async def test_orchestrator_handles_handoff(self) -> None:
        """Test that orchestrator returns human handoff message when user seeks human."""
        mock_router = MagicMock()
        mock_handoff = MagicMock()
        mock_handoff.is_seeking_human = AsyncMock(return_value=True)

        orchestrator = Orchestrator(
            router=mock_router,
            handoff_classifier=mock_handoff,
        )

        result = await orchestrator.process(
            user_id="user-1", message="I want to speak to a human", session_id="session-1"
        )

        assert result["message"] == "I'm connecting you to a human agent..."
        assert result["agent_used"] == "human_handoff"
        assert result["session_id"] == "session-1"
        mock_router.route.assert_not_called()

    @pytest.mark.asyncio
    async def test_orchestrator_maintains_history(self) -> None:
        """Test that orchestrator maintains conversation history across turns."""
        mock_router = MagicMock()
        mock_router.route = AsyncMock(return_value="general")

        mock_handoff = MagicMock()
        mock_handoff.is_seeking_human = AsyncMock(return_value=False)

        mock_general_agent = MagicMock()
        mock_general_agent.run = AsyncMock(
            side_effect=[
                {"message": "Response 1", "agent": "general"},
                {"message": "Response 2", "agent": "general"},
            ]
        )

        orchestrator = Orchestrator(
            router=mock_router,
            handoff_classifier=mock_handoff,
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

        mock_handoff = MagicMock()
        mock_handoff.is_seeking_human = AsyncMock(return_value=False)

        mock_general_agent = MagicMock()
        mock_general_agent.run = AsyncMock(
            side_effect=[
                {"message": f"Response {i}", "agent": "general"}
                for i in range(MAX_HISTORY + 2)
            ]
        )

        orchestrator = Orchestrator(
            router=mock_router,
            handoff_classifier=mock_handoff,
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
            side_effect=["general", "dns", "backup"]
        )

        mock_handoff = MagicMock()
        mock_handoff.is_seeking_human = AsyncMock(return_value=False)

        mock_general_agent = MagicMock()
        mock_general_agent.run = AsyncMock(
            return_value={"message": "General!", "agent": "general"}
        )

        mock_dns_agent = MagicMock()
        mock_dns_agent.run = AsyncMock(
            return_value={"message": "DNS!", "agent": "dns"}
        )

        mock_backup_agent = MagicMock()
        mock_backup_agent.run = AsyncMock(
            return_value={"message": "Backup!", "agent": "backup"}
        )

        orchestrator = Orchestrator(
            router=mock_router,
            handoff_classifier=mock_handoff,
            general_agent=mock_general_agent,
            dns_agent=mock_dns_agent,
            backup_agent=mock_backup_agent,
        )

        await orchestrator.process(
            user_id="user-1", message="Hi", session_id="session-1"
        )
        await orchestrator.process(
            user_id="user-1", message="Create DNS record", session_id="session-1"
        )
        await orchestrator.process(
            user_id="user-1", message="Backup my server", session_id="session-1"
        )

        usage = orchestrator.get_agent_usage("session-1")
        assert usage == ["general", "dns", "backup"]

    @pytest.mark.asyncio
    async def test_orchestrator_generates_session_id(self) -> None:
        """Test that orchestrator generates a session_id if not provided."""
        mock_router = MagicMock()
        mock_router.route = AsyncMock(return_value="general")

        mock_handoff = MagicMock()
        mock_handoff.is_seeking_human = AsyncMock(return_value=False)

        mock_general_agent = MagicMock()
        mock_general_agent.run = AsyncMock(
            return_value={"message": "Hello!", "agent": "general"}
        )

        orchestrator = Orchestrator(
            router=mock_router,
            handoff_classifier=mock_handoff,
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
            side_effect=["dns", "backup"]
        )

        mock_handoff = MagicMock()
        mock_handoff.is_seeking_human = AsyncMock(return_value=False)

        mock_dns_agent = MagicMock()
        mock_dns_agent.run = AsyncMock(
            return_value={"message": "DNS record created", "agent": "dns"}
        )

        mock_backup_agent = MagicMock()
        mock_backup_agent.run = AsyncMock(
            return_value={"message": "Backup started", "agent": "backup"}
        )

        orchestrator = Orchestrator(
            router=mock_router,
            handoff_classifier=mock_handoff,
            dns_agent=mock_dns_agent,
            backup_agent=mock_backup_agent,
        )

        result1 = await orchestrator.process(
            user_id="user-1", message="Create a DNS record", session_id="session-1"
        )
        result2 = await orchestrator.process(
            user_id="user-1", message="Start a backup", session_id="session-1"
        )

        assert result1["agent_used"] == "dns"
        assert result2["agent_used"] == "backup"
        assert mock_dns_agent.run.await_count == 1
        assert mock_backup_agent.run.await_count == 1

        # Verify history contains both interactions
        history = orchestrator.get_history("session-1")
        assert len(history) == 4
