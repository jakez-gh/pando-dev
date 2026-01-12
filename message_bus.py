"""
Message Bus for Inter-Agent Communication

Implements a simple event-based pub/sub system for agents to coordinate work.
Supports role-based agents and task handoff via structured messages.
"""

import json
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from config import BASE_DIR


class Message:
    """Structured message between agents."""

    def __init__(
        self,
        message_type: str,
        source_agent: str,
        target_agent: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        self.id = str(uuid.uuid4())
        self.message_type = message_type
        self.source_agent = source_agent
        self.target_agent = target_agent  # None = broadcast
        self.payload = payload or {}
        self.request_id = request_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "message_type": self.message_type,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "payload": self.payload,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Message":
        msg = Message(
            message_type=data["message_type"],
            source_agent=data["source_agent"],
            target_agent=data.get("target_agent"),
            payload=data.get("payload", {}),
            request_id=data.get("request_id"),
        )
        msg.id = data["id"]
        msg.timestamp = data["timestamp"]
        return msg


class MessageBus:
    """
    Central message bus for agent coordination.

    Agents subscribe to message types and get notified when relevant messages arrive.
    Supports both synchronous and asynchronous message handling.
    """

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or (BASE_DIR / "message_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._subscribers: Dict[str, List[Callable]] = {}  # type -> handlers
        self._lock = threading.RLock()
        self._message_history: List[Message] = []
        self._running = True

    def subscribe(self, message_type: str, handler: Callable[[Message], None]):
        """
        Subscribe to a message type.

        Args:
            message_type: Type of message to listen for (e.g., "task_assigned", "task_complete")
            handler: Callback function (msg: Message) -> None
        """
        with self._lock:
            if message_type not in self._subscribers:
                self._subscribers[message_type] = []
            self._subscribers[message_type].append(handler)

    def publish(self, message: Message):
        """
        Publish a message to the bus.

        Broadcasts to all subscribers of the message type.
        Logs message to history.
        """
        with self._lock:
            self._message_history.append(message)
            self._log_message(message)

        # Call subscribers synchronously
        handlers = self._subscribers.get(message.message_type, [])
        for handler in handlers:
            try:
                handler(message)
            except Exception as e:
                print(f"Error in message handler: {e}")

        # Broadcast to all subscribers if target not specified
        if message.target_agent is None:
            broadcast_handlers = self._subscribers.get("*", [])
            for handler in broadcast_handlers:
                try:
                    handler(message)
                except Exception as e:
                    print(f"Error in broadcast handler: {e}")

    def get_history(
        self, message_type: Optional[str] = None, source_agent: Optional[str] = None
    ) -> List[Message]:
        """Retrieve message history, optionally filtered."""
        with self._lock:
            history = self._message_history
            if message_type:
                history = [m for m in history if m.message_type == message_type]
            if source_agent:
                history = [m for m in history if m.source_agent == source_agent]
            return history

    def get_message(self, message_id: str) -> Optional[Message]:
        """Retrieve a specific message by ID."""
        with self._lock:
            for msg in self._message_history:
                if msg.id == message_id:
                    return msg
            return None

    def _log_message(self, message: Message):
        """Persist message to log file."""
        try:
            log_file = self.log_dir / f"messages-{datetime.utcnow().date()}.jsonl"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(message.to_dict()) + "\n")
        except IOError as e:
            print(f"Warning: Failed to log message: {e}")

    def shutdown(self):
        """Stop the message bus."""
        self._running = False


# Global message bus instance
_bus: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    """Get or create the global message bus."""
    global _bus
    if _bus is None:
        _bus = MessageBus()
    return _bus


# Common message types (can be extended)
MESSAGE_TYPES = {
    "task_assigned": "Agent has been assigned a task",
    "task_started": "Agent is starting work on a task",
    "task_complete": "Agent has completed a task",
    "task_failed": "Agent encountered an error on a task",
    "tool_called": "Agent called a tool",
    "file_modified": "A file was modified (trigger reindex)",
    "reindex_started": "Code indexing started",
    "reindex_complete": "Code indexing finished",
    "agent_ready": "Agent is ready and waiting for work",
    "agent_idle": "Agent has no more work",
    "system_status": "System status update",
}
