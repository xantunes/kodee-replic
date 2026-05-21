"""Specialized agents for the Kodee multi-agent system."""

from typing import Any, Dict, List

from langchain_core.messages import BaseMessage

from app.agents.base import BaseAgent
from app.llm.llm_service import LLMService
from app.llm.model_resolver import resolve_model
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
        self.llm_service = llm_service or LLMService(model=resolve_model("general"))
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


class DNSAgent(BaseAgent):
    """Agent for DNS management tasks."""

    name = "dns"
    system_prompt = (
        "You are Kodee, a DNS management specialist. "
        "You help users create DNS records, list existing records, and delete records. "
        "You understand A, AAAA, CNAME, MX, TXT, and NS records. "
        "Always confirm the domain and record details before making changes."
    )

    DNS_TOOL_NAMES = {
        "create_record",
        "list_records",
        "delete_record",
    }

    def __init__(
        self,
        llm_service: LLMService | None = None,
        tool_registry: ToolRegistry | None = None,
        mcp_client: MCPClient | None = None,
    ) -> None:
        """Initialize the DNS agent.

        Args:
            llm_service: LLM service for generating responses.
            tool_registry: Local tool registry.
            mcp_client: MCP client for external tools.
        """
        self.llm_service = llm_service or LLMService(model=resolve_model("dns"))
        self.tool_registry = tool_registry or ToolRegistry()
        self.mcp_client = mcp_client or MCPClient()
        self.tools: List[Dict[str, Any]] = []

    async def run(
        self, message: str, history: List[BaseMessage]
    ) -> Dict[str, Any]:
        """Process a DNS-related user message.

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

        # Filter to DNS-relevant tools
        self.tools = [
            t for t in all_tools
            if t.get("function", {}).get("name", "") in self.DNS_TOOL_NAMES
        ]

        response = await self.llm_service.chat_with_tools(messages, self.tools)
        return {"message": str(response.content), "agent": self.name}


class BackupAgent(BaseAgent):
    """Agent for backup and restore tasks."""

    name = "backup"
    system_prompt = (
        "You are Kodee, a backup and recovery specialist. "
        "You help users create backups, restore from backups, and list available backups. "
        "You provide guidance on backup strategies, retention policies, and disaster recovery. "
        "Always verify backup integrity and destination before proceeding."
    )

    BACKUP_TOOL_NAMES = {
        "create_backup",
        "restore_backup",
        "list_backups",
    }

    def __init__(
        self,
        llm_service: LLMService | None = None,
        tool_registry: ToolRegistry | None = None,
        mcp_client: MCPClient | None = None,
    ) -> None:
        """Initialize the backup agent.

        Args:
            llm_service: LLM service for generating responses.
            tool_registry: Local tool registry.
            mcp_client: MCP client for external tools.
        """
        self.llm_service = llm_service or LLMService(model=resolve_model("backup"))
        self.tool_registry = tool_registry or ToolRegistry()
        self.mcp_client = mcp_client or MCPClient()
        self.tools: List[Dict[str, Any]] = []

    async def run(
        self, message: str, history: List[BaseMessage]
    ) -> Dict[str, Any]:
        """Process a backup-related user message.

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

        # Filter to backup-relevant tools
        self.tools = [
            t for t in all_tools
            if t.get("function", {}).get("name", "") in self.BACKUP_TOOL_NAMES
        ]

        response = await self.llm_service.chat_with_tools(messages, self.tools)
        return {"message": str(response.content), "agent": self.name}


class MonitoringAgent(BaseAgent):
    """Agent for server and website monitoring tasks."""

    name = "monitoring"
    system_prompt = (
        "You are Kodee, an infrastructure monitoring specialist. "
        "You help users check server health, get website status, and monitor system metrics. "
        "You understand uptime checks, latency, CPU/memory usage, and alert thresholds. "
        "Provide actionable recommendations when issues are detected."
    )

    MONITORING_TOOL_NAMES = {
        "check_server_health",
        "get_website_status",
    }

    def __init__(
        self,
        llm_service: LLMService | None = None,
        tool_registry: ToolRegistry | None = None,
        mcp_client: MCPClient | None = None,
    ) -> None:
        """Initialize the monitoring agent.

        Args:
            llm_service: LLM service for generating responses.
            tool_registry: Local tool registry.
            mcp_client: MCP client for external tools.
        """
        self.llm_service = llm_service or LLMService(model=resolve_model("monitoring"))
        self.tool_registry = tool_registry or ToolRegistry()
        self.mcp_client = mcp_client or MCPClient()
        self.tools: List[Dict[str, Any]] = []

    async def run(
        self, message: str, history: List[BaseMessage]
    ) -> Dict[str, Any]:
        """Process a monitoring-related user message.

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

        # Filter to monitoring-relevant tools
        self.tools = [
            t for t in all_tools
            if t.get("function", {}).get("name", "") in self.MONITORING_TOOL_NAMES
        ]

        response = await self.llm_service.chat_with_tools(messages, self.tools)
        return {"message": str(response.content), "agent": self.name}
