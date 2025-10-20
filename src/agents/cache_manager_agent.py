"""
Cache Manager Agent for EdgeMind MEC orchestration system.

This agent manages model caching and predictive preloading using Strands framework.
"""

from typing import Any

from strands import Agent

from src.logging_config import AgentActivityLogger


class CacheManagerAgent:
    """
    Cache Manager Agent that handles model caching and predictive preloading.

    MCP Tools:
    - inference: For model caching, preloading, and cache optimization
    - telemetry: For cache performance logging and hit rate tracking
    """

    def __init__(self, mec_site: str = "MEC_B"):
        self.agent_id = f"cache_manager_{mec_site}"
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
        """Create actual MCP tools for cache manager agent."""
        from src.mcp_tools.mcp_integration import get_mcp_tools_for_agent

        # Get MCP tools: inference_engine, telemetry_logger, metrics_monitor
        return get_mcp_tools_for_agent("cache_manager")

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the cache manager agent."""
        return f"""You are the Cache Manager Agent for EdgeMind MEC site {self.mec_site}.

Your responsibilities:
1. Manage local model caching with 15-minute refresh cycles
2. Implement predictive preloading based on usage patterns
3. Optimize cache hit rates and model availability
4. Assess model availability when recommending MEC sites
5. Coordinate cache warming and model distribution

Available MCP Tools:
- inference_engine: Cache models, run local inference, preload models, optimize cache allocation
- telemetry_logger: Track cache hit rates, model usage patterns, and performance metrics
- metrics_monitor: Monitor MEC site performance to inform caching decisions

Cache Management Strategy:
- Local cache refresh: Every 15 minutes
- Predictive preloading: Based on historical usage patterns
- Cache priority: Frequently used models, recent requests, predicted demand
- Cache eviction: LRU with usage frequency weighting
- Model distribution: Coordinate with other sites for optimal placement

When participating in swarm consensus:
1. Use inference_engine to check model availability and cache status at target sites
2. Assess cache hit probability for expected workload using cache metrics
3. Consider model loading time and cache warming requirements
4. Use metrics_monitor to evaluate site performance for cache operations
5. Use telemetry_logger to log caching decisions and performance data
6. Recommend sites with optimal model availability and cache performance
7. If selected, coordinate model preloading and cache optimization

Performance Targets:
- Cache hit rate: >85%
- Model loading time: <5 seconds
- Cache refresh overhead: <2% of total capacity

Always include cache metrics and model availability in your recommendations."""

    def get_agent_status(self) -> dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "agent_type": "cache_manager",
            "mec_site": self.mec_site,
            "status": "active",
            "mcp_tools": len(self.mcp_tools),
            "specialization": "model_caching_and_preloading",
        }
