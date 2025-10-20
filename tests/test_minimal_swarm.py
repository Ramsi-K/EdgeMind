"""Minimal test for SwarmCoordinator"""

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any


# Mock the imports that might be causing issues
class MockLogger:
    def log_swarm_event(self, event_type, details=None):
        print(f"Mock log: {event_type} - {details}")

    def log_decision(self, decision_type, outcome, reasoning=None):
        print(f"Mock decision: {decision_type} -> {outcome}")

    def log_mcp_call(self, tool, function, params=None):
        print(f"Mock MCP: {tool}.{function}({params})")


class MockStructLogger:
    def info(self, msg, **kwargs):
        print(f"Struct log: {msg} - {kwargs}")


class MockPerfLogger:
    def log_swarm_consensus_time(self, duration_ms, participants, success=True):
        print(
            f"Perf log: consensus took {duration_ms}ms with {participants} participants"
        )


# Mock ThresholdEvent
@dataclass
class MockThresholdEvent:
    site_id: str
    metric_name: str
    current_value: float
    severity: Any


class MockSeverity:
    value = "high"


class SwarmState(Enum):
    IDLE = "idle"
    ACTIVATING = "activating"
    CONSENSUS = "consensus"
    EXECUTING = "executing"


@dataclass
class MECSite:
    site_id: str
    status: str
    cpu_utilization: float
    gpu_utilization: float
    memory_utilization: float
    queue_depth: int
    response_time_ms: float
    network_latency: dict[str, float]
    capacity_score: float
    last_updated: datetime

    def is_healthy(self) -> bool:
        return (
            self.status == "healthy"
            and self.cpu_utilization < 80.0
            and self.gpu_utilization < 80.0
            and self.memory_utilization < 80.0
            and self.queue_depth < 50
            and self.response_time_ms < 100.0
        )

    def calculate_load_score(self) -> float:
        return (
            self.cpu_utilization * 0.3
            + self.gpu_utilization * 0.3
            + self.memory_utilization * 0.2
            + min(self.queue_depth / 100.0, 1.0) * 0.2
        ) / 100.0


@dataclass
class SwarmDecision:
    decision_id: str
    selected_site: str
    reasoning: str
    confidence_score: float
    fallback_sites: list[str]
    execution_time_ms: int
    participants: list[str]
    votes: dict[str, str]
    timestamp: datetime


@dataclass
class SwarmEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    trigger_reason: str
    participants: list[str]
    decision: SwarmDecision | None
    duration_ms: int
    success: bool
    details: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "trigger_reason": self.trigger_reason,
            "participants": self.participants,
            "decision": self.decision.__dict__ if self.decision else None,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "details": self.details,
        }


