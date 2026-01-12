# pando-dev

Pando Dev is a local, branch-aware, multi-repo development assistant designed to evolve over time and eventually improve itself. It indexes your entire development environment, understands git branches and commits, and provides a tool-using agent capable of reading, writing, and reasoning about code across all your projects.

---

## Overview of Components

1. config.py  
   Central configuration for paths, DB, repo root.

2. embed.py  
   Embedding layer using BGE-small-en.

3. indexer.py (multi-branch + multi-repo aware)  
   - Detects all repos under BASE_DIR  
   - Detects all branches via Git worktrees  
   - Stores embeddings per branch  
   - Stores commit hashes per branch  
   - Avoids re-indexing unchanged branches  
   - Supports cross-repo search  
   - Supports cross-branch search  
   - Maintains index_state.json  

4. retriever.py  
   - Query by repo  
   - Query by branch  
   - Query across all repos  
   - Query across all branches  
   - Returns structured results  

5. tools.py  
   - File operations  
   - Git operations (status, diff, add, commit, checkout, pull)  
   - Branch-aware operations  
   - Repo discovery  
   - Worktree discovery  
   - Command execution  

6. agent.py  
   - Tool registry  
   - Tool-calling loop  
   - Branch-aware agent context  
   - Ready for planning layer  
   - Ready for autonomous improvement  

7. .gitignore  
   - Clean  
   - Modern  
   - Maintained by the system  
   - Includes Chroma DB, venv, caches, logs, etc.  

8. README.md  
   - Clean Markdown  
   - No nested code fences  
   - New-user friendly  
   - Installation instructions  
   - GitHub CLI instructions  
   - Python setup instructions  
   - Repo purpose  
   - Architecture overview  
   - Self-improvement philosophy  
   - Star-worthy presentation  

9. Folder structure  
   - Clean  
   - Professional  
   - GitHub-ready  
   - AI-maintainable  

---

## Installation

1. Install Python 3.11  
2. Install Git  
3. Install GitHub CLI  
4. Clone or create the pando-dev repo  
5. Create a virtual environment  
6. Install dependencies  
7. Download the embedding model  
8. Run the indexer to build the semantic database  

---

## Usage

- Run indexer.py to index all repos and branches  
- Use retriever.py to search code  
- Use agent.py to interact with the system via an LLM  
- Use tools.py for direct programmatic operations  

---

## Philosophy

Pando Dev is designed to:

- Understand your entire development environment  
- Provide semantic search across all repos and branches  
- Assist with code modification and reasoning  
- Integrate with git for safe, branch-aware operations  
- Gradually improve itself over time  
- Become a long-lived, self-evolving development companion  

