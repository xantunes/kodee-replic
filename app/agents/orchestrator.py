"""Orchestrator for managing multi-agent conversation flow with LangGraph."""

from typing import Any, Dict, List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from app.agents.base_agent import BaseAgent
from app.agents.handoff import HandoffClassifier
from app.agents.router import AgentRouter
from app.agents.specialized import BackupAgent, DNSAgent, GeneralAgent, MonitoringAgent

MAX_HISTORY = 10


class OrchestratorState(TypedDict):
    """State schema for the agent orchestration graph."""

    message: str
    history: List[BaseMessage]
    agent_name: str
    agent_response: Dict[str, Any]


class Orchestrator:
    """Manages conversation state and delegates to specialized agents."""

    def __init__(
        self,
        router: AgentRouter | None = None,
        handoff_classifier: HandoffClassifier | None = None,
        general_agent: BaseAgent | None = None,
        dns_agent: BaseAgent | None = None,
        backup_agent: BaseAgent | None = None,
        monitoring_agent: BaseAgent | None = None,
    ) -> None:
        """Initialize the orchestrator with agents and a router.

        Args:
            router: AgentRouter for classifying messages.
            handoff_classifier: HandoffClassifier for detecting human escalation.
            general_agent: Agent for general questions.
            dns_agent: Agent for DNS management tasks.
            backup_agent: Agent for backup and restore tasks.
            monitoring_agent: Agent for monitoring tasks.
        """
        self.router = router or AgentRouter()
        self.handoff_classifier = handoff_classifier or HandoffClassifier()
        self.agents: Dict[str, BaseAgent] = {
            "general": general_agent or GeneralAgent(),
            "dns": dns_agent or DNSAgent(),
            "backup": backup_agent or BackupAgent(),
            "monitoring": monitoring_agent or MonitoringAgent(),
        }
        self._history: Dict[str, List[BaseMessage]] = {}
        self._agent_usage: Dict[str, List[str]] = {}
        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph for agent orchestration.

        Returns:
            Compiled StateGraph.
        """
        graph = StateGraph(OrchestratorState)

        async def route_node(state: OrchestratorState) -> Dict[str, Any]:
            """Determine which agent should handle the message."""
            agent_name = await self.router.route(
                state["message"], state["history"]
            )
            return {"agent_name": agent_name}

        async def agent_node(state: OrchestratorState) -> Dict[str, Any]:
            """Delegate to the selected agent and capture its response."""
            agent = self.agents[state["agent_name"]]
            response = await agent.run(state["message"], state["history"])
            return {"agent_response": response}

        graph.add_node("router", route_node)
        graph.add_node("agent", agent_node)

        graph.set_entry_point("router")
        graph.add_edge("router", "agent")
        graph.add_edge("agent", END)

        return graph.compile()

    async def process(
        self,
        user_id: str,
        message: str,
        session_id: str | None = None,
    ) -> Dict[str, Any]:
        """Process a user message through the multi-agent system.

        Args:
            user_id: Unique identifier for the user.
            message: Message content from the user.
            session_id: Optional session identifier for conversation continuity.

        Returns:
            Dictionary containing the response message, agent_used, actions,
            and session_id.
        """
        if session_id is None:
            import uuid

            session_id = str(uuid.uuid4())

        # Check if user is seeking human support
        is_handoff = await self.handoff_classifier.is_seeking_human(message)
        if is_handoff:
            return {
                "message": "I'm connecting you to a human agent...",
                "agent_used": "human_handoff",
                "actions": [],
                "session_id": session_id,
            }

        history = self._history.get(session_id, [])

        state: OrchestratorState = {
            "message": message,
            "history": history,
            "agent_name": "",
            "agent_response": {},
        }

        result_state = await self._graph.ainvoke(state)

        agent_name = result_state["agent_name"]
        agent_response = result_state["agent_response"]

        # Track agent usage
        if session_id not in self._agent_usage:
            self._agent_usage[session_id] = []
        self._agent_usage[session_id].append(agent_name)

        # Update history with the user message and agent response
        history.append(HumanMessage(content=message))
        history.append(AIMessage(content=agent_response.get("message", "")))

        # Keep only the last N messages
        if len(history) > MAX_HISTORY:
            history = history[-MAX_HISTORY:]

        self._history[session_id] = history

        return {
            "message": agent_response.get("message", ""),
            "agent_used": agent_name,
            "actions": agent_response.get("actions", []),
            "session_id": session_id,
        }

    def get_history(self, session_id: str) -> List[BaseMessage]:
        """Retrieve the conversation history for a session.

        Args:
            session_id: Session identifier.

        Returns:
            List of messages in the session.
        """
        return list(self._history.get(session_id, []))

    def get_agent_usage(self, session_id: str) -> List[str]:
        """Retrieve the list of agents used in a session.

        Args:
            session_id: Session identifier.

        Returns:
            List of agent names in order of use.
        """
        return list(self._agent_usage.get(session_id, []))
