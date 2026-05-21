"""Specialized agents for the Kodee multi-agent system."""

from typing import Any, Dict, List

from langchain_core.messages import BaseMessage

from app.agents.base import BaseAgent
from app.llm.llm_service import LLMService
from app.llm.prompts import build_messages
from app.llm.tool_registry import ToolRegistry
from app.mcp.client import MCPClient


class GeneralAgent(BaseAgent):
    """Agent for general questions and chitchat."""

    name = "general"
    system_prompt = (
        "You are Kodee, a helpful general-purpose assistant. "
        "You provide clear, concise, and accurate responses to everyday questions. "
        "You can use available tools when they help answer the user's question."
    )

    def __init__(
        self,
        llm_service: LLMService | None = None,
        tool_registry: ToolRegistry | None = None,
        mcp_client: MCPClient | None = None,
    ) -> None:
        """Initialize the general agent.

        Args:
            llm_service: LLM service for generating responses.
            tool_registry: Local tool registry.
            mcp_client: MCP client for external tools.
        """
        self.llm_service = llm_service or LLMService()
        self.tool_registry = tool_registry or ToolRegistry()
        self.mcp_client = mcp_client or MCPClient()
        self.tools: List[Dict[str, Any]] = []

    async def run(
        self, message: str, history: List[BaseMessage]
    ) -> Dict[str, Any]:
        """Process a general user message.

        Args:
            message: The current user message.
            history: Previous messages in the conversation.

        Returns:
            Dictionary with the agent's response text.
        """
        messages = build_messages(user_message=message, history=history)
        local_tools = self.tool_registry.get_tools()
        mcp_tools = await self.mcp_client.list_tools()
        self.tools = local_tools + mcp_tools

        response = await self.llm_service.chat_with_tools(messages, self.tools)
        return {"message": str(response.content), "agent": self.name}


class CodeAgent(BaseAgent):
    """Agent for programming and debugging help."""

    name = "code"
    system_prompt = (
        "You are Kodee, an expert programming assistant. "
        "You write clean, efficient, and well-documented code. "
        "You help with debugging, code review, architecture decisions, and explaining concepts. "
        "When providing code, include explanations and best practices."
    )

    CODE_TOOL_NAMES = {"read_file", "write_file", "run_command", "calculate", "search_files"}

    def __init__(
        self,
        llm_service: LLMService | None = None,
        tool_registry: ToolRegistry | None = None,
        mcp_client: MCPClient | None = None,
    ) -> None:
        """Initialize the code agent.

        Args:
            llm_service: LLM service for generating responses.
            tool_registry: Local tool registry.
            mcp_client: MCP client for external tools.
        """
        self.llm_service = llm_service or LLMService()
        self.tool_registry = tool_registry or ToolRegistry()
        self.mcp_client = mcp_client or MCPClient()
        self.tools: List[Dict[str, Any]] = []

    async def run(
        self, message: str, history: List[BaseMessage]
    ) -> Dict[str, Any]:
        """Process a code-related user message.

        Args:
            message: The current user message.
            history: Previous messages in the conversation.

        Returns:
            Dictionary with the agent's response text.
        """
        messages = build_messages(user_message=message, history=history)
        local_tools = self.tool_registry.get_tools()
        mcp_tools = await self.mcp_client.list_tools()
        all_tools = local_tools + mcp_tools

        # Filter to code-relevant tools
        self.tools = [
            t for t in all_tools
            if t.get("function", {}).get("name", "") in self.CODE_TOOL_NAMES
        ]

        response = await self.llm_service.chat_with_tools(messages, self.tools)
        return {"message": str(response.content), "agent": self.name}


class ResearchAgent(BaseAgent):
    """Agent for factual research and data lookup."""

    name = "research"
    system_prompt = (
        "You are Kodee, a thorough research assistant. "
        "You prioritize accuracy and cite sources when possible. "
        "You gather comprehensive information and present it in an organized manner. "
        "When uncertain, you acknowledge limitations rather than guessing."
    )

    RESEARCH_TOOL_NAMES = {"search_web", "fetch_url", "get_weather", "get_time", "calculate"}

    def __init__(
        self,
        llm_service: LLMService | None = None,
        tool_registry: ToolRegistry | None = None,
        mcp_client: MCPClient | None = None,
    ) -> None:
        """Initialize the research agent.

        Args:
            llm_service: LLM service for generating responses.
            tool_registry: Local tool registry.
            mcp_client: MCP client for external tools.
        """
        self.llm_service = llm_service or LLMService()
        self.tool_registry = tool_registry or ToolRegistry()
        self.mcp_client = mcp_client or MCPClient()
        self.tools: List[Dict[str, Any]] = []

    async def run(
        self, message: str, history: List[BaseMessage]
    ) -> Dict[str, Any]:
        """Process a research-related user message.

        Args:
            message: The current user message.
            history: Previous messages in the conversation.

        Returns:
            Dictionary with the agent's response text.
        """
        messages = build_messages(user_message=message, history=history)
        local_tools = self.tool_registry.get_tools()
        mcp_tools = await self.mcp_client.list_tools()
        all_tools = local_tools + mcp_tools

        # Filter to research-relevant tools
        self.tools = [
            t for t in all_tools
            if t.get("function", {}).get("name", "") in self.RESEARCH_TOOL_NAMES
        ]

        response = await self.llm_service.chat_with_tools(messages, self.tools)
        return {"message": str(response.content), "agent": self.name}


class CreativeAgent(BaseAgent):
    """Agent for creative writing and ideas."""

    name = "creative"
    system_prompt = (
        "You are Kodee, a creative writing assistant. "
        "You generate imaginative, engaging, and original content. "
        "You help with storytelling, brainstorming, poetry, marketing copy, and creative projects. "
        "You encourage the user's creativity and offer diverse perspectives."
    )

    def __init__(
        self,
        llm_service: LLMService | None = None,
    ) -> None:
        """Initialize the creative agent.

        Args:
            llm_service: LLM service for generating responses.
        """
        self.llm_service = llm_service or LLMService()
        self.tools: List[Dict[str, Any]] = []

    async def run(
        self, message: str, history: List[BaseMessage]
    ) -> Dict[str, Any]:
        """Process a creative user message.

        Args:
            message: The current user message.
            history: Previous messages in the conversation.

        Returns:
            Dictionary with the agent's response text.
        """
        messages = build_messages(user_message=message, history=history)
        response = await self.llm_service.chat(messages)
        return {"message": response, "agent": self.name}
