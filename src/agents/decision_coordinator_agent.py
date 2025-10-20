"""
Decision Coordinator Agent for EdgeMind MEC orchestration system.

This agent manages swarm consensus and decision coordination using Strands framework.
"""

from typing import Any

from strands import Agent

from src.logging_config import AgentActivityLogger


class DecisionCoordinatorAgent:
    """
    Decision Coordinator Agent that manages swarm consensus and final decisions.

    MCP Tools:
    - memory_sync: For swarm state management and consensus coordination
    - telemetry: For decision logging and performance tracking
    """

    def __init__(self, mec_site: str = "MEC_C"):
        self.agent_id = f"decision_coordinator_{mec_site}"
        self.mec_site = mec_site
        self.logger = AgentActivityLogger(self.agent_id)

        # Create actual MCP tools
        self.mcp_tools = self._create_mcp_tools()

        # Create the Strands agent with MCP tools
        self.agent = Agent(
            name=self.agent_id,
            system_prompt=self._get_system_prompt(),
            tools=self.mcp_tools,
        )

    def _create_mcp_tools(self) -> list[Any]:
        """Create actual MCP tools for decision coordinator agent."""
        from src.mcp_tools.mcp_integration import get_mcp_tools_for_agent

        # Get MCP tools: memory_sync, telemetry_logger, metrics_monitor
        return get_mcp_tools_for_agent("decision_coordinator")

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the decision coordinator agent."""
        return f"""You are the Decision Coordinator Agent for EdgeMind MEC site {self.mec_site}.

Your responsibilities:
1. Coordinate swarm consensus processes and voting
2. Aggregate recommendations from other agents
3. Apply consensus algorithms (majority vote, weighted scoring)
4. Make final decisions when consensus is reached
5. Handle conflict resolution when agents disagree
6. Log all decisions and reasoning for pattern learning

Available MCP Tools:
- memory_sync: Manage swarm state, initiate consensus, collect votes, and coordinate decisions
- telemetry_logger: Log decisions, performance metrics, agent activities, and learning data
- metrics_monitor: Access MEC site metrics for informed decision making

Consensus Process:
1. Collect recommendations from all participating agents
2. Apply weighted voting based on agent expertise and confidence
3. Calculate consensus score and confidence level
4. If consensus >= 60%, proceed with majority decision
5. If consensus < 60%, request additional input or apply tie-breaking rules
6. Log final decision with full reasoning and participant votes

Decision Criteria:
- Agent expertise weight: LoadBalancer (30%), ResourceMonitor (25%), CacheManager (20%), Orchestrator (25%)
- Minimum confidence threshold: 0.6
- Required participants: At least 3 agents for valid consensus
- Tie-breaking: Defer to LoadBalancer agent recommendation

Always provide detailed consensus analysis with vote breakdown and confidence scores."""

    def get_agent_status(self) -> dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "agent_type": "decision_coordinator",
            "mec_site": self.mec_site,
            "status": "active",
            "mcp_tools": len(self.mcp_tools),
            "specialization": "consensus_and_coordination",
        }
