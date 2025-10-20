#!/usr/bin/env python3
"""
Comprehensive integration tests for SwarmCoordinator and ThresholdMonitor interaction.

Tests the complete flow from threshold breach detection to swarm consensus and decision execution.

IMPORTANT: DEMO vs PRODUCTION ARCHITECTURE
==========================================

DEMO SETUP (Current):
- Uses Anthropic Claude API calls via internet
- Each swarm decision involves LLM API calls (2-5 seconds per call)
- Performance tests account for network latency and API response times
- Suitable for demonstration and development

PRODUCTION SETUP (Target):
- Uses Small Language Models (SLMs) deployed locally with Strands agents
- Each swarm decision uses local inference (milliseconds)
- No internet connectivity required for agent decisions
- Optimized for real-time MEC edge computing scenarios

The performance expectations in these tests reflect the DEMO setup with API calls.
In production, the same logic would run orders of magnitude faster with local SLMs.
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


class TestSwarmThresholdIntegration(unittest.TestCase):
    """Integration tests for SwarmCoordinator and ThresholdMonitor."""

    def setUp(self):
        """Set up test fixtures."""
        self.thresholds = ThresholdConfig()
        self.monitor = ThresholdMonitor(self.thresholds)
        self.coordinator = SwarmCoordinator()

        # Connect monitor to coordinator
        self.monitor.add_breach_callback(self.coordinator.activate_swarm)

    def test_initialization_integration(self):
        """Test that components initialize correctly and can be connected."""
        # Verify monitor initialization
        self.assertIsInstance(self.monitor, ThresholdMonitor)
        self.assertEqual(len(self.monitor._callbacks), 1)

        # Verify coordinator initialization
        self.assertIsInstance(self.coordinator, SwarmCoordinator)
        self.assertEqual(self.coordinator.state, SwarmState.IDLE)
        self.assertEqual(len(self.coordinator.mec_sites), 3)  # Default sites
        self.assertEqual(len(self.coordinator.agents), 5)  # All agent types
        self.assertIsNotNone(self.coordinator.swarm)

    def test_normal_metrics_no_swarm_activation(self):
        """Test that normal metrics don't trigger swarm activation."""
        # Create normal metrics
        normal_metrics = create_test_metrics(
            "MEC_A",
            cpu_util=45.0,
            network_latency={
                "MEC_B": 18.0,
                "MEC_C": 19.0,
            },  # All below thresholds
        )

        # Check thresholds
        events = self.monitor.check_thresholds(normal_metrics)

        # Verify no events generated
        self.assertEqual(len(events), 0)

        # Verify no swarm events
        swarm_events = self.coordinator.get_event_history()
        self.assertEqual(len(swarm_events), 0)

        # Verify coordinator state remains idle
        self.assertEqual(self.coordinator.state, SwarmState.IDLE)

    def test_single_threshold_breach_triggers_swarm(self):
        """Test that single threshold breach triggers swarm coordination."""
        # Create breach metrics with only CPU breach, normal network latency
        breach_metrics = create_test_metrics(
            "MEC_A",
            cpu_util=95.0,
            network_latency={
                "MEC_B": 18.0,
                "MEC_C": 19.0,
            },  # Below 20ms threshold
        )

        # Check thresholds (should trigger swarm)
        events = self.monitor.check_thresholds(breach_metrics)

        # Verify threshold event generated
        self.assertGreater(len(events), 0)  # At least one event
        # Find the CPU utilization event
        cpu_events = [e for e in events if e.metric_name == "cpu_utilization"]
        self.assertEqual(len(cpu_events), 1)
        self.assertEqual(cpu_events[0].current_value, 95.0)
        self.assertEqual(cpu_events[0].severity, SeverityLevel.HIGH)

        # Verify swarm was activated
        swarm_events = self.coordinator.get_event_history()
        self.assertGreater(len(swarm_events), 0)

        # Check latest swarm event
        latest_event = swarm_events[-1]
        self.assertIn("swarm", latest_event["event_type"])

    def test_multiple_threshold_breaches(self):
        """Test handling of multiple simultaneous threshold breaches."""
        # Create metrics with multiple breaches
        multi_breach_metrics = create_test_metrics(
            "MEC_B",
            cpu_util=85.0,  # Exceeds threshold
            gpu_utilization=90.0,  # Exceeds threshold
            memory_utilization=55.0,
            queue_depth=60,  # Exceeds threshold
            response_time_ms=150.0,  # Exceeds threshold
            network_latency={"MEC_A": 18.0, "MEC_C": 22.0},
        )

        # Check thresholds
        events = self.monitor.check_thresholds(multi_breach_metrics)

        # Verify multiple threshold events
        self.assertGreater(len(events), 1)

        # Check that we have the expected breach types
        breach_metrics = [e.metric_name for e in events]
        expected_breaches = [
            "cpu_utilization",
            "gpu_utilization",
            "queue_depth",
            "response_time",
        ]
        for expected in expected_breaches:
            self.assertIn(expected, breach_metrics)

        # Verify swarm activation for each breach
        swarm_events = self.coordinator.get_event_history()
        self.assertGreater(len(swarm_events), 0)

    def test_swarm_site_failure_handling(self):
        """Test swarm coordination when MEC sites fail."""
        # Simulate site failure
        self.coordinator.simulate_site_failure("MEC_A")

        # Verify site status
        status = self.coordinator.get_swarm_status()
        self.assertEqual(status["healthy_sites"], 2)  # Should have 2 healthy sites

        # Create breach that would normally go to failed site
        breach_metrics = create_test_metrics("MEC_A", cpu_util=95.0)

        # Trigger swarm with reduced sites
        events = self.monitor.check_thresholds(breach_metrics)

        # Verify swarm handled the failure scenario
        swarm_events = self.coordinator.get_event_history()
        self.assertGreater(len(swarm_events), 0)

    def test_swarm_site_recovery(self):
        """Test swarm coordination after site recovery."""
        # First simulate failure
        self.coordinator.simulate_site_failure("MEC_B")
        initial_status = self.coordinator.get_swarm_status()
        self.assertEqual(initial_status["healthy_sites"], 2)

        # Then simulate recovery
        self.coordinator.simulate_site_recovery("MEC_B")
        recovery_status = self.coordinator.get_swarm_status()
        self.assertEqual(recovery_status["healthy_sites"], 3)

        # Verify recovered site has reasonable metrics
        recovered_site = self.coordinator.mec_sites["MEC_B"]
        self.assertEqual(recovered_site.status, "healthy")
        self.assertLess(recovered_site.cpu_utilization, 80.0)
        self.assertLess(recovered_site.response_time_ms, 100.0)

    def test_threshold_breach_recovery_cycle(self):
        """Test complete breach -> swarm -> recovery cycle."""
        site_id = "MEC_C"

        # Step 1: Create breach
        breach_metrics = create_test_metrics(
            site_id,
            cpu_util=95.0,  # Breach
            network_latency={"MEC_A": 18.0, "MEC_B": 22.0},
        )

        breach_events = self.monitor.check_thresholds(breach_metrics)

        # Verify breach detected and swarm activated
        self.assertGreater(len(breach_events), 0)
        breach_status = self.monitor.get_current_breach_status(site_id)
        self.assertTrue(breach_status["has_active_breaches"])

        # Step 2: Simulate recovery (metrics return to normal)
        recovery_metrics = create_test_metrics(
            site_id,
            cpu_util=45.0,  # Back to normal
            network_latency={
                "MEC_A": 18.0,
                "MEC_B": 19.0,
            },  # All below 20ms threshold
        )

        recovery_events = self.monitor.check_thresholds(recovery_metrics)

        # Verify recovery detected
        self.assertGreater(len(recovery_events), 0)
        recovery_event = recovery_events[0]
        self.assertEqual(recovery_event.event_type.value, "threshold_recovery")

        # Verify breach status cleared
        final_status = self.monitor.get_current_breach_status(site_id)
        self.assertFalse(final_status["has_active_breaches"])

    def test_swarm_coordinator_agent_status(self):
        """Test that swarm coordinator properly tracks agent status."""
        agent_status = self.coordinator.get_agent_status()

        # Verify all expected agents are present
        expected_agents = {
            "orchestrator",
            "load_balancer",
            "decision_coordinator",
            "resource_monitor",
            "cache_manager",
        }
        self.assertEqual(set(agent_status.keys()), expected_agents)

        # Verify each agent has proper status structure
        for agent_name, status in agent_status.items():
            self.assertIn("agent_id", status)
            self.assertIn("agent_type", status)
            self.assertIn("mec_site", status)
            self.assertIn("status", status)
            self.assertEqual(status["status"], "active")

    def test_swarm_metrics_tracking(self):
        """Test swarm performance metrics tracking."""
        metrics = self.coordinator.get_swarm_metrics()

        expected_keys = {
            "swarm_configured",
            "max_handoffs",
            "execution_timeout",
            "node_timeout",
            "total_decisions",
            "total_events",
            "agent_count",
            "mec_sites",
        }
        self.assertEqual(set(metrics.keys()), expected_keys)

        # Verify initial values
        self.assertTrue(metrics["swarm_configured"])
        self.assertEqual(metrics["max_handoffs"], 10)
        self.assertEqual(metrics["execution_timeout"], 5.0)
        self.assertEqual(metrics["agent_count"], 5)
        self.assertEqual(metrics["mec_sites"], 3)

    def test_callback_system_integration(self):
        """Test threshold monitor callback system with swarm coordinator."""
        # Verify callback is registered
        self.assertEqual(len(self.monitor._callbacks), 1)

        # Test callback removal
        self.monitor.remove_breach_callback(self.coordinator.activate_swarm)
        self.assertEqual(len(self.monitor._callbacks), 0)

        # Re-add callback
        self.monitor.add_breach_callback(self.coordinator.activate_swarm)
        self.assertEqual(len(self.monitor._callbacks), 1)

    def test_monitoring_stats_integration(self):
        """Test monitoring statistics integration."""
        # Generate some monitoring activity
        test_metrics = create_test_metrics(
            "MEC_A",
            cpu_util=45.0,
            network_latency={"MEC_B": 18.0, "MEC_C": 22.0},
        )

        # Run multiple checks
        for _ in range(5):
            self.monitor.check_thresholds(test_metrics)

        # Get monitoring stats
        stats = self.monitor.get_monitoring_stats()

        expected_keys = {
            "total_checks",
            "total_events",
            "monitored_sites",
            "average_check_time_ms",
            "active_callbacks",
        }
        self.assertEqual(set(stats.keys()), expected_keys)

        self.assertEqual(stats["total_checks"], 5)
        self.assertEqual(stats["active_callbacks"], 1)
        self.assertIn("MEC_A", stats["monitored_sites"])


