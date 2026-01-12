import os
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

from pathlib import Path

BASE_DIR = Path("C:/Users/jake/dev")

# Vector DB lives outside the repo
CHROMA_DIR = Path(os.getenv("LOCALAPPDATA")) / "pando-dev" / "db"

# Index state file also lives outside the repo
INDEX_STATE_FILE = Path(os.getenv("LOCALAPPDATA")) / "pando-dev" / "index_state.json"
