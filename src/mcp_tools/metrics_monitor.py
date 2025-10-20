"""
MCP Tool Server: Metrics Monitor

Provides real MEC site metrics data to agents for threshold monitoring
and site health assessment.
"""

import json
import random
import time
from datetime import UTC, datetime
from typing import Any, Dict, List

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Resource, Tool


class MetricsMonitorMCP:
    """MCP tool server for MEC site metrics monitoring."""

    def __init__(self, simulation_mode: bool = True):
        self.simulation_mode = simulation_mode
        self.mec_sites = {
            "MEC_A": {
                "base_cpu": 45.0,
                "base_gpu": 30.0,
                "base_memory": 55.0,
                "base_queue": 15,
                "base_latency": 25.0,
                "status": "healthy",
            },
            "MEC_B": {
                "base_cpu": 65.0,
                "base_gpu": 70.0,
                "base_memory": 60.0,
                "base_queue": 35,
                "base_latency": 45.0,
                "status": "healthy",
            },
            "MEC_C": {
                "base_cpu": 25.0,
                "base_gpu": 20.0,
                "base_memory": 40.0,
                "base_queue": 8,
                "base_latency": 15.0,
                "status": "healthy",
            },
        }
        self.last_update = time.time()

    def get_tools(self) -> List[Tool]:
        """Return available MCP tools."""
        return [
            Tool(
                name="get_mec_metrics",
                description="Get current metrics for a specific MEC site",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "site_id": {
                            "type": "string",
                            "description": "MEC site identifier (MEC_A, MEC_B, MEC_C)",
                        }
                    },
                    "required": ["site_id"],
                },
            ),
            Tool(
                name="get_all_mec_metrics",
                description="Get current metrics for all MEC sites",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="check_site_health",
                description="Check health status of a specific MEC site",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "site_id": {
                            "type": "string",
                            "description": "MEC site identifier",
                        }
                    },
                    "required": ["site_id"],
                },
            ),
            Tool(
                name="get_healthy_sites",
                description="Get list of all healthy MEC sites",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="monitor_thresholds",
                description="Check if any sites exceed performance thresholds",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "cpu_threshold": {"type": "number", "default": 80.0},
                        "gpu_threshold": {"type": "number", "default": 80.0},
                        "latency_threshold": {
                            "type": "number",
                            "default": 100.0,
                        },
                        "queue_threshold": {"type": "number", "default": 50},
                    },
                },
            ),
            Tool(
                name="ping_mec_site",
                description="Check network latency between MEC sites",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "source_site": {"type": "string"},
                        "target_site": {"type": "string"},
                    },
                    "required": ["source_site", "target_site"],
                },
            ),
        ]

    def _generate_realistic_metrics(self, site_id: str) -> Dict[str, Any]:
        """Generate realistic metrics with variance for simulation."""
        if site_id not in self.mec_sites:
            raise ValueError(f"Unknown MEC site: {site_id}")

        base = self.mec_sites[site_id]
        current_time = time.time()

        # Add time-based variance and random fluctuations
        time_factor = 1 + 0.1 * random.sin(current_time / 60)  # 60-second cycle
        variance = random.uniform(0.8, 1.2)

        # Simulate threshold breaches occasionally
        breach_probability = 0.05  # 5% chance of breach
        if random.random() < breach_probability:
            breach_multiplier = random.uniform(1.5, 2.0)
        else:
            breach_multiplier = 1.0

        cpu_util = min(
            95.0, base["base_cpu"] * time_factor * variance * breach_multiplier
        )
        gpu_util = min(
            95.0, base["base_gpu"] * time_factor * variance * breach_multiplier
        )
        memory_util = min(
            95.0,
            base["base_memory"] * time_factor * variance * breach_multiplier,
        )
        queue_depth = max(
            0,
            int(base["base_queue"] * time_factor * variance * breach_multiplier),
        )
        latency = max(
            5.0,
            base["base_latency"] * time_factor * variance * breach_multiplier,
        )

        # Determine health status
        is_healthy = (
            cpu_util < 80.0
            and gpu_util < 80.0
            and memory_util < 80.0
            and queue_depth < 50
            and latency < 100.0
        )

        return {
            "site_id": site_id,
            "cpu_utilization": round(cpu_util, 2),
            "gpu_utilization": round(gpu_util, 2),
            "memory_utilization": round(memory_util, 2),
            "queue_depth": queue_depth,
            "response_time_ms": round(latency, 2),
            "network_latency": self._get_network_latency(site_id),
            "status": "healthy" if is_healthy else "overloaded",
            "capacity_score": round(max(0.1, 1.0 - (cpu_util + gpu_util) / 200.0), 2),
            "timestamp": datetime.now(UTC).isoformat(),
            "last_updated": current_time,
        }

    def _get_network_latency(self, site_id: str) -> Dict[str, float]:
        """Get network latency to other MEC sites."""
        latencies = {}
        for other_site in self.mec_sites:
            if other_site != site_id:
                # Base latency with some variance
                base_latency = 15.0 + abs(hash(site_id + other_site)) % 20
                variance = random.uniform(0.8, 1.2)
                latencies[other_site] = round(base_latency * variance, 2)
        return latencies

    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Handle MCP tool calls."""
        if name == "get_mec_metrics":
            site_id = arguments["site_id"]
            return self._generate_realistic_metrics(site_id)

        elif name == "get_all_mec_metrics":
            return {
                site_id: self._generate_realistic_metrics(site_id)
                for site_id in self.mec_sites
            }

        elif name == "check_site_health":
            site_id = arguments["site_id"]
            metrics = self._generate_realistic_metrics(site_id)
            return {
                "site_id": site_id,
                "is_healthy": metrics["status"] == "healthy",
                "status": metrics["status"],
                "health_score": metrics["capacity_score"],
                "issues": self._identify_health_issues(metrics),
            }

        elif name == "get_healthy_sites":
            healthy_sites = []
            for site_id in self.mec_sites:
                metrics = self._generate_realistic_metrics(site_id)
                if metrics["status"] == "healthy":
                    healthy_sites.append(
                        {
                            "site_id": site_id,
                            "capacity_score": metrics["capacity_score"],
                            "response_time_ms": metrics["response_time_ms"],
                        }
                    )
            return sorted(
                healthy_sites, key=lambda x: x["capacity_score"], reverse=True
            )

        elif name == "monitor_thresholds":
            cpu_threshold = arguments.get("cpu_threshold", 80.0)
            gpu_threshold = arguments.get("gpu_threshold", 80.0)
            latency_threshold = arguments.get("latency_threshold", 100.0)
            queue_threshold = arguments.get("queue_threshold", 50)

            breaches = []
            for site_id in self.mec_sites:
                metrics = self._generate_realistic_metrics(site_id)
                site_breaches = []

                if metrics["cpu_utilization"] > cpu_threshold:
                    site_breaches.append(
                        {
                            "metric": "cpu_utilization",
                            "value": metrics["cpu_utilization"],
                            "threshold": cpu_threshold,
                        }
                    )

                if metrics["gpu_utilization"] > gpu_threshold:
                    site_breaches.append(
                        {
                            "metric": "gpu_utilization",
                            "value": metrics["gpu_utilization"],
                            "threshold": gpu_threshold,
                        }
                    )

                if metrics["response_time_ms"] > latency_threshold:
                    site_breaches.append(
                        {
                            "metric": "response_time_ms",
                            "value": metrics["response_time_ms"],
                            "threshold": latency_threshold,
                        }
                    )

                if metrics["queue_depth"] > queue_threshold:
                    site_breaches.append(
                        {
                            "metric": "queue_depth",
                            "value": metrics["queue_depth"],
                            "threshold": queue_threshold,
                        }
                    )

                if site_breaches:
                    breaches.append({"site_id": site_id, "breaches": site_breaches})

            return {
                "total_breaches": len(breaches),
                "sites_with_breaches": breaches,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        elif name == "ping_mec_site":
            source_site = arguments["source_site"]
            target_site = arguments["target_site"]

            if source_site == target_site:
                return {"latency_ms": 0.0, "status": "same_site"}

            # Simulate network latency with some variance
            base_latency = 15.0 + abs(hash(source_site + target_site)) % 20
            variance = random.uniform(0.8, 1.2)
            latency = round(base_latency * variance, 2)

            return {
                "source_site": source_site,
                "target_site": target_site,
                "latency_ms": latency,
                "status": "success",
                "timestamp": datetime.now(UTC).isoformat(),
            }

        else:
            raise ValueError(f"Unknown tool: {name}")

    def _identify_health_issues(self, metrics: Dict[str, Any]) -> List[str]:
        """Identify specific health issues from metrics."""
        issues = []
        if metrics["cpu_utilization"] > 80.0:
            issues.append(f"High CPU utilization: {metrics['cpu_utilization']}%")
        if metrics["gpu_utilization"] > 80.0:
            issues.append(f"High GPU utilization: {metrics['gpu_utilization']}%")
        if metrics["memory_utilization"] > 80.0:
            issues.append(f"High memory utilization: {metrics['memory_utilization']}%")
        if metrics["queue_depth"] > 50:
            issues.append(f"High queue depth: {metrics['queue_depth']} requests")
        if metrics["response_time_ms"] > 100.0:
            issues.append(f"High latency: {metrics['response_time_ms']}ms")
        return issues


# Standalone function for easy integration
def create_metrics_monitor_tool() -> MetricsMonitorMCP:
    """Create a metrics monitor MCP tool instance."""
    return MetricsMonitorMCP(simulation_mode=True)


if __name__ == "__main__":
    # Test the MCP tool
    import asyncio

    async def test_metrics_monitor():
        tool = create_metrics_monitor_tool()

        # Test getting metrics for a site
        metrics = await tool.handle_tool_call("get_mec_metrics", {"site_id": "MEC_A"})
        print("MEC_A Metrics:", json.dumps(metrics, indent=2))

        # Test threshold monitoring
        breaches = await tool.handle_tool_call("monitor_thresholds", {})
        print("Threshold Breaches:", json.dumps(breaches, indent=2))

    asyncio.run(test_metrics_monitor())
