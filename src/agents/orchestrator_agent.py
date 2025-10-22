"""
Orchestrator Agent for EdgeMind MEC orchestration system.

This agent monitors thresholds and triggers swarm coordination using Strands framework.
"""

import os
from typing import Any

from strands import Agent
from strands.models.anthropic import AnthropicModel
from strands.multiagent import Swarm

from src.logging_config import AgentActivityLogger
from src.orchestrator.threshold_monitor import ThresholdEvent


class OrchestratorAgent:
    """
    Orchestrator Agent that monitors thresholds and triggers swarm coordination.

    MCP Tools:
    - metrics_monitor: For threshold monitoring and MEC site health checks
    - memory_sync: For swarm state synchronization and coordination
    """

    def __init__(self, mec_site: str = "MEC_A"):
        self.agent_id = f"orchestrator_{mec_site}"
        self.mec_site = mec_site
        self.logger = AgentActivityLogger(self.agent_id)

        # Create Claude model for Strands
        self.model = AnthropicModel(
            client_args={
                "api_key": os.getenv("ANTHROPIC_API_KEY", "your-api-key-here"),
            },
            max_tokens=2048,
            model_id="claude-3-5-sonnet-20241022",
            params={
                "temperature": 0.3,  # Lower temperature for consistent orchestration decisions
            },
        )

        # Create actual MCP tools
        self.mcp_tools = self._create_mcp_tools()

        # Create the Strands agent with Claude model and MCP tools
        self.agent = Agent(
            name=self.agent_id,
            model=self.model,
            system_prompt=self._get_system_prompt(),
            tools=self.mcp_tools,
        )

        # Swarm coordination
        self.swarm = None
        self.peer_agents = {}

    def _create_mcp_tools(self) -> list[Any]:
        """Create actual MCP tools for orchestrator agent."""
        try:
            from src.mcp_tools.mcp_integration import get_mcp_tools_for_agent

            # Get MCP tools: metrics_monitor, memory_sync, telemetry_logger
            return get_mcp_tools_for_agent("orchestrator")
        except Exception as e:
            # Fallback to no tools if MCP tools fail to load
            self.logger.log_swarm_event(
                "mcp_tools_failed",
                details={"error": str(e), "fallback": "no_tools"},
            )
            return []

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the orchestrator agent."""
        return f"""You are the Orchestrator Agent for EdgeMind MEC site {self.mec_site}.

Your responsibilities:
1. Monitor performance thresholds and detect breaches
2. Coordinate with other agents for optimal MEC site selection
3. Make quick decisions for load balancing and failover

Available Tools:
- get_all_mec_metrics(): Get current metrics for all MEC sites
- monitor_thresholds(): Check threshold breaches across sites
- get_mec_metrics(site_id): Get metrics for a specific site

When handling a threshold breach:
1. Use get_all_mec_metrics() to get current site status
2. Analyze which sites have capacity for additional load
3. Select the optimal site based on CPU, GPU, queue depth, and response time
4. Provide clear reasoning for your decision

IMPORTANT: Keep your response concise and focused. Use the tools to get real data, then make your recommendation quickly.

Response format:
Analysis: [Brief analysis based on tool data]
Recommendation: [Selected MEC site]
Confidence: [0-100%]"""

    def set_swarm(self, swarm: Swarm) -> None:
        """Set the swarm for coordination."""
        self.swarm = swarm
        self.logger.log_swarm_event(
            "swarm_registered",
            details={
                "swarm_agents": (len(swarm.agents) if hasattr(swarm, "agents") else 0),
            },
        )

    def register_peer_agent(self, agent_id: str, agent: Any) -> None:
        """Register a peer agent for coordination."""
        self.peer_agents[agent_id] = agent

    async def handle_threshold_breach(
        self,
        threshold_event: ThresholdEvent,
    ) -> dict[str, Any]:
        """
        Handle threshold breach by triggering swarm coordination.

        Args:
            threshold_event: The threshold breach event that triggered this

        Returns:
            Dictionary with swarm coordination result
        """
        self.logger.log_threshold_breach(
            threshold_event.metric_name,
            threshold_event.current_value,
            threshold_event.threshold_value,
        )

        # Prepare swarm coordination message
        coordination_request = f"""
THRESHOLD BREACH DETECTED - IMMEDIATE SWARM COORDINATION REQUIRED

Breach Details:
- Site: {threshold_event.site_id}
- Metric: {threshold_event.metric_name}
- Current Value: {threshold_event.current_value}
- Threshold: {threshold_event.threshold_value}
- Severity: {threshold_event.severity.value}
- Breach Duration: {threshold_event.breach_duration_ms}ms

Required Actions:
1. Assess available MEC sites for load balancing
2. Reach consensus on optimal target site
3. Execute load balancing decision
4. Monitor execution success

Target Response Time: <100ms total orchestration time
Priority: {threshold_event.severity.value.upper()}

Use your MCP tools to coordinate with the swarm and make the optimal decision.
"""

        try:
            # Execute swarm coordination
            if self.swarm:
                result = await self.swarm.invoke_async(coordination_request)

                # Extract detailed agent interactions
                agent_interactions = []
                if hasattr(result, "node_history") and result.node_history:
                    for i, node in enumerate(result.node_history):
                        agent_interactions.append(
                            {
                                "step": i + 1,
                                "agent_id": getattr(node, "node_id", f"Agent_{i}"),
                                "output": getattr(node, "output", ""),
                                "timestamp": datetime.now(UTC).isoformat(),
                            }
                        )

                self.logger.log_decision(
                    "swarm_coordination_completed",
                    result.status,
                    f"Swarm handled threshold breach with {len(result.node_history)} agent interactions",
                )

                return {
                    "status": result.status,
                    "execution_time_ms": getattr(result, "execution_time", 0),
                    "agents_involved": (
                        [node.node_id for node in result.node_history]
                        if hasattr(result, "node_history")
                        else [self.agent_id]
                    ),
                    "final_result": getattr(result, "output", str(result.status)),
                    "token_usage": getattr(result, "accumulated_usage", None),
                    "agent_interactions": agent_interactions,
                    "swarm_result_object": result,  # Store the full result object for conversation extraction
                }

            # Fallback if no swarm available
            fallback_result = self.agent(coordination_request)

            return {  # noqa: TRY300
                "status": "completed_fallback",
                "execution_time_ms": 50,  # Estimated
                "agents_involved": [self.agent_id],
                "final_result": str(fallback_result),
                "token_usage": None,
                "agent_interactions": [
                    {
                        "step": 1,
                        "agent_id": self.agent_id,
                        "output": str(fallback_result),
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                ],
            }

        except Exception as e:
            self.logger.log_swarm_event(
                "swarm_coordination_failed",
                details={
                    "error": str(e),
                    "threshold_event": threshold_event.to_dict(),
                },
            )

            return {
                "status": "failed",
                "error": str(e),
                "execution_time_ms": 0,
                "agents_involved": [],
                "final_result": None,
            }

    def get_agent_status(self) -> dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "agent_type": "orchestrator",
            "mec_site": self.mec_site,
            "status": "active",
            "swarm_available": self.swarm is not None,
            "peer_agents": len(self.peer_agents),
            "mcp_tools": len(self.mcp_tools),
        }
