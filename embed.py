import os
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

from FlagEmbedding import BGEM3FlagModel

# Load the model once at module import.
# use_fp16=False is safer on CPU-only Windows setups.
_model = BGEM3FlagModel("BAAI/bge-small-en", use_fp16=False)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts into dense vectors.
    Returns a list of lists of floats (Python-native, JSON-serializable).
    """
    result = _model.encode(texts, batch_size=16)
    return result["dense_vecs"].tolist()
