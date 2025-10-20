"""
Threshold Monitor for EdgeMind MEC orchestration system.

This module implements threshold monitoring logic that detects breaches
and generates events with timestamps and severity levels for swarm coordination.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import structlog

from config import ThresholdConfig
from src.data.metrics_generator import MECMetrics
from src.logging_config import AgentActivityLogger


class SeverityLevel(Enum):
    """Severity levels for threshold breach events."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(Enum):
    """Types of threshold monitoring events."""

    THRESHOLD_BREACH = "threshold_breach"
    THRESHOLD_RECOVERY = "threshold_recovery"
    MONITORING_ERROR = "monitoring_error"
    SYSTEM_HEALTHY = "system_healthy"


@dataclass
class ThresholdEvent:
    """Data class representing a threshold monitoring event."""

    event_id: str
    event_type: EventType
    severity: SeverityLevel
    timestamp: datetime
    site_id: str
    metric_name: str
    current_value: float
    threshold_value: float
    breach_duration_ms: int
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary format."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "site_id": self.site_id,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "breach_duration_ms": self.breach_duration_ms,
            "details": self.details,
        }


class ThresholdMonitor:
    """
    Monitors MEC metrics against configurable thresholds and generates events.

    Features:
    - Configurable thresholds for latency, CPU, GPU, queue depth, memory
    - Breach detection with severity classification
    - Event generation with timestamps and structured logging
    - Breach duration tracking
    - Recovery detection
    - Callback system for swarm coordination triggers
    """

    def __init__(self, thresholds: ThresholdConfig):
        self.thresholds = thresholds
        self.logger = AgentActivityLogger("ThresholdMonitor")
        self.struct_logger = structlog.get_logger("threshold_monitor")

        # Internal state tracking
        self._breach_states: dict[str, dict[str, dict[str, Any]]] = {}
        self._event_counter = 0
        self._callbacks: list[Callable[[ThresholdEvent], None]] = []

        # Performance tracking
        self._last_check_time: dict[str, float] = {}
        self._check_count = 0

    def add_breach_callback(self, callback: Callable[[ThresholdEvent], None]) -> None:
        """
        Add a callback function to be called when threshold breaches occur.

        Args:
            callback: Function to call with ThresholdEvent when breach detected
        """
        self._callbacks.append(callback)

    def remove_breach_callback(
        self,
        callback: Callable[[ThresholdEvent], None],
    ) -> None:
        """Remove a previously added breach callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def check_thresholds(  # noqa: C901
        self,
        metrics: MECMetrics,
    ) -> list[ThresholdEvent]:
        """
        Check all thresholds against provided metrics and generate events.

        Args:
            metrics: MECMetrics object to check against thresholds

        Returns:
            List of ThresholdEvent objects for any breaches or recoveries
        """
        start_time = time.perf_counter()
        events = []
        site_id = metrics.site_id

        # Initialize breach state for site if not exists
        if site_id not in self._breach_states:
            self._breach_states[site_id] = {}

        # Check each threshold
        threshold_checks = [
            (
                "cpu_utilization",
                metrics.cpu_utilization,
                self.thresholds.cpu_threshold_percent,
            ),
            (
                "gpu_utilization",
                metrics.gpu_utilization,
                self.thresholds.gpu_threshold_percent,
            ),
            (
                "memory_utilization",
                metrics.memory_utilization,
                self.thresholds.memory_threshold_percent,
            ),
            (
                "queue_depth",
                float(metrics.queue_depth),
                float(self.thresholds.queue_depth_threshold),
            ),
            (
                "response_time",
                metrics.response_time_ms,
                float(self.thresholds.latency_threshold_ms),
            ),
        ]

        for metric_name, current_value, threshold_value in threshold_checks:
            event = self._check_single_threshold(
                site_id,
                metric_name,
                current_value,
                threshold_value,
                metrics.timestamp,
            )
            if event:
                events.append(event)

        # Check network latency thresholds
        for target_site, latency in metrics.network_latency.items():
            metric_name = f"network_latency_{target_site}"
            event = self._check_single_threshold(
                site_id,
                metric_name,
                latency,
                float(self.thresholds.network_latency_threshold_ms),
                metrics.timestamp,
            )
            if event:
                events.append(event)

        # Log performance metrics
        check_duration = (time.perf_counter() - start_time) * 1000
        self._check_count += 1
        self._last_check_time[site_id] = check_duration

        if events:
            self.struct_logger.info(
                "Threshold check completed",
                site_id=site_id,
                events_generated=len(events),
                check_duration_ms=check_duration,
                total_checks=self._check_count,
            )

        # Trigger callbacks for breach events
        for event in events:
            if event.event_type == EventType.THRESHOLD_BREACH:
                for callback in self._callbacks:
                    try:
                        callback(event)
                    except Exception:
                        self.struct_logger.exception(
                            "Callback execution failed",
                            callback=callback.__name__,
                            event_id=event.event_id,
                        )

        return events

    def _check_single_threshold(
        self,
        site_id: str,
        metric_name: str,
        current_value: float,
        threshold_value: float,
        timestamp: datetime,
    ) -> ThresholdEvent | None:
        """Check a single threshold and generate event if needed."""
        is_breached = current_value > threshold_value

        # Get current breach state
        current_breach_state = self._breach_states[site_id].get(
            metric_name,
            {
                "is_breached": False,
                "breach_start_time": None,
                "last_value": None,
            },
        )

        was_breached = current_breach_state["is_breached"]

        if is_breached and not was_breached:
            # New breach detected
            event = self._create_breach_event(
                site_id,
                metric_name,
                current_value,
                threshold_value,
                timestamp,
            )

            # Update breach state
            self._breach_states[site_id][metric_name] = {
                "is_breached": True,
                "breach_start_time": timestamp,
                "last_value": current_value,
            }

            self.logger.log_threshold_breach(
                metric_name,
                current_value,
                threshold_value,
            )
            return event

        if not is_breached and was_breached:
            # Recovery detected
            breach_start = current_breach_state["breach_start_time"]
            breach_duration = (
                int((timestamp - breach_start).total_seconds() * 1000)
                if breach_start
                else 0
            )

            event = self._create_recovery_event(
                site_id,
                metric_name,
                current_value,
                threshold_value,
                timestamp,
                breach_duration,
            )

            # Update breach state
            self._breach_states[site_id][metric_name] = {
                "is_breached": False,
                "breach_start_time": None,
                "last_value": current_value,
            }

            self.struct_logger.info(
                "Threshold recovery detected",
                site_id=site_id,
                metric=metric_name,
                current_value=current_value,
                threshold=threshold_value,
                breach_duration_ms=breach_duration,
            )
            return event

        if is_breached and was_breached:
            # Ongoing breach - update state but don't generate new event
            self._breach_states[site_id][metric_name]["last_value"] = current_value

        return None

    def _create_breach_event(
        self,
        site_id: str,
        metric_name: str,
        current_value: float,
        threshold_value: float,
        timestamp: datetime,
    ) -> ThresholdEvent:
        """Create a threshold breach event."""
        self._event_counter += 1
        severity = self._calculate_severity(metric_name, current_value, threshold_value)

        return ThresholdEvent(
            event_id=f"breach_{self._event_counter:06d}",
            event_type=EventType.THRESHOLD_BREACH,
            severity=severity,
            timestamp=timestamp,
            site_id=site_id,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            breach_duration_ms=0,  # New breach
            details={
                "breach_ratio": current_value / threshold_value,
                "threshold_type": "upper_bound",
                "monitoring_system": "EdgeMind-ThresholdMonitor",
            },
        )

    def _create_recovery_event(
        self,
        site_id: str,
        metric_name: str,
        current_value: float,
        threshold_value: float,
        timestamp: datetime,
        breach_duration_ms: int,
    ) -> ThresholdEvent:
        """Create a threshold recovery event."""
        self._event_counter += 1

        return ThresholdEvent(
            event_id=f"recovery_{self._event_counter:06d}",
            event_type=EventType.THRESHOLD_RECOVERY,
            severity=SeverityLevel.LOW,
            timestamp=timestamp,
            site_id=site_id,
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            breach_duration_ms=breach_duration_ms,
            details={
                "recovery_ratio": current_value / threshold_value,
                "breach_duration_ms": breach_duration_ms,
                "monitoring_system": "EdgeMind-ThresholdMonitor",
            },
        )

    def _calculate_severity(  # noqa: C901, PLR0911
        self,
        metric_name: str,
        current_value: float,
        threshold_value: float,
    ) -> SeverityLevel:
        """Calculate severity level based on how much threshold is exceeded."""
        breach_ratio = current_value / threshold_value

        # Critical thresholds for different metrics
        if metric_name in [
            "cpu_utilization",
            "gpu_utilization",
            "memory_utilization",
        ]:
            if breach_ratio >= 1.2:  # 20% over threshold
                return SeverityLevel.CRITICAL
            if breach_ratio >= 1.1:  # 10% over threshold
                return SeverityLevel.HIGH
            if breach_ratio >= 1.05:  # 5% over threshold
                return SeverityLevel.MEDIUM
            return SeverityLevel.LOW

        if metric_name == "queue_depth":
            if breach_ratio >= 2.0:  # Double the threshold
                return SeverityLevel.CRITICAL
            if breach_ratio >= 1.5:  # 50% over threshold
                return SeverityLevel.HIGH
            if breach_ratio >= 1.2:  # 20% over threshold
                return SeverityLevel.MEDIUM
            return SeverityLevel.LOW

        if metric_name == "response_time" or "network_latency" in metric_name:
            if breach_ratio >= 3.0:  # 3x threshold
                return SeverityLevel.CRITICAL
            if breach_ratio >= 2.0:  # 2x threshold
                return SeverityLevel.HIGH
            if breach_ratio >= 1.5:  # 50% over threshold
                return SeverityLevel.MEDIUM
            return SeverityLevel.LOW

        # Default severity calculation
        if breach_ratio >= 2.0:
            return SeverityLevel.CRITICAL
        if breach_ratio >= 1.5:
            return SeverityLevel.HIGH
        if breach_ratio >= 1.2:
            return SeverityLevel.MEDIUM
        return SeverityLevel.LOW

    def get_current_breach_status(self, site_id: str) -> dict[str, Any]:
        """
        Get current breach status for a MEC site.

        Args:
            site_id: MEC site identifier

        Returns:
            Dictionary with current breach status information
        """
        if site_id not in self._breach_states:
            return {
                "site_id": site_id,
                "has_active_breaches": False,
                "active_breaches": [],
                "breach_count": 0,
            }

        site_breaches = self._breach_states[site_id]
        active_breaches = []

        for metric_name, state in site_breaches.items():
            if state["is_breached"]:
                breach_duration = 0
                if state["breach_start_time"]:
                    breach_duration = int(
                        (datetime.now(UTC) - state["breach_start_time"]).total_seconds()
                        * 1000,
                    )

                active_breaches.append(
                    {
                        "metric_name": metric_name,
                        "current_value": state["last_value"],
                        "breach_duration_ms": breach_duration,
                        "breach_start_time": (
                            state["breach_start_time"].isoformat()
                            if state["breach_start_time"]
                            else None
                        ),
                    },
                )

        return {
            "site_id": site_id,
            "has_active_breaches": len(active_breaches) > 0,
            "active_breaches": active_breaches,
            "breach_count": len(active_breaches),
        }

    def get_monitoring_stats(self) -> dict[str, Any]:
        """Get monitoring performance statistics."""
        return {
            "total_checks": self._check_count,
            "total_events": self._event_counter,
            "monitored_sites": list(self._breach_states.keys()),
            "average_check_time_ms": (
                sum(self._last_check_time.values()) / len(self._last_check_time)
                if self._last_check_time
                else 0
            ),
            "active_callbacks": len(self._callbacks),
        }

    def reset_monitoring_state(self) -> None:
        """Reset all monitoring state (useful for testing)."""
        self._breach_states.clear()
        self._event_counter = 0
        self._last_check_time.clear()
        self._check_count = 0

        self.struct_logger.info("Threshold monitoring state reset")
