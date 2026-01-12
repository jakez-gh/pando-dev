# Pando System Design

## Overview

Pando is an autonomous development team that operates 24/7 across multiple repositories, making intelligent decisions, proposing improvements, and executing work while staying in constant two-way communication with users.

## Core Principles

1. **Confidence-Based Autonomy**: Decisions range from EXECUTE (high confidence) → PROPOSE (medium) → ASK (low confidence)
2. **Non-Blocking Communication**: Users answer questions asynchronously; Pando continues work with assumed answers
3. **Multi-Terminal Parallelism**: 8+ parallel terminal workers execute tasks simultaneously
4. **Event-Sourced State**: All decisions logged in JSONL for full audit trail and crash recovery
5. **Self-Improvement**: Detects code duplication, performance issues, proposes enhancements via PR branches

## Architecture

```
┌─ DIRECTION/INBOX SYSTEM ─────────────────────┐
│ User submits directions via web UI/API       │
│ Direction → Parsed → Tasks → Work Queue      │
└────────────┬─────────────────────────────────┘
             │
             ▼
┌─ TASK ENGINE ────────────────────────────────┐
│ Priority calculation, dependency tracking    │
│ State machine: PENDING → ASSIGNED → DONE     │
│ Persistent JSONL storage                     │
└────────────┬─────────────────────────────────┘
             │
             ▼
┌─ AUTONOMY ENGINE ────────────────────────────┐
│ Task similarity analysis                     │
│ Confidence calculation (task + resources)    │
│ Decision: EXECUTE | PROPOSE | ASK | ESCALATE│
│ Outcome recording & calibration              │
└────────────┬─────────────────────────────────┘
             │
             ▼
┌─ AGENT COORDINATOR ──────────────────────────┐
│ Assigns work to 8 parallel agents            │
│ Monitors execution, collects results         │
│ Detects work completion, exits gracefully    │
│ Routes escalations to user                   │
└────────────┬─────────────────────────────────┘
             │
             ▼
┌─ FLASK API / WEBSOCKET ──────────────────────┐
│ REST endpoints for task/question management  │
│ WebSocket broadcasts for real-time updates   │
│ Two-way communication with frontend          │
└──────────────────────────────────────────────┘
```

## Decision Formula

```
confidence = (similarity × 0.3 + prerequisites × 0.3 + 
              capability × 0.25 + resources × 0.15) × risk_multiplier

If confidence > 0.85:  EXECUTE (do it autonomously)
If confidence 0.65-0.85: PROPOSE (create branch, ask permission)
If confidence 0.45-0.65: BRANCH (experiment, ask to merge)
If confidence < 0.45: ASK (blocking question, wait for answer)
On critical risk: ESCALATE (immediately notify user)
```

## Data Persistence

**JSONL Files (Append-Only Event Logs):**
- `pando_directions.jsonl` - All user directions received
- `pando_tasks.jsonl` - Task lifecycle events
- `pando_questions.jsonl` - Questions posed to user
- `pando_decisions.jsonl` - Autonomy engine decisions
- `message_logs/` - Agent communication audit trail

**JSON Files (Metadata):**
- `pando_repos.json` - Repository configurations
- `index_state.json` - Indexing status

## Key Flows

### Direction → Task → Execution
1. User submits direction: "Refactor authentication module"
2. Direction API parses into tasks
3. Task Engine creates work items, prioritizes
4. Autonomy Engine analyzes task, calculates confidence
5. Agent Coordinator assigns to idle agent
6. Agent executes, reports results
7. Results stored, user notified via dashboard

### Non-Blocking Question
1. Task has ambiguity (e.g., "Use async or sync?")
2. Autonomy Engine creates Question with assumed_answer
3. Task continues with assumption
4. User answers when convenient
5. If answer differs from assumption, task re-evaluated
6. Results adjusted as needed

### Self-Improvement Proposal
1. Code scanning detects duplication
2. Autonomy Engine confidence < 0.7 (needs approval)
3. Creates feature branch with improvement
4. Poses question: "Should we refactor X?"
5. If approved, creates PR
6. If rejected, closes branch

## Configuration

Edit `config.py`:
- `CONFIDENCE_THRESHOLD_EXECUTE` - When to autonomously execute
- `CONFIDENCE_THRESHOLD_PROPOSE` - When to propose changes
- `TERMINAL_COUNT` - Number of parallel agents (default 8)
- `MODEL_NAME` - LLM model to use
- `MAX_TASK_SIZE_KB` - How much code to analyze at once

## Monitoring & Debugging

```bash
# Real-time dashboard
python interface.py monitor

# View direction queue
cat direction/inbox.txt

# Check task status
grep "task_complete" pando_tasks.jsonl

# Debug decisions
grep "decision_type" pando_decisions.jsonl

# Agent communication log
tail -f message_logs/

# System health
curl http://localhost:5000/api/status
```

## Performance Notes

- **Decision latency**: ~100-500ms per task
- **Task throughput**: 3-8 tasks/minute per agent
- **Memory usage**: ~200-500MB with full history
- **Disk usage**: ~10-50MB per day of operation

## Security & Safety

- All code changes go through PR review process
- Critical operations require user approval
- Full audit trail in JSONL
- Graceful degradation on errors
- No automatic destructive operations (deletes require approval)
