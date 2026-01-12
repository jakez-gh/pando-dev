import json
import time
import uuid
from pathlib import Path
from typing import Optional, Dict, Any

from config import BASE_DIR

QUEUE_FILE = BASE_DIR / "pando_queue.jsonl"
LOCK_FILE = BASE_DIR / "pando_queue.lock"


def _acquire_lock():
    """
    Prevent multiple writers or workers from running at once.
    
    With timeout-based cleanup for stale locks.
    """
    import os
    
    LOCK_TIMEOUT = 300  # 5 minutes - if older, consider it stale
    
    if LOCK_FILE.exists():
        try:
            mtime = LOCK_FILE.stat().st_mtime
            age = time.time() - mtime
            if age < LOCK_TIMEOUT:
                raise RuntimeError("Queue is locked by another process.")
            else:
                print(f"Warning: Stale lock detected (age: {age:.1f}s). Removing.")
                LOCK_FILE.unlink()
        except OSError:
            pass
    
    # Create lock with PID for debugging
    lock_content = json.dumps({"pid": os.getpid(), "timestamp": time.time()})
    LOCK_FILE.write_text(lock_content)


def _release_lock():
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()


def enqueue(job_type: str, payload: Dict[str, Any]) -> str:
    """
    Add a job to the queue.
    Returns the job_id.
    
    Retries on lock contention with exponential backoff.
    """
    job_id = str(uuid.uuid4())
    entry = {
        "id": job_id,
        "type": job_type,
        "payload": payload,
        "state": "pending",
        "timestamp": time.time(),
    }

    # Ensure parent directory exists
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Retry logic for lock contention
    max_retries = 3
    for attempt in range(max_retries):
        try:
            _acquire_lock()
            try:
                # Atomic append to existing queue or create new
                with open(QUEUE_FILE, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
                return job_id
            finally:
                _release_lock()
        except RuntimeError as e:
            if attempt < max_retries - 1:
                time.sleep(1.0 * (attempt + 1))  # Exponential backoff: 1s, 2s
            else:
                raise RuntimeError(f"Failed to enqueue job after {max_retries} attempts: {e}")


def read_all() -> list[dict]:
    """
    Read all queue entries.
    """
    if not QUEUE_FILE.exists():
        return []
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def dequeue() -> Optional[dict]:
    """
    Return the first pending job, or None.
    """
    jobs = read_all()
    for job in jobs:
        if job["state"] == "pending":
            return job
    return None


def update_job(job_id: str, new_state: str, result: Optional[dict] = None):
    """
    Update a job's state (processing, done, failed, canceled).
    
    Uses atomic file operations (write to temp, then rename).
    """
    jobs = read_all()
    updated = []
    for job in jobs:
        if job["id"] == job_id:
            job["state"] = new_state
            if result is not None:
                job["result"] = result
        updated.append(job)

    _acquire_lock()
    try:
        # Atomic write: temp file first, then rename
        temp_file = QUEUE_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            for job in updated:
                f.write(json.dumps(job) + "\n")
        # Atomic rename prevents corruption if crash mid-write
        temp_file.replace(QUEUE_FILE)
    finally:
        _release_lock()


def get_job(job_id: str) -> Optional[dict]:
    """
    Look up a single job by id.
    """
    jobs = read_all()
    for job in jobs:
        if job["id"] == job_id:
            return job
    return None


def list_jobs(state: Optional[str] = None) -> list[dict]:
    """
    List jobs, optionally filtered by state.
    """
    jobs = read_all()
    if state is None:
        return jobs
    return [j for j in jobs if j.get("state") == state]
