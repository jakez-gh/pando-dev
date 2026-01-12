"""
Task Engine - Manages task lifecycle and agent assignment.

Tracks task state, assigns tasks to agents, and ensures work completion detection.
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from config import BASE_DIR

TASKS_DB = BASE_DIR / "tasks" / "tasks.jsonl"


class TaskState(Enum):
    """Task lifecycle states."""

    PENDING = "pending"  # Not yet assigned
    ASSIGNED = "assigned"  # Assigned to an agent
    IN_PROGRESS = "in_progress"  # Agent is working on it
    REVIEW = "review"  # Awaiting review
    DONE = "done"  # Completed successfully
    FAILED = "failed"  # Failed, needs retry
    BLOCKED = "blocked"  # Blocked by dependencies


class TaskPriority(Enum):
    """Task priority levels."""

    CRITICAL = 100
    HIGH = 80
    MEDIUM = 50
    LOW = 20


class Task:
    """
    Represents a single task in the system.

    Tasks have a clear lifecycle and can be assigned to agents based on role.
    """

    def __init__(
        self,
        title: str,
        description: str,
        project_id: str,
        agent_role: str,
        priority: int = TaskPriority.MEDIUM.value,
        task_id: Optional[str] = None,
    ):
        self.id = task_id or str(uuid.uuid4())
        self.title = title
        self.description = description
        self.project_id = project_id
        self.agent_role = agent_role
        self.priority = priority
        self.state = TaskState.PENDING.value
        self.assigned_to: Optional[str] = None
        self.created_at = datetime.utcnow().isoformat()
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.error: Optional[str] = None
        self.dependencies: List[str] = []  # task IDs this depends on

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "project_id": self.project_id,
            "agent_role": self.agent_role,
            "priority": self.priority,
            "state": self.state,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "dependencies": self.dependencies,
        }

    @staticmethod
    def from_dict(data: Dict) -> "Task":
        task = Task(
            title=data["title"],
            description=data["description"],
            project_id=data["project_id"],
            agent_role=data["agent_role"],
            priority=data.get("priority", TaskPriority.MEDIUM.value),
            task_id=data.get("id"),
        )
        task.state = data.get("state", TaskState.PENDING.value)
        task.assigned_to = data.get("assigned_to")
        task.created_at = data.get("created_at")
        task.started_at = data.get("started_at")
        task.completed_at = data.get("completed_at")
        task.error = data.get("error")
        task.dependencies = data.get("dependencies", [])
        return task


class TaskEngine:
    """
    Central task management system.

    Handles task creation, state transitions, and agent assignment.
    """

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self._load_tasks()

    def create_task(
        self,
        title: str,
        description: str,
        project_id: str,
        agent_role: str,
        priority: int = TaskPriority.MEDIUM.value,
        dependencies: Optional[List[str]] = None,
    ) -> Task:
        """Create a new task."""
        task = Task(
            title=title,
            description=description,
            project_id=project_id,
            agent_role=agent_role,
            priority=priority,
        )
        if dependencies:
            task.dependencies = dependencies
        self.tasks[task.id] = task
        self._save_task(task)
        return task

    def assign_task(self, task_id: str, agent_id: str) -> Optional[Task]:
        """Assign a task to an agent."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        task.assigned_to = agent_id
        task.state = TaskState.ASSIGNED.value
        self._save_task(task)
        return task

    def start_task(self, task_id: str) -> Optional[Task]:
        """Mark a task as in progress."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        task.state = TaskState.IN_PROGRESS.value
        task.started_at = datetime.utcnow().isoformat()
        self._save_task(task)
        return task

    def complete_task(self, task_id: str) -> Optional[Task]:
        """Mark a task as completed."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        task.state = TaskState.DONE.value
        task.completed_at = datetime.utcnow().isoformat()
        self._save_task(task)
        return task

    def fail_task(self, task_id: str, error: str) -> Optional[Task]:
        """Mark a task as failed."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        task.state = TaskState.FAILED.value
        task.error = error
        self._save_task(task)
        return task

    def get_pending_tasks(self, agent_role: Optional[str] = None) -> List[Task]:
        """Get all pending tasks, optionally filtered by role."""
        tasks = [
            t
            for t in self.tasks.values()
            if t.state == TaskState.PENDING.value
            and (agent_role is None or t.agent_role == agent_role)
        ]
        # Sort by priority (descending) then by created_at (ascending)
        return sorted(
            tasks, key=lambda t: (-t.priority, t.created_at)
        )

    def get_assigned_tasks(self, agent_id: str) -> List[Task]:
        """Get all tasks assigned to a specific agent."""
        return [t for t in self.tasks.values() if t.assigned_to == agent_id]

    def has_work(self) -> bool:
        """Check if there are any pending or in-progress tasks."""
        for task in self.tasks.values():
            if task.state in [
                TaskState.PENDING.value,
                TaskState.ASSIGNED.value,
                TaskState.IN_PROGRESS.value,
            ]:
                return True
        return False

    def get_stats(self) -> Dict:
        """Get task statistics."""
        stats = {
            "total": len(self.tasks),
            "pending": 0,
            "assigned": 0,
            "in_progress": 0,
            "review": 0,
            "done": 0,
            "failed": 0,
            "blocked": 0,
        }
        for task in self.tasks.values():
            key = task.state.replace("in_progress", "in_progress")
            if key in stats:
                stats[key] += 1
        return stats

    def _load_tasks(self):
        """Load tasks from persistent storage."""
        if not TASKS_DB.exists():
            return
        try:
            with open(TASKS_DB, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        task = Task.from_dict(data)
                        self.tasks[task.id] = task
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to load tasks: {e}")

    def _save_task(self, task: Task):
        """Persist a task to storage."""
        TASKS_DB.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Append task to JSONL file
            with open(TASKS_DB, "a", encoding="utf-8") as f:
                f.write(json.dumps(task.to_dict()) + "\n")
        except IOError as e:
            print(f"Error: Failed to save task: {e}")


# Global task engine instance
_engine: Optional[TaskEngine] = None


def get_task_engine() -> TaskEngine:
    """Get or create the global task engine."""
    global _engine
    if _engine is None:
        _engine = TaskEngine()
    return _engine
