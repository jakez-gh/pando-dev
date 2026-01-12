#!/usr/bin/env python3
"""Enqueue a GUI development task to Pando agents."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pando_core.message_queue import get_message_queue
from task_engine import get_task_engine, TaskPriority

# Get task engine and message queue
mq = get_message_queue()
task_engine = get_task_engine()

# Create GUI development task
gui_task = task_engine.create_task(
    title="Build React GUI Dashboard",
    description="""Create a React-based GUI dashboard for Pando with:
- Real-time task status display (pending, running, completed)
- Agent status monitoring (active agents, roles, current tasks)
- System metrics (uptime, tasks completed, GPU usage)
- Message queue browser (see Copilot ↔ Pando messages)
- Simple CSS styling (no external UI frameworks, keep it minimal)
- Connect to Flask API at http://localhost:5000

Stack:
- React with hooks
- Fetch API for backend communication
- WebSocket (via Flask-SocketIO) for real-time updates
- Minimal CSS (no Bootstrap, Tailwind, etc.)

Start with:
1. Create /pando_gui/frontend/ directory structure
2. Init React app (or use simple HTML/JS if preferred)
3. Create main dashboard component
4. Add components for each section
5. Wire up Flask API endpoints
6. Deploy to http://localhost:3000

Return a working dashboard URL once complete.""",
    project_id="pando-dev",
    agent_role="designer",
    priority=TaskPriority.HIGH.value
)

# Send notification to message queue
mq.send(
    'direction',
    'copilot',
    'pando',
    {
        'task_id': gui_task.id,
        'type': 'gui_development',
        'title': 'Build React GUI Dashboard',
        'description': 'Create a real-time Pando dashboard with task/agent monitoring'
    }
)

print(f"✅ GUI task enqueued: {gui_task.id}")
print(f"   Title: {gui_task.title}")
print(f"   Role: {gui_task.agent_role}")
print(f"   Priority: HIGH")
