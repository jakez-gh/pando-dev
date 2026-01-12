# Pando Autonomous Development System - Architecture v2

**Status**: Design Phase 1 Complete  
**Version**: 2.0 (Full Autonomy Model)  
**Date**: January 12, 2026  
**Target Hardware**: 2060 GPU, 16GB RAM + Multi-Terminal  

---

## Executive Summary

Pando transitions from a coordinated task executor to a **fully autonomous development team** that:
- Works **continuously** with multiple parallel tasks
- Makes **independent decisions** within defined boundaries
- **Communicates asynchronously** with users without blocking work
- Manages **multiple repositories** and creates **PR workflows**
- **Self-improves** by proposing enhancements
- Coordinates across **multiple terminals** for parallelism
- Delegates tasks and escalates only when uncertain

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PANDO AUTONOMOUS SYSTEM                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           PANDO CORE DECISION ENGINE                     │  │
│  │  (autonomy_engine.py)                                    │  │
│  │  - Decision tree + confidence scoring                    │  │
│  │  - Proposal generation                                   │  │
│  │  - Risk assessment                                       │  │
│  │  - Escalation logic                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│           ↓                           ↓                         │
│  ┌──────────────────────┐  ┌──────────────────────────────┐    │
│  │  TASK SYSTEM         │  │  ASYNC COMMUNICATION         │    │
│  │  (task_system.py)    │  │  (async_comm.py)             │    │
│  │                      │  │                              │    │
│  │ • Self-assignment    │  │ • User Q&A queue             │    │
│  │ • Work prioritization│  │ • Non-blocking responses     │    │
│  │ • Complexity scoring │  │ • Decision backlog           │    │
│  │ • Parallel tracking  │  │ • Context preservation       │    │
│  └──────────────────────┘  └──────────────────────────────┘    │
│           ↓                           ↓                         │
│  ┌──────────────────────┐  ┌──────────────────────────────┐    │
│  │  REPO MANAGER        │  │  TERMINAL COORDINATOR        │    │
│  │  (repo_manager.py)   │  │  (terminal_coord.py)         │    │
│  │                      │  │                              │    │
│  │ • Multi-repo scanning│  │ • 4-8 parallel terminals     │    │
│  │ • gh cli integration │  │ • Task distribution          │    │
│  │ • Branch management  │  │ • Output aggregation         │    │
│  │ • PR creation/review │  │ • Cross-terminal sync        │    │
│  │ • Merge strategy     │  │                              │    │
│  └──────────────────────┘  └──────────────────────────────┘    │
│           ↓                           ↓                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           MESSAGE BUS + STATE PERSISTENCE                │  │
│  │  (message_bus.py + pando_state.jsonl)                    │  │
│  │  - All decisions logged                                  │  │
│  │  - State recovery on restart                             │  │
│  │  - Audit trail for all operations                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│           ↓                                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           WEB GUI + COPILOT INTERFACE                    │  │
│  │  (flask_backend.py + react_frontend/)                    │  │
│  │  - Real-time dashboard                                   │  │
│  │  - Approval workflows                                    │  │
│  │  - Q&A interface                                         │  │
│  │  - Performance metrics                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Pando Autonomous Decision Engine (`autonomy_engine.py`)

**Purpose**: Make independent decisions within safety boundaries

**Decision Tree**:
```
Task assigned to Pando
├─ Is this a known task type?
│  ├─ YES → Confidence score > 80%?
│  │  ├─ YES → EXECUTE autonomously
│  │  └─ NO  → Propose approach, ask user → continue on branch
│  └─ NO  → New task type
│     ├─ Can research solve it?
│     │  ├─ YES → RESEARCH, then propose
│     │  └─ NO  → ASK user for guidance
│
├─ During execution, discover issue?
│  ├─ Minor bug (not in scope)?
│  │  ├─ Fix complexity < 30 min?
│  │  │  ├─ YES → Fix on dedicated branch, propose merge
│  │  │  └─ NO  → Create issue, log, continue
│  │  └─ Fix is critical?
│  │     ├─ YES → Fix first, document decision
│  │     └─ NO  → Propose in separate task
│  │
│  └─ Better approach discovered?
│     ├─ Improvement > 20%?
│     │  ├─ YES → Branch, implement, propose
│     │  └─ NO  → Log as minor optimization
│
├─ Task blocked?
│  ├─ Waiting for info?
│  │  └─ Add to pending queue, work on something else
│  ├─ Waiting for user decision?
│  │  └─ Create branch with assumption, continue
│  └─ Technical deadlock?
│     └─ Escalate to Copilot, branch with workaround
│
└─ Task complete?
   ├─ Quality check: tests pass, code reviewed?
   │  ├─ YES → Request approval, create PR
   │  └─ NO  → Continue polishing
   └─ Similar work elsewhere?
      └─ LOG for refactoring opportunity
```

