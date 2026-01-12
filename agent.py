import json
import os
import re
import subprocess
import uuid

from retriever import search_code
import tools
from config import DEFAULT_MODEL
from message_bus import get_message_bus
from task_engine import get_task_engine
from agent_coordinator import get_coordinator

os.environ["PYTHONIOENCODING"] = "utf-8"


AGENT_ID = str(uuid.uuid4())[:8]  # Unique identifier for this agent instance
AGENT_ROLE = "implementer"  # This agent's primary role


TOOLS = {
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
    "request_reindex": tools.request_reindex,
    "get_job_status": tools.get_job_status,
}


def call_tool(tool_name: str, args: dict):
    """
    Execute a tool with error handling and retries.
    
    Normalizes args for tools with multiple possible parameter names.
    Retries on transient errors.
    """
    if tool_name not in TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}
    func = TOOLS[tool_name]

    # Normalize args for tools that commonly get weird keys from the model
    if tool_name == "list_repos":
        # Normalize possible arg names: root_dir, directory, path
        base_arg = (
            args.get("root_dir")
            or args.get("directory")
            or args.get("path")
            or None
        )
        args = {"directory": base_arg} if base_arg is not None else {}

    max_retries = 2
    for attempt in range(max_retries):
        try:
            return func(**args)
        except TypeError as e:
            if attempt == 0:
                # Fallback: try calling with no args
                try:
                    return func()
                except TypeError as e2:
                    return {"error": f"Bad args for {tool_name}: {e2}"}
            else:
                return {"error": f"Bad args for {tool_name}: {e}"}
        except Exception as e:
            # Transient error - retry once
            if attempt < max_retries - 1:
                print(f"  Warning: Tool {tool_name} failed (attempt {attempt + 1}), retrying: {str(e)[:80]}")
                import time
                time.sleep(1)
            else:
                print(f"  Error: Tool {tool_name} failed after {max_retries} attempts: {str(e)[:100]}")
                return {"error": f"Tool execution failed: {str(e)[:200]}"}


def extract_json_block(text: str) -> str | None:
    """
    Try to extract a JSON object from the model output.
    Handles both raw JSON and ```json fenced blocks.
    """
    text = text.strip()

    # Try raw JSON
    if text.startswith("{") and text.endswith("}"):
        return text

    # Try fenced ```json ... ``` block
    fence_pattern = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
    m = fence_pattern.search(text)
    if m:
        return m.group(1).strip()

    # Fallback: first {...} block in the text
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        candidate = text[brace_start:brace_end + 1].strip()
        if candidate.startswith("{") and candidate.endswith("}"):
            return candidate

    return None


def agent_step(model: str, message: str, current_task_id: str | None = None) -> dict:
    """
    Single step:
      - Ask the model what to do
      - If it returns a tool call, execute it
      - Otherwise return its response
      
    Integrates with coordinator for task lifecycle management.
    """
    tool_list = ", ".join(TOOLS.keys())

    prompt = f"""
You are Pando, an autonomous software engineering team.
You work on git repositories under a root directory.
You have access to tools: {tool_list}.

Pando Operating Rule:
- Finish one task completely before starting or suggesting another.
- Do NOT propose new tasks, refactors, or improvements until the current task is finished.
- Do NOT wander or self-assign side quests.

TOOL CALLING FORMAT (STRICT):
When you need to use a tool, respond ONLY with JSON:

{{
  "tool": "tool_name",
  "args": {{ ... }}
}}

Rules:
- Use ONLY tool names from: {tool_list}
- Use ONLY argument names that match the tool's expected parameters.
- DO NOT invent new argument names.
- DO NOT wrap JSON in code fences.
- DO NOT include explanations when calling tools.

When you have enough information and don't need tools,
respond in natural language.

User message:
{message}
"""

    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="ignore",
        timeout=300,  # 5 minute timeout for model response
    )

    if result.returncode != 0:
        return {
            "error": f"Model execution failed with code {result.returncode}",
            "stderr": result.stderr.strip()[:200],
        }

    if result.stderr:
        print(f"[Model Warning] {result.stderr.strip()[:100]}")

    output = result.stdout.strip()
    if not output:
        return {"error": "Model returned empty response"}

    json_block = extract_json_block(output)
    if json_block is not None:
        try:
            data = json.loads(json_block)
            if isinstance(data, dict) and "tool" in data:
                tool_name = data["tool"]
                args = data.get("args", {}) or {}
                if not isinstance(args, dict):
                    return {"error": f"Tool args must be an object, got: {type(args)}"}
                tool_result = call_tool(tool_name, args)
                return {"tool_call": data, "tool_result": tool_result}
        except json.JSONDecodeError as e:
            return {
                "error": f"Failed to parse JSON tool call: {e}",
                "raw_output": output,
            }

    # If no valid tool call, treat as natural language response from Pando
    return {"response": output}


