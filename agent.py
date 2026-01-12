import os
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

import json
import time
from pathlib import Path

import agent_core
import task_queue
import recovery
import direction
from logger import log

RUNS_DIR = Path("runs")


def save_run_result(result: dict) -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    project_id = result.get("project_id", "unknown")
    role = result.get("role", "unknown")
    fname = RUNS_DIR / f"run-{project_id}-{role}-{ts}.json"
    fname.write_text(json.dumps(result, indent=2), encoding="utf-8")


def main_loop(model: str = "phi3:mini") -> None:
    idle_cycles = 0
    while True:
        # 1) Check for human direction
        direction.check_inbox()

        # 2) Ensure we have some work
        task_queue.ensure_default_tasks()

        # 3) Get next task
        task = task_queue.get_next_task()

        if not task:
            idle_cycles += 1
            if idle_cycles % 3 == 1:
                log("No tasks in backlog. Sleeping for 30s...")
            time.sleep(30)
            continue

        idle_cycles = 0

        project_id = task["project_id"]
        goal = task["goal"]
        role = task.get("role", "general")

        log("=== RUNNING TASK ===")
        log(f"Project: {project_id}")
        log(f"Role   : {role}")
        log(f"Goal   : {goal}")

        result = recovery.run_with_recovery(
            project_id=project_id,
            goal=goal,
            role=role,
            runner=agent_core.run_task,
            model=model,
        )

        save_run_result(result)

        if "error" not in result:
            task_queue.complete_task(task)

        log("=== TASK RESULT SUMMARY ===")
        if "error" in result:
            log(f"ERROR: {result['error']}")
        else:
            review = result.get("review", "") or ""
            log("Review summary (first 500 chars):")
            log(review[:500])

        # short pause before next cycle
        time.sleep(5)


if __name__ == "__main__":
    log("Pando Dev multi-agent loop starting up.")
    main_loop()
