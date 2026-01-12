import os
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

import json
import subprocess
from pathlib import Path

import pathspec
from chromadb import PersistentClient

from config import BASE_DIR, CHROMA_DIR, INDEX_STATE_FILE
from embed import embed_texts


def load_index_state() -> dict:
    if INDEX_STATE_FILE.exists():
        with open(INDEX_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_index_state(state: dict) -> None:
    INDEX_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def run_git(repo_path: Path, args: list[str]) -> str | None:
    """
    Run a git command in the given repo and return stdout, or None on error.
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_git_head(repo_path: Path) -> str | None:
    return run_git(repo_path, ["rev-parse", "HEAD"])


def get_git_branch(repo_path: Path) -> str | None:
    """
    Returns branch name or 'HEAD' if detached, or None on error.
    """
    return run_git(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])


def load_gitignore(project_path: Path):
    gitignore_path = project_path / ".gitignore"
    if not gitignore_path.exists():
        return None

    with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
        patterns = f.read().splitlines()

    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)


def is_text_file(path: Path) -> bool:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            f.read(2048)
        return True
    except Exception:
        return False


def list_repos() -> list[Path]:
    """
    Discover all git repos under BASE_DIR by looking for either:
    - a .git directory, or
    - a .git file (worktree)
    """
    repos: list[Path] = []
    for root, dirs, files in os.walk(BASE_DIR):
        root_path = Path(root)

        has_git_dir = ".git" in dirs
        has_git_file = ".git" in files

        if has_git_dir or has_git_file:
            repos.append(root_path)
            # do not descend into this repo/worktree
            dirs[:] = []

    return repos


def index_repository(repo_path: Path, project_id: str, branch: str, commit: str, collection) -> None:
    print(f"Indexing repo: {project_id} (branch={branch}, commit={commit}) at {repo_path}")

    spec = load_gitignore(repo_path)

    for root, dirs, files in os.walk(repo_path):
        root_path = Path(root)

        # Apply .gitignore to directories
        if spec:
            dirs[:] = [
                d
                for d in dirs
                if not spec.match_file(os.path.relpath(root_path / d, repo_path))
            ]

        for file in files:
            if file in {".gitignore", ".gitattributes", ".gitmodules"}:
                continue

            full_path = root_path / file
            rel_path = os.path.relpath(full_path, repo_path)

            # Skip ignored files
            if spec and spec.match_file(rel_path):
                continue

            if not is_text_file(full_path):
                continue

            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except Exception as e:
                print(f"Error reading {full_path}: {e}")
                continue

            if not text.strip():
                continue

            try:
                embedding = embed_texts([text])[0]
            except Exception as e:
                print(f"Error embedding {full_path}: {e}")
                continue

            metadata = {
                "project_id": project_id,
                "branch": branch,
                "file_path": rel_path,
                "commit": commit,
            }

            doc_id = f"{project_id}:{branch}:{rel_path}"

            try:
                collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    documents=[text],
                )
            except Exception as e:
                print(f"Error adding document {doc_id} to collection: {e}")

    print(f"Finished indexing {project_id} (branch={branch})")


def main():
    # Setup Chroma
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(
        name="code_files",
        metadata={"hnsw:space": "cosine"},
    )

    index_state = load_index_state()
    repos = list_repos()

    if not repos:
        print(f"No git repositories found under {BASE_DIR}")
        return

    for repo in repos:
        project_id = repo.name
        head = get_git_head(repo)
        branch = get_git_branch(repo)

        if head is None or branch is None:
            print(f"Skipping {project_id}: no HEAD or branch detected")
            continue

        state_key = f"{project_id}:{branch}"
        last_indexed = index_state.get(state_key)

        if last_indexed == head:
            print(f"{project_id} (branch={branch}) unchanged (HEAD {head}), skipping re-index.")
            continue

        index_repository(repo, project_id, branch, head, collection)
        index_state[state_key] = head
        save_index_state(index_state)


if __name__ == "__main__":
    main()
