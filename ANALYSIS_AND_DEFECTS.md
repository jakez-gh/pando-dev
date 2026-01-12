# Pando Architecture Analysis & Defects Report

## CRITICAL DEFECTS

### 1. **Missing Imports in indexer.py** ⚠️ BLOCKER
- Missing: `import json`, `import subprocess`, `import os`, `import pathspec`
- **Impact**: Indexing will crash immediately
- **Fix**: Add imports at top

### 2. **Chroma Collection Never Receives Data** ⚠️ BLOCKER  
- `indexer.py` line 195 (`embedded_count += 1`) but never calls `collection.add()`
- Results are embedded but never stored in vector DB
- **Impact**: Semantic search returns nothing
- **Fix**: Call `collection.add(ids=[...], embeddings=[...], documents=[...], metadatas=[...])`

### 3. **Inconsistent Tool Argument Handling** ⚠️ HIGH
**Problem**: `list_repos()` called with `project_id` arg (run logs show error)
- `agent.py` normalizes args for `list_repos` but expects `directory`, `path`, or `root_dir`
- Model still tries `project_id` which doesn't exist
- **Impact**: Agents fail to list repos
- **Fix**: Document expected args clearly or extend normalization

### 4. **Missing JSON Parsing in indexer.py** ⚠️ HIGH
- Line 27: `return json.load(f)` but `json` module never imported
- **Impact**: Index state can't load, first run crashes
- **Fix**: Add `import json`

### 5. **Broken Task Tracking System** ⚠️ MEDIUM
- `backlog.json` has duplicate entries, all marked "done"
- Task tracking is write-only, no task assignment or state machine
- Planner/Designer/Implementer roles exist but no role-based task routing
- **Impact**: Agents can't identify what to work on next
- **Fix**: Create task assignment system

### 6. **No Agent Collaboration/Coordination** ⚠️ MEDIUM
- Multiple role-based agents (planner, designer, implementer, tester, maintainer) run independently
- No shared state or message passing between agents
- No mechanism for agent A to hand off work to agent B
- **Impact**: Agents work in parallel on same tasks, waste effort
- **Fix**: Add agent communication layer (inbox system started but incomplete)

### 7. **Race Conditions in Queue System** ⚠️ MEDIUM
- File-based locking is primitive: if lock holder crashes, lock is never released
- Concurrent agents could corrupt queue file
- **Impact**: Queue jobs lost or corrupted
- **Fix**: Implement process-safe locking (PID tracking, timeout-based cleanup)

### 8. **No Post-Commit Re-indexing** ⚠️ MEDIUM
- Inbox question: "Can we index while running the agent? everytime we change a file?"
- Currently, changes are indexed only when `request_reindex` is called
- After `git_commit`, old embeddings remain in vector DB
- **Impact**: Code search returns stale results after file modifications
- **Fix**: Add automatic reindex trigger on file writes or git operations

---

## DESIGN ISSUES

### 1. **Monolithic Agent vs Role-Specific Teams**
**Issue**: `agent.py` is single-entry point, but system expects role-specific agents
- Designer, Planner, Implementer, Tester, Maintainer roles in backlog but no routing
- All agents share same tools and prompts
- No role-appropriate context or constraints

**Recommendation**: 
- Create role-specific agent constructors (Designer, Planner, etc.)
- Each role gets specialized tools/constraints
- Implement agent registry for coordination

### 2. **Synchronous Queue Blocking**
**Issue**: `pando_worker.py` sleeps 1 second per loop; indexing can take minutes
- While indexing, agent can enqueue more jobs but worker is blocked
- No parallelism or worker pool

**Recommendation**:
- Multi-threaded worker pool
- Or async/await with asyncio
- Or separate indexing service

### 3. **No Request Context or Tracing**
**Issue**: Run logs don't link tool calls to original goals
- Impossible to debug why agent made a specific tool call
- No parent/child relationships between calls

**Recommendation**:
- Add request ID, context stack, breadcrumb logging
- Store full execution trace with each run

### 4. **Tool Argument Mismatch**
**Issue**: Model can invent argument names; no schema validation
- `agent.py` manually normalizes `list_repos` args
- Other tools have no normalization
- Hard for model to know correct arg names

