# AI Dev System – Local Autonomous Code Intelligence

## Overview

This project is a local, privacy‑preserving AI development assistant. It can:

- index one or more git‑style projects
- embed full file contents into a vector database
- search code semantically
- read and write files
- run shell commands within a project

It is designed as the foundation for a Devin‑style autonomous developer.

---

## Components

### 1. Embedding layer (`embed.py`)

- Uses `FlagEmbedding` and `BAAI/bge-small-en`.
- Exposes:

```python
def embed_texts(texts: list[str]) -> list[list[float]]:
    ...
