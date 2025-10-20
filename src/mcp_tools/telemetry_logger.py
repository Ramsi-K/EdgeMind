"""
MCP Tool Server: Telemetry Logger

Provides structured event logging and metrics collection for MEC orchestration.
Handles agent activity logging, performance metrics, and observability data.
"""

import json
import time
from datetime import UTC, datetime
from typing import Any, Dict, List

from mcp.types import Tool


class TelemetryLoggerMCP:
    """MCP tool server for structured event logging and metrics collection."""

    def __init__(self, simulation_mode: bool = True):
        self.simulation_mode = simulation_mode
        self.event_log = []
        self.metrics_buffer = []
        self.anomaly_reports = []
        self.performance_data = {}
        self.max_log_entries = 10000

    def get_tools(self) -> List[Tool]:
        """Return available MCP tools."""
        return [
            Tool(
                name="log_decision",
                description="Log a swarm coordination decision with context",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "decision_type": {"type": "string"},
                        "decision_data": {"type": "object"},
                        "agent_id": {"type": "string"},
                        "site_id": {"type": "string"},
                        "confidence_score": {"type": "number"},
                        "execution_time_ms": {"type": "integer"},
                    },
                    "required": ["decision_type", "decision_data", "agent_id"],
                },
            ),
            Tool(
                name="send_metrics",
                description="Send performance metrics to telemetry system",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "metric_type": {"type": "string"},
                        "metrics": {"type": "object"},
                        "site_id": {"type": "string"},
                        "agent_id": {"type": "string"},
                        "tags": {"type": "object"},
                    },
                    "required": ["metric_type", "metrics"],
                },
            ),
            Tool(
                name="report_anomaly",
                description="Report an anomaly or unusual behavior",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "anomaly_type": {"type": "string"},
                        "severity": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                        },
                        "description": {"type": "string"},
                        "affected_components": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "metrics": {"type": "object"},
                        "site_id": {"type": "string"},
                        "agent_id": {"type": "string"},
                    },
                    "required": ["anomaly_type", "severity", "description"],
                },
            ),
            Tool(
                name="log_agent_activity",
                description="Log agent activity and interactions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "activity_type": {"type": "string"},
                        "details": {"type": "object"},
                        "site_id": {"type": "string"},
                        "duration_ms": {"type": "integer"},
                        "success": {"type": "boolean"},
                    },
                    "required": ["agent_id", "activity_type", "details"],
                },
            ),
            Tool(
                name="log_mcp_call",
                description="Log MCP tool calls and responses",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tool_name": {"type": "string"},
                        "function_name": {"type": "string"},
                        "parameters": {"type": "object"},
                        "response": {"type": "object"},
                        "agent_id": {"type": "string"},
                        "execution_time_ms": {"type": "integer"},
                        "success": {"type": "boolean"},
                    },
                    "required": ["tool_name", "function_name", "agent_id"],
                },
            ),
            Tool(
                name="get_recent_events",
                description="Retrieve recent telemetry events",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "event_type": {"type": "string"},
                        "site_id": {"type": "string"},
                        "agent_id": {"type": "string"},
                        "limit": {"type": "integer", "default": 50},
                        "time_window_minutes": {
                            "type": "integer",
                            "default": 60,
                        },
                    },
                },
            ),
            Tool(
                name="get_performance_summary",
                description="Get performance metrics summary",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "site_id": {"type": "string"},
                        "metric_types": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "time_window_minutes": {
                            "type": "integer",
                            "default": 60,
                        },
                    },
                },
            ),
            Tool(
                name="export_telemetry_data",
                description="Export telemetry data for analysis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "enum": ["json", "csv"],
                            "default": "json",
                        },
                        "data_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "default": ["events", "metrics", "anomalies"],
                        },
                        "time_range_hours": {"type": "integer", "default": 24},
                    },
                },
            ),
        ]

    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Handle MCP tool calls."""
        if name == "log_decision":
            return await self._log_decision(arguments)
        elif name == "send_metrics":
            return await self._send_metrics(arguments)
        elif name == "report_anomaly":
            return await self._report_anomaly(arguments)
        elif name == "log_agent_activity":
            return await self._log_agent_activity(arguments)
        elif name == "log_mcp_call":
            return await self._log_mcp_call(arguments)
        elif name == "get_recent_events":
            return await self._get_recent_events(arguments)
        elif name == "get_performance_summary":
            return await self._get_performance_summary(arguments)
        elif name == "export_telemetry_data":
            return await self._export_telemetry_data(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _log_decision(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Log a swarm coordination decision."""
        event = {
            "event_id": f"decision_{len(self.event_log) + 1:06d}",
            "event_type": "decision",
            "timestamp": datetime.now(UTC).isoformat(),
            "decision_type": arguments["decision_type"],
            "decision_data": arguments["decision_data"],
            "agent_id": arguments["agent_id"],
            "site_id": arguments.get("site_id"),
            "confidence_score": arguments.get("confidence_score"),
            "execution_time_ms": arguments.get("execution_time_ms"),
            "tags": ["swarm_coordination", "decision_making"],
        }

        self._add_event(event)

        return {
            "event_id": event["event_id"],
            "logged": True,
            "timestamp": event["timestamp"],
            "success": True,
        }

    async def _send_metrics(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Send performance metrics to telemetry system."""
        metric_entry = {
            "metric_id": f"metric_{len(self.metrics_buffer) + 1:06d}",
            "timestamp": datetime.now(UTC).isoformat(),
            "metric_type": arguments["metric_type"],
            "metrics": arguments["metrics"],
            "site_id": arguments.get("site_id"),
            "agent_id": arguments.get("agent_id"),
            "tags": arguments.get("tags", {}),
        }

        self.metrics_buffer.append(metric_entry)

        # Also log as event
        event = {
            "event_id": f"metrics_{len(self.event_log) + 1:06d}",
            "event_type": "metrics",
            "timestamp": metric_entry["timestamp"],
            "metric_type": arguments["metric_type"],
            "site_id": arguments.get("site_id"),
            "agent_id": arguments.get("agent_id"),
            "metric_count": len(arguments["metrics"]),
            "tags": ["performance_metrics", arguments["metric_type"]],
        }

        self._add_event(event)

        return {
            "metric_id": metric_entry["metric_id"],
            "sent": True,
            "timestamp": metric_entry["timestamp"],
            "success": True,
        }

    async def _report_anomaly(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Report an anomaly or unusual behavior."""
        anomaly = {
            "anomaly_id": f"anomaly_{len(self.anomaly_reports) + 1:06d}",
            "timestamp": datetime.now(UTC).isoformat(),
            "anomaly_type": arguments["anomaly_type"],
            "severity": arguments["severity"],
            "description": arguments["description"],
            "affected_components": arguments.get("affected_components", []),
            "metrics": arguments.get("metrics", {}),
            "site_id": arguments.get("site_id"),
            "agent_id": arguments.get("agent_id"),
            "status": "reported",
        }

        self.anomaly_reports.append(anomaly)

        # Log as high-priority event
        event = {
            "event_id": f"anomaly_{len(self.event_log) + 1:06d}",
            "event_type": "anomaly",
            "timestamp": anomaly["timestamp"],
            "anomaly_type": arguments["anomaly_type"],
            "severity": arguments["severity"],
            "description": arguments["description"],
            "site_id": arguments.get("site_id"),
            "agent_id": arguments.get("agent_id"),
            "tags": [
                "anomaly",
                arguments["severity"],
                arguments["anomaly_type"],
            ],
        }

        self._add_event(event)

        return {
            "anomaly_id": anomaly["anomaly_id"],
            "reported": True,
            "severity": arguments["severity"],
            "timestamp": anomaly["timestamp"],
            "success": True,
        }

    async def _log_agent_activity(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Log agent activity and interactions."""
        event = {
            "event_id": f"activity_{len(self.event_log) + 1:06d}",
            "event_type": "agent_activity",
            "timestamp": datetime.now(UTC).isoformat(),
            "agent_id": arguments["agent_id"],
            "activity_type": arguments["activity_type"],
            "details": arguments["details"],
            "site_id": arguments.get("site_id"),
            "duration_ms": arguments.get("duration_ms"),
            "success": arguments.get("success", True),
            "tags": ["agent_activity", arguments["activity_type"]],
        }

        self._add_event(event)

        return {
            "event_id": event["event_id"],
            "logged": True,
            "timestamp": event["timestamp"],
            "success": True,
        }

    async def _log_mcp_call(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Log MCP tool calls and responses."""
        event = {
            "event_id": f"mcp_{len(self.event_log) + 1:06d}",
            "event_type": "mcp_call",
            "timestamp": datetime.now(UTC).isoformat(),
            "tool_name": arguments["tool_name"],
            "function_name": arguments["function_name"],
            "parameters": arguments.get("parameters", {}),
            "response": arguments.get("response", {}),
            "agent_id": arguments["agent_id"],
            "execution_time_ms": arguments.get("execution_time_ms"),
            "success": arguments.get("success", True),
            "tags": [
                "mcp_call",
                arguments["tool_name"],
                arguments["function_name"],
            ],
        }

        self._add_event(event)

        return {
            "event_id": event["event_id"],
            "logged": True,
            "timestamp": event["timestamp"],
            "success": True,
        }

    async def _get_recent_events(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve recent telemetry events."""
        event_type = arguments.get("event_type")
        site_id = arguments.get("site_id")
        agent_id = arguments.get("agent_id")
        limit = arguments.get("limit", 50)
        time_window_minutes = arguments.get("time_window_minutes", 60)

        # Filter events
        cutoff_time = time.time() - (time_window_minutes * 60)
        filtered_events = []

        for event in reversed(self.event_log):  # Most recent first
            event_time = datetime.fromisoformat(
                event["timestamp"].replace("Z", "+00:00")
            ).timestamp()

            if event_time < cutoff_time:
                continue

            # Apply filters
            if event_type and event.get("event_type") != event_type:
                continue
            if site_id and event.get("site_id") != site_id:
                continue
            if agent_id and event.get("agent_id") != agent_id:
                continue

            filtered_events.append(event)

            if len(filtered_events) >= limit:
                break

        return {
            "events": filtered_events,
            "total_events": len(filtered_events),
            "filters_applied": {
                "event_type": event_type,
                "site_id": site_id,
                "agent_id": agent_id,
                "time_window_minutes": time_window_minutes,
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def _get_performance_summary(
        self, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get performance metrics summary."""
        site_id = arguments.get("site_id")
        metric_types = arguments.get("metric_types", [])
        time_window_minutes = arguments.get("time_window_minutes", 60)

        # Filter metrics
        cutoff_time = time.time() - (time_window_minutes * 60)
        filtered_metrics = []

        for metric in self.metrics_buffer:
            metric_time = datetime.fromisoformat(
                metric["timestamp"].replace("Z", "+00:00")
            ).timestamp()

            if metric_time < cutoff_time:
                continue

            if site_id and metric.get("site_id") != site_id:
                continue
            if metric_types and metric.get("metric_type") not in metric_types:
                continue

            filtered_metrics.append(metric)

        # Calculate summary statistics
        summary = {
            "total_metrics": len(filtered_metrics),
            "metric_types": {},
            "sites": {},
            "agents": {},
        }

        for metric in filtered_metrics:
            # By metric type
            metric_type = metric.get("metric_type", "unknown")
            if metric_type not in summary["metric_types"]:
                summary["metric_types"][metric_type] = 0
            summary["metric_types"][metric_type] += 1

            # By site
            metric_site = metric.get("site_id", "unknown")
            if metric_site not in summary["sites"]:
                summary["sites"][metric_site] = 0
            summary["sites"][metric_site] += 1

            # By agent
            metric_agent = metric.get("agent_id", "unknown")
            if metric_agent not in summary["agents"]:
                summary["agents"][metric_agent] = 0
            summary["agents"][metric_agent] += 1

        return {
            "summary": summary,
            "time_window_minutes": time_window_minutes,
            "filters_applied": {
                "site_id": site_id,
                "metric_types": metric_types,
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def _export_telemetry_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Export telemetry data for analysis."""
        format_type = arguments.get("format", "json")
        data_types = arguments.get("data_types", ["events", "metrics", "anomalies"])
        time_range_hours = arguments.get("time_range_hours", 24)

        cutoff_time = time.time() - (time_range_hours * 3600)
        export_data = {}

        # Export events
        if "events" in data_types:
            filtered_events = [
                event
                for event in self.event_log
                if datetime.fromisoformat(
                    event["timestamp"].replace("Z", "+00:00")
                ).timestamp()
                > cutoff_time
            ]
            export_data["events"] = filtered_events

        # Export metrics
        if "metrics" in data_types:
            filtered_metrics = [
                metric
                for metric in self.metrics_buffer
                if datetime.fromisoformat(
                    metric["timestamp"].replace("Z", "+00:00")
                ).timestamp()
                > cutoff_time
            ]
            export_data["metrics"] = filtered_metrics

        # Export anomalies
        if "anomalies" in data_types:
            filtered_anomalies = [
                anomaly
                for anomaly in self.anomaly_reports
                if datetime.fromisoformat(
                    anomaly["timestamp"].replace("Z", "+00:00")
                ).timestamp()
                > cutoff_time
            ]
            export_data["anomalies"] = filtered_anomalies

        # Format data
        if format_type == "json":
            formatted_data = json.dumps(export_data, indent=2)
        else:  # CSV format would require more complex formatting
            formatted_data = str(export_data)

        return {
            "export_format": format_type,
            "data_types": data_types,
            "time_range_hours": time_range_hours,
            "total_records": sum(
                len(v) if isinstance(v, list) else 1 for v in export_data.values()
            ),
            "data_size_bytes": len(formatted_data),
            "export_timestamp": datetime.now(UTC).isoformat(),
            "success": True,
        }

    def _add_event(self, event: Dict[str, Any]) -> None:
        """Add event to log with size management."""
        self.event_log.append(event)

        # Maintain log size limit
        if len(self.event_log) > self.max_log_entries:
            self.event_log = self.event_log[-self.max_log_entries :]

    def get_stats(self) -> Dict[str, Any]:
        """Get telemetry system statistics."""
        return {
            "total_events": len(self.event_log),
            "total_metrics": len(self.metrics_buffer),
            "total_anomalies": len(self.anomaly_reports),
            "event_types": list(
                set(event.get("event_type") for event in self.event_log)
            ),
            "active_sites": list(
                set(
                    event.get("site_id")
                    for event in self.event_log
                    if event.get("site_id")
                )
            ),
            "active_agents": list(
                set(
                    event.get("agent_id")
                    for event in self.event_log
                    if event.get("agent_id")
                )
            ),
        }


# Standalone function for easy integration
def create_telemetry_logger_tool() -> TelemetryLoggerMCP:
    """Create a telemetry logger MCP tool instance."""
    return TelemetryLoggerMCP(simulation_mode=True)


if __name__ == "__main__":
    # Test the MCP tool
    import asyncio

    async def test_telemetry_logger():
        tool = create_telemetry_logger_tool()

        # Test logging a decision
        result = await tool.handle_tool_call(
            "log_decision",
            {
                "decision_type": "site_selection",
                "decision_data": {
                    "selected_site": "MEC_A",
                    "reason": "lowest_latency",
                },
                "agent_id": "orchestrator_MEC_A",
                "site_id": "MEC_A",
                "confidence_score": 0.85,
                "execution_time_ms": 45,
            },
        )
        print("Decision Log Result:", json.dumps(result, indent=2))

        # Test getting recent events
        events = await tool.handle_tool_call("get_recent_events", {"limit": 5})
        print("Recent Events:", json.dumps(events, indent=2))

    asyncio.run(test_telemetry_logger())
