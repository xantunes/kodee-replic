"""LLM service for interacting with OpenAI or Azure OpenAI via LangChain."""

from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

from app.config import settings
from app.utils.security import DESTRUCTIVE_TOOLS

MAX_TOOL_ITERATIONS = 5

ToolExecutor = Callable[[str, Dict[str, Any]], Union[str, Awaitable[str]]]
ToolExecutedCallback = Callable[[str, Dict[str, Any], str, bool], Awaitable[None]]


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
    kwargs = {
        "model": model,
        "temperature": settings.OPENAI_TEMPERATURE,
        "api_key": settings.OPENAI_API_KEY,
    }
    if settings.OPENAI_API_BASE:
        kwargs["base_url"] = settings.OPENAI_API_BASE
    return ChatOpenAI(**kwargs)


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

    async def chat_with_tools_react(
        self,
        messages: List[BaseMessage],
        tools: List[Dict[str, Any]],
        execute_local_tool: Optional[ToolExecutor] = None,
        execute_mcp_tool: Optional[ToolExecutor] = None,
        on_tool_executed: Optional[ToolExecutedCallback] = None,
    ) -> AIMessage:
        """ReAct loop: chat with tools, execute tool calls, and return final response.

        Iterates up to MAX_TOOL_ITERATIONS, executing any tool_calls returned by
        the LLM and feeding results back into the conversation.

        Args:
            messages: List of LangChain messages.
            tools: List of tool definitions in OpenAI format.
            execute_local_tool: Callback for executing local registry tools.
            execute_mcp_tool: Callback for executing MCP server tools.
            on_tool_executed: Optional async callback invoked after each tool
                execution with (tool_name, args, result, success).

        Returns:
            Final AIMessage after all tool calls are resolved.
        """
        import inspect

        async def _exec(executor: Optional[ToolExecutor], name: str, args: Dict[str, Any]) -> str:
            if executor is None:
                return ""
            try:
                result = executor(name, args)
                if inspect.isawaitable(result):
                    result = await result
                return str(result)
            except Exception as e:
                return f"Error executing tool '{name}': {e}"

        try:
            llm_with_tools = self.llm.bind_tools(tools)
            current_messages = list(messages)

            for _ in range(MAX_TOOL_ITERATIONS):
                response = await llm_with_tools.ainvoke(current_messages)

                if not response.tool_calls:
                    return response

                current_messages.append(response)

                for tool_call in response.tool_calls:
                    name = tool_call.get("name", "")
                    args = tool_call.get("args", {})
                    tool_call_id = tool_call.get("id", "")

                    # Destructive actions require user confirmation
                    if name in DESTRUCTIVE_TOOLS and not args.get("confirmed"):
                        return AIMessage(
                            content=(
                                f"I need your confirmation before proceeding with `{name}`. "
                                f"This action may be destructive. Please confirm if you want to continue."
                            ),
                            tool_calls=[],
                        )

                    # Try local tool first, then MCP
                    result = await _exec(execute_local_tool, name, args)
                    success = not (result.startswith("Error") if result else True)
                    if not result or result.startswith("Error"):
                        mcp_result = await _exec(execute_mcp_tool, name, args)
                        if mcp_result and not mcp_result.startswith("Error"):
                            result = mcp_result
                            success = True
                    if not result:
                        result = f"Error: Tool '{name}' is not available."
                        success = False

                    # Real-time persistence of tool execution
                    if on_tool_executed is not None:
                        try:
                            await on_tool_executed(name, args, result, success)
                        except Exception:
                            pass

                    current_messages.append(
                        ToolMessage(content=result, tool_call_id=tool_call_id)
                    )

            # Max iterations reached — return last response
            return response
        except Exception as e:
            return AIMessage(content=f"I'm sorry, I encountered an error: {str(e)}")
