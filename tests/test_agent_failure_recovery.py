#!/usr/bin/env python3
"""
Agent failure and recovery tests for EdgeMind MEC orchestration system.

Tests various failure scenarios and validates that the system can recover
gracefully from agent failures, network partitions, and other fault conditions.
"""

import asyncio
import time
import unittest
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from config import ThresholdConfig
from src.data.metrics_generator import MECMetrics
from src.orchestrator.threshold_monitor import (
    SeverityLevel,
    ThresholdEvent,
    ThresholdMonitor,
)
from src.swarm.swarm_coordinator import SwarmCoordinator, SwarmState


def create_test_metrics(site_id, cpu_util=95.0, **kwargs):
    """Helper function to create MECMetrics with all required fields."""
    defaults = {
        "timestamp": datetime.now(UTC),
        "gpu_utilization": 30.0,
        "memory_utilization": 55.0,
        "queue_depth": 15,
        "network_latency": {"MEC_B": 18.0, "MEC_C": 22.0},
        "response_time_ms": 25.0,
        "requests_per_second": 100,
        "active_connections": 50,
        "cache_hit_ratio": 85.0,
    }
    defaults.update(kwargs)

    return MECMetrics(site_id=site_id, cpu_utilization=cpu_util, **defaults)


class TestAgentFailureScenarios(unittest.TestCase):
    """Test various agent failure scenarios and recovery mechanisms."""

    def setUp(self):
        """Set up test fixtures for failure testing."""
        self.thresholds = ThresholdConfig()
        self.monitor = ThresholdMonitor(self.thresholds)
        self.coordinator = SwarmCoordinator()
        self.monitor.add_breach_callback(self.coordinator.activate_swarm)

    def test_orchestrator_agent_failure(self):
        """Test system behavior when orchestrator agent fails."""
        # Simulate orchestrator failure by making it raise exceptions
        original_handle = self.coordinator.orchestrator.handle_threshold_breach

        def failing_handle(*args, **kwargs):
            raise Exception("Orchestrator agent failure")

        self.coordinator.orchestrator.handle_threshold_breach = failing_handle

        # Create threshold breach
        breach_metrics = create_test_metrics("MEC_FAIL")

        # Trigger threshold breach (should handle orchestrator failure)
        events = self.monitor.check_thresholds(breach_metrics)

        # Verify breach was detected
        self.assertGreater(len(events), 0)

        # Verify swarm coordinator handled the failure
        swarm_events = self.coordinator.get_event_history()
        if swarm_events:
            latest_event = swarm_events[-1]
            # Should have failure event or graceful degradation
            self.assertIn(
                latest_event["event_type"],
                ["swarm_activation_failed", "swarm_coordination_completed"],
            )

        # Restore original handler for cleanup
        self.coordinator.orchestrator.handle_threshold_breach = original_handle

    def test_swarm_timeout_handling(self):
        """Test handling of swarm execution timeouts."""

        # Mock swarm that times out
        async def timeout_swarm(*args, **kwargs):
            await asyncio.sleep(10)  # Simulate long-running operation
            return {"status": "timeout"}

        with patch.object(
            self.coordinator.orchestrator,
            "handle_threshold_breach",
            side_effect=timeout_swarm,
        ):

            breach_metrics = create_test_metrics("MEC_TIMEOUT")

            # Measure execution time
            start_time = time.perf_counter()

            # This should timeout and handle gracefully
            try:
                events = self.monitor.check_thresholds(breach_metrics)
                end_time = time.perf_counter()

                execution_time = (end_time - start_time) * 1000

                # Should not hang indefinitely (allow for 2 swarm activations * 5s timeout each + overhead)
                self.assertLess(
                    execution_time,
                    12000,  # 12 seconds max (2 * 5s timeout + 2s overhead)
                    f"Execution took {execution_time:.0f}ms, may have hung",
                )

            except asyncio.TimeoutError:
                # Timeout is acceptable behavior
                pass

    def test_partial_agent_failure(self):
        """Test system behavior when some agents fail but others remain functional."""
        # Simulate failure of specific agents
        failed_agents = ["load_balancer", "cache_manager"]

        for agent_name in failed_agents:
            agent = self.coordinator.agents[agent_name]
            # Make agent raise exceptions
            original_agent = agent.agent
            agent.agent = MagicMock(side_effect=Exception(f"{agent_name} failed"))

        # Mock successful orchestrator response despite partial failures
        with patch.object(
            self.coordinator.orchestrator,
            "handle_threshold_breach",
            new=AsyncMock(
                return_value={
                    "status": "completed_partial",
                    "execution_time_ms": 120,
                    "agents_involved": [
                        "orchestrator_MEC_A",
                        "decision_coordinator_MEC_C",
                    ],
                    "failed_agents": failed_agents,
                    "final_result": "Partial consensus reached with available agents",
                    "token_usage": {"tokens": 80},
                }
            ),
        ) as mock_handle:

            breach_metrics = create_test_metrics("MEC_PARTIAL")

            events = self.monitor.check_thresholds(breach_metrics)

        # Verify system handled partial failure
        self.assertGreater(len(events), 0)
        swarm_events = self.coordinator.get_event_history()

        if swarm_events:
            latest_event = swarm_events[-1]
            # Should complete despite partial failures or handle failure gracefully
            self.assertTrue(
                latest_event["success"]
                or "partial" in latest_event["event_type"]
                or latest_event["event_type"]
                in ["swarm_activation_failed", "swarm_coordination_completed"]
            )

    def test_mec_site_failure_cascade(self):
        """Test handling of cascading MEC site failures."""
        # Simulate multiple site failures
        sites_to_fail = ["MEC_A", "MEC_B"]

        for site_id in sites_to_fail:
            success = self.coordinator.simulate_site_failure(site_id)
            self.assertTrue(success, f"Failed to simulate failure of {site_id}")

        # Verify reduced capacity
        status = self.coordinator.get_swarm_status()
        self.assertEqual(status["healthy_sites"], 1)  # Only MEC_C should remain

        # Test system behavior with limited capacity
        breach_metrics = create_test_metrics("MEC_C", network_latency={})

        with patch.object(
            self.coordinator.orchestrator,
            "handle_threshold_breach",
            new=AsyncMock(
                return_value={
                    "status": "completed_degraded",
                    "execution_time_ms": 150,
                    "agents_involved": ["orchestrator_MEC_A"],
                    "final_result": "Operating with single site due to failures",
                    "token_usage": {"tokens": 60},
                }
            ),
        ) as mock_handle:

            events = self.monitor.check_thresholds(breach_metrics)

        # System should handle degraded operation
        self.assertGreater(len(events), 0)

    def test_network_partition_simulation(self):
        """Test behavior during simulated network partitions."""
        # Simulate network partition by making inter-site communication fail
        original_sites = dict(self.coordinator.mec_sites)

        # Partition: MEC_A isolated, MEC_B and MEC_C connected
        partitioned_sites = {
            "MEC_A": ["MEC_A"],  # Isolated
            "MEC_B": ["MEC_B", "MEC_C"],  # Connected group
            "MEC_C": ["MEC_B", "MEC_C"],  # Connected group
        }

        # Update network latency to reflect partition
        for site_id, site in self.coordinator.mec_sites.items():
            connected_sites = partitioned_sites[site_id]
            new_latency = {}

            for other_site in original_sites:
                if other_site != site_id:
                    if other_site in connected_sites:
                        new_latency[other_site] = 20.0  # Normal latency
                    else:
                        new_latency[other_site] = (
                            9999.0  # Partition (very high latency)
                        )

            site.network_latency = new_latency

        # Test breach handling during partition
        breach_metrics = create_test_metrics(
            "MEC_A", network_latency={"MEC_B": 9999.0, "MEC_C": 9999.0}
        )

        with patch.object(
            self.coordinator.orchestrator,
            "handle_threshold_breach",
            new=AsyncMock(
                return_value={
                    "status": "completed_isolated",
                    "execution_time_ms": 200,
                    "agents_involved": ["orchestrator_MEC_A"],
                    "final_result": "Local decision due to network partition",
                    "token_usage": {"tokens": 40},
                }
            ),
        ) as mock_handle:

            events = self.monitor.check_thresholds(breach_metrics)

        # Verify partition was handled
        self.assertGreater(len(events), 0)

        # Restore original network topology
        for site_id, site in self.coordinator.mec_sites.items():
            site.network_latency = original_sites[site_id].network_latency

    def test_agent_recovery_after_failure(self):
        """Test agent recovery mechanisms after failure."""
        # Simulate agent failure and recovery cycle
        agent_name = "load_balancer"
        agent = self.coordinator.agents[agent_name]

        # Step 1: Simulate failure
        original_status = agent.get_agent_status()
        self.assertEqual(original_status["status"], "active")

        # Make agent fail
        agent.agent = MagicMock(side_effect=Exception("Agent failed"))

        # Step 2: Simulate recovery (restart agent)
        # In real system, this would involve container restart or agent reinitialization
        from src.agents.load_balancer_agent import LoadBalancerAgent

        recovered_agent = LoadBalancerAgent(agent.mec_site)
        self.coordinator.agents[agent_name] = recovered_agent

        # Step 3: Verify recovery
        recovered_status = recovered_agent.get_agent_status()
        self.assertEqual(recovered_status["status"], "active")
        self.assertEqual(recovered_status["agent_type"], "load_balancer")

        # Test that recovered agent can handle requests
        test_status = recovered_agent.get_agent_status()
        self.assertIsNotNone(test_status)
        self.assertIn("mcp_tools", test_status)

    def test_swarm_reconfiguration_after_failures(self):
        """Test swarm reconfiguration when agents fail and recover."""
        initial_agent_count = len(self.coordinator.agents)

        # Remove some agents to simulate failures
        failed_agents = ["cache_manager", "resource_monitor"]
        for agent_name in failed_agents:
            del self.coordinator.agents[agent_name]

        # Verify reduced agent count
        self.assertEqual(len(self.coordinator.agents), initial_agent_count - 2)

        # Test swarm operation with reduced agents
        with patch.object(
            self.coordinator.orchestrator,
            "handle_threshold_breach",
            new=AsyncMock(
                return_value={
                    "status": "completed_reduced",
                    "execution_time_ms": 100,
                    "agents_involved": [
                        "orchestrator_MEC_A",
                        "load_balancer_MEC_B",
                        "decision_coordinator_MEC_C",
                    ],
                    "final_result": "Swarm operated with reduced agent set",
                    "token_usage": {"tokens": 90},
                }
            ),
        ) as mock_handle:

            breach_metrics = create_test_metrics("MEC_RECONFIG")

            events = self.monitor.check_thresholds(breach_metrics)

        # Verify swarm operated with reduced capacity
        self.assertGreater(len(events), 0)

        # Simulate agent recovery
        from src.agents.cache_manager_agent import CacheManagerAgent
        from src.agents.resource_monitor_agent import ResourceMonitorAgent

        self.coordinator.agents["cache_manager"] = CacheManagerAgent("MEC_B")
        self.coordinator.agents["resource_monitor"] = ResourceMonitorAgent("MEC_A")

        # Verify full capacity restored
        self.assertEqual(len(self.coordinator.agents), initial_agent_count)

    def test_threshold_monitor_resilience(self):
        """Test threshold monitor resilience to various failure conditions."""
        # Test with invalid metrics
        invalid_metrics = create_test_metrics(
            "MEC_INVALID", cpu_util=float("inf"), gpu_utilization=-10.0
        )

        # Should handle invalid metrics gracefully
        try:
            events = self.monitor.check_thresholds(invalid_metrics)
            # If no exception, verify reasonable behavior
            self.assertIsInstance(events, list)
        except Exception as e:
            # If exception occurs, it should be handled gracefully
            self.assertIsInstance(e, (ValueError, TypeError))

        # Test with missing network latency data
        incomplete_metrics = create_test_metrics(
            "MEC_INCOMPLETE", cpu_util=45.0, network_latency={}
        )

        # Should handle incomplete data
        events = self.monitor.check_thresholds(incomplete_metrics)
        self.assertIsInstance(events, list)

    def test_callback_failure_isolation(self):
        """Test that callback failures don't affect threshold monitoring."""

        # Add a failing callback
        def failing_callback(event):
            raise Exception("Callback failure")

        self.monitor.add_breach_callback(failing_callback)

        # Verify we now have 2 callbacks (original + failing)
        self.assertEqual(len(self.monitor._callbacks), 2)

        # Create breach that should trigger callbacks
        breach_metrics = create_test_metrics("MEC_CALLBACK")

        # Should handle callback failure gracefully
        events = self.monitor.check_thresholds(breach_metrics)

        # Threshold detection should still work
        self.assertGreater(len(events), 0)
        self.assertEqual(events[0].metric_name, "cpu_utilization")

        # Remove failing callback
        self.monitor.remove_breach_callback(failing_callback)
        self.assertEqual(len(self.monitor._callbacks), 1)

    def test_concurrent_failure_handling(self):
        """Test handling of concurrent failures across multiple components."""
        import queue
        import threading

        results_queue = queue.Queue()

        def failure_worker(worker_id):
            """Worker that simulates various failure conditions."""
            try:
                if worker_id == 0:
                    # Simulate MEC site failure
                    self.coordinator.simulate_site_failure("MEC_A")
                    results_queue.put((worker_id, "site_failure", "success"))

                elif worker_id == 1:
                    # Simulate agent failure
                    agent = self.coordinator.agents["load_balancer"]
                    agent.agent = MagicMock(side_effect=Exception("Concurrent failure"))
                    results_queue.put((worker_id, "agent_failure", "success"))

                elif worker_id == 2:
                    # Simulate threshold breach during failures
                    breach_metrics = create_test_metrics("MEC_CONCURRENT")

                    events = self.monitor.check_thresholds(breach_metrics)
                    results_queue.put((worker_id, "threshold_breach", len(events)))

            except Exception as e:
                results_queue.put((worker_id, "error", str(e)))

        # Run concurrent failure scenarios
        threads = []
        for worker_id in range(3):
            thread = threading.Thread(target=failure_worker, args=(worker_id,))
            threads.append(thread)
            thread.start()

        # Wait for all workers
        for thread in threads:
            thread.join(timeout=5.0)  # 5 second timeout

        # Collect results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        # Verify all workers completed
        self.assertEqual(len(results), 3)

        # Check that system handled concurrent failures
        for worker_id, operation, result in results:
            if operation == "threshold_breach":
                self.assertGreater(
                    result, 0, f"Worker {worker_id} failed to detect breach"
                )
            else:
                self.assertEqual(
                    result,
                    "success",
                    f"Worker {worker_id} operation {operation} failed",
                )

    def test_graceful_degradation_metrics(self):
        """Test that system provides meaningful metrics during degraded operation."""
        # Simulate degraded state
        self.coordinator.simulate_site_failure("MEC_A")
        self.coordinator.simulate_site_failure("MEC_B")

        # Get status during degraded operation
        degraded_status = self.coordinator.get_swarm_status()

        # Verify degraded state is properly reported
        self.assertEqual(degraded_status["healthy_sites"], 1)
        self.assertEqual(degraded_status["total_sites"], 3)
        self.assertLess(
            degraded_status["healthy_sites"], degraded_status["total_sites"]
        )

        # Verify agent status during degradation
        agent_status = self.coordinator.get_agent_status()
        for agent_name, status in agent_status.items():
            self.assertIn("status", status)
            # Agents should still report as active even if sites are failed
            self.assertEqual(status["status"], "active")

        # Test monitoring stats during degradation
        monitor_stats = self.monitor.get_monitoring_stats()
        self.assertIn("total_checks", monitor_stats)
        self.assertIn("active_callbacks", monitor_stats)

        # Recovery
        self.coordinator.simulate_site_recovery("MEC_A")
        self.coordinator.simulate_site_recovery("MEC_B")

        recovered_status = self.coordinator.get_swarm_status()
        self.assertEqual(recovered_status["healthy_sites"], 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
