"""Base agent class for the Kodee multi-agent system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from langchain_core.messages import BaseMessage


class BaseAgent(ABC):
    """Abstract base class for all specialized agents."""

    name: str = "base"
    system_prompt: str = "You are a helpful AI assistant."
    tools: List[Dict[str, Any]] = []

    @abstractmethod
    async def run(
        self, message: str, history: List[BaseMessage], session_id: str = ""
    ) -> Dict[str, Any]:
        """Process a user message and return a response.

        Args:
            message: The current user message.
            history: Previous messages in the conversation.
            session_id: Optional session identifier for persistence.

        Returns:
            Dictionary containing the agent's response.
        """
        ...
