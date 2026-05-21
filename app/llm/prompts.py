"""System prompt templates for Kodee."""

from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage


SYSTEM_PROMPT = (
    "You are Kodee, a helpful AI assistant. "
    "You provide clear, concise, and accurate responses. "
    "When appropriate, you can use available tools to help answer user questions."
)


def build_messages(user_message: str, history: List[BaseMessage]) -> List[BaseMessage]:
    """Build a list of conversation messages including system prompt and history.

    Args:
        user_message: The current message from the user.
        history: Previous messages in the conversation.

    Returns:
        List of messages ready to send to the LLM.
    """
    messages: List[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
    messages.extend(history)
    messages.append(HumanMessage(content=user_message))
    return messages
