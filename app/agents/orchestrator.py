"""Orchestrator for managing multi-agent conversation flow with LangGraph."""

from typing import Any, Dict, List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from app.agents.base_agent import BaseAgent
from app.agents.handoff import HandoffClassifier
from app.agents.router import AgentRouter
from app.agents.specialized import BackupAgent, DNSAgent, FortigateAgent, GeneralAgent, MonitoringAgent
from app.rag.retriever import RAGRetriever
from app.services.llm_service import LLMService
from app.utils.session_store import InMemorySessionStore, SessionStore

MAX_HISTORY = 10
SUMMARIZE_THRESHOLD = 8  # start summarizing when history exceeds this


class OrchestratorState(TypedDict):
    """State schema for the agent orchestration graph."""

    message: str
    history: List[BaseMessage]
    agent_name: str
    agent_response: Dict[str, Any]
    session_id: str


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
        fortigate_agent: BaseAgent | None = None,
        retriever: RAGRetriever | None = None,
        session_store: SessionStore | None = None,
        llm_service: LLMService | None = None,
    ) -> None:
        """Initialize the orchestrator with agents and a router.

        Args:
            router: AgentRouter for classifying messages.
            handoff_classifier: HandoffClassifier for detecting human escalation.
            general_agent: Agent for general questions.
            dns_agent: Agent for DNS management tasks.
            backup_agent: Agent for backup and restore tasks.
            monitoring_agent: Agent for monitoring tasks.
            fortigate_agent: Agent for FortiGate firewall tasks.
            retriever: RAG retriever for knowledge base augmentation.
            session_store: Optional persistent session store (e.g., Redis).
            llm_service: LLM service for context summarization.
        """
        self.router = router or AgentRouter()
        self.handoff_classifier = handoff_classifier or HandoffClassifier()
        self.agents: Dict[str, BaseAgent] = {
            "general": general_agent or GeneralAgent(),
            "dns": dns_agent or DNSAgent(),
            "backup": backup_agent or BackupAgent(),
            "monitoring": monitoring_agent or MonitoringAgent(),
            "fortigate": fortigate_agent or FortigateAgent(),
        }
        self.retriever = retriever or RAGRetriever()
        self.session_store = session_store or InMemorySessionStore()
        self.llm_service = llm_service
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
            response = await agent.run(
                state["message"], state["history"], session_id=state.get("session_id", "")
            )
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

        # RAG: retrieve relevant knowledge base documents
        try:
            retrieved_docs = await self.retriever.retrieve(message, top_k=5)
            if retrieved_docs:
                augmented_message = await self.retriever.augment_prompt(
                    message, retrieved_docs
                )
                message = augmented_message
        except Exception:
            # Graceful degradation: proceed without RAG if retrieval fails
            pass

        state: OrchestratorState = {
            "message": message,
            "history": history,
            "agent_name": "",
            "agent_response": {},
            "session_id": session_id or "",
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

        # Intelligent context management: summarize old turns instead of truncating
        if len(history) > SUMMARIZE_THRESHOLD:
            # Keep the last 4 messages, summarize everything before that
            to_summarize = history[:-4]
            recent = history[-4:]
            summary = await self._summarize_history(to_summarize)
            from langchain_core.messages import SystemMessage

            history = [
                SystemMessage(content=f"Previous conversation summary: {summary}")
            ] + recent

        self._history[session_id] = history

        # Persist to session store (async, best-effort)
        try:
            await self.session_store.set_history(session_id, history)
        except Exception:
            pass

        return {
            "message": agent_response.get("message", ""),
            "agent_used": agent_name,
            "actions": agent_response.get("actions", []),
            "session_id": session_id,
        }

    async def _summarize_history(self, messages: List[BaseMessage]) -> str:
        """Generate a concise summary of old conversation turns.

        Args:
            messages: List of messages to summarize.

        Returns:
            A summary string of the conversation so far.
        """
        if not self.llm_service:
            # Fallback: join message contents if no LLM available
            return " ".join(
                f"{m.__class__.__name__}: {m.content}"
                for m in messages[:4]
            )

        from langchain_core.messages import SystemMessage

        summary_prompt = (
            "Summarize the following conversation in 1-2 sentences. "
            "Preserve key facts, decisions, and user intent.\n\n"
        )
        for m in messages:
            role = "User" if isinstance(m, HumanMessage) else "Assistant"
            summary_prompt += f"{role}: {m.content}\n"

        try:
            summary = await self.llm_service.chat([SystemMessage(content=summary_prompt)])
            return summary
        except Exception:
            return "[Previous conversation summary unavailable]"

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
