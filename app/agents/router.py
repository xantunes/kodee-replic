"""Agent router for classifying user messages and selecting the appropriate agent."""

from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.llm.llm_service import LLMService
from app.llm.model_resolver import resolve_model

ROUTING_PROMPT = (
    "Given the user message, classify into one of: "
    "general (chitchat, simple questions), "
    "code (programming, debugging), "
    "research (facts, data lookup), "
    "creative (writing, ideas), "
    "data (data analysis, CSV/JSON processing, charts), "
    "image (image generation prompts, vision tasks). "
    "Respond with ONLY the agent name."
)

AVAILABLE_AGENTS = {"general", "code", "research", "creative", "data", "image"}


class AgentRouter:
    """Routes user messages to the appropriate specialized agent."""

    def __init__(self, llm_service: LLMService | None = None) -> None:
        """Initialize the agent router.

        Args:
            llm_service: Optional LLMService instance for classification.
        """
        self.llm_service = llm_service or LLMService(model=resolve_model("router"))

    async def route(self, message: str, history: List[BaseMessage]) -> str:
        """Classify the user message and return the agent name.

        Args:
            message: The current user message.
            history: Previous messages in the conversation (unused but kept for API consistency).

        Returns:
            Name of the agent that should handle the message.
        """
        classification_messages: List[BaseMessage] = [
            SystemMessage(content=ROUTING_PROMPT),
            HumanMessage(content=message),
        ]
        result = await self.llm_service.chat(classification_messages)
        agent_name = result.strip().lower()

        if agent_name not in AVAILABLE_AGENTS:
            return "general"
        return agent_name
