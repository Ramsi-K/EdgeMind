"""
MCP Tool Server: Memory Sync

Provides swarm state synchronization and consensus coordination using
AWS Bedrock AgentCore Memory for persistent coordination state.
"""

import json
import random
import time
from datetime import UTC, datetime
from typing import Any, Dict, List

from mcp.types import Tool


class MemorySyncMCP:
    """MCP tool server for swarm state synchronization and consensus coordination."""

    def __init__(self, simulation_mode: bool = True):
        self.simulation_mode = simulation_mode
        self.swarm_state = {
            "consensus_history": [],
            "active_decisions": {},
            "agent_states": {},
            "coordination_sessions": {},
            "memory_store": {},
        }
        self.session_counter = 0
        self.decision_counter = 0

    def get_tools(self) -> List[Tool]:
        """Return available MCP tools."""
        return [
            Tool(
                name="sync_swarm_state",
                description="Synchronize swarm coordination state across agents",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "state_data": {"type": "object"},
                        "session_id": {"type": "string"},
                        "operation": {
                            "type": "string",
                            "enum": ["read", "write", "merge"],
                            "default": "write",
                        },
                    },
                    "required": ["agent_id", "state_data"],
                },
            ),
            Tool(
                name="initiate_consensus",
                description="Start a new consensus coordination session",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "initiator_agent": {"type": "string"},
                        "consensus_topic": {"type": "string"},
                        "participants": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "timeout_ms": {"type": "integer", "default": 5000},
                        "context_data": {"type": "object"},
                    },
                    "required": [
                        "initiator_agent",
                        "consensus_topic",
                        "participants",
                    ],
                },
            ),
            Tool(
                name="submit_vote",
                description="Submit a vote for an active consensus decision",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "agent_id": {"type": "string"},
                        "vote_data": {"type": "object"},
                        "confidence": {"type": "number"},
                        "reasoning": {"type": "string"},
                    },
                    "required": ["session_id", "agent_id", "vote_data"],
                },
            ),
            Tool(
                name="get_consensus_status",
                description="Get status of active consensus sessions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "agent_id": {"type": "string"},
                    },
                },
            ),
            Tool(
                name="store_coordination_memory",
                description="Store long-term coordination patterns and learnings",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "memory_key": {"type": "string"},
                        "memory_data": {"type": "object"},
                        "memory_type": {
                            "type": "string",
                            "enum": [
                                "pattern",
                                "decision",
                                "performance",
                                "anomaly",
                            ],
                        },
                        "retention_hours": {
                            "type": "integer",
                            "default": 168,
                        },  # 1 week
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["memory_key", "memory_data", "memory_type"],
                },
            ),
            Tool(
                name="retrieve_coordination_memory",
                description="Retrieve stored coordination patterns and learnings",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "memory_key": {"type": "string"},
                        "memory_type": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "limit": {"type": "integer", "default": 10},
                    },
                },
            ),
            Tool(
                name="update_agent_state",
                description="Update agent state in swarm coordination",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_id": {"type": "string"},
                        "state": {
                            "type": "string",
                            "enum": [
                                "idle",
                                "active",
                                "voting",
                                "executing",
                                "failed",
                            ],
                        },
                        "current_task": {"type": "string"},
                        "performance_metrics": {"type": "object"},
                        "last_activity": {"type": "string"},
                    },
                    "required": ["agent_id", "state"],
                },
            ),
            Tool(
                name="get_swarm_overview",
                description="Get comprehensive swarm coordination overview",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_history": {
                            "type": "boolean",
                            "default": False,
                        },
                        "time_window_minutes": {
                            "type": "integer",
                            "default": 60,
                        },
                    },
                },
            ),
        ]

    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Handle MCP tool calls."""
        if name == "sync_swarm_state":
            return await self._sync_swarm_state(arguments)
        elif name == "initiate_consensus":
            return await self._initiate_consensus(arguments)
        elif name == "submit_vote":
            return await self._submit_vote(arguments)
        elif name == "get_consensus_status":
            return await self._get_consensus_status(arguments)
        elif name == "store_coordination_memory":
            return await self._store_coordination_memory(arguments)
        elif name == "retrieve_coordination_memory":
            return await self._retrieve_coordination_memory(arguments)
        elif name == "update_agent_state":
            return await self._update_agent_state(arguments)
        elif name == "get_swarm_overview":
            return await self._get_swarm_overview(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _sync_swarm_state(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize swarm coordination state across agents."""
        agent_id = arguments["agent_id"]
        state_data = arguments["state_data"]
        session_id = arguments.get("session_id", "global")
        operation = arguments.get("operation", "write")

        if session_id not in self.swarm_state["coordination_sessions"]:
            self.swarm_state["coordination_sessions"][session_id] = {
                "created_at": datetime.now(UTC).isoformat(),
                "participants": [],
                "state_updates": [],
            }

        session = self.swarm_state["coordination_sessions"][session_id]

        if operation == "write":
            # Write new state data
            state_update = {
                "agent_id": agent_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "state_data": state_data,
                "operation": "write",
            }
            session["state_updates"].append(state_update)

            if agent_id not in session["participants"]:
                session["participants"].append(agent_id)

            return {
                "session_id": session_id,
                "agent_id": agent_id,
                "operation": "write",
                "state_synced": True,
                "timestamp": state_update["timestamp"],
                "success": True,
            }

        elif operation == "read":
            # Read current state
            latest_states = {}
            for update in reversed(session["state_updates"]):
                if update["agent_id"] not in latest_states:
                    latest_states[update["agent_id"]] = update["state_data"]

            return {
                "session_id": session_id,
                "operation": "read",
                "current_states": latest_states,
                "participants": session["participants"],
                "total_updates": len(session["state_updates"]),
                "success": True,
            }

        elif operation == "merge":
            # Merge state with existing data
            # In a real implementation, this would use sophisticated merging logic
            merged_state = state_data.copy()

            # Simple merge: combine with latest state from other agents
            for update in reversed(session["state_updates"]):
                if update["agent_id"] != agent_id:
                    for key, value in update["state_data"].items():
                        if key not in merged_state:
                            merged_state[key] = value

            state_update = {
                "agent_id": agent_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "state_data": merged_state,
                "operation": "merge",
            }
            session["state_updates"].append(state_update)

            return {
                "session_id": session_id,
                "agent_id": agent_id,
                "operation": "merge",
                "merged_state": merged_state,
                "timestamp": state_update["timestamp"],
                "success": True,
            }

    async def _initiate_consensus(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Start a new consensus coordination session."""
        self.session_counter += 1
        session_id = f"consensus_{self.session_counter:06d}"

        initiator_agent = arguments["initiator_agent"]
        consensus_topic = arguments["consensus_topic"]
        participants = arguments["participants"]
        timeout_ms = arguments.get("timeout_ms", 5000)
        context_data = arguments.get("context_data", {})

        # Create consensus session
        consensus_session = {
            "session_id": session_id,
            "initiator_agent": initiator_agent,
            "consensus_topic": consensus_topic,
            "participants": participants,
            "timeout_ms": timeout_ms,
            "context_data": context_data,
            "status": "active",
            "votes": {},
            "created_at": datetime.now(UTC).isoformat(),
            "expires_at": datetime.fromtimestamp(
                time.time() + timeout_ms / 1000, UTC
            ).isoformat(),
        }

        self.swarm_state["coordination_sessions"][session_id] = consensus_session

        return {
            "session_id": session_id,
            "consensus_topic": consensus_topic,
            "participants": participants,
            "timeout_ms": timeout_ms,
            "status": "active",
            "created_at": consensus_session["created_at"],
            "expires_at": consensus_session["expires_at"],
            "success": True,
        }

    async def _submit_vote(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a vote for an active consensus decision."""
        session_id = arguments["session_id"]
        agent_id = arguments["agent_id"]
        vote_data = arguments["vote_data"]
        confidence = arguments.get("confidence", 0.5)
        reasoning = arguments.get("reasoning", "")

        if session_id not in self.swarm_state["coordination_sessions"]:
            return {
                "error": f"Consensus session {session_id} not found",
                "success": False,
            }

        session = self.swarm_state["coordination_sessions"][session_id]

        if session["status"] != "active":
            return {
                "error": f"Consensus session {session_id} is not active",
                "success": False,
                "status": session["status"],
            }

        # Check if session has expired
        expires_at = datetime.fromisoformat(
            session["expires_at"].replace("Z", "+00:00")
        )
        if datetime.now(UTC) > expires_at:
            session["status"] = "expired"
            return {
                "error": f"Consensus session {session_id} has expired",
                "success": False,
                "status": "expired",
            }

        # Submit vote
        vote = {
            "agent_id": agent_id,
            "vote_data": vote_data,
            "confidence": confidence,
            "reasoning": reasoning,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        session["votes"][agent_id] = vote

        # Check if consensus is reached
        total_participants = len(session["participants"])
        votes_received = len(session["votes"])

        consensus_reached = votes_received >= total_participants

        if consensus_reached:
            # Calculate consensus result
            consensus_result = self._calculate_consensus(session["votes"])
            session["status"] = "completed"
            session["consensus_result"] = consensus_result
            session["completed_at"] = datetime.now(UTC).isoformat()

            # Store in consensus history
            self.swarm_state["consensus_history"].append(
                {
                    "session_id": session_id,
                    "topic": session["consensus_topic"],
                    "result": consensus_result,
                    "participants": session["participants"],
                    "votes": session["votes"],
                    "completed_at": session["completed_at"],
                }
            )

        return {
            "session_id": session_id,
            "agent_id": agent_id,
            "vote_submitted": True,
            "votes_received": votes_received,
            "total_participants": total_participants,
            "consensus_reached": consensus_reached,
            "session_status": session["status"],
            "timestamp": vote["timestamp"],
            "success": True,
        }

    async def _get_consensus_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of active consensus sessions."""
        session_id = arguments.get("session_id")
        agent_id = arguments.get("agent_id")

        if session_id:
            # Get specific session status
            if session_id not in self.swarm_state["coordination_sessions"]:
                return {
                    "error": f"Consensus session {session_id} not found",
                    "success": False,
                }

            session = self.swarm_state["coordination_sessions"][session_id]
            return {
                "session": session,
                "votes_received": len(session["votes"]),
                "total_participants": len(session["participants"]),
                "success": True,
            }
        else:
            # Get all active sessions
            active_sessions = []
            for sid, session in self.swarm_state["coordination_sessions"].items():
                if session["status"] == "active":
                    session_info = {
                        "session_id": sid,
                        "topic": session["consensus_topic"],
                        "participants": session["participants"],
                        "votes_received": len(session["votes"]),
                        "expires_at": session["expires_at"],
                    }

                    # Filter by agent if specified
                    if not agent_id or agent_id in session["participants"]:
                        active_sessions.append(session_info)

            return {
                "active_sessions": active_sessions,
                "total_active": len(active_sessions),
                "success": True,
            }

    async def _store_coordination_memory(
        self, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Store long-term coordination patterns and learnings."""
        memory_key = arguments["memory_key"]
        memory_data = arguments["memory_data"]
        memory_type = arguments["memory_type"]
        retention_hours = arguments.get("retention_hours", 168)
        tags = arguments.get("tags", [])

        memory_entry = {
            "memory_key": memory_key,
            "memory_data": memory_data,
            "memory_type": memory_type,
            "tags": tags,
            "stored_at": datetime.now(UTC).isoformat(),
            "expires_at": datetime.fromtimestamp(
                time.time() + retention_hours * 3600, UTC
            ).isoformat(),
            "access_count": 0,
            "last_accessed": None,
        }

        self.swarm_state["memory_store"][memory_key] = memory_entry

        return {
            "memory_key": memory_key,
            "memory_type": memory_type,
            "stored": True,
            "retention_hours": retention_hours,
            "expires_at": memory_entry["expires_at"],
            "success": True,
        }

    async def _retrieve_coordination_memory(
        self, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Retrieve stored coordination patterns and learnings."""
        memory_key = arguments.get("memory_key")
        memory_type = arguments.get("memory_type")
        tags = arguments.get("tags", [])
        limit = arguments.get("limit", 10)

        if memory_key:
            # Retrieve specific memory
            if memory_key not in self.swarm_state["memory_store"]:
                return {
                    "error": f"Memory key {memory_key} not found",
                    "success": False,
                }

            memory_entry = self.swarm_state["memory_store"][memory_key]

            # Check if expired
            expires_at = datetime.fromisoformat(
                memory_entry["expires_at"].replace("Z", "+00:00")
            )
            if datetime.now(UTC) > expires_at:
                del self.swarm_state["memory_store"][memory_key]
                return {
                    "error": f"Memory key {memory_key} has expired",
                    "success": False,
                }

            # Update access statistics
            memory_entry["access_count"] += 1
            memory_entry["last_accessed"] = datetime.now(UTC).isoformat()

            return {
                "memory_entry": memory_entry,
                "success": True,
            }
        else:
            # Search memories by type and tags
            matching_memories = []

            for key, memory_entry in self.swarm_state["memory_store"].items():
                # Check expiration
                expires_at = datetime.fromisoformat(
                    memory_entry["expires_at"].replace("Z", "+00:00")
                )
                if datetime.now(UTC) > expires_at:
                    continue

                # Apply filters
                if memory_type and memory_entry["memory_type"] != memory_type:
                    continue

                if tags:
                    if not any(tag in memory_entry["tags"] for tag in tags):
                        continue

                matching_memories.append(
                    {
                        "memory_key": key,
                        "memory_type": memory_entry["memory_type"],
                        "tags": memory_entry["tags"],
                        "stored_at": memory_entry["stored_at"],
                        "access_count": memory_entry["access_count"],
                    }
                )

                if len(matching_memories) >= limit:
                    break

            return {
                "matching_memories": matching_memories,
                "total_found": len(matching_memories),
                "filters_applied": {
                    "memory_type": memory_type,
                    "tags": tags,
                },
                "success": True,
            }

    async def _update_agent_state(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update agent state in swarm coordination."""
        agent_id = arguments["agent_id"]
        state = arguments["state"]
        current_task = arguments.get("current_task")
        performance_metrics = arguments.get("performance_metrics", {})
        last_activity = arguments.get("last_activity")

        agent_state = {
            "agent_id": agent_id,
            "state": state,
            "current_task": current_task,
            "performance_metrics": performance_metrics,
            "last_activity": last_activity or datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }

        self.swarm_state["agent_states"][agent_id] = agent_state

        return {
            "agent_id": agent_id,
            "state": state,
            "updated": True,
            "timestamp": agent_state["updated_at"],
            "success": True,
        }

    async def _get_swarm_overview(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive swarm coordination overview."""
        include_history = arguments.get("include_history", False)
        time_window_minutes = arguments.get("time_window_minutes", 60)

        # Active sessions
        active_sessions = [
            session
            for session in self.swarm_state["coordination_sessions"].values()
            if session["status"] == "active"
        ]

        # Agent states
        agent_states = self.swarm_state["agent_states"]

        # Recent consensus history
        recent_consensus = []
        if include_history:
            cutoff_time = time.time() - (time_window_minutes * 60)
            for consensus in self.swarm_state["consensus_history"]:
                completed_time = datetime.fromisoformat(
                    consensus["completed_at"].replace("Z", "+00:00")
                ).timestamp()
                if completed_time > cutoff_time:
                    recent_consensus.append(consensus)

        # Memory store statistics
        memory_stats = {
            "total_memories": len(self.swarm_state["memory_store"]),
            "memory_types": {},
        }

        for memory in self.swarm_state["memory_store"].values():
            mem_type = memory["memory_type"]
            if mem_type not in memory_stats["memory_types"]:
                memory_stats["memory_types"][mem_type] = 0
            memory_stats["memory_types"][mem_type] += 1

        overview = {
            "active_sessions": len(active_sessions),
            "total_agents": len(agent_states),
            "agent_states": {
                agent_id: state["state"] for agent_id, state in agent_states.items()
            },
            "memory_statistics": memory_stats,
            "recent_consensus_count": len(recent_consensus),
            "timestamp": datetime.now(UTC).isoformat(),
        }

        if include_history:
            overview["recent_consensus"] = recent_consensus
            overview["active_session_details"] = active_sessions

        return {
            "swarm_overview": overview,
            "success": True,
        }

    def _calculate_consensus(self, votes: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate consensus result from votes."""
        if not votes:
            return {"result": "no_votes", "confidence": 0.0}

        # Simple consensus: majority vote with confidence weighting
        vote_counts = {}
        total_confidence = 0

        for vote in votes.values():
            vote_key = str(vote["vote_data"])
            confidence = vote["confidence"]

            if vote_key not in vote_counts:
                vote_counts[vote_key] = {"count": 0, "confidence_sum": 0}

            vote_counts[vote_key]["count"] += 1
            vote_counts[vote_key]["confidence_sum"] += confidence
            total_confidence += confidence

        # Find winning vote
        winner = max(vote_counts.items(), key=lambda x: x[1]["count"])
        winning_vote = winner[0]
        winning_confidence = winner[1]["confidence_sum"] / winner[1]["count"]

        return {
            "result": "consensus_reached",
            "winning_vote": winning_vote,
            "confidence": round(winning_confidence, 3),
            "vote_distribution": vote_counts,
            "total_votes": len(votes),
        }


# Standalone function for easy integration
def create_memory_sync_tool() -> MemorySyncMCP:
    """Create a memory sync MCP tool instance."""
    return MemorySyncMCP(simulation_mode=True)


if __name__ == "__main__":
    # Test the MCP tool
    import asyncio

    async def test_memory_sync():
        tool = create_memory_sync_tool()

        # Test initiating consensus
        consensus = await tool.handle_tool_call(
            "initiate_consensus",
            {
                "initiator_agent": "orchestrator_MEC_A",
                "consensus_topic": "site_selection",
                "participants": [
                    "orchestrator_MEC_A",
                    "load_balancer_MEC_B",
                    "decision_coordinator_MEC_C",
                ],
            },
        )
        print("Consensus Initiated:", json.dumps(consensus, indent=2))

        # Test submitting a vote
        vote = await tool.handle_tool_call(
            "submit_vote",
            {
                "session_id": consensus["session_id"],
                "agent_id": "orchestrator_MEC_A",
                "vote_data": {"selected_site": "MEC_C"},
                "confidence": 0.85,
                "reasoning": "MEC_C has lowest latency and highest capacity",
            },
        )
        print("Vote Submitted:", json.dumps(vote, indent=2))

    asyncio.run(test_memory_sync())