**Data Structure**:
```python
class Decision:
    task_id: str
    decision_type: str  # EXECUTE, PROPOSE, ASK, BRANCH, ESCALATE
    confidence: float  # 0-1
    reasoning: str
    alternatives: List[str]
    risks: List[str]
    timestamp: datetime
    context: Dict  # Full task context
```

**Confidence Scoring Formula**:
```
confidence = (
    (task_similarity * 0.3) +           # How similar to past tasks
    (prerequisite_ready * 0.3) +        # Are all deps available?
    (model_capability * 0.25) +         # Can LLM handle this?
    (resource_available * 0.15)         # GPU/RAM/time available?
) * risk_multiplier
```

**Risk Multiplier**:
- Destructive operation (merge, delete)? × 0.7
- External dependency? × 0.8
- Requires user data? × 0.5
- Otherwise: × 1.0

---

### 2. Pando Task System (`task_system.py`)

**Purpose**: Pando manages its own work queue with self-assignment

**Task Categories**:
```
PRIMARY (User-requested):
  - New feature
  - Bug fix
  - Enhancement
  - Documentation
  - Investigation

SECONDARY (Self-generated):
  - Refactoring opportunity
  - Technical debt
  - Performance optimization
  - Test coverage gap
  - Dependency upgrade

MAINTENANCE:
  - Repository health check
  - Stale branch cleanup
  - Message log rotation
  - Performance profiling
```

**Priority Calculation**:
```
priority = (
    (urgency * 0.4) +              # User requested? Blocked task?
    (impact * 0.3) +               # How much does this help?
    (effort_ratio * 0.2) +         # High value/effort ratio?
    (blocker_count * 0.1)          # How many tasks does it unblock?
) * category_multiplier

category_multiplier:
  PRIMARY: 1.0
  SECONDARY: 0.6 (only if PRIMARY queue empty for 1 hour)
  MAINTENANCE: 0.2 (only if idle)
```

**Self-Assignment Logic**:
```
If work is available:
  1. Calculate priority for each task
  2. Select highest priority
  3. Assign to self with confidence score
  4. If confidence < 60%: create branch, ask Copilot for guidance
  5. If 60-80%: branch with assumptions, notify Copilot
  6. If > 80%: execute on working branch

Track metrics:
  - completion_rate (%)
  - quality_score (0-100)
  - time_to_completion (minutes)
  - escalation_rate (%)
```

**Work Distribution Across Terminals**:
```
Terminal 1: Primary development task
Terminal 2: Secondary development task (if parallel)
Terminal 3: Repository scans + background work
Terminal 4: Testing + validation
Terminal 5-8: Parallel branches if needed
```

---

### 3. Async User Communication (`async_comm.py`)

**Purpose**: Users can ask questions, give guidance without blocking Pando's work

**Question Queue Structure**:
```
pending_questions = [
    {
        id: "q_20260112_001",
        timestamp: datetime,
        content: "Should we use FastAPI or Flask?",
        pando_context: {
            current_task: "build_api_server",
            blocking: false,  # Pando can continue
            assumed_decision: "use FastAPI, we'll change if needed"
        },
        priority: "high",
        deadline: null,  # null = whenever you get to it
        status: "pending"
    }
]
```

**Response Processing**:
```
1. User answers question
2. Response queued to Pando
3. Pando notes decision in current branch
4. If contradicts assumption: rebase branch, adjust
5. Continue work

Example:
  Q: "FastAPI or Flask?"
  Pando assumed: "FastAPI, branch: feature/api-fastapi"
  User responds: "Actually Flask"
  Pando action: "Rebase to feature/api-flask, adjust code"
  Continue immediately
```

