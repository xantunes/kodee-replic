"""LLM service for interacting with OpenAI via LangChain."""

from typing import Any, Dict, List

from langchain_core.messages import AIMessage, BaseMessage
from langchain_openai import ChatOpenAI

from app.config import settings


class LLMService:
    """Service for interacting with the LLM."""

    def __init__(self) -> None:
        """Initialize the LLM client."""
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            api_key=settings.OPENAI_API_KEY,
        )

    async def chat(self, messages: List[BaseMessage]) -> str:
        """Send messages to the LLM and return the response content.

        Args:
            messages: List of LangChain messages.

        Returns:
            Response content as a string, or an error message.
        """
        try:
            response = await self.llm.ainvoke(messages)
            return str(response.content)
        except Exception as e:
            return f"I'm sorry, I encountered an error communicating with the AI: {str(e)}"

    async def chat_with_tools(
        self, messages: List[BaseMessage], tools: List[Dict[str, Any]]
    ) -> AIMessage:
        """Send messages to the LLM with tools bound and return the full response.

        Args:
            messages: List of LangChain messages.
            tools: List of tool definitions in OpenAI format.

        Returns:
            AIMessage which may contain tool_calls.
        """
        try:
            llm_with_tools = self.llm.bind_tools(tools)
            response = await llm_with_tools.ainvoke(messages)
            return response
        except Exception as e:
            return AIMessage(content=f"I'm sorry, I encountered an error: {str(e)}")
