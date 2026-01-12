# Pando - Getting Started

## Quick Start

**Prerequisites:** Python 3.10+, venv

```bash
# 1. Activate virtual environment
./venv/Scripts/activate  # Windows

# 2. Start the Flask backend
python pando_gui/backend/app.py
# Server runs on http://localhost:5000

# 3. Start an agent
python agent.py
# Agent waits for tasks, executes, reports results

# 4. Submit directions/tasks
# Use the web UI at http://localhost:5000 or POST to /api/directions
```

## How to Send Directions to Pando

### Web UI (Recommended)
1. Open http://localhost:5000
2. Go to "Directions" panel
3. Type your direction and submit
4. Pando will parse and create tasks automatically

### API
```bash
curl -X POST http://localhost:5000/api/directions \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Review and refactor the authentication module",
    "priority": "high",
    "deadline": null
  }'
```

## System Architecture

- **Core System**: `pando_core/` - Autonomy engine, task system, communication
- **Backend API**: `pando_gui/backend/app.py` - REST + WebSocket endpoints
- **Frontend**: React dashboard (in `pando_gui/frontend/` when ready)
- **Agents**: `agent.py` - Autonomous worker processes
- **Persistence**: JSONL files for state, JSON for metadata

## Key Files

| File | Purpose |
|------|---------|
| `agent.py` | Main agent entry point, requests and executes work |
| `agent_coordinator.py` | Coordinates multiple agents, detects completion |
| `task_engine.py` | Task lifecycle and priority management |
| `message_bus.py` | Event pub/sub for inter-agent communication |
| `pando_gui/backend/app.py` | Flask API server |
| `config.py` | System configuration |

## Common Tasks

**Check system status:**
```bash
curl http://localhost:5000/api/status
```

**Get pending tasks:**
```bash
curl http://localhost:5000/api/tasks
```

**Answer a question:**
```bash
curl -X POST http://localhost:5000/api/questions/Q_123/answer \
  -H "Content-Type: application/json" \
  -d '{"answer": "Yes, use async patterns"}'
```

## Monitoring

**View active agents:**
```bash
python interface.py monitor
```

**Check message logs:**
```bash
tail -f message_logs/*.jsonl
```

## Next Steps

1. Submit a direction via web UI
2. Watch `agent.py` process it
3. Monitor results in dashboard
4. Pando will ask for clarification if needed
5. System exits when work is complete
