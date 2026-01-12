import os
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


def get_git_head(repo_path: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


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
    Discover all git repos under BASE_DIR by looking for .git directories.
    """
    repos: list[Path] = []
    for root, dirs, files in os.walk(BASE_DIR):
        root_path = Path(root)
        if ".git" in dirs:
            repos.append(root_path)
            # Do not descend further into this repo
            dirs[:] = []
    return repos


def index_repository(repo_path: Path, project_id: str, collection) -> None:
    print(f"Indexing repo: {project_id} at {repo_path}")

    spec = load_gitignore(repo_path)

    for root, dirs, files in os.walk(repo_path):
        root_path = Path(root)

        # Apply .gitignore to directories
        if spec:
            dirs[:] = [
                d for d in dirs
                if not spec.match_file(os.path.relpath(root_path / d, repo_path))
            ]

        for file in files:
            # Skip Git metadata files
            if file in {".gitignore", ".gitattributes", ".gitmodules"}:
                continue

            full_path = root_path / file
            rel_path = os.path.relpath(full_path, repo_path)

            # Skip ignored files
            if spec and spec.match_file(rel_path):
                continue

            if not is_text_file(full_path):
                continue

            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

            embedding = embed_texts([text])[0]

            metadata = {
                "project_id": project_id,
                "file_path": rel_path,
            }

            doc_id = f"{project_id}:{rel_path}"

            collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[text],
            )

    print(f"Finished indexing {project_id}")


def main():
    # Setup Chroma
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

        if head is None:
            print(f"Skipping {project_id}: not a git repo or no HEAD")
            continue

        last_indexed = index_state.get(project_id)

        if last_indexed == head:
            print(f"{project_id} unchanged (HEAD {head}), skipping re-index.")
            continue

        # For simplicity: we add new docs; cleanup of stale docs can be added later.
        index_repository(repo, project_id, collection)

        index_state[project_id] = head
        save_index_state(index_state)


if __name__ == "__main__":
    main()
