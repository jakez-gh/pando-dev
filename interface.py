"""
Pando Team Interface - CLI for human interaction with the Pando system.

Allows humans to:
- View agent status and task progress
- Assign new tasks
- Review messages and decisions
- Monitor system health
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from message_bus import get_message_bus
from task_engine import get_task_engine, TaskState
from agent_coordinator import get_coordinator

INTERFACE_HISTORY = Path(__file__).parent / "interface_history.jsonl"


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def print_section(text: str):
    """Print a formatted section."""
    print(f"\n▶ {text}")
    print("-" * 70)


def show_agent_status():
    """Display current agent status."""
    coordinator = get_coordinator()
    print_section("Agent Status")

    if not coordinator.agents:
        print("  No agents registered yet")
        return

    for agent_id, agent in coordinator.agents.items():
        role = agent["role"]
        status = agent["status"]
        completed = agent["tasks_completed"]
        current = agent["current_task"] or "none"

        status_emoji = "🟢" if status == "idle" else "🔴"
        print(f"  {status_emoji} {agent_id} (role: {role})")
        print(f"     Status: {status} | Completed: {completed} tasks | Current: {current}")


def show_task_status():
    """Display task progress."""
    engine = get_task_engine()
    stats = engine.get_stats()

    print_section("Task Progress")
    total = stats["total"]
    done = stats["done"]

    if total == 0:
        print("  No tasks created yet")
        return

    progress = done / total * 100
    bar_length = 30
    filled = int(bar_length * done / total)
    bar = "█" * filled + "░" * (bar_length - filled)

    print(f"  [{bar}] {done}/{total} ({progress:.1f}%)")
    print()
    print(f"  Pending:      {stats['pending']}")
    print(f"  Assigned:     {stats['assigned']}")
    print(f"  In Progress:  {stats['in_progress']}")
    print(f"  Review:       {stats['review']}")
    print(f"  Done:         {stats['done']}")
    print(f"  Failed:       {stats['failed']}")
    print(f"  Blocked:      {stats['blocked']}")


def show_messages(limit: int = 20):
    """Display recent messages."""
    bus = get_message_bus()
    messages = bus.get_history()[-limit:]

    print_section(f"Recent Messages (last {limit})")

    if not messages:
        print("  No messages yet")
        return

    for msg in messages:
        timestamp = msg.timestamp[11:19]  # HH:MM:SS
        msg_type = msg.message_type
        source = msg.source_agent

        # Color-code by type
        emoji = {
            "task_assigned": "📋",
            "task_started": "▶️ ",
            "task_complete": "✓",
            "task_failed": "✗",
            "agent_ready": "🟢",
            "agent_idle": "🟡",
            "system_status": "ℹ",
        }.get(msg_type, "•")

        print(f"  {emoji} [{timestamp}] {msg_type:20s} from {source}")
        if msg.payload:
            for key, val in msg.payload.items():
                if key not in ["task_id", "role"]:
                    print(f"      {key}: {val}")


def show_pending_tasks():
    """Display pending tasks waiting for agents."""
    engine = get_task_engine()
    pending = engine.get_pending_tasks()

    print_section("Pending Tasks")

    if not pending:
        print("  No pending tasks - all work assigned!")
        return

    for i, task in enumerate(pending[:10], 1):
        priority_emoji = "🔴" if task.priority >= 80 else "🟡" if task.priority >= 50 else "🟢"
        print(f"  {i}. {priority_emoji} [{task.agent_role}] {task.title}")
        print(f"     {task.description[:60]}")


def show_system_status():
    """Display overall system status."""
    coordinator = get_coordinator()
    stats = coordinator.get_stats()

    print_header("PANDO SYSTEM STATUS")

    # Work complete status
    if coordinator.work_complete:
        print("  ✓ ALL WORK COMPLETE")
    else:
        print("  ⏳ WORKING...")

    print()
    print(f"  Timestamp: {datetime.utcnow().isoformat()}")
    print()

    show_agent_status()
    show_task_status()
    show_pending_tasks()
    show_messages(limit=10)

    print_section("System Summary")
    print(f"  Total agents:      {stats['agents_registered']}")
    print(f"  Tasks completed:   {stats['total_tasks_completed']}")
    print(f"  Total tasks:       {stats['task_stats']['total']}")
    print(f"  Work complete:     {'Yes ✓' if coordinator.work_complete else 'No ⏳'}")


def add_task_interactive():
    """Interactively create a new task."""
    engine = get_task_engine()

    print_section("Create New Task")

    print("Enter task details (or press Enter to cancel):")

    title = input("  Title: ").strip()
    if not title:
        print("  Cancelled.")
        return

    description = input("  Description: ").strip()
    if not description:
        print("  Cancelled.")
        return

    print("\n  Available roles: planner, designer, implementer, tester, maintainer")
    role = input("  Agent role: ").strip().lower()
    if role not in ["planner", "designer", "implementer", "tester", "maintainer"]:
        print(f"  Invalid role: {role}")
        return

    print("  Priority: 20 (low), 50 (medium), 80 (high), 100 (critical)")
    priority_str = input("  Priority (default 50): ").strip()
    priority = int(priority_str) if priority_str.isdigit() else 50

    task = engine.create_task(
        title=title,
        description=description,
        project_id="pando-dev",
        agent_role=role,
        priority=priority,
    )

    print(f"\n  ✓ Task created: {task.id}")
    print(f"    Title: {task.title}")
    print(f"    Role:  {task.agent_role}")


def view_task_detail(task_id: str):
    """View detailed information about a task."""
    engine = get_task_engine()
    task = engine.tasks.get(task_id)

    if not task:
        print(f"  Task not found: {task_id}")
        return

    print_section(f"Task Detail: {task.title}")
    print(f"  ID:           {task.id}")
    print(f"  Title:        {task.title}")
    print(f"  Description:  {task.description}")
    print(f"  Project:      {task.project_id}")
    print(f"  Role:         {task.agent_role}")
    print(f"  Priority:     {task.priority}")
    print(f"  State:        {task.state}")
    print(f"  Assigned to:  {task.assigned_to or 'unassigned'}")
    print(f"  Created:      {task.created_at}")
    print(f"  Started:      {task.started_at or 'not started'}")
    print(f"  Completed:    {task.completed_at or 'not completed'}")
    if task.error:
        print(f"  Error:        {task.error}")


def main_menu():
    """Interactive menu."""
    while True:
        print_header("PANDO TEAM INTERFACE")

        print("Choose an option:")
        print("  1. System status")
        print("  2. Agent status")
        print("  3. Task progress")
        print("  4. Recent messages")
        print("  5. Add task")
        print("  6. View task detail")
        print("  7. Refresh (monitor mode)")
        print("  0. Exit")
        print()

        choice = input("Enter choice (0-7): ").strip()

        if choice == "1":
            show_system_status()
        elif choice == "2":
            show_agent_status()
        elif choice == "3":
            show_task_status()
        elif choice == "4":
            show_messages()
        elif choice == "5":
            add_task_interactive()
        elif choice == "6":
            task_id = input("Enter task ID: ").strip()
            view_task_detail(task_id)
        elif choice == "7":
            monitor_mode()
        elif choice == "0":
            print("\nGoodbye!")
            break
        else:
            print("Invalid choice")

        input("\nPress Enter to continue...")


def monitor_mode():
    """Continuous monitoring mode."""
    print_header("MONITOR MODE (Press Ctrl+C to exit)")

    try:
        while True:
            coordinator = get_coordinator()

            # Clear screen (simple version for all platforms)
            print("\033[2J\033[H", end="")

            show_system_status()

            if coordinator.work_complete:
                print("\n✓ System detected all work is complete - stopping monitor.")
                break

            time.sleep(2)
    except KeyboardInterrupt:
        print("\n\nMonitor mode exited.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            show_system_status()
        elif sys.argv[1] == "monitor":
            monitor_mode()
        elif sys.argv[1] == "agents":
            show_agent_status()
        elif sys.argv[1] == "tasks":
            show_task_status()
        elif sys.argv[1] == "messages":
            show_messages()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python interface.py [status|monitor|agents|tasks|messages]")
    else:
        main_menu()