**Guidance Channels**:
```
SYNC (blocking, urgent):
  - "STOP current work, fix X"
  - "Change direction to Y"
  
ASYNC (non-blocking):
  - "Consider approach Z" (noted, evaluated next opportunity)
  - "After this task, focus on W" (queued in task system)
  - "Question about X?" (answered when convenient)

PROPOSAL RESPONSE:
  - "Approve this PR"
  - "Modify and re-propose"
  - "Reject, here's why"
```

---

### 4. Multi-Repository Manager (`repo_manager.py`)

**Purpose**: Manage all repos in ~/dev and external clones

**Repository Discovery**:
```
1. Scan ~/dev folder
2. Identify all git repos
3. For each repo:
   - Read current branch
   - Count pending branches
   - Identify main/master branch
   - Track open PRs (if GitHub)
   - Check for uncommitted changes
4. Store in pando_repos.json
```

**Repository Operations**:
```
SCANNING:
  ├─ Identify issues/opportunities
  ├─ Search for similar code (cross-repo)
  ├─ Find dependency conflicts
  └─ Detect stale branches

BRANCHING:
  ├─ Feature: feature/description-YYYYMMDD
  ├─ Bugfix: fix/issue-number-YYYYMMDD
  ├─ Research: research/topic-YYYYMMDD
  ├─ Assumption: assume/decision-YYYYMMDD
  └─ All branch from: git checkout main && git pull

PR WORKFLOW:
  1. Code complete on branch
  2. Push to branch: git push origin feature/X
  3. Create PR: gh pr create --title "X" --body "..."
  4. Self-review using static analysis tool
  5. Request review from Reviewer Agent (separate agent)
  6. Reviewer Agent checks:
     - Code quality
     - Tests pass
     - No breaking changes
     - Aligned with requirements
  7. If approved: gh pr merge --squash
  8. Delete branch: git branch -D feature/X
  9. Update pando_repos.json
```

**External Repo Cloning**:
```
Use gh cli to:
  1. Clone: gh repo clone owner/repo ~/dev/repo
  2. Fetch latest: git fetch upstream
  3. Create working branches for modifications
  4. Create forks if contributing back
  5. Track cloned repos in external_repos.json
```

---

### 5. Multi-Terminal Coordinator (`terminal_coord.py`)

**Purpose**: Distribute work across 4-8 simultaneous terminals

**Terminal Roles**:
```
Terminal 1: PRIMARY DEVELOPMENT
  - Main feature/bugfix implementation
  - Code execution
  - Testing

Terminal 2: SECONDARY DEVELOPMENT (if work available)
  - Parallel task execution
  - Independent feature branch
  - May conflict merge if work incomplete

Terminal 3: BACKGROUND SCANNING
  - Repository health checks
  - Dependency updates
  - Code quality analysis
  - Proposal generation

Terminal 4: TESTING & VALIDATION
  - Test suite execution
  - Coverage analysis
  - Performance benchmarking
  - Integration testing

Terminal 5-8: PARALLEL BRANCHES
  - When exploring alternatives
  - When waiting for decisions
  - Example: "Implement with Approach A on Terminal 5, Approach B on Terminal 6"
```

**Work Distribution Algorithm**:
```
available_tasks = get_all_tasks()

for terminal in available_terminals:
    if terminal == PRIMARY:
        task = select_highest_priority(available_tasks)
        assign_to_terminal(terminal, task)
    elif terminal == SECONDARY:
        if len(available_tasks) > 1:
            task = select_second_priority(available_tasks)
            assign_to_terminal(terminal, task)
    elif terminal == BACKGROUND:
        scan_task = get_next_scan()
        assign_to_terminal(terminal, scan_task)
    elif terminal == TESTING:
        test_task = get_next_test()
        assign_to_terminal(terminal, test_task)

Coordination:
  - All terminals write to message_bus
  - State synchronized via pando_state.jsonl
  - Conflicts detected: escalate to decision engine
  - Output aggregated in GUI
```

---

### 6. Web GUI Architecture

**Stack**: Flask (Python backend) + React (TypeScript frontend) + WebSocket

**Backend**: `pando_gui.py`
```python
# Flask routes
GET  /api/status          → Current status, active tasks
GET  /api/tasks           → Task queue, priorities
GET  /api/questions       → Pending user questions
POST /api/answers/:id     → User answer to question
POST /api/approve/:pr     → Approve PR
POST /api/directive       → Give synchronous directive
GET  /api/repos           → Repository status
GET  /api/branches        → Branch activity
GET  /api/metrics         → Performance metrics
WS   /ws                  → WebSocket for real-time updates
```