**Recommendation**:
- Generate tool schema (JSON Schema) from function signatures
- Pass schemas to model in prompt
- Validate args against schema before calling

### 5. **No Error Recovery in Agent Loop**
**Issue**: If tool call fails, agent returns error but no retry logic
- No exponential backoff
- No fallback tools
- Agent might give up too easily

**Recommendation**:
- Implement retry strategy with backoff
- Provide fallback tools when primary fails

### 6. **Incomplete Inbox System**
**Issue**: `direction/inbox.txt` exists but system never reads it
- Human instructions not surfaced to agents
- No feedback loop for humans

**Recommendation**:
- Parse inbox on each run
- Route human instructions to appropriate agent role
- Write agent responses back to inbox

---

## PLANNING / TASK TRACKING DEFECTS

### 1. **No Active Task State Machine**
- Tasks only have status = "done" or "pending"
- No "in_progress", "blocked", "review", "failed" states
- Can't track what agent is currently working on

### 2. **No Task Ownership**
- Tasks not assigned to specific agent roles
- All agents see same backlog; no dedicated queues

### 3. **Duplicates in Backlog**
- Same "plan improvements", "design changes", "implement improvements" goals repeated 10+ times
- No deduplication or archival

### 4. **No Metrics or Success Criteria**
- Goals are text strings, no measurable outcomes
- Can't tell if a goal was achieved

---

## AGENT COLLABORATION DEFECTS

### 1. **No Handoff Protocol**
- Planner finishes → Implementer doesn't know what to implement
- Implementer finishes → Tester doesn't know what to test
- No shared "work inbox" or message format

### 2. **No Shared Context**
- Each agent runs independently
- No way for Designer to see Planner's notes
- No shared decision log or ADR (Architecture Decision Record)

### 3. **No Conflict Resolution**
- If two agents try to commit same file, whoever commits last wins
- No merge conflict detection or resolution

### 4. **Run Logs Don't Cross-Reference**
- Each run is isolated JSON file
- No way to correlate: designer decision → implementer action → tester verification

---

## OPERATIONAL DEFECTS

### 1. **Runs Directory Bloat**
- 500+ run JSON files, no cleanup
- No archive or retention policy
- Makes it hard to find recent runs

### 2. **No Logging Level Control**
- All print() statements go to stdout
- No structured logging (JSON, levels, timestamps)
- No way to filter logs

### 3. **No Metrics Collection**
- How many repos indexed?
- How many tool calls per run?
- How many errors?
- Unknown

---

## CODE QUALITY DEFECTS

### 1. **Bare except() clauses** (indexer.py line 64)
```python
except Exception:
    return False
```
- Swallows all exceptions silently
- Could hide bugs
- Fix: Specific exception handling + logging

### 2. **No Type Hints** (except Python 3.10+ union syntax in agent.py)
- Hard for IDE to help
- Hard for humans to understand signatures
- Fix: Add mypy-compatible hints

### 3. **Magic Numbers**
- 2000 chars per chunk (why?)
- 200 char overlap (why?)
- 512 KB file limit (why?)
- Fix: Move to config with documentation

### 4. **No Docstrings** (most functions)
- Unclear what functions do
- No parameter descriptions
- Fix: Add comprehensive docstrings

### 5. **Path Handling Inconsistencies**
- `indexer.py` uses `Path` + `os.path.relpath`
- `tools.py` uses `Path` correctly
- `pando_queue.py` uses `Path`
- Some inconsistency in path normalization

---

## PRIORITY FIXES (Implement First)

1. **Add missing imports** (indexer.py) - blocks execution
2. **Add collection.add() calls** (indexer.py) - blocks search
3. **Fix tool argument docs/validation** - blocks agent cooperation
4. **Add JSON exception handling** - improve robustness
5. **Add agent collaboration layer** - enable team workflows
6. **Add task tracking state machine** - enable planning
7. **Add post-commit indexing** - keep search results fresh

---

## ARCHITECTURE IMPROVEMENTS (Higher Level)

1. Create `agent_roles.py` with Designer, Planner, Implementer, etc.
2. Create `message_bus.py` for inter-agent communication
3. Create `task_engine.py` with state machine and assignment
4. Create `observability.py` with structured logging and metrics
5. Refactor run logs into structured event stream (not JSON files)
6. Add request tracing throughout system
