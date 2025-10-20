#!/usr/bin/env python3
"""
Unit tests for individual Strands agents in EdgeMind MEC orchestration system.

Tests each agent's core functionality, MCP tool integration, and status reporting.
"""

import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.agents.cache_manager_agent import CacheManagerAgent
from src.agents.decision_coordinator_agent import DecisionCoordinatorAgent
from src.agents.load_balancer_agent import LoadBalancerAgent
from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.resource_monitor_agent import ResourceMonitorAgent
from src.orchestrator.threshold_monitor import SeverityLevel, ThresholdEvent


class TestOrchestratorAgent(unittest.TestCase):
    """Unit tests for OrchestratorAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = OrchestratorAgent(mec_site="TEST_MEC")

    def test_agent_initialization(self):
        """Test agent initialization and basic properties."""
        self.assertEqual(self.agent.mec_site, "TEST_MEC")
        self.assertEqual(self.agent.agent_id, "orchestrator_TEST_MEC")
        self.assertIsNotNone(self.agent.agent)
        self.assertIsNotNone(self.agent.model)
        self.assertIsInstance(self.agent.mcp_tools, list)

    def test_get_agent_status(self):
        """Test agent status reporting."""
        status = self.agent.get_agent_status()

        expected_keys = {
            "agent_id",
            "agent_type",
            "mec_site",
            "status",
            "swarm_available",
            "peer_agents",
            "mcp_tools",
        }
        self.assertEqual(set(status.keys()), expected_keys)

        self.assertEqual(status["agent_id"], "orchestrator_TEST_MEC")
        self.assertEqual(status["agent_type"], "orchestrator")
        self.assertEqual(status["mec_site"], "TEST_MEC")
        self.assertEqual(status["status"], "active")
        self.assertFalse(status["swarm_available"])  # No swarm set initially
        self.assertEqual(status["peer_agents"], 0)

    def test_set_swarm(self):
        """Test swarm registration."""
        mock_swarm = MagicMock()
        mock_swarm.agents = [MagicMock(), MagicMock()]

        self.agent.set_swarm(mock_swarm)

        self.assertEqual(self.agent.swarm, mock_swarm)
        status = self.agent.get_agent_status()
        self.assertTrue(status["swarm_available"])

    def test_register_peer_agent(self):
        """Test peer agent registration."""
        mock_agent = MagicMock()

        self.agent.register_peer_agent("test_peer", mock_agent)

        self.assertIn("test_peer", self.agent.peer_agents)
        self.assertEqual(self.agent.peer_agents["test_peer"], mock_agent)

        status = self.agent.get_agent_status()
        self.assertEqual(status["peer_agents"], 1)

    async def test_handle_threshold_breach_no_swarm(self):
        """Test threshold breach handling without swarm (fallback mode)."""
        # Create mock threshold event
        threshold_event = MagicMock()
        threshold_event.site_id = "TEST_MEC"
        threshold_event.metric_name = "cpu_utilization"
        threshold_event.current_value = 95.0
        threshold_event.threshold_value = 80.0
        threshold_event.severity = SeverityLevel.HIGH
        threshold_event.breach_duration_ms = 1000

        # Mock the agent's response
        with patch.object(
            self.agent.agent, "__call__", return_value="Fallback response"
        ):
            result = await self.agent.handle_threshold_breach(threshold_event)

        # Verify fallback result structure
        expected_keys = {
            "status",
            "execution_time_ms",
            "agents_involved",
            "final_result",
            "token_usage",
        }
        self.assertEqual(set(result.keys()), expected_keys)
        self.assertEqual(result["status"], "completed_fallback")
        self.assertEqual(result["agents_involved"], ["orchestrator_TEST_MEC"])
        self.assertEqual(result["final_result"], "Fallback response")

    async def test_handle_threshold_breach_with_swarm(self):
        """Test threshold breach handling with swarm coordination."""
        # Set up mock swarm
        mock_swarm = MagicMock()
        mock_result = MagicMock()
        mock_result.status = "completed"
        mock_result.execution_time = 75
        mock_result.node_history = [
            MagicMock(node_id="agent1"),
            MagicMock(node_id="agent2"),
        ]
        mock_result.result = "Swarm decision: MEC_B selected"
        mock_result.accumulated_usage = {"tokens": 150}

        mock_swarm.invoke_async = AsyncMock(return_value=mock_result)
        self.agent.set_swarm(mock_swarm)

        # Create threshold event
        threshold_event = MagicMock()
        threshold_event.site_id = "TEST_MEC"
        threshold_event.metric_name = "cpu_utilization"
        threshold_event.current_value = 95.0
        threshold_event.threshold_value = 80.0
        threshold_event.severity = SeverityLevel.HIGH
        threshold_event.breach_duration_ms = 1000

        result = await self.agent.handle_threshold_breach(threshold_event)

        # Verify swarm result structure
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["execution_time_ms"], 75)
        self.assertEqual(result["agents_involved"], ["agent1", "agent2"])
        self.assertEqual(result["final_result"], "Swarm decision: MEC_B selected")
        self.assertEqual(result["token_usage"], {"tokens": 150})

    async def test_handle_threshold_breach_swarm_failure(self):
        """Test threshold breach handling when swarm fails."""
        # Set up mock swarm that raises exception
        mock_swarm = MagicMock()
        mock_swarm.invoke_async = AsyncMock(side_effect=Exception("Swarm timeout"))
        self.agent.set_swarm(mock_swarm)

        threshold_event = MagicMock()
        threshold_event.site_id = "TEST_MEC"
        threshold_event.metric_name = "cpu_utilization"
        threshold_event.current_value = 95.0
        threshold_event.to_dict = MagicMock(return_value={"test": "data"})

        result = await self.agent.handle_threshold_breach(threshold_event)

        # Verify failure result structure
        self.assertEqual(result["status"], "failed")
        self.assertIn("Swarm timeout", result["error"])
        self.assertEqual(result["execution_time_ms"], 0)
        self.assertEqual(result["agents_involved"], [])
        self.assertIsNone(result["final_result"])


class TestLoadBalancerAgent(unittest.TestCase):
    """Unit tests for LoadBalancerAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = LoadBalancerAgent(mec_site="TEST_MEC_B")

    def test_agent_initialization(self):
        """Test agent initialization and basic properties."""
        self.assertEqual(self.agent.mec_site, "TEST_MEC_B")
        self.assertEqual(self.agent.agent_id, "load_balancer_TEST_MEC_B")
        self.assertIsNotNone(self.agent.agent)
        self.assertIsInstance(self.agent.mcp_tools, list)

    def test_get_agent_status(self):
        """Test agent status reporting."""
        status = self.agent.get_agent_status()

        expected_keys = {
            "agent_id",
            "agent_type",
            "mec_site",
            "status",
            "mcp_tools",
            "specialization",
        }
        self.assertEqual(set(status.keys()), expected_keys)

        self.assertEqual(status["agent_id"], "load_balancer_TEST_MEC_B")
        self.assertEqual(status["agent_type"], "load_balancer")
        self.assertEqual(status["mec_site"], "TEST_MEC_B")
        self.assertEqual(status["status"], "active")
        self.assertEqual(status["specialization"], "site_selection_and_scaling")

    def test_system_prompt_content(self):
        """Test that system prompt contains required elements."""
        prompt = self.agent._get_system_prompt()

        # Check for key responsibilities
        self.assertIn("Load Balancer Agent", prompt)
        self.assertIn("TEST_MEC_B", prompt)
        self.assertIn("metrics_monitor", prompt)
        self.assertIn("container_ops", prompt)
        self.assertIn("Site Selection Criteria", prompt)

        # Check for quantitative criteria
        self.assertIn("40% weight", prompt)  # Site health weight
        self.assertIn("30% weight", prompt)  # Utilization weight
        self.assertIn("20% weight", prompt)  # Network latency weight
        self.assertIn("10% weight", prompt)  # Queue depth weight


