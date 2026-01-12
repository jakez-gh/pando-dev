# Pando Quick Start Guide

## What's New

### 4 New Core Systems
1. **message_bus.py** - Event-driven communication between agents
2. **task_engine.py** - Task lifecycle and state management  
3. **agent_coordinator.py** - Coordinates multiple agents, detects work completion
4. **interface.py** - CLI monitoring and control dashboard

### Key Capability
The system now **automatically exits when all work is done** instead of running forever.

## Quick Commands

### Monitor the System
```bash
python interface.py monitor
```
Real-time dashboard that updates every 2 seconds. Press Ctrl+C to exit.

### Run an Agent
```bash
python agent.py
```
Agent will:
- Register itself as an "implementer"
- Wait for tasks from the coordinator
- Execute them one by one
- Exit automatically when work is done

### Run the Background Worker
```bash
python pando_worker.py
```
Processes reindex jobs and publishes status messages.

### Quick System Status
```bash
python interface.py status
```
Shows: agent count, task progress, recent messages, system health.

### Add a Task
```bash
python interface.py
# Select option 6: Add task
```
Interactive prompt to create and assign work.

### View Recent Messages
```bash
python interface.py messages
```
Shows last 20 events from the message bus (what agents are doing).

## How It Works

```
┌──────────────────┐
│  interface.py    │  ← You monitor here
│ (the dashboard)  │
└────────┬─────────┘
         │
         ▼
    ┌─────────────────────────────────────────────┐
    │  Message Bus (event stream)                 │
    │  • agent_ready, task_assigned, task_complete│
    │  • reindex_started, reindex_complete        │
    └─────────────────────────────────────────────┘
         ▲
         │
    ┌────┴────────────────────────────────────┐
    │                                          │
    ▼                                          ▼
┌─────────────┐                        ┌──────────────────┐
│  agent.py   │◄───────────────────────│  coordinator.py  │
│ (worker)    │  task assignment       │ (work manager)   │
│             │──────────────────────► │                  │
│ executes    │   task complete        │ detects when     │
│ tools       │                        │ work is all done │
└─────────────┘                        └──────────────────┘
    ▲
    │
┌───┴──────────────┐
│  pando_queue.py  │
│  pando_worker.py │
│  indexer.py      │
│ (infrastructure) │
└──────────────────┘
```

## What Each Component Does

### agent.py
- **Now**: Registers with coordinator, asks for tasks, completes them, exits when done
- **Was**: Ran forever with hardcoded instructions

### coordinator.py (NEW)
- Tracks which agents are doing what
- Assigns tasks based on agent role
- **Detects when work is complete** (all tasks done + agents idle)
- Tells agents when to stop

### task_engine.py (NEW)
- Stores tasks with states: PENDING → ASSIGNED → IN_PROGRESS → DONE/FAILED
- Priority-based task assignment
- Persistent storage (tasks.jsonl)

### message_bus.py (NEW)
- All agents publish status updates
- Enables monitoring and auditing
- Saves message history to disk

### interface.py (NEW)
- Real-time dashboard for humans
- See agent status, tasks, messages
- Manually create tasks if needed
- Monitor mode refreshes every 2 seconds

## The Fix: No More Infinite Loops

**Before**:
```python
# Old way - infinite loop
while True:
    do_work()
    # Never exits!
```

**After**:
```python
# New way - exits when work done
coordinator = get_coordinator()
while coordinator.should_continue_running():
    task = coordinator.assign_work(agent_id)
    if task:
        complete_task(task)
        coordinator.task_complete(agent_id, task.id)
    # Loop exits when should_continue_running() returns False
```

## Fixed Bugs

✅ **JSON Corruption** - Index files can now recover from corruption  
✅ **Deadlocked Queues** - Stale locks are auto-cleaned every 5 minutes  
✅ **Lost Updates** - Atomic file operations prevent data loss  
✅ **Poor Error Handling** - Tool calls now retry with backoff  

## Data Files

New persistent storage:
- `tasks/tasks.jsonl` - All tasks and their states
- `message_logs/messages-*.jsonl` - Message history by date
- `coordinator_state.json` - Agent registration and status

## Troubleshooting

### Agent won't exit
```bash
python interface.py tasks
# If you see pending tasks, they need to be completed
```

### No agents showing
```bash
# Run: python agent.py
# Agent needs to be running to register
```

### Messages not appearing
```bash
# Check: ls message_logs/
# Messages are saved to messages-YYYY-MM-DD.jsonl
```

### Want to reset everything
```bash
rm tasks/tasks.jsonl
rm message_logs/*.jsonl
rm coordinator_state.json
```
Then start fresh: `python interface.py monitor`

## Architecture Summary

| Component | Purpose | Status |
|-----------|---------|--------|
| agent.py | Executes work | ✅ Enhanced |
| task_engine.py | Tracks tasks | ✅ NEW |
| coordinator.py | Assigns work, detects completion | ✅ NEW |
| message_bus.py | Event communication | ✅ NEW |
| interface.py | Human monitoring | ✅ NEW |
| pando_queue.py | Async job queue | ✅ Fixed |
| indexer.py | Code indexing | ✅ Fixed |
| pando_worker.py | Background processing | ✅ Enhanced |

## Next Steps

1. **Start monitoring**: `python interface.py monitor`
2. **Run an agent**: `python agent.py` (in another terminal)
3. **Add a task**: `python interface.py` → Select "Add task"
4. **Watch it complete**: Task moves from PENDING → ASSIGNED → IN_PROGRESS → DONE
5. **Agent exits**: When no more tasks, agent says "✓ ALL WORK COMPLETE" and stops

---

**Questions?** Check [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) for detailed documentation.
