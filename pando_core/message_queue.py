"""
Bidirectional Communication System

Allows Copilot and Pando to communicate without blocking each other.
Uses a message queue that both can read/write asynchronously.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import threading

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages between Copilot and Pando"""
    DIRECTION = "direction"           # Copilot → Pando: Task to do
    STATUS = "status"                  # Pando → Copilot: Status update
    QUESTION = "question"              # Pando → Copilot: Needs input
    ANSWER = "answer"                  # Copilot → Pando: Response to question
    ALERT = "alert"                    # Pando → Copilot: Important alert
    METRIC = "metric"                  # Pando → Copilot: Metrics/stats
    CONTROL = "control"                # Copilot → Pando: System control (pause, resume, etc)


@dataclass
class Message:
    """A bidirectional message"""
    message_id: str
    type: str  # MessageType enum value
    sender: str  # "copilot" or "pando"
    recipient: str  # "copilot" or "pando"
    content: Dict
    timestamp: str
    read: bool = False
    
    def to_dict(self):
        return asdict(self)


class MessageQueue:
    """Bidirectional message queue between Copilot and Pando"""
    
    def __init__(self, queue_file: str = "pando_messages.jsonl"):
        self.queue_file = Path(queue_file)
        self.lock = threading.Lock()
        self.queue_file.parent.mkdir(exist_ok=True)
    
    def send(
        self,
        message_type: str,
        sender: str,
        recipient: str,
        content: Dict
    ) -> str:
        """
        Send a message (non-blocking)
        
        Args:
            message_type: One of MessageType values
            sender: "copilot" or "pando"
            recipient: "copilot" or "pando"
            content: Message content dict
            
        Returns:
            message_id
        """
        message_id = f"MSG_{uuid.uuid4().hex[:12]}"
        
        message = Message(
            message_id=message_id,
            type=message_type,
            sender=sender,
            recipient=recipient,
            content=content,
            timestamp=datetime.now().isoformat(),
            read=False
        )
        
        # Append to queue (append-only for crash safety)
        with self.lock:
            with open(self.queue_file, 'a') as f:
                f.write(json.dumps(message.to_dict()) + "\n")
        
        logger.info(f"Message sent: {sender} → {recipient}: {message_type}")
        return message_id
    
    def get_unread(self, recipient: str) -> List[Message]:
        """Get unread messages for recipient (non-blocking)"""
        messages = []
        
        with self.lock:
            if not self.queue_file.exists():
                return messages
            
            with open(self.queue_file) as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    data = json.loads(line)
                    msg = Message(**data)
                    
                    # Return unread messages for this recipient
                    if msg.recipient == recipient and not msg.read:
                        messages.append(msg)
        
        return messages
    
    def mark_read(self, message_id: str):
        """Mark a message as read"""
        # Read all messages
        all_messages = []
        
        with self.lock:
            if self.queue_file.exists():
                with open(self.queue_file) as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            msg = Message(**data)
                            if msg.message_id == message_id:
                                msg.read = True
                            all_messages.append(msg)
            
            # Rewrite entire file with updated read status
            with open(self.queue_file, 'w') as f:
                for msg in all_messages:
                    f.write(json.dumps(msg.to_dict()) + "\n")
    
    def get_recent(self, sender: Optional[str] = None, count: int = 20) -> List[Message]:
        """Get recent messages, optionally filtered by sender"""
        messages = []
        
        with self.lock:
            if not self.queue_file.exists():
                return messages
            
            with open(self.queue_file) as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    data = json.loads(line)
                    msg = Message(**data)
                    
                    if sender is None or msg.sender == sender:
                        messages.append(msg)
        
        # Return last N
        return messages[-count:]
    
    def cleanup_old(self, days: int = 7):
        """Remove messages older than N days"""
        cutoff = datetime.now() - timedelta(days=days)
        
        messages = []
        
        with self.lock:
            if not self.queue_file.exists():
                return
            
            with open(self.queue_file) as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    data = json.loads(line)
                    msg = Message(**data)
                    msg_time = datetime.fromisoformat(msg.timestamp)
                    
                    # Keep if newer than cutoff
                    if msg_time > cutoff:
                        messages.append(msg)
            
            # Rewrite file
            with open(self.queue_file, 'w') as f:
                for msg in messages:
                    f.write(json.dumps(msg.to_dict()) + "\n")
        
        logger.info(f"Cleaned up messages older than {days} days")


# Singleton instance
_message_queue_instance = None


def get_message_queue() -> MessageQueue:
    """Get or create singleton message queue"""
    global _message_queue_instance
    if _message_queue_instance is None:
        _message_queue_instance = MessageQueue()
    return _message_queue_instance


# Convenience functions for common operations

def copilot_send_direction(text: str, priority: str = "medium") -> str:
    """Copilot sends a direction to Pando"""
    queue = get_message_queue()
    return queue.send(
        message_type=MessageType.DIRECTION.value,
        sender="copilot",
        recipient="pando",
        content={"text": text, "priority": priority}
    )


def pando_send_status(status_info: Dict) -> str:
    """Pando sends status to Copilot"""
    queue = get_message_queue()
    return queue.send(
        message_type=MessageType.STATUS.value,
        sender="pando",
        recipient="copilot",
        content=status_info
    )


def pando_check_for_directions() -> List[Message]:
    """Pando checks for new directions (non-blocking)"""
    queue = get_message_queue()
    return queue.get_unread("pando")


def copilot_check_for_updates() -> List[Message]:
    """Copilot checks for updates from Pando (non-blocking)"""
    queue = get_message_queue()
    return queue.get_unread("copilot")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    queue = get_message_queue()
    
    # Copilot sends a direction
    msg_id = copilot_send_direction("Review the code quality", "high")
    print(f"Direction sent: {msg_id}")
    
    # Pando checks for directions
    directions = pando_check_for_directions()
    print(f"Pando found {len(directions)} directions")
    
    for direction in directions:
        print(f"  - {direction.content}")
        queue.mark_read(direction.message_id)
    
    # Pando sends status
    status_msg_id = pando_send_status({
        "agents_active": 3,
        "tasks_completed": 5,
        "health": "good"
    })
    print(f"Status sent: {status_msg_id}")
    
    # Copilot checks for updates
    updates = copilot_check_for_updates()
    print(f"Copilot found {len(updates)} updates")