class TestDecisionCoordinatorAgent(unittest.TestCase):
    """Unit tests for DecisionCoordinatorAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = DecisionCoordinatorAgent(mec_site="TEST_MEC_C")

    def test_agent_initialization(self):
        """Test agent initialization and basic properties."""
        self.assertEqual(self.agent.mec_site, "TEST_MEC_C")
        self.assertEqual(self.agent.agent_id, "decision_coordinator_TEST_MEC_C")
        self.assertIsNotNone(self.agent.agent)
        self.assertIsInstance(self.agent.mcp_tools, list)

    def test_get_agent_status(self):
        """Test agent status reporting."""
        status = self.agent.get_agent_status()

        expected_keys = {
            "agent_id",
            "agent_type",
            "mec_site",
            "status",
            "mcp_tools",
            "specialization",
        }
        self.assertEqual(set(status.keys()), expected_keys)

        self.assertEqual(status["agent_id"], "decision_coordinator_TEST_MEC_C")
        self.assertEqual(status["agent_type"], "decision_coordinator")
        self.assertEqual(status["specialization"], "consensus_and_coordination")

    def test_system_prompt_consensus_process(self):
        """Test that system prompt includes consensus process details."""
        prompt = self.agent._get_system_prompt()

        # Check for consensus process steps
        self.assertIn("Consensus Process", prompt)
        self.assertIn("memory_sync", prompt)
        self.assertIn("telemetry", prompt)
        self.assertIn("consensus >= 60%", prompt)
        self.assertIn("LoadBalancer (30%)", prompt)
        self.assertIn("ResourceMonitor (25%)", prompt)
        self.assertIn("Minimum confidence threshold: 0.6", prompt)


class TestCacheManagerAgent(unittest.TestCase):
    """Unit tests for CacheManagerAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = CacheManagerAgent(mec_site="TEST_MEC_CACHE")

    def test_agent_initialization(self):
        """Test agent initialization and basic properties."""
        self.assertEqual(self.agent.mec_site, "TEST_MEC_CACHE")
        self.assertEqual(self.agent.agent_id, "cache_manager_TEST_MEC_CACHE")
        self.assertIsNotNone(self.agent.agent)
        self.assertIsInstance(self.agent.mcp_tools, list)

    def test_get_agent_status(self):
        """Test agent status reporting."""
        status = self.agent.get_agent_status()

        self.assertEqual(status["agent_type"], "cache_manager")
        self.assertEqual(status["specialization"], "model_caching_and_preloading")

    def test_system_prompt_cache_strategy(self):
        """Test that system prompt includes cache management strategy."""
        prompt = self.agent._get_system_prompt()

        # Check for cache management details
        self.assertIn("15-minute refresh cycles", prompt)
        self.assertIn("inference", prompt)
        self.assertIn("telemetry", prompt)
        self.assertIn("Cache hit rate: >85%", prompt)
        self.assertIn("Model loading time: <5 seconds", prompt)
        self.assertIn("predictive preloading", prompt)


