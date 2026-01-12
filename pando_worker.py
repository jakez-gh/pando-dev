import time
from pathlib import Path

from pando_queue import dequeue, update_job
from indexer import index_repository
from config import BASE_DIR
from chromadb import PersistentClient
from message_bus import get_message_bus


def run_worker():
    print("Pando Queue Worker started.")
    print("Watching for jobs...")

    client = PersistentClient(path=str(BASE_DIR / "chroma"))
    collection = client.get_or_create_collection(
        name="code_files",
        metadata={"hnsw:space": "cosine"},
    )
    
    message_bus = get_message_bus()

    while True:
        job = dequeue()
        if not job:
            time.sleep(1)
            continue

        job_id = job["id"]
        job_type = job["type"]
        payload = job["payload"]

        print(f"Processing job {job_id}: {job_type}")

        update_job(job_id, "processing")
        message_bus.publish("reindex_started", source="worker", payload={"job_id": job_id, "job_type": job_type})

        try:
            if job_type == "reindex_repo":
                repo_path = Path(payload["repo_path"])
                project_id = payload["project_id"]

                index_repository(repo_path, project_id, collection)
                update_job(job_id, "done", {"status": "ok"})
                message_bus.publish("reindex_complete", source="worker", payload={"job_id": job_id, "status": "ok"})

            else:
                error_msg = "Unknown job type"
                update_job(job_id, "failed", {"error": error_msg})
                message_bus.publish("reindex_failed", source="worker", payload={"job_id": job_id, "error": error_msg})

        except Exception as e:
            error_msg = str(e)
            update_job(job_id, "failed", {"error": error_msg})
            message_bus.publish("reindex_failed", source="worker", payload={"job_id": job_id, "error": error_msg})

        time.sleep(0.1)


if __name__ == "__main__":
    try:
        run_worker()
    except KeyboardInterrupt:
        print("\nPando Worker shutting down cleanly.")