if __name__ == "__main__":
    import time
    
    # Initialize coordinator and register this agent
    coordinator = get_coordinator()
    message_bus = get_message_bus()
    task_engine = get_task_engine()
    
    coordinator.register_agent(AGENT_ID, AGENT_ROLE)
    message_bus.publish("agent_ready", source=AGENT_ID, payload={"role": AGENT_ROLE})
    print(f"[Agent {AGENT_ID}] Registered as '{AGENT_ROLE}', waiting for work...")
    
    try:
        step_count = 0
        empty_cycle_count = 0
        while coordinator.should_continue_running():
            step_count += 1
            
            # Request work from coordinator
            task = coordinator.assign_work(AGENT_ID)
            if task is None:
                empty_cycle_count += 1
                if empty_cycle_count % 5 == 1:  # Every 5 cycles, print status
                    print(f"[Agent {AGENT_ID}] No work available... (cycle {empty_cycle_count})")
                time.sleep(2)
                continue
            
            empty_cycle_count = 0
            task_id = task["id"]
            task_title = task["title"]
            print(f"\n[Agent {AGENT_ID}] Step {step_count}: Working on '{task_title}'")
            
            # Mark task as in progress
            coordinator.task_started(AGENT_ID, task_id)
            message_bus.publish(
                "task_started",
                source=AGENT_ID,
                target=task_id,
                payload={"agent": AGENT_ID}
            )
            
            # Execute the task
            try:
                result = agent_step(
                    DEFAULT_MODEL,
                    f"Task: {task_title}\n\nDescription: {task.get('description', 'No description')}\n\nComplete this task fully.",
                    current_task_id=task_id
                )
                
                # Handle tool calls in a loop until task is complete
                max_iterations = 10
                iteration = 0
                while iteration < max_iterations:
                    iteration += 1
                    if "tool_call" in result:
                        print(f"  Tool: {result['tool_call'].get('tool')}")
                        # Continue with feedback
                        result = agent_step(
                            DEFAULT_MODEL,
                            f"Tool result: {json.dumps(result.get('tool_result', {}))}\n\nContinue working on task: {task_title}",
                            current_task_id=task_id
                        )
                    elif "response" in result:
                        print(f"  Response: {result['response'][:100]}...")
                        break
                    else:
                        break
                
                # Mark task as complete
                coordinator.task_complete(AGENT_ID, task_id)
                message_bus.publish(
                    "task_complete",
                    source=AGENT_ID,
                    target=task_id,
                    payload={"result": "success"}
                )
                print(f"[Agent {AGENT_ID}] Task {task_id} completed.")
                
            except Exception as e:
                print(f"[Agent {AGENT_ID}] Task {task_id} failed: {e}")
                coordinator.task_failed(AGENT_ID, task_id, str(e))
                message_bus.publish(
                    "task_failed",
                    source=AGENT_ID,
                    target=task_id,
                    payload={"error": str(e)}
                )
        
        print(f"\n[Agent {AGENT_ID}] All work complete. Shutting down gracefully.")
        
    except KeyboardInterrupt:
        print(f"\n[Agent {AGENT_ID}] Interrupted by user. Shutting down cleanly.")