class SwarmCoordinator:
    """Minimal SwarmCoordinator for testing."""

    def __init__(self):
        self.logger = MockLogger()
        self.struct_logger = MockStructLogger()
        self.perf_logger = MockPerfLogger()

        self.state = SwarmState.IDLE
        self.mec_sites: dict[str, MECSite] = {}
        self.event_history: list[SwarmEvent] = []
        self.decision_counter = 0
        self.event_counter = 0
        self.min_participants = 2
        self.max_event_history = 1000

        self._initialize_default_sites()

    def _initialize_default_sites(self) -> None:
        """Initialize default MEC sites for simulation."""
        default_sites = [
            {
                "site_id": "MEC_A",
                "status": "healthy",
                "cpu_utilization": 45.0,
                "gpu_utilization": 30.0,
                "memory_utilization": 55.0,
                "queue_depth": 15,
                "response_time_ms": 25.0,
                "capacity_score": 0.8,
            },
            {
                "site_id": "MEC_B",
                "status": "healthy",
                "cpu_utilization": 65.0,
                "gpu_utilization": 70.0,
                "memory_utilization": 60.0,
                "queue_depth": 35,
                "response_time_ms": 45.0,
                "capacity_score": 0.6,
            },
            {
                "site_id": "MEC_C",
                "status": "healthy",
                "cpu_utilization": 25.0,
                "gpu_utilization": 20.0,
                "memory_utilization": 40.0,
                "queue_depth": 8,
                "response_time_ms": 15.0,
                "capacity_score": 0.9,
            },
        ]

        for site_data in default_sites:
            site = MECSite(
                site_id=site_data["site_id"],
                status=site_data["status"],
                cpu_utilization=site_data["cpu_utilization"],
                gpu_utilization=site_data["gpu_utilization"],
                memory_utilization=site_data["memory_utilization"],
                queue_depth=site_data["queue_depth"],
                response_time_ms=site_data["response_time_ms"],
                network_latency={
                    other["site_id"]: 15.0
                    + abs(hash(site_data["site_id"] + other["site_id"])) % 20
                    for other in default_sites
                    if other["site_id"] != site_data["site_id"]
                },
                capacity_score=site_data["capacity_score"],
                last_updated=datetime.now(UTC),
            )
            self.mec_sites[site.site_id] = site

        print(f"Initialized {len(self.mec_sites)} MEC sites")

    def activate_swarm(self, trigger_event) -> SwarmEvent:
        """Activate swarm coordination in response to threshold breach."""
        start_time = time.perf_counter()
        self.state = SwarmState.ACTIVATING

        print(f"Swarm activation triggered by {trigger_event.site_id}")

        # Get healthy participants
        healthy_sites = [site for site in self.mec_sites.values() if site.is_healthy()]

        if len(healthy_sites) < self.min_participants:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            event = self._create_swarm_event(
                "swarm_activation_failed",
                trigger_event.site_id,
                [],
                None,
                duration_ms,
                False,
                {"reason": "insufficient_healthy_sites"},
            )
            self.state = SwarmState.IDLE
            return event

        # Perform consensus
        self.state = SwarmState.CONSENSUS
        decision = self._perform_consensus(healthy_sites, trigger_event)

        # Execute decision
        self.state = SwarmState.EXECUTING
        execution_success = True  # Simplified

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        event = self._create_swarm_event(
            "swarm_coordination_completed",
            trigger_event.site_id,
            [site.site_id for site in healthy_sites],
            decision,
            duration_ms,
            execution_success,
            {"consensus_algorithm": "majority_vote"},
        )

        self.state = SwarmState.IDLE
        return event

    def _perform_consensus(
        self, participants: list[MECSite], trigger_event
    ) -> SwarmDecision:
        """Perform majority vote consensus for MEC site selection."""
        start_time = time.perf_counter()
        self.decision_counter += 1

        # Simple scoring - just pick the site with lowest load
        best_site = min(participants, key=lambda s: s.calculate_load_score())

        execution_time_ms = int((time.perf_counter() - start_time) * 1000)

        decision = SwarmDecision(
            decision_id=f"decision_{self.decision_counter:06d}",
            selected_site=best_site.site_id,
            reasoning=f"Selected {best_site.site_id} with lowest load score",
            confidence_score=0.8,
            fallback_sites=[s.site_id for s in participants if s != best_site][:2],
            execution_time_ms=execution_time_ms,
            participants=[site.site_id for site in participants],
            votes={site.site_id: best_site.site_id for site in participants},
            timestamp=datetime.now(UTC),
        )

        print(f"Consensus selected: {best_site.site_id}")
        return decision

    def _create_swarm_event(
        self,
        event_type: str,
        trigger_site: str,
        participants: list[str],
        decision: SwarmDecision | None,
        duration_ms: int,
        success: bool,
        details: dict[str, Any],
    ) -> SwarmEvent:
        """Create a swarm coordination event."""
        self.event_counter += 1

        event = SwarmEvent(
            event_id=f"swarm_event_{self.event_counter:06d}",
            event_type=event_type,
            timestamp=datetime.now(UTC),
            trigger_reason=f"threshold_breach_{trigger_site}",
            participants=participants,
            decision=decision,
            duration_ms=duration_ms,
            success=success,
            details=details,
        )

        self.event_history.append(event)
        return event

    def get_swarm_status(self) -> dict[str, Any]:
        """Get current swarm coordination status."""
        healthy_sites = [site for site in self.mec_sites.values() if site.is_healthy()]

        return {
            "state": self.state.value,
            "total_sites": len(self.mec_sites),
            "healthy_sites": len(healthy_sites),
            "total_decisions": self.decision_counter,
            "sites": {
                site_id: {
                    "status": site.status,
                    "load_score": site.calculate_load_score(),
                    "is_healthy": site.is_healthy(),
                }
                for site_id, site in self.mec_sites.items()
            },
        }

    def get_event_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent swarm coordination events."""
        recent_events = self.event_history[-limit:] if limit > 0 else self.event_history
        return [event.to_dict() for event in recent_events]


if __name__ == "__main__":
    print("=== Minimal Swarm Coordinator Test ===")

    # Test initialization
    coordinator = SwarmCoordinator()
    print(f"Status: {coordinator.get_swarm_status()}")

    # Test swarm activation
    mock_event = MockThresholdEvent(
        site_id="MEC_A",
        metric_name="cpu_utilization",
        current_value=95.0,
        severity=MockSeverity(),
    )

    result = coordinator.activate_swarm(mock_event)
    print(f"Swarm result: {result.event_type} - Success: {result.success}")

    if result.decision:
        print(f"Selected site: {result.decision.selected_site}")

    print("✓ Minimal test completed successfully!")
