"""Integration tests for the Kodee Replica chat API."""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from langchain_core.messages import AIMessage
from starlette.testclient import TestClient

from app.agents.orchestrator import Orchestrator
from app.agents.router import AgentRouter
from app.llm.llm_service import LLMService
from app.main import app as fastapi_app
from app.services.chat_service import ChatService


class TestIntegrationChat:
    """Integration tests for the HTTP chat endpoint."""

    @pytest.mark.asyncio
    async def test_full_chat_flow(self, client: AsyncClient) -> None:
        """POST /chat should return a well-formed response."""
        with patch.object(
            ChatService, "process_message", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = {
                "message": "Hello from Kodee!",
                "actions": [],
                "session_id": "session-abc-123",
            }

            payload = {
                "user_id": "user-123",
                "message": "Hello, Kodee!",
            }
            response = await client.post("/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "session_id" in data
        assert "actions" in data
        assert isinstance(data["message"], str)
        assert isinstance(data["session_id"], str)
        assert isinstance(data["actions"], list)

    @pytest.mark.asyncio
    async def test_chat_with_tool_call(self, client: AsyncClient) -> None:
        """Mock LLM returning a tool call and verify actions in the response."""
        with patch.object(
            ChatService, "process_message", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = {
                "message": "The result is 42.",
                "actions": [
                    {
                        "tool": "calculate",
                        "args": {"expression": "6 * 7"},
                        "result": "42",
                        "source": "local",
                    }
                ],
                "session_id": "session-tool-123",
            }

            payload = {
                "user_id": "user-456",
                "message": "What is 6 times 7?",
            }
            response = await client.post("/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "The result is 42."
        assert len(data["actions"]) == 1
        assert data["actions"][0]["tool"] == "calculate"
        assert data["actions"][0]["result"] == "42"

    @pytest.mark.asyncio
    async def test_chat_preserves_session_id(self, client: AsyncClient) -> None:
        """Passing session_id should preserve it in the response."""
        with patch.object(
            ChatService, "process_message", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = {
                "message": "Follow-up response",
                "actions": [],
                "session_id": "existing-session",
            }

            payload = {
                "user_id": "user-789",
                "message": "Follow-up question",
                "session_id": "existing-session",
            }
            response = await client.post("/chat", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "existing-session"


class TestIntegrationWebSocket:
    """Integration tests for the WebSocket chat endpoint."""

    def test_websocket_chat(self) -> None:
        """Connect to /ws/{user_id}, send a message, and receive a response."""
        with patch.object(
            ChatService, "process_message", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = {
                "message": "WebSocket response",
                "actions": [],
                "session_id": "ws-session-1",
            }

            client = TestClient(fastapi_app)
            with client.websocket_connect("/ws/user-ws-1") as ws:
                ws.send_json({"message": "Hello via WS", "session_id": None})
                data = ws.receive_json()

            assert "message" in data
            assert data["message"] == "WebSocket response"
            assert "session_id" in data

    def test_websocket_multiple_messages(self) -> None:
        """Send multiple messages over the same WebSocket and verify responses."""
        responses = [
            {"message": "Response 1", "actions": [], "session_id": "ws-session-2"},
            {"message": "Response 2", "actions": [], "session_id": "ws-session-2"},
        ]

        with patch.object(
            ChatService, "process_message", new_callable=AsyncMock
        ) as mock_process:
            mock_process.side_effect = responses

            client = TestClient(fastapi_app)
            with client.websocket_connect("/ws/user-ws-2") as ws:
                ws.send_json({"message": "Message 1", "session_id": "ws-session-2"})
                data1 = ws.receive_json()

                ws.send_json({"message": "Message 2", "session_id": "ws-session-2"})
                data2 = ws.receive_json()

            assert data1["message"] == "Response 1"
            assert data2["message"] == "Response 2"


class TestIntegrationMultiTurn:
    """Integration tests for multi-turn conversation behavior."""

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self) -> None:
        """Multiple messages in the same session should maintain history."""
        mock_router = MagicMock()
        mock_router.route = AsyncMock(return_value="general")

        mock_handoff = MagicMock()
        mock_handoff.is_seeking_human = AsyncMock(return_value=False)

        mock_general_agent = MagicMock()
        mock_general_agent.run = AsyncMock(
            side_effect=[
                {"message": "Turn 1 reply", "agent": "general"},
                {"message": "Turn 2 reply", "agent": "general"},
            ]
        )

        orchestrator = Orchestrator(
            router=mock_router,
            handoff_classifier=mock_handoff,
            general_agent=mock_general_agent,
        )

        result1 = await orchestrator.process(
            user_id="user-mt", message="First message", session_id="mt-session"
        )
        result2 = await orchestrator.process(
            user_id="user-mt", message="Second message", session_id="mt-session"
        )

        assert result1["message"] == "Turn 1 reply"
        assert result2["message"] == "Turn 2 reply"

        history = orchestrator.get_history("mt-session")
        assert len(history) == 4  # 2 Human + 2 AI messages

    @pytest.mark.asyncio
    async def test_agent_routing(self) -> None:
        """Mock router to route to different agents and verify agent_used."""
        mock_router = MagicMock()
        mock_router.route = AsyncMock(
            side_effect=["dns", "backup", "monitoring"]
        )

        mock_handoff = MagicMock()
        mock_handoff.is_seeking_human = AsyncMock(return_value=False)

        mock_dns_agent = MagicMock()
        mock_dns_agent.run = AsyncMock(
            return_value={"message": "DNS insight", "agent": "dns"}
        )

        mock_backup_agent = MagicMock()
        mock_backup_agent.run = AsyncMock(
            return_value={"message": "Backup complete", "agent": "backup"}
        )

        mock_monitoring_agent = MagicMock()
        mock_monitoring_agent.run = AsyncMock(
            return_value={"message": "Server is healthy", "agent": "monitoring"}
        )

        orchestrator = Orchestrator(
            router=mock_router,
            handoff_classifier=mock_handoff,
            dns_agent=mock_dns_agent,
            backup_agent=mock_backup_agent,
            monitoring_agent=mock_monitoring_agent,
        )

        result1 = await orchestrator.process(
            user_id="user-1", message="Create a DNS record", session_id="route-session"
        )
        result2 = await orchestrator.process(
            user_id="user-1", message="Start a backup", session_id="route-session"
        )
        result3 = await orchestrator.process(
            user_id="user-1", message="Check server health", session_id="route-session"
        )

        assert result1["agent_used"] == "dns"
        assert result2["agent_used"] == "backup"
        assert result3["agent_used"] == "monitoring"

        usage = orchestrator.get_agent_usage("route-session")
        assert usage == ["dns", "backup", "monitoring"]
