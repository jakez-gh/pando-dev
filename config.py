from pathlib import Path

# Root directory where your git repos live.
# For your current layout this will be the pando-dev folder itself.
BASE_DIR = Path(__file__).resolve().parent

# Chroma DB storage directory
CHROMA_DIR = BASE_DIR / "chroma"

# Where we store indexing state (per repo HEAD)
INDEX_STATE_FILE = BASE_DIR / "index_state.json"

# Safe mode for long runs / weaker hardware
SAFE_MODE = True

# Default model for the agent
# You can bump this if you feel comfortable, but this is safe on your laptop.
DEFAULT_MODEL = "llama3.1-8b-12k"

# Maximum context tokens the agent should assume when prompting
# (this is a logical limit; actual context is set in your Ollama model config)
MAX_CONTEXT_TOKENS = 12000