**Frontend**: React components
```
Dashboard
├─ StatusCard
│  ├─ Current task (with progress bar)
│  ├─ Active terminals (count, tasks)
│  └─ System health
├─ TaskQueue
│  ├─ Upcoming tasks (by priority)
│  ├─ Drag to reorder (if needed)
│  └─ Quick add task
├─ PendingQuestions
│  ├─ List of awaiting user input
│  ├─ Input fields
│  └─ Quick response buttons
├─ RepositoryStatus
│  ├─ Active branches per repo
│  ├─ PR status
│  └─ Uncommitted changes alert
├─ TerminalMonitor
│  ├─ 4-8 terminal outputs (collapsible)
│  ├─ Real-time log streaming
│  └─ Terminal selection
└─ MetricsPanel
   ├─ Completion rate
   ├─ Quality score
   ├─ Time per task
   └─ Success rate by category
```

---

## Data Models

### pando_state.jsonl
```jsonl
{"timestamp":"2026-01-12T10:30:00Z","event":"system_start","pando_version":"2.0"}
{"timestamp":"2026-01-12T10:30:05Z","event":"task_assigned","task_id":"t_001","task":"implement_feature_x","priority":95,"confidence":0.85}
{"timestamp":"2026-01-12T10:31:00Z","event":"decision_made","decision":"EXECUTE","reasoning":"confidence > 0.8, similar task 92% match","branch":"feature/x-20260112"}
{"timestamp":"2026-01-12T10:35:00Z","event":"question_posed","q_id":"q_001","question":"Should we use caching library Y?","blocking":false,"assumed":"yes"}
{"timestamp":"2026-01-12T10:40:00Z","event":"user_response","q_id":"q_001","response":"Use library Y, good choice"}
{"timestamp":"2026-01-12T11:00:00Z","event":"pr_created","pr_id":"pr_001","branch":"feature/x-20260112","title":"Implement feature X"}
{"timestamp":"2026-01-12T11:05:00Z","event":"pr_approved","pr_id":"pr_001","by":"reviewer_agent"}
{"timestamp":"2026-01-12T11:06:00Z","event":"pr_merged","pr_id":"pr_001","branch":"feature/x-20260112"}
```

### pando_repos.json
```json
{
  "repositories": [
    {
      "name": "pando-dev",
      "path": "c:\\Users\\jake\\dev\\pando-dev",
      "type": "local",
      "main_branch": "main",
      "active_branches": [
        "feature/gui-dashboard-20260112",
        "fix/async-comm-deadlock-20260112"
      ],
      "open_prs": 2,
      "uncommitted_changes": false,
      "last_scan": "2026-01-12T11:00:00Z"
    }
  ],
  "external_repos": [
    {
      "name": "some-library",
      "original_url": "https://github.com/owner/some-library",
      "local_path": "c:\\Users\\jake\\dev\\some-library",
      "forked": false,
      "branches_for_contribution": []
    }
  ]
}
```

### pando_decisions.json
```json
{
  "decision_history": [
    {
      "id": "d_001",
      "timestamp": "2026-01-12T10:31:00Z",
      "task_id": "t_001",
      "decision_type": "EXECUTE",
      "confidence": 0.85,
      "reasoning": "Similar to previous task, high confidence in approach",
      "selected_approach": "approach_a",
      "alternatives_rejected": ["approach_b", "approach_c"],
      "outcome": "success",
      "actual_time": 35,
      "estimated_time": 40,
      "feedback": null
    }
  ],
  "feedback_loop": {
    "successful_decisions": 47,
    "failed_decisions": 3,
    "escalated_decisions": 5,
    "quality_score": 0.93,
    "confidence_calibration": 0.89
  }
}
```

---

## Decision Boundaries (Pando Autonomy Limits)

### AUTONOMOUS (No approval needed):
- [ ] Implement feature that's clearly specified, confidence > 85%
- [ ] Fix bug with clear reproduction, isolated scope
- [ ] Write tests, documentation, comments
- [ ] Optimize code (if passes all tests)
- [ ] Refactor (if passes all tests)
- [ ] Update dependencies (if no breaking changes, tests pass)
- [ ] Clean up dead code
- [ ] Organize imports, fix linting issues

