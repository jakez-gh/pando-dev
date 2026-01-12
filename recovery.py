import os
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

from typing import Any, Callable

from logger import log
import task_queue


def run_with_recovery(
    project_id: str,
    goal: str,
    role: str,
    runner: Callable[[str, str, str, str], dict[str, Any]],
    model: str,
) -> dict[str, Any]:
    """
    Run a single task with self-recovery.
    If an exception occurs, enqueue a recovery task and return an error result.
    """
    try:
        return runner(model, project_id, goal, role)
    except Exception as e:
        err = str(e)
        log(f"ERROR while running task for {project_id} [{role}]: {err}")
        task_queue.add_recovery_task(project_id, err)
        return {
            "error": err,
            "project_id": project_id,
            "goal": goal,
            "role": role,
        }
