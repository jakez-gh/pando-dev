import os
import subprocess
from pathlib import Path

from config import BASE_DIR
from pando_queue import enqueue, get_job


def request_reindex(project_id: str) -> dict:
    """
    Enqueue a reindex job for the given project.
    """
    job_id = enqueue(
        "reindex_repo",
        {
            "project_id": project_id,
            "repo_path": str(BASE_DIR / project_id),
        },
    )
    return {"job_id": job_id, "project_id": project_id}


def get_job_status(job_id: str) -> dict:
    """
    Return the current status of a queue job.
    """
    job = get_job(job_id)
    if job is None:
        return {"error": "job_not_found", "job_id": job_id}
    return {
        "job_id": job["id"],
        "type": job["type"],
        "state": job["state"],
        "result": job.get("result"),
        "timestamp": job.get("timestamp"),
        "payload": job.get("payload"),
    }


def list_repos(
    directory: str | None = None,
    path: str | None = None,
    root_dir: str | None = None,
) -> list[str]:
    """
    Return a list of repo IDs (directory names) under a base directory that contain a .git folder.

    The model may call this with `directory`, `path`, or `root_dir`.
    """
    base_arg = root_dir or path or directory

    if base_arg:
        # Normalize common variants of "dev" root
        if base_arg in ("/dev", "dev", "./dev", ".\\dev"):
            base = BASE_DIR
        else:
            candidate = Path(base_arg)
            if not candidate.is_absolute():
                base = (BASE_DIR / candidate).resolve()
            else:
                base = candidate
    else:
        base = BASE_DIR

    repos: list[str] = []
    for root, dirs, files in os.walk(base):
        root_path = Path(root)
        if ".git" in dirs:
            repos.append(root_path.name)
            # Do not descend further into this repo
            dirs[:] = []
    return sorted(set(repos))


def project_path(project_id: str) -> Path:
    return BASE_DIR / project_id


def list_files(project_id: str) -> list[str]:
    root = project_path(project_id)
    files: list[str] = []
    for r, dirs, fs in os.walk(root):
        for f in fs:
            full = Path(r) / f
            rel = os.path.relpath(full, root)
            files.append(rel)
    return sorted(files)


def read_file(project_id: str, file_path: str) -> str:
    full = project_path(project_id) / file_path
    with open(full, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def write_file(project_id: str, file_path: str, content: str) -> bool:
    full = project_path(project_id) / file_path
    full.parent.mkdir(parents=True, exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return True


def apply_patch(project_id: str, file_path: str, new_content: str) -> bool:
    """
    For now, patching == replace entire file contents with new_content.
    """
    return write_file(project_id, file_path, new_content)


def run_command(project_id: str, command: str) -> dict:
    root = project_path(project_id)
    result = subprocess.run(
        command,
        cwd=root,
        shell=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }


# Git helpers

def git_status(project_id: str) -> dict:
    return run_command(project_id, "git status")


def git_diff(project_id: str) -> dict:
    return run_command(project_id, "git diff")


def git_add_all(project_id: str) -> dict:
    return run_command(project_id, "git add .")


def git_checkout(project_id: str, branch: str, create: bool = False) -> dict:
    cmd = f"git checkout -b {branch}" if create else f"git checkout {branch}"
    return run_command(project_id, cmd)


def git_commit(project_id: str, message: str) -> dict:
    cmd = f'git commit -am "{message}"'
    return run_command(project_id, cmd)


def git_pull(project_id: str) -> dict:
    return run_command(project_id, "git pull")


if __name__ == "__main__":
    print("Repos under", BASE_DIR)
    print(list_repos())
