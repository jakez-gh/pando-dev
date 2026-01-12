import os
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

import json
from pathlib import Path
from typing import Any

import tools
from config import BASE_DIR
from logger import log

TASKS_DIR = Path("tasks")
BACKLOG_FILE = TASKS_DIR / "backlog.json"


def _ensure_tasks_dir() -> None:
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    if not BACKLOG_FILE.exists():
        BACKLOG_FILE.write_text("[]", encoding="utf-8")


def _load_backlog() -> list[dict[str, Any]]:
    _ensure_tasks_dir()
    try:
        return json.loads(BACKLOG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_backlog(tasks: list[dict[str, Any]]) -> None:
    _ensure_tasks_dir()
    BACKLOG_FILE.write_text(json.dumps(tasks, indent=2), encoding="utf-8")


def add_task(
    project_id: str,
    goal: str,
    priority: int = 100,
    kind: str = "improvement",
    role: str = "general",
) -> None:
    tasks = _load_backlog()
    tasks.append(
        {
            "project_id": project_id,
            "goal": goal,
            "priority": priority,
            "kind": kind,
            "role": role,
            "status": "pending",
        }
    )
    _save_backlog(tasks)
    log(f"Added task: [{role}] {project_id} :: {goal[:80]}...")


def add_recovery_task(project_id: str, error: str) -> None:
    goal = f"Recover from error in project {project_id}: {error[:400]}"
    add_task(project_id, goal, priority=10, kind="recovery", role="maintainer")


def get_next_task() -> dict[str, Any] | None:
    tasks = _load_backlog()
    pending = [t for t in tasks if t.get("status") == "pending"]
    if not pending:
        return None

    pending.sort(key=lambda t: t.get("priority", 100))
    task = pending[0]
    task["status"] = "in_progress"
    _save_backlog(tasks)
    return task


def complete_task(task: dict[str, Any]) -> None:
    tasks = _load_backlog()
    for t in tasks:
        if (
            t.get("project_id") == task.get("project_id")
            and t.get("goal") == task.get("goal")
            and t.get("status") == "in_progress"
        ):
            t["status"] = "done"
            break
    _save_backlog(tasks)


def ensure_default_tasks() -> None:
    """
    If there are no pending tasks, auto-populate a small set of
    role-specific tasks for each repo under BASE_DIR.
    """
    tasks = _load_backlog()
    has_pending = any(t.get("status") == "pending" for t in tasks)
    if has_pending:
        return

    repos = tools.list_repos()
    if not repos:
        return

    log("No pending tasks. Seeding default multi-role tasks.")
    for repo in repos:
        # Planner: decide what to work on
        add_task(
            project_id=repo,
            goal=f"Plan next most valuable improvements for repository {repo}.",
            priority=40,
            kind="auto",
            role="planner",
        )
        # Designer: think about architecture / design
        add_task(
            project_id=repo,
            goal=f"Design code and architecture changes to make {repo} easier to maintain.",
            priority=50,
            kind="auto",
            role="designer",
        )
        # Implementer: actually change code
        add_task(
            project_id=repo,
            goal=f"Implement small, safe improvements in {repo} based on recent plans and reviews.",
            priority=60,
            kind="auto",
            role="implementer",
        )
        # Tester: tests / checks
        add_task(
            project_id=repo,
            goal=f"Add or improve tests and basic checks for {repo}.",
            priority=70,
            kind="auto",
            role="tester",
        )
        # Maintainer: refactors, cleanup, docs
        add_task(
            project_id=repo,
            goal=f"Refactor, clean up, and document {repo} to make it easier for the AI to maintain.",
            priority=80,
            kind="auto",
            role="maintainer",
        )
