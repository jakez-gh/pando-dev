from FlagEmbedding import BGEM3FlagModel
import torch

# Load the model once at module import.
# First run will download "BAAI/bge-small-en" from HuggingFace and cache it.
# After that, it will work fully offline using the local cache.
#
# Prefer GPU (CUDA) when available, fallback to CPU
device = "cuda" if torch.cuda.is_available() else "cpu"
use_fp16 = device == "cuda"  # FP16 is safe on modern GPUs, unsafe on CPU
model = BGEM3FlagModel("BAAI/bge-small-en", use_fp16=use_fp16, device=device)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts into dense vectors.
    Returns a list of lists of floats.
    """
    # Smaller batch_size keeps memory usage under control on a laptop.
    embeddings = model.encode(texts, batch_size=8)
    return embeddings["dense_vecs"].tolist()
