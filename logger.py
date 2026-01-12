import os
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"

import time


def log(msg: str) -> None:
    """Simple timestamped log line."""
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
