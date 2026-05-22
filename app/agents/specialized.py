"""Specialized agents for the Kodee multi-agent system."""

from typing import Any, Dict, List

from langchain_core.messages import BaseMessage

from app.agents.base_agent import BaseAgent
from app.services.llm_service import LLMService
from app.llm.model_resolver import resolve_model
from app.llm.prompts import build_messages
from app.llm.tool_registry import ToolRegistry
from app.mcp.client import MCPClient
from app.mcp.fortigate_client import FortigateClientPool
from app.services.persistence import get_conversation_id_by_session, persist_tool_execution


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
        self, message: str, history: List[BaseMessage], session_id: str = ""
    ) -> Dict[str, Any]:
        """Process a general user message.

        Args:
            message: The current user message.
            history: Previous messages in the conversation.
            session_id: Optional session identifier for persistence.

        Returns:
            Dictionary with the agent's response text.
        """
        messages = build_messages(user_message=message, history=history)
        local_tools = self.tool_registry.get_tools()
        mcp_tools = await self.mcp_client.list_tools()
        self.tools = local_tools + mcp_tools

        async def _on_tool_executed(name: str, args: dict, result: str, success: bool) -> None:
            conv_id = await get_conversation_id_by_session(session_id)
            if conv_id is not None:
                await persist_tool_execution(
                    conversation_id=conv_id,
                    tool_name=name,
                    arguments=args,
                    result={"output": result},
                    success=success,
                )

        response = await self.llm_service.chat_with_tools_react(
            messages, self.tools,
            execute_local_tool=self.tool_registry.execute_tool,
            execute_mcp_tool=self.mcp_client.call_tool,
            on_tool_executed=_on_tool_executed if session_id else None,
        )
        return {"message": str(response.content), "agent": self.name}


class FortigateAgent(BaseAgent):
    """Agent for FortiGate firewall management tasks across multiple firewalls."""

    name = "fortigate"
    system_prompt = (
        "You are Kodee, a FortiGate firewall specialist managing multiple firewalls: "
        "Internet, Datacenter, VPN, and Rede Interna. "
        "You help users manage firewall policies, monitor interfaces, "
        "check VPN status, analyze configurations, and run diagnostics. "
        "When the user asks about a specific firewall, use the corresponding tools. "
        "Always confirm the impact before making changes to firewall rules. "
        "Use readonly operations when possible."
    )

    FORTIGATE_TOOL_PREFIXES = (
        "internet_",
        "datacenter_",
        "vpn_",
        "interna_",
        "fortios_",
    )

    def __init__(
        self,
        llm_service: LLMService | None = None,
        tool_registry: ToolRegistry | None = None,
        mcp_client: FortigateClientPool | None = None,
    ) -> None:
        """Initialize the FortiGate agent.

        Args:
            llm_service: LLM service for generating responses.
            tool_registry: Local tool registry.
            mcp_client: FortiGate client pool for multiple firewalls.
        """
        self.llm_service = llm_service or LLMService(model=resolve_model("fortigate"))
        self.tool_registry = tool_registry or ToolRegistry()
        self.mcp_client = mcp_client or FortigateClientPool()
        self.tools: List[Dict[str, Any]] = []

    async def run(
        self, message: str, history: List[BaseMessage], session_id: str = ""
    ) -> Dict[str, Any]:
        """Process a FortiGate-related user message across multiple firewalls.

        Args:
            message: The current user message.
            history: Previous messages in the conversation.
            session_id: Optional session identifier for persistence.

        Returns:
            Dictionary with the agent's response text.
        """
        messages = build_messages(user_message=message, history=history)
        local_tools = self.tool_registry.get_tools()
        mcp_tools = await self.mcp_client.list_all_tools()
        all_tools = local_tools + mcp_tools

        # Filter to FortiGate-relevant tools (all prefixed tools from firewalls)
        self.tools = [
            t for t in all_tools
            if t.get("function", {}).get("name", "").startswith(self.FORTIGATE_TOOL_PREFIXES)
        ]

        async def _on_tool_executed(name: str, args: dict, result: str, success: bool) -> None:
            conv_id = await get_conversation_id_by_session(session_id)
            if conv_id is not None:
                await persist_tool_execution(
                    conversation_id=conv_id,
                    tool_name=name,
                    arguments=args,
                    result={"output": result},
                    success=success,
                )

        response = await self.llm_service.chat_with_tools_react(
            messages, self.tools,
            execute_local_tool=self.tool_registry.execute_tool,
            execute_mcp_tool=self.mcp_client.call_tool,
            on_tool_executed=_on_tool_executed if session_id else None,
        )
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
        self, message: str, history: List[BaseMessage], session_id: str = ""
    ) -> Dict[str, Any]:
        """Process a DNS-related user message.

        Args:
            message: The current user message.
            history: Previous messages in the conversation.
            session_id: Optional session identifier for persistence.

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

        async def _on_tool_executed(name: str, args: dict, result: str, success: bool) -> None:
            conv_id = await get_conversation_id_by_session(session_id)
            if conv_id is not None:
                await persist_tool_execution(
                    conversation_id=conv_id,
                    tool_name=name,
                    arguments=args,
                    result={"output": result},
                    success=success,
                )

        response = await self.llm_service.chat_with_tools_react(
            messages, self.tools,
            execute_local_tool=self.tool_registry.execute_tool,
            execute_mcp_tool=self.mcp_client.call_tool,
            on_tool_executed=_on_tool_executed if session_id else None,
        )
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
        self, message: str, history: List[BaseMessage], session_id: str = ""
    ) -> Dict[str, Any]:
        """Process a backup-related user message.

        Args:
            message: The current user message.
            history: Previous messages in the conversation.
            session_id: Optional session identifier for persistence.

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

        async def _on_tool_executed(name: str, args: dict, result: str, success: bool) -> None:
            conv_id = await get_conversation_id_by_session(session_id)
            if conv_id is not None:
                await persist_tool_execution(
                    conversation_id=conv_id,
                    tool_name=name,
                    arguments=args,
                    result={"output": result},
                    success=success,
                )

        response = await self.llm_service.chat_with_tools_react(
            messages, self.tools,
            execute_local_tool=self.tool_registry.execute_tool,
            execute_mcp_tool=self.mcp_client.call_tool,
            on_tool_executed=_on_tool_executed if session_id else None,
        )
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
        self, message: str, history: List[BaseMessage], session_id: str = ""
    ) -> Dict[str, Any]:
        """Process a monitoring-related user message.

        Args:
            message: The current user message.
            history: Previous messages in the conversation.
            session_id: Optional session identifier for persistence.

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

        async def _on_tool_executed(name: str, args: dict, result: str, success: bool) -> None:
            conv_id = await get_conversation_id_by_session(session_id)
            if conv_id is not None:
                await persist_tool_execution(
                    conversation_id=conv_id,
                    tool_name=name,
                    arguments=args,
                    result={"output": result},
                    success=success,
                )

        response = await self.llm_service.chat_with_tools_react(
            messages, self.tools,
            execute_local_tool=self.tool_registry.execute_tool,
            execute_mcp_tool=self.mcp_client.call_tool,
            on_tool_executed=_on_tool_executed if session_id else None,
        )
        return {"message": str(response.content), "agent": self.name}
