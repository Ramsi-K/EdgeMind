"""
Load Balancer Agent for EdgeMind MEC orchestration system.

This agent handles MEC site selection and load distribution using Strands framework.
"""

from typing import Any

from strands import Agent

from src.logging_config import AgentActivityLogger


class LoadBalancerAgent:
    """
    Load Balancer Agent that evaluates MEC sites and makes selection decisions.

    MCP Tools:
    - metrics_monitor: For MEC site capacity and performance assessment
    - container_ops: For scaling and deployment operations
    """

    def __init__(self, mec_site: str = "MEC_B"):
        self.agent_id = f"load_balancer_{mec_site}"
        self.mec_site = mec_site
        self.logger = AgentActivityLogger(self.agent_id)

        # Create dummy MCP tools for simulation
        self.mcp_tools = self._create_dummy_mcp_tools()

        # Create the Strands agent with MCP tools
        self.agent = Agent(
            name=self.agent_id,
            system_prompt=self._get_system_prompt(),
            tools=self.mcp_tools,
        )

    def _create_dummy_mcp_tools(self) -> list[Any]:
        """Create dummy MCP tools for simulation."""
        # For now, return empty list - will be replaced with actual MCP tools
        # In real implementation, these would be:
        # - metrics_monitor.mcp for site assessment
        # - container_ops.mcp for scaling operations
        return []

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the load balancer agent."""
        return f"""You are the Load Balancer Agent for EdgeMind MEC site {self.mec_site}.

Your responsibilities:
1. Evaluate MEC site capacity and performance metrics
2. Calculate optimal load distribution across available sites
3. Assess site health and availability for workload placement
4. Recommend target sites based on current load and capacity
5. Execute load balancing decisions through container scaling

Available MCP Tools:
- metrics_monitor: Get real-time MEC site metrics and capacity data
- container_ops: Scale containers and deploy workloads to target sites

Site Selection Criteria (in priority order):
1. Site health and availability (40% weight)
2. Current CPU/GPU/Memory utilization (30% weight)
3. Network latency to requesting site (20% weight)
4. Queue depth and response time (10% weight)

When participating in swarm consensus:
1. Use metrics_monitor to get current site metrics
2. Calculate load scores for all available sites
3. Recommend the site with the best capacity/performance ratio
4. If selected for execution, use container_ops to implement the decision

Always provide quantitative reasoning with specific metrics and scores."""

    def get_agent_status(self) -> dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "agent_type": "load_balancer",
            "mec_site": self.mec_site,
            "status": "active",
            "mcp_tools": len(self.mcp_tools),
            "specialization": "site_selection_and_scaling",
        }
