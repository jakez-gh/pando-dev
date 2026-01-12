from chromadb import PersistentClient

from config import CHROMA_DIR
from embed import embed_texts


client = PersistentClient(path=str(CHROMA_DIR))

collection = client.get_or_create_collection(
    name="code_files",
    metadata={"hnsw:space": "cosine"},
)


def search_code(query: str, project_id: str | None = None, n_results: int = 5):
    """
    Semantic code search over all indexed repos.

    If project_id is provided, restricts search to that repo.
    """
    query_embedding = embed_texts([query])[0]

    where = {}
    if project_id:
        where["project_id"] = project_id

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where,
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
                "document": results["documents"][0][i],
                "distance": results["distances"][0][i],
            }
        )

    return formatted


if __name__ == "__main__":
    hits = search_code("database connection", project_id=None, n_results=3)
    for h in hits:
        print("\n--- Result ---")
        print("Project:", h["project_id"])
        print("File   :", h["file_path"])
        print("Dist   :", h["distance"])
        print(h["document"][:400], "...")
