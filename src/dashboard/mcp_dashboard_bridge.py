"""
MCP Dashboard Bridge

Connects MCP tool calls to Streamlit dashboard real-time display.
Provides data feed for agent activity stream and metrics panels.
"""

import asyncio
import json
import time
from datetime import UTC, datetime
from typing import Any, Dict, List

from src.mcp_tools.mcp_integration import mcp_integration


class MCPDashboardBridge:
    """Bridge between MCP tools and Streamlit dashboard."""

    def __init__(self):
        self.activity_stream = []
        self.metrics_cache = {}
        self.swarm_events = []
        self.container_operations = []
        self.max_activity_entries = 1000
        self.last_update = time.time()

    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for dashboard display."""
        try:
            # Get metrics from all MEC sites
            all_metrics = await mcp_integration.call_tool(
                "metrics_monitor", "get_all_mec_metrics", {}
            )

            # Cache the metrics
            self.metrics_cache = {
                "metrics": all_metrics,
                "timestamp": datetime.now(UTC).isoformat(),
                "last_update": time.time(),
            }

            # Add to activity stream
            self._add_activity_entry(
                {
                    "type": "metrics_update",
                    "source": "metrics_monitor",
                    "data": {"sites_updated": len(all_metrics)},
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

            return self.metrics_cache

        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
                "metrics": {},
            }

    async def get_swarm_visualization_data(self) -> Dict[str, Any]:
        """Get swarm coordination data for visualization panel."""
        try:
            # Get swarm overview from memory sync
            swarm_overview = await mcp_integration.call_tool(
                "memory_sync", "get_swarm_overview", {"include_history": True}
            )

            # Get container status for all sites
            container_data = {}
            for site_id in ["MEC_A", "MEC_B", "MEC_C"]:
                try:
                    status = await mcp_integration.call_tool(
                        "container_ops",
                        "get_container_status",
                        {"site_id": site_id},
                    )
                    container_data[site_id] = status
                except Exception:
                    container_data[site_id] = {"error": "unavailable"}

            visualization_data = {
                "swarm_overview": swarm_overview,
                "container_status": container_data,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            # Add to activity stream
            self._add_activity_entry(
                {
                    "type": "swarm_update",
                    "source": "memory_sync",
                    "data": {
                        "active_sessions": swarm_overview.get("swarm_overview", {}).get(
                            "active_sessions", 0
                        ),
                        "total_agents": swarm_overview.get("swarm_overview", {}).get(
                            "total_agents", 0
                        ),
                    },
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

            return visualization_data

        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
                "swarm_overview": {},
                "container_status": {},
            }

    async def get_agent_activity_stream(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get agent activity stream for dashboard display."""
        try:
            # Get recent telemetry events
            recent_events = await mcp_integration.call_tool(
                "telemetry_logger",
                "get_recent_events",
                {
                    "limit": limit,
                    "time_window_minutes": 30,
                },
            )

            # Combine with local activity stream
            all_activities = []

            # Add telemetry events
            for event in recent_events.get("events", []):
                all_activities.append(
                    {
                        "type": "telemetry_event",
                        "source": "telemetry_logger",
                        "event_type": event.get("event_type"),
                        "agent_id": event.get("agent_id"),
                        "site_id": event.get("site_id"),
                        "details": event.get("details", {}),
                        "timestamp": event.get("timestamp"),
                        "success": event.get("success", True),
                    }
                )

            # Add local activity entries
            all_activities.extend(self.activity_stream[-limit:])

            # Sort by timestamp (most recent first)
            all_activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            return all_activities[:limit]

        except Exception as e:
            return [
                {
                    "type": "error",
                    "source": "dashboard_bridge",
                    "details": {"error": str(e)},
                    "timestamp": datetime.now(UTC).isoformat(),
                    "success": False,
                }
            ]

    async def simulate_agent_mcp_calls(self) -> Dict[str, Any]:
        """Simulate agent MCP tool calls for dashboard demonstration."""
        simulation_results = []

        try:
            # Simulate orchestrator checking metrics
            metrics_result = await mcp_integration.call_tool(
                "metrics_monitor",
                "monitor_thresholds",
                {
                    "cpu_threshold": 80.0,
                    "gpu_threshold": 80.0,
                    "latency_threshold": 100.0,
                },
            )

            simulation_results.append(
                {
                    "agent": "orchestrator_MEC_A",
                    "tool": "metrics_monitor",
                    "function": "monitor_thresholds",
                    "result": metrics_result,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

            # Simulate load balancer scaling containers
            if metrics_result.get("total_breaches", 0) > 0:
                scaling_result = await mcp_integration.call_tool(
                    "container_ops",
                    "scale_containers",
                    {
                        "site_id": "MEC_A",
                        "scaling_factor": 1.2,
                    },
                )

                simulation_results.append(
                    {
                        "agent": "load_balancer_MEC_B",
                        "tool": "container_ops",
                        "function": "scale_containers",
                        "result": scaling_result,
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )

            # Simulate cache manager checking model status
            cache_result = await mcp_integration.call_tool(
                "inference_engine",
                "get_model_cache_status",
                {"site_id": "MEC_A"},
            )

            simulation_results.append(
                {
                    "agent": "cache_manager_MEC_B",
                    "tool": "inference_engine",
                    "function": "get_model_cache_status",
                    "result": cache_result,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

            # Log all simulated activities
            for result in simulation_results:
                await mcp_integration.call_tool(
                    "telemetry_logger",
                    "log_mcp_call",
                    {
                        "tool_name": result["tool"],
                        "function_name": result["function"],
                        "agent_id": result["agent"],
                        "response": result["result"],
                        "success": True,
                    },
                )

                self._add_activity_entry(
                    {
                        "type": "mcp_call",
                        "source": result["agent"],
                        "tool": result["tool"],
                        "function": result["function"],
                        "success": result["result"].get("success", True),
                        "timestamp": result["timestamp"],
                    }
                )

            return {
                "simulation_results": simulation_results,
                "total_calls": len(simulation_results),
                "timestamp": datetime.now(UTC).isoformat(),
                "success": True,
            }

        except Exception as e:
            return {
                "error": str(e),
                "simulation_results": simulation_results,
                "timestamp": datetime.now(UTC).isoformat(),
                "success": False,
            }

    async def trigger_swarm_coordination(self) -> Dict[str, Any]:
        """Trigger a swarm coordination session for dashboard demonstration."""
        try:
            # Initiate consensus session
            consensus_result = await mcp_integration.call_tool(
                "memory_sync",
                "initiate_consensus",
                {
                    "initiator_agent": "orchestrator_MEC_A",
                    "consensus_topic": "threshold_breach_response",
                    "participants": [
                        "orchestrator_MEC_A",
                        "load_balancer_MEC_B",
                        "decision_coordinator_MEC_C",
                        "resource_monitor_MEC_A",
                        "cache_manager_MEC_B",
                    ],
                    "context_data": {
                        "trigger": "cpu_threshold_breach",
                        "affected_site": "MEC_A",
                        "severity": "high",
                    },
                },
            )

            session_id = consensus_result.get("session_id")

            if session_id:
                # Simulate votes from agents
                votes = [
                    {
                        "agent_id": "orchestrator_MEC_A",
                        "vote_data": {"selected_site": "MEC_C"},
                        "confidence": 0.85,
                        "reasoning": "MEC_C has lowest CPU utilization",
                    },
                    {
                        "agent_id": "load_balancer_MEC_B",
                        "vote_data": {"selected_site": "MEC_C"},
                        "confidence": 0.90,
                        "reasoning": "MEC_C has best capacity score",
                    },
                    {
                        "agent_id": "decision_coordinator_MEC_C",
                        "vote_data": {"selected_site": "MEC_C"},
                        "confidence": 0.80,
                        "reasoning": "Consensus favors MEC_C",
                    },
                ]

                vote_results = []
                for vote in votes:
                    vote_result = await mcp_integration.call_tool(
                        "memory_sync",
                        "submit_vote",
                        {
                            "session_id": session_id,
                            **vote,
                        },
                    )
                    vote_results.append(vote_result)

                # Log the coordination event
                await mcp_integration.call_tool(
                    "telemetry_logger",
                    "log_decision",
                    {
                        "decision_type": "swarm_coordination",
                        "decision_data": {
                            "session_id": session_id,
                            "consensus_reached": True,
                            "selected_site": "MEC_C",
                        },
                        "agent_id": "decision_coordinator_MEC_C",
                        "confidence_score": 0.85,
                        "execution_time_ms": 150,
                    },
                )

                self._add_activity_entry(
                    {
                        "type": "swarm_coordination",
                        "source": "memory_sync",
                        "data": {
                            "session_id": session_id,
                            "participants": len(votes),
                            "consensus_reached": True,
                        },
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )

                return {
                    "consensus_result": consensus_result,
                    "vote_results": vote_results,
                    "coordination_success": True,
                    "timestamp": datetime.now(UTC).isoformat(),
                }

            return {
                "error": "Failed to create consensus session",
                "consensus_result": consensus_result,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
                "coordination_success": False,
            }

    def _add_activity_entry(self, entry: Dict[str, Any]) -> None:
        """Add entry to activity stream with size management."""
        self.activity_stream.append(entry)

        # Maintain size limit
        if len(self.activity_stream) > self.max_activity_entries:
            self.activity_stream = self.activity_stream[-self.max_activity_entries :]

    def get_dashboard_status(self) -> Dict[str, Any]:
        """Get overall dashboard bridge status."""
        return {
            "bridge_active": True,
            "activity_entries": len(self.activity_stream),
            "metrics_cached": bool(self.metrics_cache),
            "last_update": self.last_update,
            "mcp_tools_available": [
                "metrics_monitor",
                "container_ops",
                "inference_engine",
                "telemetry_logger",
                "memory_sync",
            ],
            "timestamp": datetime.now(UTC).isoformat(),
        }


# Global instance for dashboard integration
dashboard_bridge = MCPDashboardBridge()


async def get_dashboard_data() -> Dict[str, Any]:
    """Get comprehensive dashboard data."""
    return {
        "metrics": await dashboard_bridge.get_real_time_metrics(),
        "swarm_data": await dashboard_bridge.get_swarm_visualization_data(),
        "activity_stream": await dashboard_bridge.get_agent_activity_stream(),
        "bridge_status": dashboard_bridge.get_dashboard_status(),
    }


if __name__ == "__main__":
    # Test the dashboard bridge
    async def test_dashboard_bridge():
        bridge = MCPDashboardBridge()

        # Test metrics
        metrics = await bridge.get_real_time_metrics()
        print("Metrics:", json.dumps(metrics, indent=2))

        # Test activity stream
        activities = await bridge.get_agent_activity_stream(limit=5)
        print("Activities:", json.dumps(activities, indent=2))

    asyncio.run(test_dashboard_bridge())
