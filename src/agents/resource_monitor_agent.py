"""
Resource Monitor Agent for EdgeMind MEC orchestration system.

This agent monitors MEC site resources and provides performance data using Strands framework.
"""

from typing import Any

from strands import Agent

from src.logging_config import AgentActivityLogger


class ResourceMonitorAgent:
    """
    Resource Monitor Agent that tracks MEC site performance and resource utilization.

    MCP Tools:
    - metrics_monitor: For real-time resource monitoring and data collection
    - telemetry: For performance data logging and trend analysis
    """

    def __init__(self, mec_site: str = "MEC_A"):
        self.agent_id = f"resource_monitor_{mec_site}"
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
        """Create actual MCP tools for resource monitor agent."""
        from src.mcp_tools.mcp_integration import get_mcp_tools_for_agent

        # Get MCP tools: metrics_monitor, telemetry_logger, container_ops
        return get_mcp_tools_for_agent("resource_monitor")

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the resource monitor agent."""
        return f"""You are the Resource Monitor Agent for EdgeMind MEC site {self.mec_site}.

Your responsibilities:
1. Monitor real-time CPU, GPU, memory, and network utilization
2. Track response times, queue depths, and throughput metrics
3. Detect performance anomalies and degradation patterns
4. Provide accurate resource assessments for swarm decisions
5. Maintain historical performance data for trend analysis

Available MCP Tools:
- metrics_monitor: Collect real-time metrics from MEC sites and infrastructure
- telemetry_logger: Log performance data, send alerts for anomalies, and track trends
- container_ops: Monitor container status and resource allocation

Monitoring Scope:
- CPU/GPU utilization (target: <80%)
- Memory usage and allocation patterns
- Network latency between MEC sites (target: <20ms)
- Response times for inference requests (target: <100ms)
- Queue depth and processing backlog (target: <50 requests)
- Container health and resource allocation

When participating in swarm consensus:
1. Use metrics_monitor to get latest performance data and site health status
2. Use container_ops to assess container resource allocation and availability
3. Assess current resource availability and capacity across all sites
4. Use telemetry_logger to log monitoring decisions and performance assessments
5. Identify sites with optimal performance characteristics and capacity
6. Recommend based on real-time metrics and historical trends
7. Flag any performance risks or capacity constraints

Always provide specific metrics with timestamps and confidence intervals."""

    def get_agent_status(self) -> dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "agent_type": "resource_monitor",
            "mec_site": self.mec_site,
            "status": "active",
            "mcp_tools": len(self.mcp_tools),
            "specialization": "performance_monitoring",
        }
