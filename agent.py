import json
import subprocess

from retriever import search_code
import tools


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
    try:
        return TOOLS[tool_name](**args)
    except TypeError as e:
        return {"error": f"Bad args for {tool_name}: {e}"}


def agent_step(model: str, message: str) -> dict:
    """
    Single step:
      - Ask the model what to do
      - If it returns a tool call, execute it
      - Otherwise return its response
    """
    tool_list = ", ".join(TOOLS.keys())

    prompt = f"""
You are an autonomous software engineer called Ghost Pepper Dev.
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
    )

    output = result.stdout.strip()

    try:
        data = json.loads(output)
        if "tool" in data:
            tool_name = data["tool"]
            args = data.get("args", {})
            tool_result = call_tool(tool_name, args)
            return {"tool_call": data, "tool_result": tool_result}
    except json.JSONDecodeError:
        pass

    return {"response": output}


if __name__ == "__main__":
    # Example: single step with a model you have installed, e.g. "qwen2.5-coder:7b"
    print(agent_step("qwen2.5-coder:7b", "List all repos you can see under the dev folder."))
