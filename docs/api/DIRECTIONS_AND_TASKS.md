# Directions & Tasks API

## Overview

A **Direction** is a high-level request from the user. The system parses it into concrete **Tasks** and executes them autonomously.

## Direction API

### Submit a Direction

**POST** `/api/directions`

```json
{
  "text": "Review and optimize the database query layer",
  "priority": "high",
  "deadline": "2026-01-20",
  "context": "Performance is slow on reports"
}
```

**Response:**
```json
{
  "direction_id": "DIR_20260112_001",
  "status": "parsed",
  "tasks_created": 3,
  "tasks": [
    {
      "task_id": "T_001",
      "title": "Analyze database queries",
      "priority": "high",
      "status": "pending"
    },
    {
      "task_id": "T_002",
      "title": "Add query indexes",
      "priority": "high",
      "status": "pending"
    },
    {
      "task_id": "T_003",
      "title": "Write performance tests",
      "priority": "medium",
      "status": "pending"
    }
  ]
}
```

### Get Directions

**GET** `/api/directions`

Returns all directions and their status.

```json
{
  "total": 5,
  "directions": [
    {
      "direction_id": "DIR_20260112_001",
      "text": "Review and optimize database layer",
      "priority": "high",
      "status": "in_progress",
      "created_at": "2026-01-12T10:30:00Z",
      "tasks_completed": 2,
      "tasks_total": 3
    }
  ]
}
```

### Get Direction Details

**GET** `/api/directions/{direction_id}`

Shows the direction and all associated tasks.

## Task API

### Get Task Queue

**GET** `/api/tasks`

```json
{
  "pending": [
    {
      "task_id": "T_001",
      "title": "Review authentication module",
      "priority": 80,
      "status": "pending",
      "assigned_to": null,
      "estimated_minutes": 45
    }
  ],
  "assigned": [
    {
      "task_id": "T_002",
      "title": "Refactor admin routes",
      "priority": 70,
      "status": "in_progress",
      "assigned_to": "agent_1",
      "progress": 65
    }
  ],
  "completed": [
    {
      "task_id": "T_003",
      "title": "Add logging",
      "status": "done",
      "completed_at": "2026-01-12T09:45:00Z",
      "duration_minutes": 30
    }
  ]
}
```

### Get Task Details

**GET** `/api/tasks/{task_id}`

```json
{
  "task_id": "T_001",
  "title": "Review authentication module",
  "description": "Audit the auth system for security issues",
  "priority": 80,
  "status": "pending",
  "created_at": "2026-01-12T10:30:00Z",
  "direction_id": "DIR_001",
  "assigned_to": null,
  "category": "review",
  "estimated_minutes": 45,
  "dependencies": ["T_000"],
  "blockers": [],
  "questions": [
    {
      "question_id": "Q_042",
      "text": "Should we add 2FA support?",
      "assumed_answer": "Yes, preferred",
      "blocking_level": "non_blocking"
    }
  ]
}
```

### Complete a Task

**POST** `/api/tasks/{task_id}/complete`

```json
{
  "result": "Completed successfully",
  "notes": "Added XYZ improvements",
  "artifacts": [
    {
      "type": "pull_request",
      "url": "https://github.com/...",
      "branch": "feature/auth-review-20260112"
    }
  ]
}
```

## Web UI Components

### Directions Panel
- Shows all directions (pending, in-progress, completed)
- Submit new directions via text input
- View associated tasks and their status
- See progress bar per direction

### Tasks Queue
- Filter by: pending, assigned, completed
- Sort by: priority, created time, completion time
- Click to see details and questions
- Bulk operations: prioritize, reassign, cancel

### Real-Time Updates
- WebSocket updates on task status changes
- Question notifications appear immediately
- Direction progress updates live
- Agent activity stream shows what's happening

## Direction Parsing

The system automatically parses directions into tasks:

**Input:** "Refactor the payment module and add Stripe integration tests"

**Parsed Tasks:**
1. Analyze payment module code
2. Create refactoring plan
3. Refactor payment logic
4. Add Stripe integration tests
5. Run tests and verify
6. Create PR and request review

Each task gets appropriate priority, dependencies, and estimated effort.

## Priority Levels

| Level | Value | Use Case |
|-------|-------|----------|
| CRITICAL | 100 | Security, outages, blockers |
| HIGH | 80 | Features, important bugs |
| MEDIUM | 50 | Improvements, tech debt |
| LOW | 20 | Nice-to-haves, exploration |

## Status Progression

```
pending → assigned → in_progress → review → done
                        ↓
                      failed (with retry)
                        ↓
                      blocked (waiting for user)
```

## Examples

### Example 1: Code Review Direction

```bash
curl -X POST http://localhost:5000/api/directions \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Review the notification system for security issues",
    "priority": "high"
  }'
```

### Example 2: Feature Direction

```bash
curl -X POST http://localhost:5000/api/directions \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Add dark mode support to the web UI",
    "priority": "medium",
    "deadline": "2026-01-25"
  }'
```

### Example 3: Bug Fix Direction

```bash
curl -X POST http://localhost:5000/api/directions \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Fix the memory leak in the background worker and add tests",
    "priority": "critical",
    "context": "OOM errors reported in production"
  }'
```
