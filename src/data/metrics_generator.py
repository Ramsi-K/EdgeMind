"""
MEC Metrics Data Generator for EdgeMind orchestration system.

This module provides realistic MEC metrics generation with configurable
threshold breach scenarios, time-series data with variance, and synthetic
data patterns for simulation purposes.
"""

import math
import random
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from config import MECConfig, MECSiteConfig, ThresholdConfig


class MetricType(Enum):
    """Types of metrics that can be generated."""

    CPU_UTILIZATION = "cpu_utilization"
    GPU_UTILIZATION = "gpu_utilization"
    MEMORY_UTILIZATION = "memory_utilization"
    NETWORK_LATENCY = "network_latency"
    QUEUE_DEPTH = "queue_depth"
    RESPONSE_TIME = "response_time"


class OperationMode(Enum):
    """Operation modes for metric generation."""

    NORMAL = "normal"
    THRESHOLD_BREACH = "threshold_breach"
    SWARM_ACTIVE = "swarm_active"
    MEC_FAILURE = "mec_failure"


@dataclass
class MECMetrics:
    """Data class representing MEC site metrics at a point in time."""

    site_id: str
    timestamp: datetime
    cpu_utilization: float  # percentage (0-100)
    gpu_utilization: float  # percentage (0-100)
    memory_utilization: float  # percentage (0-100)
    queue_depth: int  # number of pending requests
    network_latency: dict[str, float]  # latency to other MEC sites in ms
    response_time_ms: float  # average response time in ms
    requests_per_second: int  # current RPS
    active_connections: int  # number of active connections
    cache_hit_ratio: float  # percentage (0-100)

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary format."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MECMetrics":
        """Create MECMetrics from dictionary."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class MECMetricsGenerator:
    """
    Generates realistic MEC metrics with configurable patterns and scenarios.

    Features:
    - Realistic baseline patterns with natural variance
    - Configurable threshold breach scenarios
    - Time-series data generation with trends
    - Multiple operation modes (normal, breach, swarm, failure)
    - Correlated metrics (CPU spike affects latency, etc.)
    """

    def __init__(self, config: MECConfig):
        self.config = config
        self.thresholds = config.thresholds
        self.mec_sites = config.mec_sites

        # Internal state for time-series generation
        self._baseline_values: dict[str, dict[str, float]] = {}
        self._trend_factors: dict[str, dict[str, float]] = {}
        self._breach_scenarios: dict[str, dict[str, Any]] = {}
        self._operation_mode = OperationMode.NORMAL
        self._scenario_start_time: datetime | None = None
        self._scenario_duration_seconds = 30  # Default scenario duration

        self._initialize_baseline_values()
        self._initialize_trend_factors()

    def _initialize_baseline_values(self) -> None:
        """Initialize baseline values for each MEC site."""
        for site_id in self.mec_sites:
            self._baseline_values[site_id] = {
                "cpu_utilization": random.uniform(20.0, 40.0),
                "gpu_utilization": random.uniform(15.0, 35.0),
                "memory_utilization": random.uniform(30.0, 50.0),
                "queue_depth": random.randint(5, 15),
                "response_time_ms": random.uniform(25.0, 45.0),
                "requests_per_second": random.randint(50, 150),
                "active_connections": random.randint(100, 300),
                "cache_hit_ratio": random.uniform(75.0, 90.0),
            }

    def _initialize_trend_factors(self) -> None:
        """Initialize trend factors for gradual changes over time."""
        for site_id in self.mec_sites:
            self._trend_factors[site_id] = {
                "cpu_trend": random.uniform(-0.1, 0.1),
                "gpu_trend": random.uniform(-0.1, 0.1),
                "memory_trend": random.uniform(-0.05, 0.05),
                "latency_trend": random.uniform(-0.02, 0.02),
            }

    def set_operation_mode(
        self,
        mode: OperationMode,
        target_site: str | None = None,
        duration_seconds: int = 30,
    ) -> None:
        """
        Set the operation mode for metric generation.

        Args:
            mode: The operation mode to set
            target_site: Target MEC site for scenarios (if applicable)
            duration_seconds: Duration of the scenario
        """
        self._operation_mode = mode
        self._scenario_start_time = datetime.now(UTC)
        self._scenario_duration_seconds = duration_seconds

        if mode == OperationMode.THRESHOLD_BREACH and target_site:
            self._setup_breach_scenario(target_site)

    def _setup_breach_scenario(self, site_id: str) -> None:
        """Setup a threshold breach scenario for a specific site."""
        scenario_type = random.choice(["cpu_spike", "latency_spike", "queue_overload"])

        if scenario_type == "cpu_spike":
            self._breach_scenarios[site_id] = {
                "type": "cpu_spike",
                "target_cpu": random.uniform(85.0, 95.0),
                "target_gpu": random.uniform(70.0, 85.0),
                "spike_duration": random.randint(10, 25),
            }
        elif scenario_type == "latency_spike":
            self._breach_scenarios[site_id] = {
                "type": "latency_spike",
                "target_latency": random.uniform(120.0, 180.0),
                "affected_connections": random.choice(["all", "partial"]),
                "spike_duration": random.randint(15, 30),
            }
        elif scenario_type == "queue_overload":
            self._breach_scenarios[site_id] = {
                "type": "queue_overload",
                "target_queue_depth": random.randint(60, 100),
                "target_response_time": random.uniform(150.0, 250.0),
                "overload_duration": random.randint(20, 35),
            }

    def generate_metrics(self, site_id: str) -> MECMetrics:
        """
        Generate current metrics for a specific MEC site.

        Args:
            site_id: The MEC site identifier

        Returns:
            MECMetrics object with current values
        """
        if site_id not in self.mec_sites:
            msg = f"Unknown MEC site: {site_id}"
            raise ValueError(msg)

        site_config = self.mec_sites[site_id]
        current_time = datetime.now(UTC)

        # Check if we're in a scenario and if it should end
        if self._scenario_start_time:
            elapsed = (current_time - self._scenario_start_time).total_seconds()
            if elapsed > self._scenario_duration_seconds:
                self._operation_mode = OperationMode.NORMAL
                self._scenario_start_time = None
                self._breach_scenarios.clear()

        # Generate base metrics with variance
        base_metrics = self._generate_base_metrics(site_id, current_time)

        # Apply operation mode modifications
        if self._operation_mode == OperationMode.THRESHOLD_BREACH:
            base_metrics = self._apply_breach_scenario(site_id, base_metrics)
        elif self._operation_mode == OperationMode.SWARM_ACTIVE:
            base_metrics = self._apply_swarm_coordination_effects(site_id, base_metrics)
        elif self._operation_mode == OperationMode.MEC_FAILURE:
            base_metrics = self._apply_failure_scenario(site_id, base_metrics)

        # Generate network latency to other sites
        network_latency = self._generate_network_latency(site_id, site_config)

        return MECMetrics(
            site_id=site_id,
            timestamp=current_time,
            cpu_utilization=base_metrics["cpu_utilization"],
            gpu_utilization=base_metrics["gpu_utilization"],
            memory_utilization=base_metrics["memory_utilization"],
            queue_depth=base_metrics["queue_depth"],
            network_latency=network_latency,
            response_time_ms=base_metrics["response_time_ms"],
            requests_per_second=base_metrics["requests_per_second"],
            active_connections=base_metrics["active_connections"],
            cache_hit_ratio=base_metrics["cache_hit_ratio"],
        )

    def _generate_base_metrics(
        self,
        site_id: str,
        current_time: datetime,
    ) -> dict[str, Any]:
        """Generate base metrics with natural variance and trends."""
        baseline = self._baseline_values[site_id]
        trends = self._trend_factors[site_id]

        # Time-based factors for realistic patterns
        time_factor = math.sin(current_time.timestamp() / 3600) * 0.1  # Hourly pattern
        daily_factor = (
            math.sin(current_time.timestamp() / 86400) * 0.05
        )  # Daily pattern

        # Generate metrics with variance and trends
        cpu_util = self._apply_variance_and_bounds(
            baseline["cpu_utilization"] + trends["cpu_trend"] + time_factor * 10,
            variance=5.0,
            min_val=0.0,
            max_val=100.0,
        )

        gpu_util = self._apply_variance_and_bounds(
            baseline["gpu_utilization"] + trends["gpu_trend"] + time_factor * 8,
            variance=4.0,
            min_val=0.0,
            max_val=100.0,
        )

        memory_util = self._apply_variance_and_bounds(
            baseline["memory_utilization"] + trends["memory_trend"] + daily_factor * 5,
            variance=3.0,
            min_val=0.0,
            max_val=100.0,
        )

        # Queue depth correlates with CPU usage
        queue_base = baseline["queue_depth"] + (cpu_util - 30) * 0.5
        queue_depth = max(
            0,
            int(
                self._apply_variance_and_bounds(
                    queue_base,
                    variance=3.0,
                    min_val=0,
                    max_val=200,
                ),
            ),
        )

        # Response time correlates with queue depth and CPU
        response_base = (
            baseline["response_time_ms"] + queue_depth * 0.8 + (cpu_util - 30) * 0.3
        )
        response_time = self._apply_variance_and_bounds(
            response_base,
            variance=5.0,
            min_val=10.0,
            max_val=500.0,
        )

        # RPS inversely correlates with response time
        rps_base = baseline["requests_per_second"] * (50.0 / max(response_time, 25.0))
        requests_per_second = max(
            1,
            int(
                self._apply_variance_and_bounds(
                    rps_base,
                    variance=10.0,
                    min_val=1,
                    max_val=1000,
                ),
            ),
        )

        active_connections = max(
            10,
            int(
                self._apply_variance_and_bounds(
                    baseline["active_connections"] + requests_per_second * 0.5,
                    variance=20.0,
                    min_val=10,
                    max_val=2000,
                ),
            ),
        )

        cache_hit_ratio = self._apply_variance_and_bounds(
            baseline["cache_hit_ratio"] - (cpu_util - 30) * 0.1,
            variance=2.0,
            min_val=50.0,
            max_val=99.0,
        )

        return {
            "cpu_utilization": cpu_util,
            "gpu_utilization": gpu_util,
            "memory_utilization": memory_util,
            "queue_depth": queue_depth,
            "response_time_ms": response_time,
            "requests_per_second": requests_per_second,
            "active_connections": active_connections,
            "cache_hit_ratio": cache_hit_ratio,
        }

    def _apply_variance_and_bounds(
        self,
        base_value: float,
        variance: float,
        min_val: float,
        max_val: float,
    ) -> float:
        """Apply random variance to a value and enforce bounds."""
        varied_value = base_value + random.gauss(0, variance)
        return max(min_val, min(max_val, varied_value))

    def _apply_breach_scenario(
        self,
        site_id: str,
        base_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """Apply threshold breach scenario modifications."""
        if site_id not in self._breach_scenarios:
            return base_metrics

        scenario = self._breach_scenarios[site_id]
        scenario_type = scenario["type"]

        if scenario_type == "cpu_spike":
            base_metrics["cpu_utilization"] = scenario["target_cpu"]
            base_metrics["gpu_utilization"] = scenario["target_gpu"]
            # CPU spike affects other metrics
            base_metrics["response_time_ms"] *= 1.5
            base_metrics["queue_depth"] = int(base_metrics["queue_depth"] * 1.8)

        elif scenario_type == "latency_spike":
            base_metrics["response_time_ms"] = scenario["target_latency"]
            # High latency affects queue buildup
            base_metrics["queue_depth"] = int(base_metrics["queue_depth"] * 2.0)
            base_metrics["requests_per_second"] = int(
                base_metrics["requests_per_second"] * 0.6,
            )

        elif scenario_type == "queue_overload":
            base_metrics["queue_depth"] = scenario["target_queue_depth"]
            base_metrics["response_time_ms"] = scenario["target_response_time"]
            base_metrics["cpu_utilization"] = min(
                95.0,
                base_metrics["cpu_utilization"] * 1.3,
            )

        return base_metrics

    def _apply_swarm_coordination_effects(
        self,
        site_id: str,
        base_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """Apply effects of active swarm coordination."""
        # During swarm coordination, there's increased inter-MEC communication
        # and some load redistribution effects
        base_metrics["cpu_utilization"] = min(
            100.0,
            base_metrics["cpu_utilization"] * 1.1,
        )
        base_metrics["response_time_ms"] *= 0.9  # Improved through load balancing
        base_metrics["queue_depth"] = int(
            base_metrics["queue_depth"] * 0.8,
        )  # Better distribution

        return base_metrics

    def _apply_failure_scenario(
        self,
        site_id: str,
        base_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """Apply MEC site failure scenario."""
        # Simulate degraded performance or complete failure
        failure_severity = random.choice(["partial", "severe"])

        if failure_severity == "partial":
            base_metrics["cpu_utilization"] = min(
                100.0,
                base_metrics["cpu_utilization"] * 1.5,
            )
            base_metrics["response_time_ms"] *= 2.0
            base_metrics["queue_depth"] = int(base_metrics["queue_depth"] * 3.0)
            base_metrics["cache_hit_ratio"] *= 0.7
        else:  # severe
            base_metrics["cpu_utilization"] = 0.0
            base_metrics["gpu_utilization"] = 0.0
            base_metrics["response_time_ms"] = 999.0
            base_metrics["queue_depth"] = 0
            base_metrics["requests_per_second"] = 0
            base_metrics["active_connections"] = 0

        return base_metrics

    def _generate_network_latency(
        self,
        site_id: str,
        site_config: MECSiteConfig,
    ) -> dict[str, float]:
        """Generate network latency to other MEC sites."""
        latency_map = {}
        base_latencies = site_config.network_latency_ms

        for target_site, base_latency in base_latencies.items():
            # Add realistic variance to network latency
            if self._operation_mode == OperationMode.MEC_FAILURE:
                # High latency during failures
                latency = base_latency * random.uniform(3.0, 8.0)
            elif self._operation_mode == OperationMode.SWARM_ACTIVE:
                # Slightly higher latency during coordination
                latency = base_latency * random.uniform(1.1, 1.3)
            else:
                # Normal variance
                latency = base_latency * random.uniform(0.8, 1.2)

            latency_map[target_site] = round(latency, 2)

        return latency_map

    def generate_time_series(
        self,
        site_id: str,
        duration_minutes: int = 60,
        interval_seconds: int = 5,
    ) -> list[MECMetrics]:
        """
        Generate a time series of metrics for analysis and testing.

        Args:
            site_id: MEC site identifier
            duration_minutes: Duration of the time series
            interval_seconds: Interval between data points

        Returns:
            List of MECMetrics objects representing the time series
        """
        metrics_series = []
        start_time = datetime.now(UTC)
        total_points = (duration_minutes * 60) // interval_seconds

        for i in range(total_points):
            # Simulate time progression
            current_time = start_time + timedelta(seconds=i * interval_seconds)

            # Inject some scenarios during the time series
            if i == total_points // 4:  # 25% through, start breach scenario
                self.set_operation_mode(OperationMode.THRESHOLD_BREACH, site_id, 120)
            elif i == total_points // 2:  # 50% through, swarm coordination
                self.set_operation_mode(OperationMode.SWARM_ACTIVE, duration_seconds=60)
            elif i == 3 * total_points // 4:  # 75% through, back to normal
                self.set_operation_mode(OperationMode.NORMAL)

            metrics = self.generate_metrics(site_id)
            metrics.timestamp = current_time  # Override with series time
            metrics_series.append(metrics)

        return metrics_series

    def get_current_thresholds(self) -> ThresholdConfig:
        """Get current threshold configuration."""
        return self.thresholds

    def is_threshold_breached(self, metrics: MECMetrics) -> dict[str, bool]:
        """
        Check if any thresholds are breached for given metrics.

        Args:
            metrics: MECMetrics to check

        Returns:
            Dictionary mapping metric names to breach status
        """
        breaches = {
            "cpu_utilization": metrics.cpu_utilization
            > self.thresholds.cpu_threshold_percent,
            "gpu_utilization": metrics.gpu_utilization
            > self.thresholds.gpu_threshold_percent,
            "memory_utilization": metrics.memory_utilization
            > self.thresholds.memory_threshold_percent,
            "queue_depth": metrics.queue_depth > self.thresholds.queue_depth_threshold,
            "response_time": metrics.response_time_ms
            > self.thresholds.latency_threshold_ms,
        }

        # Check network latency thresholds
        for target_site, latency in metrics.network_latency.items():
            breaches[f"network_latency_{target_site}"] = (
                latency > self.thresholds.network_latency_threshold_ms
            )

        return breaches

    def get_breach_summary(self, metrics: MECMetrics) -> dict[str, Any]:
        """
        Get a summary of threshold breaches for given metrics.

        Args:
            metrics: MECMetrics to analyze

        Returns:
            Summary dictionary with breach information
        """
        breaches = self.is_threshold_breached(metrics)
        breach_count = sum(breaches.values())

        return {
            "site_id": metrics.site_id,
            "timestamp": metrics.timestamp.isoformat(),
            "total_breaches": breach_count,
            "has_breaches": breach_count > 0,
            "breached_metrics": [
                metric for metric, breached in breaches.items() if breached
            ],
            "breach_details": breaches,
            "severity": (
                "high"
                if breach_count >= 3
                else "medium" if breach_count >= 1 else "low"
            ),
        }
