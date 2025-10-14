"""
Logging configuration for EdgeMind MEC orchestration system.

This module provides structured logging configuration for agent activity
tracking,
performance monitoring, and system observability.
"""

import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog


def configure_logging(
    log_level: str = "INFO",
    log_format: str = "structured",
    *,
    enable_agent_activity: bool = True,
    enable_performance_metrics: bool = True,
) -> None:
    """
    Configure structured logging for the MEC orchestration system.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ("structured" or "plain")
        enable_agent_activity: Enable agent activity logging
        enable_performance_metrics: Enable performance metrics logging
    """

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            add_timestamp,
            add_mec_context,
            (
                structlog.processors.JSONRenderer()
                if log_format == "structured"
                else structlog.dev.ConsoleRenderer()
            ),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure file handlers
    if enable_agent_activity:
        setup_agent_activity_logger()

    if enable_performance_metrics:
        setup_performance_metrics_logger()


def add_timestamp(
    logger: Any,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Add timestamp to log events."""
    event_dict["timestamp"] = datetime.now(UTC).isoformat()
    return event_dict


def add_mec_context(
    logger: Any,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Add MEC-specific context to log events."""
    event_dict["system"] = "EdgeMind-MEC"
    event_dict["component"] = event_dict.get("component", "unknown")
    return event_dict


def setup_agent_activity_logger() -> None:
    """Set up dedicated logger for agent activity tracking."""
    agent_logger = logging.getLogger("agent_activity")
    agent_handler = logging.FileHandler("logs/agent_activity.log")
    agent_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    agent_handler.setFormatter(agent_formatter)
    agent_logger.addHandler(agent_handler)
    agent_logger.setLevel(logging.INFO)


def setup_performance_metrics_logger() -> None:
    """Set up dedicated logger for performance metrics."""
    perf_logger = logging.getLogger("performance_metrics")
    perf_handler = logging.FileHandler("logs/performance_metrics.log")
    perf_formatter = logging.Formatter("%(asctime)s - %(message)s")
    perf_handler.setFormatter(perf_formatter)
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(logging.INFO)


class AgentActivityLogger:
    """Specialized logger for agent activity tracking."""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = structlog.get_logger("agent_activity").bind(
            agent=agent_name,
            component="agent",
        )

    def log_mcp_call(
        self,
        tool_name: str,
        function_name: str,
        params: dict[str, Any] | None = None,
    ) -> None:
        """Log MCP tool function calls."""
        self.logger.info(
            "MCP tool call",
            tool=tool_name,
            function=function_name,
            parameters=params or {},
            action_type="mcp_call",
        )

    def log_swarm_event(
        self,
        event_type: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Log swarm coordination events."""
        self.logger.info(
            "Swarm event",
            event_type=event_type,
            details=details or {},
            action_type="swarm_coordination",
        )

    def log_threshold_breach(self, metric: str, value: float, threshold: float) -> None:
        """Log threshold breach events."""
        self.logger.warning(
            "Threshold breach detected",
            metric=metric,
            current_value=value,
            threshold=threshold,
            action_type="threshold_breach",
        )

    def log_decision(
        self,
        decision_type: str,
        outcome: str,
        reasoning: str | None = None,
    ) -> None:
        """Log agent decisions."""
        self.logger.info(
            "Agent decision",
            decision_type=decision_type,
            outcome=outcome,
            reasoning=reasoning,
            action_type="decision",
        )


class PerformanceMetricsLogger:
    """Specialized logger for performance metrics tracking."""

    def __init__(self):
        self.logger = structlog.get_logger("performance_metrics").bind(
            component="performance",
        )

    def log_response_time(
        self,
        operation: str,
        duration_ms: float,
        *,
        success: bool = True,
    ) -> None:
        """Log operation response times."""
        self.logger.info(
            "Performance metric",
            metric_type="response_time",
            operation=operation,
            duration_ms=duration_ms,
            success=success,
        )

    def log_resource_utilization(
        self,
        site_id: str,
        cpu_percent: float,
        gpu_percent: float,
        memory_percent: float,
    ) -> None:
        """Log resource utilization metrics."""
        self.logger.info(
            "Resource utilization",
            metric_type="resource_utilization",
            site_id=site_id,
            cpu_percent=cpu_percent,
            gpu_percent=gpu_percent,
            memory_percent=memory_percent,
        )

    def log_swarm_consensus_time(
        self,
        consensus_duration_ms: float,
        participants: int,
        *,
        success: bool = True,
    ) -> None:
        """Log swarm consensus performance."""
        self.logger.info(
            "Swarm consensus performance",
            metric_type="consensus_time",
            duration_ms=consensus_duration_ms,
            participants=participants,
            success=success,
        )


# Initialize logging based on environment variables
def init_logging_from_env() -> None:
    """Initialize logging configuration from environment variables."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_format = os.getenv("LOG_FORMAT", "structured")
    agent_activity_enabled = (
        os.getenv("AGENT_ACTIVITY_LOG_ENABLED", "true").lower() == "true"
    )
    performance_metrics_enabled = (
        os.getenv("PERFORMANCE_METRICS_LOG_ENABLED", "true").lower() == "true"
    )

    configure_logging(
        log_level=log_level,
        log_format=log_format,
        enable_agent_activity=agent_activity_enabled,
        enable_performance_metrics=performance_metrics_enabled,
    )


# Auto-initialize logging when module is imported
init_logging_from_env()
