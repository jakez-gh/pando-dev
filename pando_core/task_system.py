"""
Pando Task Management System

Pando manages its own work queue with intelligent self-assignment.
Prioritizes tasks, estimates effort, and distributes work across terminals.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class TaskCategory(Enum):
    """Types of work Pando can do"""
    PRIMARY = "PRIMARY"              # User-requested feature/fix/enhancement
    INVESTIGATION = "INVESTIGATION"  # Research/analysis
    SECONDARY = "SECONDARY"          # Self-generated improvements
    MAINTENANCE = "MAINTENANCE"      # Repo health, cleanup
    OPTIMIZATION = "OPTIMIZATION"    # Performance/quality improvements
    TESTING = "TESTING"              # Test coverage gaps
    DOCUMENTATION = "DOCUMENTATION"  # User/code documentation


class TaskStatus(Enum):
    """Lifecycle states for tasks"""
    PENDING = "PENDING"        # Waiting to be assigned
    ASSIGNED = "ASSIGNED"      # Assigned to terminal
    IN_PROGRESS = "IN_PROGRESS"  # Currently executing
    BLOCKED = "BLOCKED"        # Waiting for info/decision
    PAUSED = "PAUSED"          # Intentionally paused
    REVIEW = "REVIEW"          # Awaiting review (PR stage)
    COMPLETED = "COMPLETED"    # Successfully finished
    FAILED = "FAILED"          # Execution failed
    CANCELLED = "CANCELLED"    # Explicitly cancelled


@dataclass
class Task:
    """Represents a unit of work"""
    id: str
    category: TaskCategory
    description: str
    status: TaskStatus
    priority: float  # 0.0-1.0
    estimated_minutes: float
    actual_minutes: Optional[float] = None
    assigned_terminal: Optional[int] = None
    assigned_to: str = "pando"
    branch_name: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    blocking_questions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    success: Optional[bool] = None
    notes: Optional[str] = None
    repository: str = "pando-dev"  # Which repo this applies to
    
    def mark_started(self, terminal: int):
        """Mark task as started on terminal"""
        self.status = TaskStatus.IN_PROGRESS
        self.assigned_terminal = terminal
        self.started_at = datetime.now().isoformat()
    
    def mark_completed(self, success: bool, notes: str = ""):
        """Mark task as completed"""
        status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        self.status = status
        self.success = success
        self.completed_at = datetime.now().isoformat()
        self.notes = notes
        
        if self.started_at:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
            self.actual_minutes = (end - start).total_seconds() / 60
    
    def mark_blocked(self, question_id: str):
        """Mark task as blocked waiting for response"""
        self.status = TaskStatus.BLOCKED
        self.blocking_questions.append(question_id)
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict"""
        return {
            **asdict(self),
            'category': self.category.value,
            'status': self.status.value,
        }


