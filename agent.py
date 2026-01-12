import json
import os
import re
import subprocess

from retriever import search_code
import tools
from config import DEFAULT_MODEL

os.environ["PYTHONIOENCODING"] = "utf-8"


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
}


def call_tool(tool_name: str, args: dict):
    if tool_name not in TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}
    func = TOOLS[tool_name]
    # Extra safety: ignore unexpected args instead of crashing
    try:
        return func(**args)
    except TypeError:
        # Try calling with no args as a fallback
        try:
            return func()
        except TypeError as e:
            return {"error": f"Bad args for {tool_name}: {e}"}


def extract_json_block(text: str) -> str | None:
    """
    Try to extract a JSON object from the model output.
    Handles both raw JSON and ```json fenced blocks.
    """
    text = text.strip()

    # Try raw JSON first
    if text.startswith("{") and text.endswith("}"):
        return text

    # Try to find a fenced ```json ... ``` block
    fence_pattern = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)
    m = fence_pattern.search(text)
    if m:
        return m.group(1).strip()

    # Fallback: attempt to find the first {...} block
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        return text[brace_start:brace_end + 1].strip()

    return None


def agent_step(model: str, message: str) -> dict:
    """
    Single step:
      - Ask the model what to do
      - If it returns a tool call, execute it
      - Otherwise return its response
    """
    tool_list = ", ".join(TOOLS.keys())

        prompt = f"""
You are an autonomous software engineer called Pando Dev.
You work on git repositories under a root directory.
You have access to tools: {tool_list}.

When you need to use a tool, respond ONLY with JSON:

{{
  "tool": "tool_name",
  "args": {{ ... }}
}}

Do NOT include explanations when calling tools.
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
    )

    if result.stderr:
        # Helpful when something goes wrong with Ollama / model
        print("Model stderr:", result.stderr.strip())

    output = result.stdout.strip()

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

    # If we get here, treat it as a natural language response
    return {"response": output}


if __name__ == "__main__":
    # Example: single step with your default model
    result = agent_step(DEFAULT_MODEL, "List all repos you can see under the dev folder.")
    print(result)