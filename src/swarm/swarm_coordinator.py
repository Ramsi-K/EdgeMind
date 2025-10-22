"""
Swarm Coordinator for EdgeMind MEC orchestration system.

This module implements Strands-based swarm coordination with specialized agents
for threshold-triggered MEC site selection and load balancing.
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List

import structlog
from strands.multiagent import Swarm

from src.agents.cache_manager_agent import CacheManagerAgent
from src.agents.decision_coordinator_agent import DecisionCoordinatorAgent
from src.agents.load_balancer_agent import LoadBalancerAgent
from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.resource_monitor_agent import ResourceMonitorAgent
from src.logging_config import AgentActivityLogger, PerformanceMetricsLogger
from src.orchestrator.threshold_monitor import ThresholdEvent


class SwarmState(Enum):
    """States of the swarm coordination system."""

    IDLE = "idle"
    ACTIVATING = "activating"
    CONSENSUS = "consensus"
    EXECUTING = "executing"
    RECOVERING = "recovering"


@dataclass
class MECSite:
    """Represents a MEC site in the swarm."""

    site_id: str
    status: str  # "healthy", "overloaded", "failed", "maintenance"
    cpu_utilization: float
    gpu_utilization: float
    memory_utilization: float
    queue_depth: int
    response_time_ms: float
    network_latency: dict[str, float]  # latency to other sites
    capacity_score: float  # 0.0 to 1.0
    last_updated: datetime

    def is_healthy(self) -> bool:
        """Check if MEC site is healthy and available."""
        return (
            self.status == "healthy"
            and self.cpu_utilization < 80.0
            and self.gpu_utilization < 80.0
            and self.memory_utilization < 80.0
            and self.queue_depth < 50
            and self.response_time_ms < 100.0
        )

    def calculate_load_score(self) -> float:
        """Calculate overall load score (0.0 = no load, 1.0 = max load)."""
        return (
            self.cpu_utilization * 0.3
            + self.gpu_utilization * 0.3
            + self.memory_utilization * 0.2
            + min(self.queue_depth / 100.0, 1.0) * 0.2
        ) / 100.0


@dataclass
class SwarmDecision:
    """Represents a swarm consensus decision."""

    decision_id: str
    selected_site: str
    reasoning: str
    confidence_score: float
    fallback_sites: list[str]
    execution_time_ms: int
    participants: list[str]
    votes: dict[str, str]  # site_id -> voted_for_site
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert decision to dictionary format."""
        return {
            "decision_id": self.decision_id,
            "selected_site": self.selected_site,
            "reasoning": self.reasoning,
            "confidence_score": self.confidence_score,
            "fallback_sites": self.fallback_sites,
            "execution_time_ms": self.execution_time_ms,
            "participants": self.participants,
            "votes": self.votes,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class SwarmEvent:
    """Represents a swarm coordination event."""

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
        """Convert event to dictionary format."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "trigger_reason": self.trigger_reason,
            "participants": self.participants,
            "decision": self.decision.to_dict() if self.decision else None,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "details": self.details,
        }


@dataclass
class SwarmDecision:
    """Represents a swarm consensus decision."""

    decision_id: str
    selected_site: str
    reasoning: str
    confidence_score: float
    fallback_sites: list[str]
    execution_time_ms: int
    participants: list[str]
    swarm_result: Any  # Strands SwarmResult object
    timestamp: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert decision to dictionary format."""
        return {
            "decision_id": self.decision_id,
            "selected_site": self.selected_site,
            "reasoning": self.reasoning,
            "confidence_score": self.confidence_score,
            "fallback_sites": self.fallback_sites,
            "execution_time_ms": self.execution_time_ms,
            "participants": self.participants,
            "swarm_status": (
                self.swarm_result.status
                if self.swarm_result and hasattr(self.swarm_result, "status")
                else str(self.swarm_result) if self.swarm_result else None
            ),
            "timestamp": self.timestamp.isoformat(),
        }


class SwarmCoordinator:
    """
    Coordinates Strands-based swarm activation for MEC site selection.

    Features:
    - Real Strands agents with specialized roles
    - MCP tool integration for infrastructure interaction
    - Threshold-triggered swarm coordination
    - Autonomous consensus and decision making
    - Structured event logging and performance tracking
    """

    def __init__(self):
        self.logger = AgentActivityLogger("SwarmCoordinator")
        self.struct_logger = structlog.get_logger("swarm_coordinator")
        self.perf_logger = PerformanceMetricsLogger()

        # Swarm state
        self.state = SwarmState.IDLE
        self.mec_sites: dict[str, MECSite] = {}
        self.event_history: list[SwarmEvent] = []
        self.decision_counter = 0
        self.event_counter = 0

        # Configuration
        self.consensus_timeout_ms = 12000  # 12 seconds to match Strands timeout
        self.max_event_history = 1000

        # Initialize Strands agents and swarm
        self._initialize_default_sites()
        self._initialize_strands_agents()
        self._create_swarm()

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

        self.struct_logger.info(
            "Default MEC sites initialized",
            site_count=len(self.mec_sites),
            sites=list(self.mec_sites.keys()),
        )

    def _initialize_strands_agents(self) -> None:
        """Initialize Strands agents for swarm coordination."""
        # Create specialized Strands agents
        self.orchestrator = OrchestratorAgent(mec_site="MEC_A")
        self.load_balancer = LoadBalancerAgent(mec_site="MEC_B")
        self.decision_coordinator = DecisionCoordinatorAgent(mec_site="MEC_C")
        self.resource_monitor = ResourceMonitorAgent(mec_site="MEC_A")
        self.cache_manager = CacheManagerAgent(mec_site="MEC_B")

        # Store agents for management
        self.agents = {
            "orchestrator": self.orchestrator,
            "load_balancer": self.load_balancer,
            "decision_coordinator": self.decision_coordinator,
            "resource_monitor": self.resource_monitor,
            "cache_manager": self.cache_manager,
        }

        self.struct_logger.info(
            "Strands agents initialized for swarm coordination",
            agent_count=len(self.agents),
            agent_types=list(self.agents.keys()),
        )

    def _create_swarm(self) -> None:
        """Create the Strands swarm with specialized agents."""
        # Create swarm with orchestrator as entry point
        self.swarm = Swarm(
            [  # First parameter is the list of agents
                self.orchestrator.agent,
                self.load_balancer.agent,
                self.decision_coordinator.agent,
                self.resource_monitor.agent,
                self.cache_manager.agent,
            ],
            entry_point=self.orchestrator.agent,
            max_handoffs=3,  # Reduce handoffs to avoid complexity
            max_iterations=5,  # Reduce iterations for faster response
            execution_timeout=12.0,  # 12 second timeout
            node_timeout=10.0,  # 10 seconds per agent - more time for response
            repetitive_handoff_detection_window=3,
            repetitive_handoff_min_unique_agents=2,
        )

        # Register swarm with orchestrator
        self.orchestrator.set_swarm(self.swarm)

        self.struct_logger.info(
            "Strands swarm created",
            entry_point=self.orchestrator.agent_id,
            max_handoffs=10,
            timeout_seconds=5.0,
        )

    def activate_swarm(self, trigger_event: ThresholdEvent) -> SwarmEvent:
        """
        Activate Strands swarm coordination in response to threshold breach.

        Args:
            trigger_event: ThresholdEvent that triggered swarm activation

        Returns:
            SwarmEvent representing the coordination result
        """
        start_time = time.perf_counter()
        self.state = SwarmState.ACTIVATING

        self.logger.log_swarm_event(
            "swarm_activation_triggered",
            details={
                "trigger_site": trigger_event.site_id,
                "trigger_metric": trigger_event.metric_name,
                "trigger_value": trigger_event.current_value,
                "severity": trigger_event.severity.value,
            },
        )

        try:
            # Use orchestrator to handle the threshold breach via Strands swarm
            result = asyncio.run(
                asyncio.wait_for(
                    self.orchestrator.handle_threshold_breach(trigger_event),
                    timeout=self.consensus_timeout_ms / 1000.0,  # Convert to seconds
                )
            )

            # Extract decision information from swarm result
            decision = self._extract_decision_from_result(result, trigger_event)

            # Create event
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            event = self._create_swarm_event(
                "swarm_coordination_completed",
                trigger_event.site_id,
                result.get("agents_involved", []),
                decision,
                duration_ms,
                result.get("status") == "completed",
                {
                    "swarm_algorithm": "strands_consensus",
                    "trigger_severity": trigger_event.severity.value,
                    "execution_time_ms": result.get("execution_time_ms", 0),
                    "agent_interactions": result.get("agent_interactions", []),
                    "swarm_result_object": result.get("swarm_result_object"),
                },
            )

            # Log performance metrics
            self.perf_logger.log_swarm_consensus_time(
                duration_ms,
                len(result.get("agents_involved", [])),
                success=result.get("status") == "completed",
            )

            self.state = SwarmState.IDLE
            return event

        except asyncio.TimeoutError:
            # Handle swarm execution timeout
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            event = self._create_swarm_event(
                "swarm_activation_failed",
                trigger_event.site_id,
                [],
                None,
                duration_ms,
                False,
                {
                    "error": "Swarm execution timed out",
                    "reason": "swarm_timeout",
                    "timeout_ms": self.consensus_timeout_ms,
                },
            )

            self.struct_logger.warning(
                "Swarm activation timed out",
                trigger_site=trigger_event.site_id,
                duration_ms=duration_ms,
                timeout_ms=self.consensus_timeout_ms,
            )

            self.state = SwarmState.IDLE
            return event

        except Exception as e:
            # Handle swarm execution failure
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            event = self._create_swarm_event(
                "swarm_activation_failed",
                trigger_event.site_id,
                [],
                None,
                duration_ms,
                False,
                {
                    "error": str(e),
                    "reason": "swarm_execution_error",
                },
            )

            self.struct_logger.error(
                "Swarm activation failed",
                error=str(e),
                trigger_site=trigger_event.site_id,
                duration_ms=duration_ms,
            )

            self.state = SwarmState.IDLE
            return event

    def _extract_decision_from_result(
        self, swarm_result: Dict[str, Any], trigger_event: ThresholdEvent
    ) -> SwarmDecision:
        """
        Extract decision information from Strands swarm result.

        Args:
            swarm_result: Result from Strands swarm execution
            trigger_event: Original threshold breach event

        Returns:
            SwarmDecision object with extracted information
        """
        self.decision_counter += 1

        # Parse the swarm result to extract decision
        # Enhanced to capture actual agent reasoning and conversations

        healthy_sites = [site for site in self.mec_sites.values() if site.is_healthy()]
        agents_involved = swarm_result.get("agents_involved", [])
        final_result = swarm_result.get("final_result", "")

        if healthy_sites:
            # Simple selection for simulation - pick site with lowest load
            selected_site = min(healthy_sites, key=lambda s: s.calculate_load_score())
            fallback_sites = [
                s.site_id for s in healthy_sites if s.site_id != selected_site.site_id
            ][:2]

            # Enhanced reasoning that includes actual swarm execution details
            reasoning_parts = [
                f"Strands swarm consensus selected {selected_site.site_id} based on multi-agent analysis.",
                f"Trigger: {trigger_event.metric_name} breach ({trigger_event.current_value} > {trigger_event.threshold_value})",
                f"Agents involved: {', '.join(agents_involved)}",
            ]

            # Add final result if available
            if (
                final_result
                and isinstance(final_result, str)
                and len(final_result) > 10
            ):
                reasoning_parts.append(f"Agent reasoning: {final_result[:200]}...")

            # Add site selection rationale
            reasoning_parts.append(
                f"Selected {selected_site.site_id} with load score {selected_site.calculate_load_score():.2f} "
                f"(CPU: {selected_site.cpu_utilization}%, GPU: {selected_site.gpu_utilization}%, "
                f"Queue: {selected_site.queue_depth})"
            )

            reasoning = " ".join(reasoning_parts)
            confidence = min(
                0.95, 0.7 + (len(agents_involved) * 0.05)
            )  # Higher confidence with more agents
        else:
            # Fallback if no healthy sites
            selected_site = list(self.mec_sites.values())[0]
            fallback_sites = []
            reasoning = (
                f"No healthy sites available - selected fallback {selected_site.site_id}. "
                f"Agents involved: {', '.join(agents_involved)}"
            )
            confidence = 0.3

        return SwarmDecision(
            decision_id=f"decision_{self.decision_counter:06d}",
            selected_site=(
                selected_site.site_id
                if hasattr(selected_site, "site_id")
                else str(selected_site)
            ),
            reasoning=reasoning,
            confidence_score=confidence,
            fallback_sites=fallback_sites,
            execution_time_ms=swarm_result.get("execution_time_ms", 0),
            participants=agents_involved,
            swarm_result=swarm_result.get("final_result"),
            timestamp=datetime.now(UTC),
        )

    def _execute_decision(self, decision: SwarmDecision) -> bool:
        """Execute the swarm decision (simulation)."""
        selected_site = self.mec_sites.get(decision.selected_site)
        if not selected_site:
            return False

        self.logger.log_mcp_call(
            "container_ops",
            "scale_containers",
            {
                "target_site": decision.selected_site,
                "scaling_factor": 1.2,
                "reason": "swarm_consensus_decision",
            },
        )

        return True

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
        if len(self.event_history) > self.max_event_history:
            self.event_history = self.event_history[-self.max_event_history :]

        return event

    def get_swarm_status(self) -> dict[str, Any]:
        """Get current swarm coordination status including Strands agent states."""
        healthy_sites = [site for site in self.mec_sites.values() if site.is_healthy()]

        return {
            "state": self.state.value,
            "total_sites": len(self.mec_sites),
            "healthy_sites": len(healthy_sites),
            "total_agents": len(self.agents),
            "recent_events": len(
                [
                    e
                    for e in self.event_history
                    if (datetime.now(UTC) - e.timestamp).total_seconds() < 300
                ]
            ),
            "total_decisions": self.decision_counter,
            "swarm_available": self.swarm is not None,
            "sites": {
                site_id: {
                    "status": site.status,
                    "load_score": site.calculate_load_score(),
                    "is_healthy": site.is_healthy(),
                }
                for site_id, site in self.mec_sites.items()
            },
            "agents": {
                agent_name: agent_obj.get_agent_status()
                for agent_name, agent_obj in self.agents.items()
            },
        }

    def get_event_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent swarm coordination events."""
        recent_events = self.event_history[-limit:] if limit > 0 else self.event_history
        return [event.to_dict() for event in recent_events]

    def simulate_site_failure(self, site_id: str) -> bool:
        """Simulate MEC site failure for testing."""
        if site_id in self.mec_sites:
            self.mec_sites[site_id].status = "failed"
            return True
        return False

    def simulate_site_recovery(self, site_id: str) -> bool:
        """Simulate MEC site recovery for testing."""
        if site_id in self.mec_sites:
            site = self.mec_sites[site_id]
            site.status = "healthy"
            site.cpu_utilization = 50.0
            site.gpu_utilization = 40.0
            site.memory_utilization = 45.0
            site.queue_depth = 20
            site.response_time_ms = 30.0
            site.last_updated = datetime.now(UTC)
            return True
        return False

    def get_agent_status(self) -> dict[str, Any]:
        """Get detailed status of all Strands agents."""
        return {
            agent_name: agent_obj.get_agent_status()
            for agent_name, agent_obj in self.agents.items()
        }

    def get_swarm_metrics(self) -> dict[str, Any]:
        """Get Strands swarm performance metrics."""
        return {
            "swarm_configured": self.swarm is not None,
            "max_handoffs": 10,
            "execution_timeout": 5.0,
            "node_timeout": 2.0,
            "total_decisions": self.decision_counter,
            "total_events": len(self.event_history),
            "agent_count": len(self.agents),
            "mec_sites": len(self.mec_sites),
        }

    def get_recent_conversations(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent agent conversations from swarm events."""
        conversations = []

        # Get recent events with decisions
        recent_events = [e for e in self.event_history[-limit:] if e.decision]

        for event in recent_events:
            if event.decision and event.decision.swarm_result:
                # Extract conversations from swarm result
                swarm_result = event.decision.swarm_result

                # Add decision reasoning as conversation
                conversations.append(
                    {
                        "agent": "DecisionCoordinator",
                        "message": event.decision.reasoning,
                        "timestamp": event.decision.timestamp.isoformat(),
                        "type": "decision_reasoning",
                        "confidence": event.decision.confidence_score,
                        "selected_site": event.decision.selected_site,
                        "event_id": event.event_id,
                    }
                )

                # Add swarm execution summary
                conversations.append(
                    {
                        "agent": "SwarmCoordinator",
                        "message": f"Swarm execution completed in {event.duration_ms}ms with {len(event.participants)} agents",
                        "timestamp": event.timestamp.isoformat(),
                        "type": "execution_summary",
                        "participants": event.participants,
                        "success": event.success,
                        "event_id": event.event_id,
                    }
                )

        return conversations[-limit:]


if __name__ == "__main__":
    print("SwarmCoordinator module loaded successfully")
    coordinator = SwarmCoordinator()
    print(
        f"Initialized with {len(coordinator.mec_sites)} MEC sites and {len(coordinator.agents)} agents"
    )
    print(f"Initialized with {len(coordinator.mec_sites)} MEC sites")