class TestSwarmPerformanceIntegration(unittest.TestCase):
    """Performance-focused integration tests.

    IMPORTANT: These tests measure DEMO performance with Anthropic API calls.
    Production deployment with local SLMs would achieve 100-1000x better performance.
    """

    def setUp(self):
        """Set up performance test fixtures."""
        self.thresholds = ThresholdConfig()
        self.monitor = ThresholdMonitor(self.thresholds)
        self.coordinator = SwarmCoordinator()
        self.monitor.add_breach_callback(self.coordinator.activate_swarm)

    def test_threshold_check_performance(self):
        """Test threshold checking performance (without swarm activation)."""
        # Use metrics that don't trigger swarm activation to avoid LLM calls
        test_metrics = create_test_metrics(
            "MEC_PERF",
            cpu_util=45.0,  # Below 80% threshold
            network_latency={
                "MEC_B": 18.0,
                "MEC_C": 19.0,
            },  # Below 20ms threshold
        )

        # Measure threshold checking performance
        start_time = time.perf_counter()

        for _ in range(100):  # 100 threshold checks
            self.monitor.check_thresholds(test_metrics)

        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        avg_time_per_check = total_time_ms / 100

        # Verify performance target: each check should be < 50ms (more realistic)
        self.assertLess(
            avg_time_per_check,
            50.0,
            f"Average threshold check time {avg_time_per_check:.2f}ms exceeds 50ms target",
        )

    def test_swarm_activation_performance_simulation(self):
        """Test swarm activation with realistic expectations for DEMO setup.

        NOTE: This test reflects DEMO performance with Anthropic API calls.
        In production with local SLMs, this would be 100-1000x faster.
        """
        breach_metrics = create_test_metrics(
            "MEC_PERF",
            cpu_util=95.0,  # Breach
            network_latency={"MEC_B": 18.0, "MEC_C": 19.0},  # Normal latency
        )

        # Measure total time including threshold check + swarm activation
        start_time = time.perf_counter()
        events = self.monitor.check_thresholds(breach_metrics)
        end_time = time.perf_counter()

        total_time_ms = (end_time - start_time) * 1000

        # Verify we have events and swarm was activated
        self.assertGreater(len(events), 0)
        swarm_events = self.coordinator.get_event_history()
        self.assertGreater(len(swarm_events), 0)

        # DEMO performance target: API calls can take seconds
        # Production with local SLMs would be <100ms for same operation
        self.assertLess(
            total_time_ms,
            30000,
            f"Swarm activation took {total_time_ms:.2f}ms",
        )
        print(
            f"DEMO swarm activation time: {total_time_ms:.2f}ms (Production with local SLMs: ~50-100ms)"
        )

    def test_concurrent_threshold_monitoring(self):
        """Test concurrent threshold monitoring performance."""
        import threading

        results = []

        def monitor_worker(worker_id):
            """Worker function for concurrent monitoring."""
            test_metrics = create_test_metrics(
                f"MEC_WORKER_{worker_id}",
                cpu_util=45.0,
                network_latency={"MEC_B": 18.0, "MEC_C": 22.0},
            )

            start_time = time.perf_counter()
            for _ in range(10):
                self.monitor.check_thresholds(test_metrics)
            end_time = time.perf_counter()

            results.append((worker_id, (end_time - start_time) * 1000))

        # Run 5 concurrent monitoring threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=monitor_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all workers completed successfully
        self.assertEqual(len(results), 5)

        # Check that concurrent monitoring didn't cause excessive delays
        max_time = max(time_ms for _, time_ms in results)
        avg_time = sum(time_ms for _, time_ms in results) / len(results)

        print(f"Concurrent monitoring - Max: {max_time:.2f}ms, Avg: {avg_time:.2f}ms")

        # DEMO performance targets (with API calls): reasonable for concurrent access
        # Production with local SLMs would be 10-100x faster
        self.assertLess(max_time, 10000.0)  # Max 10 seconds for 10 checks (DEMO)
        self.assertLess(avg_time, 5000.0)  # Average < 5 seconds for 10 checks (DEMO)


if __name__ == "__main__":
    unittest.main(verbosity=2)
