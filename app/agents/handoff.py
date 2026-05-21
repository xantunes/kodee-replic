"""Handoff classifier for detecting human escalation requests."""

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm.llm_service import LLMService
from app.llm.model_resolver import resolve_model


HANDOFF_PROMPT = (
    "Analyze if the user is asking to speak to a human, asking for a real person, "
    "or expressing frustration that requires human intervention. "
    "Respond with ONLY 'yes' or 'no'."
)


class HandoffClassifier:
    """Classifies whether a user message is seeking human support."""

    def __init__(self, llm_service: LLMService | None = None) -> None:
        """Initialize the handoff classifier.

        Args:
            llm_service: Optional LLMService instance for classification.
        """
        self.llm_service = llm_service or LLMService(model=resolve_model("handoff"))

    async def is_seeking_human(self, message: str) -> bool:
        """Determine if the user message indicates a desire for human support.

        Args:
            message: The current user message.

        Returns:
            True if the user wants human help, False otherwise.
        """
        classification_messages = [
            SystemMessage(content=HANDOFF_PROMPT),
            HumanMessage(content=message),
        ]
        result = await self.llm_service.chat(classification_messages)
        return result.strip().lower() == "yes"