class TaskSystem:
    """
    Pando's task management system.
    
    Responsibilities:
    - Accept user-requested tasks
    - Self-generate secondary tasks
    - Prioritize and estimate effort
    - Assign to terminals
    - Track completion
    """
    
    def __init__(self, state_file: str = "pando_tasks.jsonl"):
        self.state_file = state_file
        self.tasks: Dict[str, Task] = {}
        self.terminal_assignments: Dict[int, Optional[str]] = {
            i: None for i in range(1, 9)  # 8 terminals
        }
        self.load_state()
    
    def load_state(self):
        """Load task state from file"""
        try:
            with open(self.state_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        task = Task(
                            id=data['id'],
                            category=TaskCategory(data['category']),
                            description=data['description'],
                            status=TaskStatus(data['status']),
                            priority=data['priority'],
                            estimated_minutes=data['estimated_minutes'],
                            **{k: v for k, v in data.items()
                               if k not in ['id', 'category', 'description', 'status',
                                           'priority', 'estimated_minutes', 'category']}
                        )
                        self.tasks[task.id] = task
        except FileNotFoundError:
            logger.info(f"No task state file found: {self.state_file}")
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted task state: {e}")

    def save_state(self):
        """Save task state to file (append-only)"""
        try:
            # Append only new/changed tasks
            # This is a simplified version; production would track changes
            with open(self.state_file, 'w') as f:
                for task in self.tasks.values():
                    f.write(json.dumps(task.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to save task state: {e}")

    def create_task(
        self,
        description: str,
        category: TaskCategory,
        estimated_minutes: float,
        priority: float = 0.5,
        depends_on: Optional[List[str]] = None,
        repository: str = "pando-dev"
    ) -> Task:
        """
        Create a new task.
        
        Args:
            description: What needs to be done
            category: Type of work
            estimated_minutes: How long it should take
            priority: 0.0-1.0 (higher = more urgent)
            depends_on: Task IDs this depends on
            repository: Which repo this applies to
        
        Returns:
            Created Task object
        """
        task_id = f"t_{uuid.uuid4().hex[:8]}"
        task = Task(
            id=task_id,
            category=category,
            description=description,
            status=TaskStatus.PENDING,
            priority=priority,
            estimated_minutes=estimated_minutes,
            depends_on=depends_on or [],
            repository=repository,
        )
        
        self.tasks[task_id] = task
        logger.info(f"Created task {task_id}: {description}")
        self.save_state()
        return task

    def get_next_task(self) -> Optional[Task]:
        """
        Get the highest-priority available task.
        
        Returns:
            Next task to work on, or None if no tasks
        """
        # Filter available tasks
        available = [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING
            and all(self.tasks.get(dep_id, Task(
                id=dep_id, category=TaskCategory.PRIMARY, description="",
                status=TaskStatus.COMPLETED, priority=0, estimated_minutes=0
            )).status == TaskStatus.COMPLETED for dep_id in task.depends_on)
        ]
        
        if not available:
            return None
        
        # Sort by priority (higher first)
        available.sort(key=lambda t: t.priority, reverse=True)
        return available[0]

    def get_all_available_tasks(self) -> List[Task]:
        """Get all tasks that could be worked on"""
        return [
            task for task in self.tasks.values()
            if task.status in [TaskStatus.PENDING, TaskStatus.BLOCKED]
        ]

    def calculate_priority(
        self,
        task: Task,
        urgency: float = 0.5,  # 0.0-1.0
        impact: float = 0.5,   # 0.0-1.0
    ) -> float:
        """
        Calculate effective priority for a task.
        
        Formula:
        priority = (urgency * 0.4) + (impact * 0.3) + (effort_ratio * 0.2) + (blocker_count * 0.1)
        
        Then adjust by category multiplier.
        """
        
        # Calculate effort ratio (value per unit time)
        effort_ratio = impact / max(task.estimated_minutes, 1.0)
        effort_ratio = min(1.0, effort_ratio)
        
        # Count how many tasks depend on this one
        blocker_count = sum(
            1 for t in self.tasks.values()
            if task.id in t.depends_on
        ) / len(self.tasks) if self.tasks else 0
        
        # Base priority
        base_priority = (
            (urgency * 0.4) +
            (impact * 0.3) +
            (effort_ratio * 0.2) +
            (blocker_count * 0.1)
        )
        
        # Apply category multiplier
        category_multipliers = {
            TaskCategory.PRIMARY: 1.0,
            TaskCategory.INVESTIGATION: 0.8,
            TaskCategory.SECONDARY: 0.6,
            TaskCategory.OPTIMIZATION: 0.5,
            TaskCategory.TESTING: 0.5,
            TaskCategory.DOCUMENTATION: 0.4,
            TaskCategory.MAINTENANCE: 0.2,
        }
        
        multiplier = category_multipliers.get(task.category, 0.5)
        return base_priority * multiplier

    def assign_task_to_terminal(self, task_id: str, terminal: int) -> bool:
        """
        Assign a task to a terminal for execution.
        
        Returns:
            True if successful, False if task not found or already assigned
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return False
        
        if task.status != TaskStatus.PENDING:
            logger.error(f"Task {task_id} is not pending (status: {task.status.value})")
            return False
        
        # Check if terminal is free
        if self.terminal_assignments[terminal] is not None:
            logger.error(f"Terminal {terminal} is already assigned")
            return False
        
        task.mark_started(terminal)
        self.terminal_assignments[terminal] = task_id
        self.save_state()
        logger.info(f"Assigned task {task_id} to terminal {terminal}")
        return True

    def complete_task(
        self,
        task_id: str,
        success: bool,
        notes: str = "",
        branch: Optional[str] = None
    ) -> bool:
        """
        Mark a task as completed or failed.
        
        Returns:
            True if successful, False if task not found
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task not found: {task_id}")
            return False
        
        if task.assigned_terminal:
            self.terminal_assignments[task.assigned_terminal] = None
        
        task.mark_completed(success, notes)
        if branch:
            task.branch_name = branch
        
        self.save_state()
        logger.info(f"Task {task_id} completed: success={success}")
        return True

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get current status of a task"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            'id': task.id,
            'description': task.description,
            'status': task.status.value,
            'progress': self._estimate_progress(task),
            'assigned_terminal': task.assigned_terminal,
            'estimated_remaining_minutes': (
                task.estimated_minutes - (task.actual_minutes or 0)
                if task.status == TaskStatus.IN_PROGRESS else task.estimated_minutes
            ),
            'blocking_questions': task.blocking_questions,
        }

    def _estimate_progress(self, task: Task) -> float:
        """
        Estimate progress through a task (0.0-1.0)
        
        Based on elapsed time vs estimated time
        """
        if task.status == TaskStatus.PENDING:
            return 0.0
        elif task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            return 1.0
        elif task.status == TaskStatus.IN_PROGRESS and task.started_at:
            start = datetime.fromisoformat(task.started_at)
            elapsed = (datetime.now() - start).total_seconds() / 60
            progress = elapsed / max(task.estimated_minutes, 1.0)
            return min(0.95, progress)  # Cap at 95% until actually done
        elif task.status == TaskStatus.BLOCKED:
            return 0.5  # Assume 50% when blocked
        
        return 0.0

    def get_statistics(self) -> Dict:
        """Get overall task statistics"""
        completed = [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
        failed = [t for t in self.tasks.values() if t.status == TaskStatus.FAILED]
        pending = [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
        in_progress = [t for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS]
        
        actual_times = [t.actual_minutes for t in completed if t.actual_minutes]
        avg_actual = sum(actual_times) / len(actual_times) if actual_times else 0
        
        success_rate = (
            len(completed) / (len(completed) + len(failed))
            if (len(completed) + len(failed)) > 0 else 0.0
        )
        
        return {
            'total_tasks': len(self.tasks),
            'completed': len(completed),
            'failed': len(failed),
            'pending': len(pending),
            'in_progress': len(in_progress),
            'success_rate': success_rate,
            'avg_actual_time_minutes': avg_actual,
            'tasks_by_category': {
                cat.value: len([t for t in self.tasks.values() if t.category == cat])
                for cat in TaskCategory
            },
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    system = TaskSystem()
    
    # Create some tasks
    t1 = system.create_task(
        "Implement JWT authentication",
        TaskCategory.PRIMARY,
        estimated_minutes=120,
        priority=0.95,
        repository="pando-dev"
    )
    
    t2 = system.create_task(
        "Add rate limiting to API",
        TaskCategory.PRIMARY,
        estimated_minutes=90,
        priority=0.85,
        depends_on=[t1.id],
    )
    
    t3 = system.create_task(
        "Write integration tests",
        TaskCategory.TESTING,
        estimated_minutes=120,
        priority=0.75,
        depends_on=[t1.id, t2.id],
    )
    
    # Get next task
    next_task = system.get_next_task()
    print(f"\nNext task: {next_task.description if next_task else 'None'}")
    
    # Assign it
    if next_task:
        system.assign_task_to_terminal(next_task.id, 1)
        print(f"Assigned to terminal 1")
    
    # Get stats
    stats = system.get_statistics()
    print(f"\nStatistics: {stats}")
