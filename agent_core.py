import os
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

import json
import subprocess
from typing import Any

from retriever import search_code
import tools
from logger import log


TOOLS: dict[str, Any] = {
    "list_repos": tools.list_repos,
    "list_files": tools.list_files,
    "read_file": tools.read_file,
    "write_file": tools.write_file,
    "apply_patch": tools.apply_patch,
    "run_command": tools.run_command,
    "search_code": search_code,
    "git_status": tools.git_status,
    "git_diff": tools.git_diff,
    "git_add_all": tools.git_add_all,
    "git_checkout": tools.git_checkout,
    "git_commit": tools.git_commit,
    "git_pull": tools.git_pull,
    "git_current_branch": tools.git_current_branch,
    "git_list_branches": tools.git_list_branches,
    "git_head": tools.git_head,
    "git_push": tools.git_push,
}


def call_tool(tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    if tool_name not in TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return TOOLS[tool_name](**args)
    except TypeError as e:
        return {"error": f"Bad args for {tool_name}: {e}"}
    except Exception as e:
        return {"error": f"Exception in {tool_name}: {e}"}


def model_call(model: str, prompt: str) -> str:
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout.strip()


# -----------------------------
# ROLE-SPECIFIC PLANNING
# -----------------------------
def _role_caption(role: str) -> str:
    role = (role or "general").lower()
    if role == "planner":
        return "You specialize in planning and breaking work into steps."
    if role == "designer":
        return "You specialize in design, architecture, and clarifying how things should be structured."
    if role == "implementer":
        return "You specialize in implementing small, safe code changes."
    if role == "tester":
        return "You specialize in tests, validation, and checks."
    if role == "maintainer":
        return "You specialize in refactoring, cleanup, docs, and long-term maintainability."
    return "You are a general-purpose software engineer."


def plan_task(model: str, project_id: str, goal: str, role: str) -> list[dict[str, Any]]:
    tool_list = ", ".join(TOOLS.keys())
    role_caption = _role_caption(role)

    planning_prompt = f"""
You are Pando Dev, acting as: {role.upper()}.

{role_caption}

PROJECT: {project_id}

TASK GOAL:
{goal}

TOOLS: {tool_list}

You MUST produce a JSON array of steps.
Each step MUST be:

{{
  "description": "...",
  "tool": "tool_name_or_null",
  "args": {{ ... }}
}}

If a step is thinking only, use:
  "tool": null,
  "args": {{}}

For any file operation, include "project_id": "{project_id}" in args.

NO Markdown. NO backticks. JSON ONLY.
"""

    log(f"Planning task for {project_id} [{role}] with goal: {goal[:80]}...")
    out = model_call(model, planning_prompt)

    try:
        plan = json.loads(out)
        if isinstance(plan, list):
            return plan
    except Exception:
        log(f"Failed to parse plan JSON: {out[:200]}")

    return [
        {
            "description": f"Could not parse plan for goal: {goal}",
            "tool": None,
            "args": {},
        }
    ]


# -----------------------------
# BRANCH SAFETY
# -----------------------------
SAFE_BASE_BRANCHES = {"main", "master"}
AI_BRANCH_PREFIX = "ai/"


def ensure_ai_branch(project_id: str) -> str:
    import time

    current = tools.git_current_branch(project_id)
    if current is None:
        return ""

    if current in SAFE_BASE_BRANCHES:
        ts = time.strftime("%Y%m%d-%H%M%S")
        new_branch = f"{AI_BRANCH_PREFIX}{ts}"
        log(f"On protected branch {current}. Creating AI branch {new_branch}.")
        tools.git_checkout(project_id, new_branch, create=True)
        return new_branch

    return current


# -----------------------------
# EXECUTION + REVIEW + COMMIT
# -----------------------------
def run_task(model: str, project_id: str, goal: str, role: str) -> dict[str, Any]:
    """
    High-level entry point for one task:
    - plan (role-aware)
    - execute steps
    - review
    - commit/push
    """
    plan = plan_task(model, project_id, goal, role)

    log_entries: list[dict[str, Any]] = []

    branch = ensure_ai_branch(project_id)
    log_entries.append({"event": "branch_policy", "branch": branch})
    log(f"Executing plan on branch {branch} for {project_id} [{role}].")

    # Execute plan
    for i, step in enumerate(plan, start=1):
        desc = step.get("description", "")
        tool_name = step.get("tool")
        args = step.get("args", {}) or {}

        entry = {"step": i, "description": desc, "tool": tool_name, "args": args}

        if tool_name is None:
            entry["result"] = "thinking step"
            log(f"[{project_id}][{role}] Step {i}: thinking only.")
            log_entries.append(entry)
            continue

        if tool_name not in TOOLS:
            entry["result"] = f"Unknown tool: {tool_name}"
            log(f"[{project_id}][{role}] Step {i}: unknown tool {tool_name}.")
            log_entries.append(entry)
            continue

        log(f"[{project_id}][{role}] Step {i}: {tool_name}({args}).")
        try:
            entry["result"] = TOOLS[tool_name](**args)
        except Exception as e:
            entry["result"] = {"error": str(e)}
            log(f"[{project_id}][{role}] Step {i} ERROR: {e}")

        log_entries.append(entry)

    # Self-review
    diff = tools.git_diff(project_id).get("stdout", "")
    log(f"[{project_id}][{role}] Generating self-review.")

    review_prompt = f"""
You are Pando Dev reviewing changes for project {project_id} on branch {branch}.

ROLE: {role}

DIFF:
{diff}

Provide, in plain text:
1. Summary of changes.
2. Risks.
3. Next enhancements you recommend.
4. Questions for the human (if any).
"""

    review_text = model_call(model, review_prompt)

    # Commit/push with strict JSON
    log(f"[{project_id}][{role}] Deciding whether to commit/push.")
    commit_prompt = f"""
You are Pando Dev acting as {role}.

Here is the diff for project {project_id} on branch {branch}:

{diff}

If there are meaningful changes to commit, output a JSON array of tool calls to:

1. git_add_all
2. git_commit (with a message)
3. git_push

Format:

[
  {{"tool": "git_add_all", "args": {{"project_id": "{project_id}"}}}},
  {{"tool": "git_commit", "args": {{"project_id": "{project_id}", "message": "your commit message"}}}},
  {{"tool": "git_push", "args": {{"project_id": "{project_id}"}}}}
]

If there is NOTHING to commit, output an empty JSON array: [].

NO Markdown. JSON ONLY.
"""

    commit_output = model_call(model, commit_prompt)
    commit_actions: list[dict[str, Any]] = []

    try:
        calls = json.loads(commit_output)
        if isinstance(calls, dict):
            calls = [calls]
        if isinstance(calls, list):
            for c in calls:
                if isinstance(c, dict) and "tool" in c:
                    tool_name = c["tool"]
                    args = c.get("args", {}) or {}
                    log(f"[{project_id}][{role}] Commit action: {tool_name}({args}).")
                    result = call_tool(tool_name, args)
                    commit_actions.append(
                        {"tool": tool_name, "args": args, "result": result}
                    )
    except Exception:
        log(f"[{project_id}][{role}] Could not parse commit JSON: {commit_output[:200]}")
        commit_actions.append(
            {
                "tool": None,
                "args": {},
                "result": f"Could not parse commit JSON: {commit_output[:200]}",
            }
        )

    return {
        "project_id": project_id,
        "goal": goal,
        "role": role,
        "log": log_entries,
        "diff": diff,
        "review": review_text,
        "commit_actions": commit_actions,
    }
