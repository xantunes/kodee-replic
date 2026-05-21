"""LLM service for interacting with OpenAI or Azure OpenAI via LangChain."""

from typing import Any, Dict, List

from langchain_core.messages import AIMessage, BaseMessage

from app.config import settings


def _create_llm(model_override: str = "") -> Any:
    """Create the appropriate LLM client based on configuration.

    Args:
        model_override: Specific model/deployment to use. Falls back to
            settings.OPENAI_MODEL or settings.AZURE_OPENAI_DEPLOYMENT.

    Returns:
        ChatOpenAI or AzureChatOpenAI instance.
    """
    if settings.AZURE_OPENAI_ENDPOINT:
        from langchain_openai import AzureChatOpenAI

        deployment = model_override or settings.AZURE_OPENAI_DEPLOYMENT or settings.OPENAI_MODEL
        return AzureChatOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_deployment=deployment,
            temperature=settings.OPENAI_TEMPERATURE,
        )

    from langchain_openai import ChatOpenAI

    model = model_override or settings.OPENAI_MODEL
    return ChatOpenAI(
        model=model,
        temperature=settings.OPENAI_TEMPERATURE,
        api_key=settings.OPENAI_API_KEY,
    )


class LLMService:
    """Service for interacting with the LLM."""

    def __init__(self, model: str = "") -> None:
        """Initialize the LLM client.

        Args:
            model: Optional model override (e.g. 'gpt-4.1-mini').
        """
        self.llm = _create_llm(model_override=model)

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