### BRANCH + PROPOSE (Ask user approval):
- [ ] Implement when confidence 60-85%
- [ ] Change architecture or design
- [ ] Add new dependency
- [ ] Break backward compatibility
- [ ] Large refactoring
- [ ] Performance optimization > 10% gain (worth code review)
- [ ] Approach choice when multiple valid options exist

### ASK BEFORE (Blocking decision):
- [ ] Delete code/files
- [ ] Merge to main branch
- [ ] External API integration
- [ ] User-facing behavior change
- [ ] Anything outside my scope/expertise
- [ ] When confidence < 60%

### ESCALATE IMMEDIATELY:
- [ ] Security vulnerability
- [ ] Data loss risk
- [ ] License compliance question
- [ ] Complete blockers (can't proceed any direction)
- [ ] Requests outside my capabilities

---

## Workflow Examples

### Example 1: Normal Task Execution

```
STEP 1: User submits task
"Implement user authentication with JWT"

STEP 2: Pando analyzes
├─ confidence_score: 0.88 (done this 3x before)
├─ estimated_time: 2 hours
└─ prerequisites: ✓ Flask, ✓ PyJWT, ✓ Database ready

STEP 3: Pando decides
DECISION: EXECUTE (confidence > 0.85)

STEP 4: Pando executes on branch
Terminal 1: git checkout -b feature/jwt-auth-20260112
Terminal 1: [ writes code ]

STEP 5: Pando self-tests
Terminal 4: [ runs tests, checks coverage ]
Result: 12 tests pass, 95% coverage

STEP 6: Pando creates PR
Terminal 1: gh pr create --title "Feature: JWT authentication"

STEP 7: Reviewer Agent reviews
Reviewer: "Looks good, but add docstring to auth_required"

STEP 8: Pando addresses feedback
Terminal 1: [ adds docstring, commits ]

STEP 9: Reviewer approves
Reviewer: "Approved!"

STEP 10: Pando merges
Terminal 1: gh pr merge --squash
Terminal 1: git checkout main && git pull

TOTAL TIME: 2.5 hours (2 hours code + 0.5 hours review/iteration)
```

### Example 2: Uncertain Task with Parallel Exploration

```
STEP 1: User submits task
"Improve database query performance for large result sets"

STEP 2: Pando analyzes
├─ confidence_score: 0.65 (not clear which approach is best)
├─ alternatives: [pagination, caching, indexing, query optimization]
└─ decision: Cannot choose with confidence

STEP 3: Pando proposes multiple approaches
User question Q1: "Should I optimize with pagination or caching or both?"
Pando created branch: assume/pagination-first-20260112
Pando message: "I'll implement pagination first, we can add caching if needed"

STEP 4: Pando continues working on assumption
Terminal 1: Implements pagination on assume/pagination-first-20260112
Terminal 2: Researches caching strategy on assume/caching-research-20260112
Terminal 3: Analyzes existing queries for index opportunities

STEP 5: User responds while Pando is working
User: "Go with both pagination AND intelligent caching"
Pando message: "Got it, adjusting branch strategy..."

STEP 6: Pando rebases assumption branch
Terminal 1: Pivots to feature/pagination-caching-20260112
Terminal 1: Integrates caching research from Terminal 2
Terminal 1: Incorporates index suggestions from Terminal 3

STEP 7: Unified implementation
All work converges on main feature branch
Tests written, passing

STEP 8: PR, review, merge
Normal flow

RESULT: User guidance came in at 10 min mark, Pando had already 70% of solution path ready
```

### Example 3: Continuous Self-Improvement

```
PANDO BACKGROUND SCANNING (Terminal 3):

Scan 1: Finds 3 repos with similar utility functions
Proposal P1: "Consolidate repeated utility_functions into shared library"
Branch: refactor/shared-utils-20260112
Status: Proposed to user (non-blocking)

Scan 2: Detects 5 deprecated dependencies
Proposal P2: "Update 5 dependencies, all upgrades backward-compatible"
Branch: upgrade/dependencies-20260112
Status: Proposed to user

Scan 3: Analyzes performance logs
Proposal P3: "Caching would reduce API calls by 40%"
Branch: feature/caching-layer-20260112
Status: Proposed to user

USER AT THIS POINT:
- Still assigned primary task to Pando
- Sees 3 proposals
- Can approve/reject/delay any
- Pando continues primary task on Terminal 1
- Gets notified when each proposal is resolved
```

---

## Delegation Model (Copilot → Pando)

### Phase 1: Guided (Week 1)
- [ ] Copilot assigns specific tasks
- [ ] Copilot monitors all decisions
- [ ] Copilot corrects course if needed
- [ ] Pando gathers data on decision quality
- [ ] Success metric: > 80% autonomous decisions succeed

### Phase 2: Supervised (Week 2-3)
- [ ] Copilot sets decision boundaries
- [ ] Pando operates within boundaries
- [ ] Copilot reviews decisions retroactively
- [ ] Boundaries adjusted based on performance
- [ ] Success metric: > 90% autonomous decisions succeed, < 5% escalations

### Phase 3: Autonomous (Week 3+)
- [ ] Pando operates independently
- [ ] Copilot receives summaries
- [ ] Copilot intervenes only if metrics degrade
- [ ] Success metric: > 95% decision quality, system stable

---

## Recovery & Auditing

**State Recovery on Restart**:
```
1. Load pando_state.jsonl (full event log)
2. Replay state to last consistent point
3. Check for orphaned branches
4. Check for stuck terminals
5. Resume from last incomplete task
6. Notify user of recovery action
```

**Audit Trail**:
```
Every decision logged with:
  - What was decided
  - Why (reasoning)
  - Confidence score
  - Outcome (success/fail)
  - Time taken
  - User feedback

Enables:
  - Performance analysis
  - Decision quality calibration
  - Pattern discovery
  - Continuous improvement
```

---

## Success Metrics

**For Pando**:
- Task completion rate: > 90%
- Code quality (tests pass): > 95%
- Decision quality (succeed): > 90%
- Escalation rate: < 10%
- Avg time to completion: Decreasing trend

**For Copilot**:
- Hands-on time: Decreasing over 3 weeks
- Interventions needed: Decreasing
- Confidence in Pando: Increasing
- Success in automated tasks: > 95% by week 3

---

## Technology Stack

**Core**:
- Python 3.10+
- Ollama (local LLM, Llama 3.1 8B)
- SQLite (state DB)
- JSONL (event logs)

**Web GUI**:
- Flask (Python)
- React 18 (TypeScript)
- WebSocket (real-time updates)
- Chart.js (metrics visualization)

**Tools**:
- gh CLI (GitHub operations)
- git (version control)
- pytest (testing)

**Deployment**:
- Multi-terminal (8 parallel Windows terminals)
- Shared state via JSONL + SQLite
- Message bus for coordination
- WebSocket for GUI updates

---

## File Structure (Post-Implementation)

```
pando-dev/
├─ pando_core/
│  ├─ __init__.py
│  ├─ autonomy_engine.py (decision making)
│  ├─ task_system.py (work queue + self-assignment)
│  ├─ async_comm.py (user Q&A)
│  ├─ repo_manager.py (git + gh operations)
│  ├─ terminal_coord.py (multi-terminal)
│  └─ state_manager.py (persistence)
├─ pando_gui/
│  ├─ backend/
│  │  ├─ app.py (Flask main)
│  │  ├─ routes.py (API endpoints)
│  │  └─ websocket_handler.py
│  └─ frontend/
│     ├─ src/
│     │  ├─ components/
│     │  │  ├─ Dashboard.tsx
│     │  │  ├─ TaskQueue.tsx
│     │  │  ├─ QuestionPanel.tsx
│     │  │  ├─ RepositoryStatus.tsx
│     │  │  ├─ TerminalMonitor.tsx
│     │  │  └─ MetricsPanel.tsx
│     │  └─ App.tsx
│     └─ package.json
├─ pando_state.jsonl (event log)
├─ pando_repos.json (repo metadata)
├─ pando_decisions.json (decision history)
└─ config.json (Pando configuration)
```

---

## Next Phase: Implementation

See GUI_MOCKUPS.md for visual design.

Then: Build in this order
1. autonomy_engine.py + decision framework
2. task_system.py + self-assignment
3. async_comm.py + user interaction
4. repo_manager.py + git operations
5. terminal_coord.py + multi-terminal
6. GUI (Flask + React)
7. Integration + testing
8. Deployment to 8 terminals
