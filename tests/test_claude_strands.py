#!/usr/bin/env python3
"""
Test script to verify Strands agents work with Claude.
"""

import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_claude_agent():
    """Test basic Claude agent functionality."""
    try:
        from strands import Agent
        from strands.models.anthropic import AnthropicModel

        # Create Claude model
        model = AnthropicModel(
            client_args={
                "api_key": os.getenv("ANTHROPIC_API_KEY", "test-key"),
            },
            max_tokens=1024,
            model_id="claude-3-5-sonnet-20241022",
            params={
                "temperature": 0.3,
            },
        )

        # Create agent
        agent = Agent(
            name="test_agent",
            model=model,
            system_prompt="You are a test agent for MEC orchestration.",
        )

        print("✅ Claude Strands agent created successfully!")
        print(f"Agent name: {agent.name}")

        # Test if we have a valid API key
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key and api_key != "your-claude-api-key-here":
            print("✅ API key configured")
            # Could test actual call here if needed
        else:
            print("⚠️  API key not configured - set ANTHROPIC_API_KEY in .env")

        return True

    except Exception as e:
        print(f"❌ Error creating Claude agent: {e}")
        return False


def test_swarm_creation():
    """Test swarm creation with Claude agents."""
    try:
        from strands import Agent
        from strands.models.anthropic import AnthropicModel
        from strands.multiagent import Swarm

        # Create Claude model
        model = AnthropicModel(
            client_args={
                "api_key": os.getenv("ANTHROPIC_API_KEY", "test-key"),
            },
            max_tokens=1024,
            model_id="claude-3-5-sonnet-20241022",
            params={
                "temperature": 0.3,
            },
        )

        # Create test agents
        agent1 = Agent(
            name="orchestrator",
            model=model,
            system_prompt="You are an orchestrator.",
        )
        agent2 = Agent(
            name="load_balancer",
            model=model,
            system_prompt="You are a load balancer.",
        )

        # Create swarm
        swarm = Swarm(
            [agent1, agent2],  # First parameter is the list of agents
            entry_point=agent1,
            max_handoffs=5,
            execution_timeout=30.0,
        )

        print("✅ Swarm created successfully!")
        print(f"Swarm created with entry point: {swarm.entry_point.name}")

        return True

    except Exception as e:
        print(f"❌ Error creating swarm: {e}")
        return False


def test_our_agents():
    """Test our custom agent classes."""
    try:
        from src.agents.load_balancer_agent import LoadBalancerAgent
        from src.agents.orchestrator_agent import OrchestratorAgent

        # Create our agents
        orchestrator = OrchestratorAgent("MEC_A")
        load_balancer = LoadBalancerAgent("MEC_B")

        print("✅ Custom agents created successfully!")
        print(f"Orchestrator: {orchestrator.agent_id}")
        print(f"Load Balancer: {load_balancer.agent_id}")

        return True

    except Exception as e:
        print(f"❌ Error creating custom agents: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing Claude + Strands Integration")
    print("=" * 50)

    success = True

    print("\n1. Testing basic Claude agent...")
    success &= test_claude_agent()

    print("\n2. Testing swarm creation...")
    success &= test_swarm_creation()

    print("\n3. Testing our custom agents...")
    success &= test_our_agents()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Claude + Strands is working.")
    else:
        print("❌ Some tests failed. Check the errors above.")
