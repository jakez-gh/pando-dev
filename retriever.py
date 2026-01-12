import os
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

from chromadb import PersistentClient

from config import CHROMA_DIR
from embed import embed_texts

# Ensure DB directory exists
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Initialize Chroma client + collection
client = PersistentClient(path=str(CHROMA_DIR))
collection = client.get_or_create_collection(
    name="code_files",
    metadata={"hnsw:space": "cosine"},
)


def search_code(
    query: str,
    project_id: str | None = None,
    branch: str | None = None,
    n_results: int = 5,
):
    """
    Semantic code search over all indexed repos/branches.

    - If project_id is provided, restricts to that repo.
    - If branch is provided, restricts to that branch.
    """
    query_embedding = embed_texts([query])[0]

    where: dict = {}
    if project_id:
        where["project_id"] = project_id
    if branch:
        where["branch"] = branch

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where or None,
    )

    formatted = []
    if not results["ids"]:
        return formatted

    for i in range(len(results["ids"][0])):
        formatted.append(
            {
                "id": results["ids"][0][i],
                "file_path": results["metadatas"][0][i]["file_path"],
                "project_id": results["metadatas"][0][i]["project_id"],
                "branch": results["metadatas"][0][i]["branch"],
                "commit": results["metadatas"][0][i]["commit"],
                "document": results["documents"][0][i],
                "distance": results["distances"][0][i],
            }
        )

    return formatted


if __name__ == "__main__":
    hits = search_code("database connection", project_id=None, branch=None, n_results=3)
    for h in hits:
        print("\n--- Result ---")
        print("Project:", h["project_id"])
        print("Branch :", h["branch"])
        print("File   :", h["file_path"])
        print("Commit :", h["commit"])
        print("Dist   :", h["distance"])
        print(h["document"][:400], "...")