class TestResourceMonitorAgent(unittest.TestCase):
    """Unit tests for ResourceMonitorAgent."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = ResourceMonitorAgent(mec_site="TEST_MEC_MONITOR")

    def test_agent_initialization(self):
        """Test agent initialization and basic properties."""
        self.assertEqual(self.agent.mec_site, "TEST_MEC_MONITOR")
        self.assertEqual(self.agent.agent_id, "resource_monitor_TEST_MEC_MONITOR")
        self.assertIsNotNone(self.agent.agent)
        self.assertIsInstance(self.agent.mcp_tools, list)

    def test_get_agent_status(self):
        """Test agent status reporting."""
        status = self.agent.get_agent_status()

        self.assertEqual(status["agent_type"], "resource_monitor")
        self.assertEqual(status["specialization"], "performance_monitoring")

    def test_system_prompt_monitoring_scope(self):
        """Test that system prompt includes monitoring scope and targets."""
        prompt = self.agent._get_system_prompt()

        # Check for monitoring targets
        self.assertIn("CPU/GPU utilization (target: <80%)", prompt)
        self.assertIn("Network latency between MEC sites (target: <20ms)", prompt)
        self.assertIn("Response times for inference requests (target: <100ms)", prompt)
        self.assertIn(
            "Queue depth and processing backlog (target: <50 requests)", prompt
        )
        self.assertIn("metrics_monitor", prompt)
        self.assertIn("telemetry", prompt)


class TestAgentMCPToolIntegration(unittest.TestCase):
    """Test MCP tool integration across all agents."""

    def setUp(self):
        """Set up test fixtures for all agents."""
        self.orchestrator = OrchestratorAgent("MEC_A")
        self.load_balancer = LoadBalancerAgent("MEC_B")
        self.decision_coordinator = DecisionCoordinatorAgent("MEC_C")
        self.cache_manager = CacheManagerAgent("MEC_B")
        self.resource_monitor = ResourceMonitorAgent("MEC_A")

    def test_all_agents_have_mcp_tools(self):
        """Test that all agents have MCP tools initialized."""
        agents = [
            self.orchestrator,
            self.load_balancer,
            self.decision_coordinator,
            self.cache_manager,
            self.resource_monitor,
        ]

        for agent in agents:
            self.assertIsInstance(agent.mcp_tools, list)
            # Currently empty list for simulation, but structure is correct
            self.assertIsNotNone(agent.mcp_tools)

    def test_agent_system_prompts_mention_mcp_tools(self):
        """Test that all agent system prompts mention their MCP tools."""
        # Orchestrator should mention metrics_monitor and memory_sync
        orchestrator_prompt = self.orchestrator._get_system_prompt()
        self.assertIn("metrics_monitor", orchestrator_prompt)
        self.assertIn("memory_sync", orchestrator_prompt)

        # Load Balancer should mention metrics_monitor and container_ops
        lb_prompt = self.load_balancer._get_system_prompt()
        self.assertIn("metrics_monitor", lb_prompt)
        self.assertIn("container_ops", lb_prompt)

        # Decision Coordinator should mention memory_sync and telemetry
        dc_prompt = self.decision_coordinator._get_system_prompt()
        self.assertIn("memory_sync", dc_prompt)
        self.assertIn("telemetry", dc_prompt)

        # Cache Manager should mention inference and telemetry
        cm_prompt = self.cache_manager._get_system_prompt()
        self.assertIn("inference", cm_prompt)
        self.assertIn("telemetry", cm_prompt)

        # Resource Monitor should mention metrics_monitor and telemetry
        rm_prompt = self.resource_monitor._get_system_prompt()
        self.assertIn("metrics_monitor", rm_prompt)
        self.assertIn("telemetry", rm_prompt)

    def test_agent_status_includes_mcp_tool_count(self):
        """Test that agent status includes MCP tool count."""
        agents = [
            self.orchestrator,
            self.load_balancer,
            self.decision_coordinator,
            self.cache_manager,
            self.resource_monitor,
        ]

        for agent in agents:
            status = agent.get_agent_status()
            self.assertIn("mcp_tools", status)
            self.assertIsInstance(status["mcp_tools"], int)
            self.assertGreaterEqual(status["mcp_tools"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
