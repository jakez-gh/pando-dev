import os
import json
import subprocess
from pathlib import Path

import pathspec
from chromadb import PersistentClient

from config import BASE_DIR, CHROMA_DIR, INDEX_STATE_FILE
from embed import embed_texts

# Directories we never want to index (even if not in .gitignore)
IGNORE_DIRS = {
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "ENV",
    "chroma",
    "chroma_db",
    "runs",
    "tasks",
}

# Skip files larger than this many bytes (to avoid OOM)
MAX_FILE_BYTES = 512 * 1024  # 512 KB

# Chunking parameters
CHARS_PER_CHUNK = 2000
CHUNK_OVERLAP = 200


def load_index_state() -> dict:
    """Load index state from file, with error recovery."""
    if INDEX_STATE_FILE.exists():
        try:
            with open(INDEX_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Warning: Index state file corrupted: {e}. Starting fresh.")
            return {}
        except IOError as e:
            print(f"Warning: Failed to read index state: {e}")
            return {}
    return {}


def save_index_state(state: dict) -> None:
    """Save index state to file with error handling."""
    try:
        INDEX_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Write to temp file first, then rename (atomic operation)
        temp_file = INDEX_STATE_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        temp_file.replace(INDEX_STATE_FILE)  # Atomic rename
    except IOError as e:
        print(f"Error: Failed to save index state: {e}")
        raise


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
    We must NOT filter out '.git' before we check for it.
    """
    repos: list[Path] = []
    for root, dirs, files in os.walk(BASE_DIR):
        root_path = Path(root)

        # First, detect repos
        if ".git" in dirs:
            repos.append(root_path)
            # Do not descend further into this repo
            dirs[:] = []
            continue

        # Then apply ignore rules (excluding .git which we already handled)
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

    return repos


def chunk_text(text: str) -> list[str]:
    """
    Split text into overlapping chunks.
    """
    chunks: list[str] = []
    n = len(text)
    if n <= CHARS_PER_CHUNK:
        return [text]

    start = 0
    while start < n:
        end = start + CHARS_PER_CHUNK
        chunk = text[start:end]
        chunks.append(chunk)
        if end >= n:
            break
        start = end - CHUNK_OVERLAP

    return chunks


def index_repository(repo_path: Path, project_id: str, collection) -> None:
    print(f"Indexing repo: {project_id} at {repo_path}")

    spec = load_gitignore(repo_path)

    file_count = 0
    embedded_count = 0
    skipped_large = 0

    for root, dirs, files in os.walk(repo_path):
        root_path = Path(root)

        # Apply IGNORE_DIRS on directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and d != ".git"]

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

            # Skip non-text files
            if not is_text_file(full_path):
                continue

            # Skip very large files by size
            try:
                size = full_path.stat().st_size
            except OSError:
                continue

            if size > MAX_FILE_BYTES:
                skipped_large += 1
                if skipped_large <= 10:
                    print(f"  Skipping large file (> {MAX_FILE_BYTES} bytes): {rel_path}")
                elif skipped_large == 11:
                    print("  ... further large files will be skipped silently")
                continue

            file_count += 1
            if file_count % 20 == 0:
                print(f"  Scanned {file_count} files so far...")

            # Show which file we are embedding
            print(f"  Embedding file: {rel_path}")

            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

            # Skip empty files
            if not text.strip():
                continue

            chunks = chunk_text(text)
            for idx, chunk in enumerate(chunks):
                # Embed one chunk at a time to keep memory usage low
                embedding = embed_texts([chunk])[0]
                embedded_count += 1
                if embedded_count % 10 == 0:
                    print(f"  Embedded {embedded_count} chunks...")

                metadata = {
                    "project_id": project_id,
                    "file_path": rel_path,
                    "chunk_index": idx,
                }

                doc_id = f"{project_id}:{rel_path}:{idx}"

                collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    documents=[chunk],
                )

    print(f"Finished indexing {project_id}.")
    print(f"  Total chunks indexed: {embedded_count}")
    if skipped_large > 0:
        print(f"  Skipped {skipped_large} large files (> {MAX_FILE_BYTES} bytes).")


def main():
    print(f"Using BASE_DIR = {BASE_DIR}")
    print(f"Chroma path   = {CHROMA_DIR}")

    # Optional: rebuild DB from scratch by deleting the directory manually
    # if needed. For now we rely on HEAD tracking in INDEX_STATE_FILE.

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

    print("Discovered repositories:")
    for r in repos:
        print(f"  - {r}")

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

        index_repository(repo, project_id, collection)

        index_state[project_id] = head
        save_index_state(index_state)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nIndexing interrupted by user.")
