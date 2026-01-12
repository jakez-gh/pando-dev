import os
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

from pathlib import Path

from logger import log
import task_queue

DIRECTION_DIR = Path("direction")
INBOX_FILE = DIRECTION_DIR / "inbox.txt"


def _ensure_direction_dir() -> None:
    DIRECTION_DIR.mkdir(parents=True, exist_ok=True)


def check_inbox(default_project: str = "pando-dev") -> None:
    """
    Check for new direction in direction/inbox.txt.

    Format (flexible, keys optional):

    PROJECT: some-repo
    ROLE: implementer
    PRIORITY: 20
    GOAL: Improve error handling in tools.py

    If PROJECT is omitted, default_project is used.
    If ROLE is omitted, 'general' is used.
    If PRIORITY is omitted, 50 is used.
    If file contains only text, treat entire file as GOAL.
    """
    _ensure_direction_dir()
    if not INBOX_FILE.exists():
        return

    content = INBOX_FILE.read_text(encoding="utf-8", errors="ignore").strip()
    if not content:
        return

    # Clear the inbox early, so we don't re-process
    INBOX_FILE.write_text("", encoding="utf-8")

    log(f"New direction received:\n{content}")

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    data: dict[str, str] = {}

    for line in lines:
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip().upper()] = val.strip()

    if not data:
        # Treat whole content as GOAL
        goal = content
        project = default_project
        role = "general"
        priority = 50
    else:
        goal = data.get("GOAL", content)
        project = data.get("PROJECT", default_project)
        role = data.get("ROLE", "general").lower()
        try:
            priority = int(data.get("PRIORITY", "50"))
        except ValueError:
            priority = 50

    task_queue.add_task(project_id=project, goal=goal, priority=priority, role=role, kind="human")
    log(f"Direction converted to task for project {project}, role {role}, priority {priority}.")
