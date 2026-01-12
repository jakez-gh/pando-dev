"""
Direction/Inbox Management System

Converts high-level user directions into structured tasks.
Replaces the text file inbox with proper API and persistence.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class Direction:
    """User direction - high-level request"""
    direction_id: str
    text: str
    priority: str  # critical, high, medium, low
    deadline: Optional[str]
    context: Optional[str]
    created_at: str
    status: str  # parsed, in_progress, completed, cancelled
    tasks_created: int = 0
    tasks_completed: int = 0
    
    def to_dict(self):
        return asdict(self)


class DirectionAPI:
    """Manages directions and conversion to tasks"""
    
    def __init__(self, directions_file: str = "pando_directions.jsonl"):
        self.directions_file = Path(directions_file)
        self.directions_file.parent.mkdir(exist_ok=True)
        self._load_existing()
    
    def _load_existing(self):
        """Load existing directions from JSONL"""
        self.directions = {}
        if self.directions_file.exists():
            with open(self.directions_file) as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        direction = Direction(**data)
                        self.directions[direction.direction_id] = direction
    
    def submit_direction(
        self,
        text: str,
        priority: str = "medium",
        deadline: Optional[str] = None,
        context: Optional[str] = None
    ) -> dict:
        """
        Submit a new direction.
        
        Args:
            text: The direction text (e.g., "Review auth module for security issues")
            priority: critical, high, medium, low
            deadline: Optional deadline date (ISO format)
            context: Optional additional context
            
        Returns:
            Direction object with ID and status
        """
        direction_id = f"DIR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        direction = Direction(
            direction_id=direction_id,
            text=text,
            priority=priority,
            deadline=deadline,
            context=context,
            created_at=datetime.now().isoformat(),
            status="parsed",
            tasks_created=0,
            tasks_completed=0
        )
        
        # Persist
        self.directions[direction_id] = direction
        self._persist_direction(direction)
        
        logger.info(f"Direction submitted: {direction_id}")
        
        return {
            "direction_id": direction_id,
            "text": text,
            "priority": priority,
            "status": "parsed",
            "created_at": direction.created_at
        }
    
    def _persist_direction(self, direction: Direction):
        """Append direction to JSONL"""
        with open(self.directions_file, "a") as f:
            f.write(json.dumps(direction.to_dict()) + "\n")
    
    def get_directions(
        self,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> list[dict]:
        """Get all directions, optionally filtered"""
        results = []
        for direction in self.directions.values():
            if status and direction.status != status:
                continue
            if priority and direction.priority != priority:
                continue
            results.append(direction.to_dict())
        
        # Sort by created_at descending
        results.sort(key=lambda x: x["created_at"], reverse=True)
        return results
    
    def get_direction(self, direction_id: str) -> Optional[dict]:
        """Get a specific direction"""
        if direction_id in self.directions:
            return self.directions[direction_id].to_dict()
        return None
    
    def update_direction_status(
        self,
        direction_id: str,
        status: str,
        tasks_completed: Optional[int] = None
    ):
        """Update direction status"""
        if direction_id not in self.directions:
            return False
        
        direction = self.directions[direction_id]
        direction.status = status
        
        if tasks_completed is not None:
            direction.tasks_completed = tasks_completed
        
        self._persist_direction(direction)
        logger.info(f"Direction {direction_id} status updated to {status}")
        return True
    
    def parse_direction_into_tasks(self, text: str) -> list[dict]:
        """
        Parse a direction text into concrete tasks.
        
        This uses simple heuristics. In production, could use LLM.
        
        Example:
            "Review auth module and add 2FA support"
            →
            [
                {"title": "Review auth module", "priority": "high"},
                {"title": "Design 2FA system", "priority": "high"},
                {"title": "Implement 2FA", "priority": "high"},
                {"title": "Add 2FA tests", "priority": "medium"},
            ]
        """
        tasks = []
        
        # Simple parsing: split on "and", "then", "also"
        parts = [p.strip() for p in text.split(" and ")]
        
        keywords = {
            "review": "review",
            "refactor": "refactor",
            "optimize": "optimize",
            "add": "feature",
            "implement": "feature",
            "fix": "bugfix",
            "test": "test",
            "document": "documentation",
            "debug": "debugging"
        }
        
        for i, part in enumerate(parts):
            # Detect task type
            category = "general"
            for keyword, cat in keywords.items():
                if keyword in part.lower():
                    category = cat
                    break
            
            # Priority: first task high, others medium
            priority = "high" if i == 0 else "medium"
            
            # Estimate effort
            effort_map = {
                "review": 45,
                "refactor": 120,
                "optimize": 90,
                "feature": 180,
                "bugfix": 60,
                "test": 90,
                "documentation": 45,
                "debugging": 120,
                "general": 60
            }
            estimated_minutes = effort_map.get(category, 60)
            
            task = {
                "title": part,
                "category": category,
                "priority": priority,
                "estimated_minutes": estimated_minutes,
                "status": "pending"
            }
            tasks.append(task)
        
        logger.info(f"Parsed direction into {len(tasks)} tasks")
        return tasks
    
    def get_stats(self) -> dict:
        """Get statistics about directions"""
        total = len(self.directions)
        by_status = {}
        by_priority = {}
        
        for direction in self.directions.values():
            by_status[direction.status] = by_status.get(direction.status, 0) + 1
            by_priority[direction.priority] = by_priority.get(direction.priority, 0) + 1
        
        total_tasks = sum(d.tasks_created for d in self.directions.values())
        completed_tasks = sum(d.tasks_completed for d in self.directions.values())
        
        return {
            "total_directions": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "total_tasks_created": total_tasks,
            "total_tasks_completed": completed_tasks
        }


# Singleton instance
_direction_api_instance = None


def get_direction_api() -> DirectionAPI:
    """Get or create the singleton DirectionAPI instance"""
    global _direction_api_instance
    if _direction_api_instance is None:
        _direction_api_instance = DirectionAPI()
    return _direction_api_instance


if __name__ == "__main__":
    # Example usage
    api = get_direction_api()
    
    # Submit a direction
    result = api.submit_direction(
        text="Review the authentication module for security issues and add 2FA support",
        priority="high",
        context="Security audit requested"
    )
    print(f"Direction submitted: {result['direction_id']}")
    
    # Parse into tasks
    tasks = api.parse_direction_into_tasks(result['text'])
    print(f"\nParsed tasks ({len(tasks)}):")
    for task in tasks:
        print(f"  - {task['title']} ({task['priority']}, ~{task['estimated_minutes']}min)")
    
    # Get stats
    stats = api.get_stats()
    print(f"\nStats: {stats}")
