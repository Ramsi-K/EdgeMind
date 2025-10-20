"""
MCP Integration Helper

Provides easy integration of MCP tools with Strands agents.
Creates Strands-compatible @tool decorated functions for agent usage.
"""

import asyncio
from typing import Any, Dict, List

from strands import tool

from .container_ops import create_container_ops_tool
from .inference_engine import create_inference_engine_tool
from .memory_sync import create_memory_sync_tool
from .metrics_monitor import create_metrics_monitor_tool
from .telemetry_logger import create_telemetry_logger_tool


class MCPToolIntegration:
    """Integration helper for MCP tools with Strands agents."""

    def __init__(self):
        # Create tool instances
        self.metrics_monitor = create_metrics_monitor_tool()
        self.container_ops = create_container_ops_tool()
        self.inference_engine = create_inference_engine_tool()
        self.telemetry_logger = create_telemetry_logger_tool()
        self.memory_sync = create_memory_sync_tool()

    def get_orchestrator_tools(self) -> List[Any]:
        """Get Strands-compatible tools for OrchestratorAgent."""
        return [
            *self._create_metrics_tools(),
            *self._create_memory_sync_tools(),
            *self._create_telemetry_tools(),
        ]

    def get_load_balancer_tools(self) -> List[Any]:
        """Get Strands-compatible tools for LoadBalancerAgent."""
        return [
            *self._create_metrics_tools(),
            *self._create_container_ops_tools(),
            *self._create_telemetry_tools(),
        ]

    def get_decision_coordinator_tools(self) -> List[Any]:
        """Get Strands-compatible tools for DecisionCoordinatorAgent."""
        return [
            *self._create_memory_sync_tools(),
            *self._create_telemetry_tools(),
            *self._create_metrics_tools(),
        ]

    def get_cache_manager_tools(self) -> List[Any]:
        """Get Strands-compatible tools for CacheManagerAgent."""
        return [
            *self._create_inference_engine_tools(),
            *self._create_telemetry_tools(),
            *self._create_metrics_tools(),
        ]

    def get_resource_monitor_tools(self) -> List[Any]:
        """Get Strands-compatible tools for ResourceMonitorAgent."""
        return [
            *self._create_metrics_tools(),
            *self._create_telemetry_tools(),
            *self._create_container_ops_tools(),
        ]

    def _create_metrics_tools(self) -> List[Any]:
        """Create Strands-compatible metrics monitoring tools."""

        @tool
        def get_mec_metrics(site_id: str) -> dict:
            """Get current metrics for a specific MEC site.

            Args:
                site_id: MEC site identifier (MEC_A, MEC_B, MEC_C)

            Returns:
                Current metrics including CPU, GPU, memory utilization and health status
            """
            result = asyncio.run(
                self.metrics_monitor.handle_tool_call(
                    "get_mec_metrics", {"site_id": site_id}
                )
            )
            return {"status": "success", "content": [{"text": str(result)}]}

        @tool
        def get_all_mec_metrics() -> dict:
            """Get current metrics for all MEC sites.

            Returns:
                Metrics for all MEC sites with health status and performance data
            """
            result = asyncio.run(
                self.metrics_monitor.handle_tool_call("get_all_mec_metrics", {})
            )
            return {"status": "success", "content": [{"text": str(result)}]}

        @tool
        def monitor_thresholds(
            cpu_threshold: float = 80.0,
            gpu_threshold: float = 80.0,
            latency_threshold: float = 100.0,
            queue_threshold: int = 50,
        ) -> dict:
            """Check if any sites exceed performance thresholds.

            Args:
                cpu_threshold: CPU utilization threshold percentage
                gpu_threshold: GPU utilization threshold percentage
                latency_threshold: Response time threshold in milliseconds
                queue_threshold: Queue depth threshold

            Returns:
                List of sites with threshold breaches and severity information
            """
            result = asyncio.run(
                self.metrics_monitor.handle_tool_call(
                    "monitor_thresholds",
                    {
                        "cpu_threshold": cpu_threshold,
                        "gpu_threshold": gpu_threshold,
                        "latency_threshold": latency_threshold,
                        "queue_threshold": queue_threshold,
                    },
                )
            )
            return {"status": "success", "content": [{"text": str(result)}]}

        return [get_mec_metrics, get_all_mec_metrics, monitor_thresholds]

    def _create_container_ops_tools(self) -> List[Any]:
        """Create Strands-compatible container operations tools."""

        @tool
        def scale_containers(
            site_id: str,
            service_name: str = None,
            target_replicas: int = None,
            scaling_factor: float = None,
        ) -> dict:
            """Scale container replicas at a specific MEC site.

            Args:
                site_id: MEC site identifier
                service_name: Service to scale (optional, scales all if not specified)
                target_replicas: Target number of replicas
                scaling_factor: Scaling multiplier (alternative to target_replicas)

            Returns:
                Scaling operation results with success status and timing
            """
            args = {"site_id": site_id}
            if service_name:
                args["service_name"] = service_name
            if target_replicas:
                args["target_replicas"] = target_replicas
            if scaling_factor:
                args["scaling_factor"] = scaling_factor

            result = asyncio.run(
                self.container_ops.handle_tool_call("scale_containers", args)
            )
            return {"status": "success", "content": [{"text": str(result)}]}

        @tool
        def get_container_status(site_id: str) -> dict:
            """Get current container status for a MEC site.

            Args:
                site_id: MEC site identifier

            Returns:
                Container status including running/failed counts and health information
            """
            result = asyncio.run(
                self.container_ops.handle_tool_call(
                    "get_container_status", {"site_id": site_id}
                )
            )
            return {"status": "success", "content": [{"text": str(result)}]}

        return [scale_containers, get_container_status]

    def _create_inference_engine_tools(self) -> List[Any]:
        """Create Strands-compatible inference engine tools."""

        @tool
        def get_model_cache_status(site_id: str, model_name: str = None) -> dict:
            """Get model cache status for a MEC site.

            Args:
                site_id: MEC site identifier
                model_name: Specific model name (optional)

            Returns:
                Cache status including cached models, sizes, and hit rates
            """
            args = {"site_id": site_id}
            if model_name:
                args["model_name"] = model_name

            result = asyncio.run(
                self.inference_engine.handle_tool_call("get_model_cache_status", args)
            )
            return {"status": "success", "content": [{"text": str(result)}]}

        @tool
        def preload_models(
            site_id: str, models: List[str], priority: str = "medium"
        ) -> dict:
            """Preload models based on predicted usage patterns.

            Args:
                site_id: MEC site identifier
                models: List of model names to preload
                priority: Preloading priority (low, medium, high)

            Returns:
                Preloading results with success status and timing
            """
            result = asyncio.run(
                self.inference_engine.handle_tool_call(
                    "preload_models",
                    {
                        "site_id": site_id,
                        "models": models,
                        "priority": priority,
                    },
                )
            )
            return {"status": "success", "content": [{"text": str(result)}]}

        return [get_model_cache_status, preload_models]

    def _create_telemetry_tools(self) -> List[Any]:
        """Create Strands-compatible telemetry logging tools."""

        @tool
        def log_decision(
            decision_type: str,
            decision_data: dict,
            agent_id: str,
            site_id: str = None,
            confidence_score: float = None,
            execution_time_ms: int = None,
        ) -> dict:
            """Log a swarm coordination decision with context.

            Args:
                decision_type: Type of decision being made
                decision_data: Decision details and reasoning
                agent_id: ID of the agent making the decision
                site_id: MEC site involved in decision
                confidence_score: Confidence level of the decision
                execution_time_ms: Time taken to make decision

            Returns:
                Logging confirmation with event ID and timestamp
            """
            args = {
                "decision_type": decision_type,
                "decision_data": decision_data,
                "agent_id": agent_id,
            }
            if site_id:
                args["site_id"] = site_id
            if confidence_score:
                args["confidence_score"] = confidence_score
            if execution_time_ms:
                args["execution_time_ms"] = execution_time_ms

            result = asyncio.run(
                self.telemetry_logger.handle_tool_call("log_decision", args)
            )
            return {"status": "success", "content": [{"text": str(result)}]}

        @tool
        def log_agent_activity(
            agent_id: str,
            activity_type: str,
            details: dict,
            site_id: str = None,
            duration_ms: int = None,
            success: bool = True,
        ) -> dict:
            """Log agent activity and interactions.

            Args:
                agent_id: ID of the agent performing activity
                activity_type: Type of activity being performed
                details: Activity details and context
                site_id: MEC site where activity occurred
                duration_ms: Duration of the activity
                success: Whether the activity was successful

            Returns:
                Logging confirmation with event ID and timestamp
            """
            args = {
                "agent_id": agent_id,
                "activity_type": activity_type,
                "details": details,
            }
            if site_id:
                args["site_id"] = site_id
            if duration_ms:
                args["duration_ms"] = duration_ms
            if success is not None:
                args["success"] = success

            result = asyncio.run(
                self.telemetry_logger.handle_tool_call("log_agent_activity", args)
            )
            return {"status": "success", "content": [{"text": str(result)}]}

        return [log_decision, log_agent_activity]

    def _create_memory_sync_tools(self) -> List[Any]:
        """Create Strands-compatible memory synchronization tools."""

        @tool
        def initiate_consensus(
            initiator_agent: str,
            consensus_topic: str,
            participants: List[str],
            timeout_ms: int = 5000,
            context_data: dict = None,
        ) -> dict:
            """Start a new consensus coordination session.

            Args:
                initiator_agent: Agent starting the consensus
                consensus_topic: Topic for consensus decision
                participants: List of participating agent IDs
                timeout_ms: Consensus timeout in milliseconds
                context_data: Additional context for decision

            Returns:
                Consensus session details with session ID and expiration
            """
            args = {
                "initiator_agent": initiator_agent,
                "consensus_topic": consensus_topic,
                "participants": participants,
                "timeout_ms": timeout_ms,
            }
            if context_data:
                args["context_data"] = context_data

            result = asyncio.run(
                self.memory_sync.handle_tool_call("initiate_consensus", args)
            )
            return {"status": "success", "content": [{"text": str(result)}]}

        @tool
        def submit_vote(
            session_id: str,
            agent_id: str,
            vote_data: dict,
            confidence: float = 0.5,
            reasoning: str = "",
        ) -> dict:
            """Submit a vote for an active consensus decision.

            Args:
                session_id: Consensus session identifier
                agent_id: Voting agent identifier
                vote_data: Vote details and recommendation
                confidence: Confidence level in the vote
                reasoning: Explanation for the vote

            Returns:
                Vote submission result with consensus status
            """
            result = asyncio.run(
                self.memory_sync.handle_tool_call(
                    "submit_vote",
                    {
                        "session_id": session_id,
                        "agent_id": agent_id,
                        "vote_data": vote_data,
                        "confidence": confidence,
                        "reasoning": reasoning,
                    },
                )
            )
            return {"status": "success", "content": [{"text": str(result)}]}

        @tool
        def get_swarm_overview(
            include_history: bool = False, time_window_minutes: int = 60
        ) -> dict:
            """Get comprehensive swarm coordination overview.

            Args:
                include_history: Whether to include recent consensus history
                time_window_minutes: Time window for recent activity

            Returns:
                Swarm status including active sessions, agent states, and metrics
            """
            result = asyncio.run(
                self.memory_sync.handle_tool_call(
                    "get_swarm_overview",
                    {
                        "include_history": include_history,
                        "time_window_minutes": time_window_minutes,
                    },
                )
            )
            return {"status": "success", "content": [{"text": str(result)}]}

        return [initiate_consensus, submit_vote, get_swarm_overview]

    async def call_tool(
        self, tool_name: str, function_name: str, arguments: Dict[str, Any]
    ) -> Any:
        """Call a specific MCP tool function."""
        tool_map = {
            "metrics_monitor": self.metrics_monitor,
            "container_ops": self.container_ops,
            "inference_engine": self.inference_engine,
            "telemetry_logger": self.telemetry_logger,
            "memory_sync": self.memory_sync,
        }

        if tool_name not in tool_map:
            raise ValueError(f"Unknown tool: {tool_name}")

        tool_instance = tool_map[tool_name]
        return await tool_instance.handle_tool_call(function_name, arguments)


# Global instance for easy access
mcp_integration = MCPToolIntegration()


def get_mcp_tools_for_agent(agent_type: str) -> List[Any]:
    """Get Strands-compatible MCP tools for a specific agent type."""
    tool_map = {
        "orchestrator": mcp_integration.get_orchestrator_tools,
        "load_balancer": mcp_integration.get_load_balancer_tools,
        "decision_coordinator": mcp_integration.get_decision_coordinator_tools,
        "cache_manager": mcp_integration.get_cache_manager_tools,
        "resource_monitor": mcp_integration.get_resource_monitor_tools,
    }

    if agent_type not in tool_map:
        return []

    return tool_map[agent_type]()


async def call_mcp_tool(
    tool_name: str, function_name: str, arguments: Dict[str, Any]
) -> Any:
    """Convenience function to call MCP tools."""
    return await mcp_integration.call_tool(tool_name, function_name, arguments)
