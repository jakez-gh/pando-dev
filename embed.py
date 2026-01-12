from FlagEmbedding import BGEM3FlagModel

# Load the model once at module import.
# First run will download "BAAI/bge-small-en" from HuggingFace and cache it.
# After that, it will work fully offline using the local cache.
#
# use_fp16=False is safer on CPU-only or mixed setups like your laptop.
model = BGEM3FlagModel("BAAI/bge-small-en", use_fp16=False)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts into dense vectors.
    Returns a list of lists of floats.
    """
    # Smaller batch_size keeps memory usage under control on a laptop.
    embeddings = model.encode(texts, batch_size=8)
    return embeddings["dense_vecs"].tolist()
