#!/usr/bin/env python3
"""
Test script for Strands-based SwarmCoordinator integration.

This script demonstrates the complete flow:
1. ThresholdMonitor detects breach
2. SwarmCoordinator activates Strands swarm
3. Specialized agents collaborate for consensus
4. Decision is executed and logged
"""

import time
from datetime import UTC, datetime

from config import ThresholdConfig
from src.data.metrics_generator import MECMetrics
from src.orchestrator.threshold_monitor import ThresholdMonitor
from src.swarm.swarm_coordinator import SwarmCoordinator


def test_strands_swarm_integration():
    """Test the complete Strands swarm integration flow."""
    print("=== EdgeMind Strands Swarm Integration Test ===\n")

    # Initialize components
    thresholds = ThresholdConfig()
    monitor = ThresholdMonitor(thresholds)
    coordinator = SwarmCoordinator()

    # Connect threshold monitor to swarm coordinator
    monitor.add_breach_callback(coordinator.activate_swarm)

    print("✓ Components initialized")
    print(f"✓ Swarm status: {coordinator.get_swarm_status()}")
    print(f"✓ Agent status: {coordinator.get_agent_status()}")
    print()

    # Test 1: Normal metrics (no breach)
    print("Test 1: Normal metrics (should not trigger swarm)")
    normal_metrics = MECMetrics(
        site_id="MEC_A",
        cpu_utilization=45.0,
        gpu_utilization=30.0,
        memory_utilization=55.0,
        queue_depth=15,
        response_time_ms=25.0,
        network_latency={"MEC_B": 18.0, "MEC_C": 22.0},
        timestamp=datetime.now(UTC),
    )

    events = monitor.check_thresholds(normal_metrics)
    print(f"Events generated: {len(events)}")
    print(f"Swarm events: {len(coordinator.get_event_history())}")
    print()

    # Test 2: CPU threshold breach (should trigger Strands swarm)
    print("Test 2: CPU threshold breach (should trigger Strands swarm)")
    breach_metrics = MECMetrics(
        site_id="MEC_A",
        cpu_utilization=95.0,  # Exceeds 80% threshold
        gpu_utilization=30.0,
        memory_utilization=55.0,
        queue_depth=15,
        response_time_ms=25.0,
        network_latency={"MEC_B": 18.0, "MEC_C": 22.0},
        timestamp=datetime.now(UTC),
    )

    events = monitor.check_thresholds(breach_metrics)
    print(f"Threshold events generated: {len(events)}")
    if events:
        print(f"Breach event: {events[0].metric_name} = {events[0].current_value}")

    swarm_events = coordinator.get_event_history()
    print(f"Swarm events: {len(swarm_events)}")
    if swarm_events:
        latest_event = swarm_events[-1]
        print(f"Latest swarm event: {latest_event['event_type']}")
        print(f"Success: {latest_event['success']}")
        print(f"Duration: {latest_event['duration_ms']}ms")

        if latest_event.get("decision"):
            decision = latest_event["decision"]
            print(f"Selected site: {decision['selected_site']}")
            print(f"Confidence: {decision['confidence_score']:.2f}")
            print(f"Participants: {decision['participants']}")
            print(f"Reasoning: {decision['reasoning']}")
    print()

    # Test 3: Multiple threshold breaches
    print("Test 3: Multiple threshold breaches")
    multi_breach_metrics = MECMetrics(
        site_id="MEC_B",
        cpu_utilization=85.0,  # Exceeds threshold
        gpu_utilization=90.0,  # Exceeds threshold
        memory_utilization=55.0,
        queue_depth=60,  # Exceeds threshold
        response_time_ms=150.0,  # Exceeds threshold
        network_latency={"MEC_A": 18.0, "MEC_C": 22.0},
        timestamp=datetime.now(UTC),
    )

    events = monitor.check_thresholds(multi_breach_metrics)
    print(f"Threshold events generated: {len(events)}")
    for event in events:
        print(
            f"  - {event.metric_name}: {event.current_value} "
            f"(severity: {event.severity.value})"
        )

    time.sleep(0.1)  # Small delay to ensure different timestamps

    swarm_events = coordinator.get_event_history()
    print(f"Total swarm events: {len(swarm_events)}")
    print()

    # Test 4: Swarm metrics and performance
    print("Test 4: Swarm performance metrics")
    swarm_metrics = coordinator.get_swarm_metrics()
    print(f"Swarm configured: {swarm_metrics['swarm_configured']}")
    print(f"Total decisions: {swarm_metrics['total_decisions']}")
    print(f"Agent count: {swarm_metrics['agent_count']}")
    print(f"Execution timeout: {swarm_metrics['execution_timeout']}s")
    print()

    # Summary
    print("=== Test Summary ===")
    final_status = coordinator.get_swarm_status()
    print(f"Total swarm decisions: {final_status['total_decisions']}")
    print(f"Total swarm events: {len(coordinator.get_event_history())}")
    print(f"Current swarm state: {final_status['state']}")
    print(f"Swarm available: {final_status['swarm_available']}")

    # Show agent status
    print("\nStrands Agent Status:")
    agent_status = coordinator.get_agent_status()
    for agent_name, status in agent_status.items():
        print(
            f"  {status['agent_type']}: {status['status']} "
            f"(site: {status['mec_site']}, tools: {status['mcp_tools']})"
        )

    # Show site status
    print("\nMEC Site Status:")
    for site_id, site_info in final_status["sites"].items():
        print(
            f"  {site_id}: {site_info['status']} "
            f"(load: {site_info['load_score']:.2f})"
        )

    print("\n✓ Strands swarm integration test completed successfully!")


if __name__ == "__main__":
    test_strands_swarm_integration()
