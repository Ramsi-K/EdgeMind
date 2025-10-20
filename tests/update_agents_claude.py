#!/usr/bin/env python3
"""
Script to update all Strands agents to use Claude/Anthropic model.
"""

import os
import re


def update_agent_file(filepath):
    """Update a single agent file to use Claude."""
    with open(filepath, "r") as f:
        content = f.read()

    # Add Claude imports if not present
    if "from strands.models.anthropic import AnthropicModel" not in content:
        # Find the strands import line and add Claude import after it
        content = re.sub(
            r"(from strands import Agent)",
            r"\1\nfrom strands.models.anthropic import AnthropicModel\nimport os",
            content,
        )

    # Update the __init__ method to include Claude model
    if "AnthropicModel" not in content:
        # Find the agent creation and add model
        pattern = r"(self\.agent = Agent\(\s*name=self\.agent_id,\s*)(system_prompt=self\._get_system_prompt\(\),\s*tools=self\.mcp_tools,\s*\))"
        replacement = r"""\1model=self._create_claude_model(),
            \2"""

        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)

        # Add the Claude model creation method
        method_to_add = '''
    def _create_claude_model(self):
        """Create Claude model for this agent."""
        return AnthropicModel(
            client_args={
                "api_key": os.getenv("ANTHROPIC_API_KEY", "your-api-key-here"),
            },
            max_tokens=2048,
            model_id="claude-3-5-sonnet-20241022",
            params={
                "temperature": 0.3,  # Consistent decision making for MEC orchestration
            }
        )
'''

        # Insert the method before the _create_dummy_mcp_tools method
        content = re.sub(
            r"(\s+def _create_dummy_mcp_tools)", method_to_add + r"\1", content
        )

    with open(filepath, "w") as f:
        f.write(content)

    print(f"Updated {filepath}")


def main():
    """Update all agent files."""
    agent_files = [
        "src/agents/load_balancer_agent.py",
        "src/agents/decision_coordinator_agent.py",
        "src/agents/resource_monitor_agent.py",
        "src/agents/cache_manager_agent.py",
    ]

    for filepath in agent_files:
        if os.path.exists(filepath):
            update_agent_file(filepath)
        else:
            print(f"File not found: {filepath}")


if __name__ == "__main__":
    main()
