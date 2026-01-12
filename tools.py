import os
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

import subprocess
from pathlib import Path

from config import BASE_DIR


def _run(cwd: Path, command: str) -> dict:
    """
    Run a shell command in the given working directory and return a structured result.
    """
    result = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "command": command,
        "cwd": str(cwd),
    }


def list_repos() -> list[str]:
    """
    Return a list of repo IDs (directory names) under BASE_DIR that contain a .git folder or file.
    This supports both normal repos and git worktrees.
    """
    repos: list[str] = []
    for root, dirs, files in os.walk(BASE_DIR):
        root_path = Path(root)

        has_git_dir = ".git" in dirs
        has_git_file = ".git" in files

        if has_git_dir or has_git_file:
            repos.append(root_path.name)
            dirs[:] = []

    return sorted(set(repos))


def project_path(project_id: str) -> Path:
    return BASE_DIR / project_id


# -----------------------------
# FILE OPERATIONS
# -----------------------------
def list_files(project_id: str) -> list[str]:
    root = project_path(project_id)
    files: list[str] = []
    for r, dirs, fs in os.walk(root):
        for f in fs:
            full = Path(r) / f
            rel = os.path.relpath(full, root)
            files.append(rel)
    return sorted(files)


def read_file(
    project_id: str | None = None,
    file_path: str | None = None,
    filename: str | None = None,
) -> str:
    """
    Read a file from a project.

    Preferred usage:
      read_file(project_id="pando-dev", file_path="indexer.py")

    To be robust to model behavior, `filename` is accepted as an alias for `file_path`
    when project_id is implied or already known by the caller.
    """
    if file_path is None and filename is not None:
        file_path = filename

    if project_id is None:
        raise ValueError("project_id is required")

    if file_path is None:
        raise ValueError("file_path or filename is required")

    full = project_path(project_id) / file_path
    with open(full, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def write_file(
    project_id: str | None = None,
    file_path: str | None = None,
    content: str | None = None,
    filename: str | None = None,
) -> bool:
    """
    Write content to a file in a project.

    Preferred usage:
      write_file(project_id="pando-dev", file_path="indexer.py", content="...")

    To be robust to model behavior, `filename` is accepted as an alias for `file_path`.
    """
    if file_path is None and filename is not None:
        file_path = filename

    if project_id is None:
        raise ValueError("project_id is required")

    if file_path is None:
        raise ValueError("file_path or filename is required")

    if content is None:
        raise ValueError("content is required")

    full = project_path(project_id) / file_path
    full.parent.mkdir(parents=True, exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def apply_patch(
    project_id: str | None = None,
    file_path: str | None = None,
    new_content: str | None = None,
    filename: str | None = None,
) -> bool:
    """
    For now, patching == replace entire file contents with new_content.
    """
    if new_content is None:
        raise ValueError("new_content is required")
    return write_file(project_id=project_id, file_path=file_path, filename=filename, content=new_content)


def run_command(project_id: str, command: str) -> dict:
    root = project_path(project_id)
    return _run(root, command)


# -----------------------------
# GIT HELPERS
# -----------------------------
def git_status(project_id: str) -> dict:
    return run_command(project_id, "git status")


def git_diff(project_id: str) -> dict:
    return run_command(project_id, "git diff")


def git_add_all(project_id: str) -> dict:
    return run_command(project_id, "git add .")


def git_checkout(project_id: str, branch: str, create: bool = False) -> dict:
    cmd = f"git checkout -b {branch}" if create else f"git checkout {branch}"
    return run_command(project_id, cmd)


def git_current_branch(project_id: str) -> str | None:
    root = project_path(project_id)
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_list_branches(project_id: str) -> list[str]:
    root = project_path(project_id)
    result = subprocess.run(
        ["git", "branch", "--format=%(refname:short)"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def git_commit(project_id: str, message: str) -> dict:
    cmd = f'git commit -am "{message}"'
    return run_command(project_id, cmd)


def git_pull(project_id: str) -> dict:
    return run_command(project_id, "git pull")


def git_head(project_id: str) -> str | None:
    root = project_path(project_id)
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def git_push(project_id: str, remote: str = "origin", branch: str | None = None) -> dict:
    if branch is None:
        branch = git_current_branch(project_id)
    if branch is None:
        return {"error": "No current branch"}
    return run_command(project_id, f"git push {remote} {branch}")


if __name__ == "__main__":
    print("Repos under", BASE_DIR)
    print(list_repos())
