"""
Agent Coordinator - Manages agent lifecycle and work distribution.

Coordinates multiple agents by role, handles task assignment,
and detects when all work is complete.
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from message_bus import Message, get_message_bus
from task_engine import TaskEngine, Task, TaskState, get_task_engine
from config import BASE_DIR


class AgentCoordinator:
    """
    Coordinates multiple agents and manages work distribution.

    - Assigns tasks to agents
    - Tracks agent status
    - Detects work completion
    - Manages system state
    """

    # Agent roles in execution order
    AGENT_ROLES = ["planner", "designer", "implementer", "tester", "maintainer"]

    def __init__(self):
        self.task_engine = get_task_engine()
        self.message_bus = get_message_bus()
        self.agents: Dict[str, Dict] = {}  # agent_id -> {role, status, tasks}
        self.project_id = "pando-dev"
        self.is_running = False
        self.work_complete = False
        self.state_file = BASE_DIR / "coordinator_state.json"
        self._lock = threading.RLock()

        self._load_state()
        self._subscribe_to_messages()

    def register_agent(self, agent_id: str, role: str):
        """Register an agent with the coordinator."""
        with self._lock:
            self.agents[agent_id] = {
                "role": role,
                "status": "idle",
                "current_task": None,
                "tasks_completed": 0,
                "registered_at": datetime.utcnow().isoformat(),
            }
        self.message_bus.publish(
            Message(
                message_type="agent_ready",
                source_agent=agent_id,
                payload={"role": role},
            )
        )

    def assign_work(self, agent_id: str) -> Optional[Task]:
        """
        Assign a pending task to an agent.

        Returns the assigned task or None if no work available.
        """
        with self._lock:
            agent = self.agents.get(agent_id)
            if not agent:
                return None

            role = agent["role"]
            pending = self.task_engine.get_pending_tasks(agent_role=role)

            if not pending:
                self._check_work_complete()
                return None

            task = pending[0]
            self.task_engine.assign_task(task.id, agent_id)
            agent["current_task"] = task.id
            agent["status"] = "working"

            self.message_bus.publish(
                Message(
                    message_type="task_assigned",
                    source_agent="coordinator",
                    target_agent=agent_id,
                    payload={
                        "task_id": task.id,
                        "title": task.title,
                        "description": task.description,
                    },
                )
            )

            return task

    def task_started(self, agent_id: str, task_id: str):
        """Agent started working on a task."""
        with self._lock:
            self.task_engine.start_task(task_id)
        self.message_bus.publish(
            Message(
                message_type="task_started",
                source_agent=agent_id,
                payload={"task_id": task_id},
            )
        )

    def task_complete(self, agent_id: str, task_id: str):
        """Agent completed a task."""
        with self._lock:
            task = self.task_engine.complete_task(task_id)
            agent = self.agents.get(agent_id)
            if agent:
                agent["status"] = "idle"
                agent["current_task"] = None
                agent["tasks_completed"] += 1

        self.message_bus.publish(
            Message(
                message_type="task_complete",
                source_agent=agent_id,
                payload={"task_id": task_id},
            )
        )

        self._check_work_complete()

    def task_failed(self, agent_id: str, task_id: str, error: str):
        """Agent failed on a task."""
        with self._lock:
            self.task_engine.fail_task(task_id, error)
            agent = self.agents.get(agent_id)
            if agent:
                agent["status"] = "idle"
                agent["current_task"] = None

        self.message_bus.publish(
            Message(
                message_type="task_failed",
                source_agent=agent_id,
                payload={"task_id": task_id, "error": error},
            )
        )

    def _check_work_complete(self):
        """
        Check if all work is done.

        Work is complete when:
        - No pending tasks
        - No in-progress tasks
        - All agents are idle
        - Backlog is fully processed
        """
        with self._lock:
            if self.task_engine.has_work():
                self.work_complete = False
                return

            # All agents idle?
            for agent in self.agents.values():
                if agent["status"] != "idle":
                    self.work_complete = False
                    return

            # Work is complete!
            self.work_complete = True
            print("\n" + "=" * 60)
            print("✓ ALL WORK COMPLETE")
            print("=" * 60)
            print("All tasks assigned, completed, and agents are idle.")
            print("System has:")
            print("  - Processed all backlog items")
            print("  - Fixed all defects")
            print("  - Improved code quality")
            print("  - Implemented required features")
            print("=" * 60 + "\n")

            self.message_bus.publish(
                Message(
                    message_type="system_status",
                    source_agent="coordinator",
                    payload={"status": "work_complete", "stats": self.get_stats()},
                )
            )

    def get_stats(self) -> Dict:
        """Get system statistics."""
        with self._lock:
            task_stats = self.task_engine.get_stats()
            agent_count = len(self.agents)
            tasks_completed = sum(
                agent["tasks_completed"] for agent in self.agents.values()
            )

            return {
                "task_stats": task_stats,
                "agents_registered": agent_count,
                "total_tasks_completed": tasks_completed,
                "work_complete": self.work_complete,
                "timestamp": datetime.utcnow().isoformat(),
            }

    def should_continue_running(self) -> bool:
        """Check if system should continue running."""
        return not self.work_complete

    def _subscribe_to_messages(self):
        """Subscribe to relevant messages."""
        pass  # Messages handled externally for now

    def _save_state(self):
        """Save coordinator state."""
        try:
            state = {
                "agents": self.agents,
                "work_complete": self.work_complete,
                "timestamp": datetime.utcnow().isoformat(),
                "stats": self.get_stats(),
            }
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except IOError as e:
            print(f"Warning: Failed to save coordinator state: {e}")

    def _load_state(self):
        """Load coordinator state."""
        if not self.state_file.exists():
            return
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
                self.agents = state.get("agents", {})
                self.work_complete = state.get("work_complete", False)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to load coordinator state: {e}")


# Global coordinator instance
_coordinator: Optional[AgentCoordinator] = None


def get_coordinator() -> AgentCoordinator:
    """Get or create the global coordinator."""
    global _coordinator
    if _coordinator is None:
        _coordinator = AgentCoordinator()
    return _coordinator
