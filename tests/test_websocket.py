"""WebSocket-specific tests for the Kodee Replica chat API."""

from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from app.main import app as fastapi_app
from app.services.chat_service import ChatService


class TestWebSocket:
    """Tests for the WebSocket endpoint."""

    def test_websocket_connect_and_chat(self) -> None:
        """Connect to WebSocket, send a message, and receive a response."""
        with patch.object(
            ChatService, "process_message", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = {
                "message": "WebSocket hello!",
                "actions": [],
                "session_id": "ws-sess-1",
            }

            client = TestClient(fastapi_app)
            with client.websocket_connect("/ws/user-1") as ws:
                ws.send_json({"message": "Hello", "session_id": None})
                data = ws.receive_json()

            assert data["message"] == "WebSocket hello!"
            assert data["session_id"] == "ws-sess-1"
            assert data["actions"] == []

    def test_websocket_disconnect(self) -> None:
        """Client disconnect should close the WebSocket gracefully."""
        with patch.object(
            ChatService, "process_message", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = {
                "message": "OK",
                "actions": [],
                "session_id": "ws-sess-2",
            }

            client = TestClient(fastapi_app)
            with client.websocket_connect("/ws/user-2") as ws:
                ws.send_json({"message": "Hi", "session_id": None})
                ws.receive_json()
                # Normal close is handled by exiting the context manager

            # If we reach here without exception, disconnect was graceful
            assert True

    def test_websocket_multiple_messages(self) -> None:
        """Send multiple messages over the same WebSocket connection."""
        responses = [
            {
                "message": "Reply 1",
                "actions": [],
                "session_id": "ws-sess-3",
            },
            {
                "message": "Reply 2",
                "actions": [{"tool": "calculate", "result": "4"}],
                "session_id": "ws-sess-3",
            },
            {
                "message": "Reply 3",
                "actions": [],
                "session_id": "ws-sess-3",
            },
        ]

        with patch.object(
            ChatService, "process_message", new_callable=AsyncMock
        ) as mock_process:
            mock_process.side_effect = responses

            client = TestClient(fastapi_app)
            with client.websocket_connect("/ws/user-3") as ws:
                ws.send_json({"message": "Msg 1", "session_id": "ws-sess-3"})
                data1 = ws.receive_json()

                ws.send_json({"message": "Msg 2", "session_id": "ws-sess-3"})
                data2 = ws.receive_json()

                ws.send_json({"message": "Msg 3", "session_id": "ws-sess-3"})
                data3 = ws.receive_json()

            assert data1["message"] == "Reply 1"
            assert data2["message"] == "Reply 2"
            assert len(data2["actions"]) == 1
            assert data3["message"] == "Reply 3"

            assert mock_process.await_count == 3
