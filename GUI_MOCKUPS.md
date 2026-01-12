# Pando GUI Design Mockups & Interaction Flows

**Version**: 2.0  
**Status**: Design Phase 1  
**Technology**: Flask + React + WebSocket  

---

## Main Dashboard (Default View)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ PANDO AUTONOMOUS DEVELOPMENT SYSTEM                              127.0.0.1:5000 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─ STATUS ─────────────────────────────────────────────────────────────┐  │
│  │                                                                      │  │
│  │  Current Task: "Implement JWT authentication"        [████████░░] 75% │  │
│  │  Time Elapsed: 1h 23m                                  Est: 30m left  │  │
│  │                                                                      │  │
│  │  Active Terminals: 4/8                   System Health: ✓ OPTIMAL   │  │
│  │  ├─ Terminal 1: feature/jwt-auth-20260112 [RUNNING]                 │  │
│  │  ├─ Terminal 2: [IDLE - waiting for work]                           │  │
│  │  ├─ Terminal 3: [SCANNING repositories...]                          │  │
│  │  └─ Terminal 4: [TESTING feature/jwt-auth]                          │  │
│  │                                                                      │  │
│  │  Confidence Level: 0.88 (High) | Decision Quality: 92%              │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ PENDING USER ACTIONS ────────────────────────────────────────────────┐  │
│  │                                                                      │  │
│  │  [⚠] Question: Should we use Redis or in-memory caching?           │  │
│  │      └─ Task: feature/jwt-auth-20260112 (non-blocking)             │  │
│  │      └─ Assumed: in-memory for now, switch if needed               │  │
│  │                                                                      │  │
│  │      [ Redis  ]  [ In-memory  ]  [ Let me decide later ]           │  │
│  │                                                                      │  │
│  │  [→] Proposal: Consolidate 3 shared utilities                       │  │
│  │      └─ Branch: refactor/shared-utils-20260112                     │  │
│  │      └─ Improvement: Reduces duplication by 35%                    │  │
│  │                                                                      │  │
│  │      [ Approve  ]  [ Review code  ]  [ Defer  ]                   │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ NEXT IN QUEUE ───────────────────────────────────────────────────────┐  │
│  │                                                                      │  │
│  │  1. [⭐⭐⭐⭐⭐] Add API rate limiting         Est: 2h    (assigned)   │  │
│  │  2. [⭐⭐⭐⭐⭐] Write integration tests        Est: 1.5h  (queued)    │  │
│  │  3. [⭐⭐⭐⭐  ] Update documentation          Est: 45m   (queued)    │  │
│  │  4. [⭐⭐⭐    ] Refactor database queries    Est: 3h    (proposed)  │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ REPOSITORY STATUS ───────────────────────────────────────────────────┐  │
│  │                                                                      │  │
│  │  pando-dev           │ 2 active branches │ 1 open PR  │ Clean      │  │
│  │  my-api-server       │ 3 active branches │ 0 open PRs │ Clean      │  │
│  │  utils-library       │ 1 active branch   │ 2 open PRs │ Clean      │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  [ TABS ] Status │ Tasks │ Questions │ Repos │ Terminals │ Metrics │ Logs  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Terminal Monitor (Collapsible)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ PANDO AUTONOMOUS DEVELOPMENT SYSTEM                              127.0.0.1:5000 │
├──────────────────────────────────────────────────────────────────────────────┤
│  [ TABS ] Status │ Tasks │ Questions │ Repos │ TERMINALS │ Metrics │ Logs    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─ TERMINAL 1: Development [▼] ────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  $ git checkout -b feature/jwt-auth-20260112                     │  │
│  │  Switched to new branch 'feature/jwt-auth-20260112'             │  │
│  │  $ python -m pytest test_jwt_auth.py -v                         │  │
│  │  test_valid_token_decode ... PASS                               │  │
│  │  test_expired_token_rejection ... PASS                          │  │
│  │  test_invalid_signature ... PASS                                │  │
│  │  ═══════════════════════════════════════════════════════════   │  │
│  │  3 passed in 0.45s ✓                                            │  │
│  │  $                                                               │  │
│  │                                                                    │  │
│  │  [ ⬆ Scroll up  |  Auto-scroll: ON  |  Export log ]            │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ TERMINAL 2: Idle [▼] ────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  [IDLE - awaiting next task]                                     │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ TERMINAL 3: Scanning [▼] ────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  [SCANNING] pando-dev... found 45 Python files                   │  │
│  │  [ANALYSIS] Checking for code duplication... 3% found            │  │
│  │  [PROPOSAL] Consolidate utility functions (refactor-utils)      │  │
│  │  [SCANNING] my-api-server... found 120 Python files              │  │
│  │                                                                    │  │
│  │  [ ⬆ Scroll up  |  Auto-scroll: ON  |  Export log ]            │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ TERMINAL 4: Testing [▼] ────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  $ pytest test_jwt_auth.py::test_refresh_token -v               │  │
│  │  test_refresh_token_generates_new_token ... PASS                 │  │
│  │  test_refresh_token_updates_expiry ... PASS                      │  │
│  │  $ coverage report                                               │  │
│  │  Name                  Stmts   Miss  Cover                       │  │
│  │  jwt_auth.py             45      2    95%                        │  │
│  │  ─────────────────────────────────────────────────────────       │  │
│  │  TOTAL                    45      2    95%                        │  │
│  │                                                                    │  │
│  │  [ ⬆ Scroll up  |  Auto-scroll: ON  |  Export log ]            │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ TERMINAL 5-8: [Collapsed] ───────────────────────────────────────────┐  │
│  │  [ Expand to view additional terminals ]                         │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  [ Collapse All ]  [ Expand All ]  [ Auto-scroll: ALL ]  [ Clear logs ]    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Questions & Decisions Panel

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ PANDO AUTONOMOUS DEVELOPMENT SYSTEM                              127.0.0.1:5000 │
├──────────────────────────────────────────────────────────────────────────────┤
│  [ TABS ] Status │ Tasks │ QUESTIONS │ Repos │ Terminals │ Metrics │ Logs    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─ PENDING DECISIONS (User Input Required) ──────────────────────────────┐  │
│  │                                                                    │  │
│  │  Q1: Should we use Redis or in-memory caching?                   │  │
│  │      Time: 2 minutes ago                                          │  │
│  │      Task: "Implement JWT authentication"                         │  │
│  │      Blocking: NO (Pando assumed: in-memory)                     │  │
│  │      Branch: feature/jwt-auth-20260112                           │  │
│  │                                                                    │  │
│  │      Pando's assumption: "I'll use in-memory caching with     │  │
│  │      LRU eviction for performance. We can switch to Redis    │  │
│  │      if scalability becomes an issue."                        │  │
│  │                                                                    │  │
│  │      [ Redis (distributed)  ]                                   │  │
│  │      [ In-memory LRU (fast)  ]                                  │  │
│  │      [ Hybrid approach      ]                                   │  │
│  │      [ Discuss with Pando   ]                                  │  │
│  │                                                                    │  │
│  │      Pando will: Continue development, integrate your choice    │  │
│  │                                                                    │  │
│  ├────────────────────────────────────────────────────────────────┤  │
│  │                                                                    │  │
│  │  Q2: Architecture: REST-only or REST+WebSocket?                 │  │
│  │      Time: 8 minutes ago                                         │  │
│  │      Task: "Design API server"                                   │  │
│  │      Blocking: YES (Cannot proceed without decision)             │  │
│  │      Branch: feature/api-design-20260112 [PAUSED]                │  │
│  │                                                                    │  │
│  │      Pando's note: "I have 2 branches ready to go. REST-only     │  │
│  │      is simpler but limits real-time features. WebSocket adds    │  │
│  │      complexity but enables live updates. What's more           │  │
│  │      important for your use case?"                              │  │
│  │                                                                    │  │
│  │      [ REST-only (simpler)          ]                           │  │
│  │      [ REST + WebSocket (real-time) ]                           │  │
│  │      [ Let me check requirements    ]                           │  │
│  │                                                                    │  │
│  │      Note: Pando paused work, working on other tasks             │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ RESOLVED DECISIONS ──────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  ✓ Q: Use PostgreSQL or SQLite?                                  │  │
│  │    You answered: PostgreSQL                                       │  │
│  │    Pando action: Updated feature/database-20260111 branch        │  │
│  │    PR #5 created and approved                                     │  │
│  │                                                                    │  │
│  │  ✓ Q: Framework: Flask or FastAPI?                               │  │
│  │    You answered: FastAPI                                          │  │
│  │    Pando action: Rebased to feature/fastapi-20260111              │  │
│  │    PR #4 merged                                                   │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  [ Filter: All │ Pending │ Blocking │ Resolved ]  [ Clear history ]       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Task Queue Manager

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ PANDO AUTONOMOUS DEVELOPMENT SYSTEM                              127.0.0.1:5000 │
├──────────────────────────────────────────────────────────────────────────────┤
│  [ TABS ] Status │ TASKS │ Questions │ Repos │ Terminals │ Metrics │ Logs    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─ NEW TASK ────────────────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  Description: [ Type task description or paste requirement ]    │  │
│  │                                                                    │  │
│  │  Priority: [⭐⭐⭐⭐⭐ 5 (Highest) ▼]                           │  │
│  │                                                                    │  │
│  │  Estimated Time: [ 2 hours        ▼]                           │  │
│  │                                                                    │  │
│  │  Dependency: [   - None -          ▼]                          │  │
│  │                                                                    │  │
│  │  [ + Add Task ]  [ Clear ]                                       │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ ACTIVE & QUEUED ──────────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  [ACTIVE] ⭐⭐⭐⭐⭐ Implement JWT authentication                  │  │
│  │           Progress: ████████░░ 75%  │  Elapsed: 1h 23m           │  │
│  │           Branch: feature/jwt-auth-20260112                      │  │
│  │           Terminal: 1 (dev) + 4 (testing)                        │  │
│  │           [ Cancel ] [ Pause ] [ View details ]                  │  │
│  │                                                                    │  │
│  ├────────────────────────────────────────────────────────────────┤  │
│  │                                                                    │  │
│  │  [NEXT] ⭐⭐⭐⭐⭐ Add API rate limiting                           │  │
│  │         Est: 2 hours  │  Will start when: JWT task completes    │  │
│  │         [ Details ] [ Reschedule ] [ Delete ]                   │  │
│  │                                                                    │  │
│  ├────────────────────────────────────────────────────────────────┤  │
│  │                                                                    │  │
│  │  [QUEUED] ⭐⭐⭐⭐⭐ Write integration tests                        │  │
│  │           Est: 1.5 hours  │  Depends on: JWT authentication    │  │
│  │           [ Details ] [ Reschedule ] [ Delete ]                 │  │
│  │                                                                    │  │
│  ├────────────────────────────────────────────────────────────────┤  │
│  │                                                                    │  │
│  │  [QUEUED] ⭐⭐⭐⭐ Update documentation                           │  │
│  │           Est: 45 min  │  Depends on: Rate limiting implemented│  │
│  │           [ Details ] [ Reschedule ] [ Delete ]                 │  │
│  │                                                                    │  │
│  ├────────────────────────────────────────────────────────────────┤  │
│  │                                                                    │  │
│  │  [PROPOSED] ⭐⭐⭐ Refactor database queries                      │  │
│  │             Est: 3 hours  │  Status: Waiting for approval       │  │
│  │             Branch: refactor/db-queries-20260112                │  │
│  │             [ Approve ] [ Review ] [ Reject ]                  │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ STATISTICS ───────────────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  Total tasks created: 47                                          │  │
│  │  Completed today: 12                                              │  │
│  │  Avg completion time: 1h 45m                                      │  │
│  │  Success rate: 94%                                                │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  [ Filter: Active │ Next │ Queued │ Proposed │ All ]  [ Export ]          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Repository & Branch Manager

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ PANDO AUTONOMOUS DEVELOPMENT SYSTEM                              127.0.0.1:5000 │
├──────────────────────────────────────────────────────────────────────────────┤
│  [ TABS ] Status │ Tasks │ Questions │ REPOS │ Terminals │ Metrics │ Logs    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─ REPOSITORIES ─────────────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  pando-dev ✓ Clean                                               │  │
│  │  ├─ Main branch: main (last pull: 5m ago)                       │  │
│  │  ├─ Active branches:                                             │  │
│  │  │  ├─ feature/jwt-auth-20260112 (IN PROGRESS) [Terminal 1]    │  │
│  │  │  ├─ feature/api-rate-limit-20260112 (PROPOSED) [Terminal 2]  │  │
│  │  │  └─ refactor/shared-utils-20260112 (AWAITING APPROVAL)       │  │
│  │  ├─ Open PRs: 2                                                  │  │
│  │  │  ├─ [draft] Consolidate utilities (refactor/shared-utils)    │  │
│  │  │  └─ Review needed: JWT auth implementation                   │  │
│  │  ├─ Last commit (main): c3f4a5b "Fix typo in README"           │  │
│  │  └─ [ View history ] [ Cleanup stale branches ]                │  │
│  │                                                                    │  │
│  │ ────────────────────────────────────────────────────────────────│  │
│  │                                                                    │  │
│  │  my-api-server ✓ Clean                                           │  │
│  │  ├─ Main branch: main (last pull: 2h ago)                       │  │
│  │  ├─ Active branches:                                             │  │
│  │  │  ├─ feature/websocket-support-20260112 [Terminal 3 Scanning] │  │
│  │  │  └─ fix/connection-timeout-20260111 (MERGED)                 │  │
│  │  ├─ Open PRs: 1                                                  │  │
│  │  │  └─ WebSocket real-time updates                              │  │
│  │  ├─ Last commit (main): a1b2c3d "Update requirements.txt"       │  │
│  │  └─ [ View history ] [ Cleanup stale branches ]                │  │
│  │                                                                    │  │
│  │ ────────────────────────────────────────────────────────────────│  │
│  │                                                                    │  │
│  │  utils-library ✓ Clean                                           │  │
│  │  ├─ Main branch: master (last pull: 1h ago)                     │  │
│  │  ├─ Active branches:                                             │  │
│  │  │  └─ feature/performance-optimization-20260112                │  │
│  │  ├─ Open PRs: 0                                                  │  │
│  │  ├─ Last commit (master): f5e6d7c "Add performance tests"       │  │
│  │  └─ [ View history ] [ Cleanup stale branches ]                │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ BRANCH DETAILS: feature/jwt-auth-20260112 ──────────────────────────┐  │
│  │                                                                    │  │
│  │  Created: 2h 15m ago                                              │  │
│  │  Status: IN PROGRESS                                              │  │
│  │  Commits: 8  │  Files changed: 15  │  +450 lines, -20 lines      │  │
│  │  Tests: 12 passing, 0 failing                                     │  │
│  │  Code coverage: 95%                                               │  │
│  │                                                                    │  │
│  │  Commits:                                                          │  │
│  │  • 1h 50m ago: Add JWT token validation                           │  │
│  │  • 1h 30m ago: Add refresh token mechanism                        │  │
│  │  • 45m ago: Add test suite                                        │  │
│  │  • 30m ago: Update docs                                           │  │
│  │                                                                    │  │
│  │  [ Pull latest ] [ View diff ] [ Delete branch ] [ Push ]        │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  [ Refresh ] [ Clone external repo ] [ Cleanup all stale ]  [ Export ]    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Metrics & Performance Dashboard

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ PANDO AUTONOMOUS DEVELOPMENT SYSTEM                              127.0.0.1:5000 │
├──────────────────────────────────────────────────────────────────────────────┤
│  [ TABS ] Status │ Tasks │ Questions │ Repos │ Terminals │ METRICS │ Logs    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  TIME PERIOD: [ Today ▼ ]  [ This Week ]  [ This Month ]  [ All time ]      │
│                                                                              │
│  ┌─ DECISION QUALITY ─────────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  Overall Quality: 92%  ████████░░                                │  │
│  │                                                                    │  │
│  │  Decision Type       │ Quality │ Count │ Trend                  │  │
│  │  ─────────────────────────────────────────────────────────────│  │
│  │  EXECUTE (autonomous) │   94%   │  32   │  ↑ (was 92%)          │  │
│  │  PROPOSE (to user)    │   87%   │  8    │  ↔ (was 87%)          │  │
│  │  BRANCH (exploratory) │   91%   │  5    │  ↑ (was 88%)          │  │
│  │  ASK (blocked)        │   100%  │  2    │  ↑ (new)              │  │
│  │  ESCALATE (critical)  │   100%  │  1    │  ↑ (new)              │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ TASK COMPLETION ──────────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  Completion Rate: 94%                                             │  │
│  │                                                                    │  │
│  │  Today: 12 completed, 1 in progress, 3 queued                    │  │
│  │  This week: 47 completed, 8 failed, 12 escalated                │  │
│  │  Success rate: 94% (47 ÷ 50 = 94%)                              │  │
│  │                                                                    │  │
│  │  Avg time by category:                                            │  │
│  │  • Features: 2h 15m                                               │  │
│  │  • Bug fixes: 45m                                                 │  │
│  │  • Refactoring: 1h 30m                                            │  │
│  │  • Documentation: 30m                                             │  │
│  │                                                                    │  │
│  │  [Chart: Completion trend over 7 days]                            │  │
│  │     ▂▄▆█████░░░                                                   │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ RESOURCE UTILIZATION ─────────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  Terminal Usage: 4/8 terminals active                             │  │
│  │  GPU Memory: 6.2 GB / 8 GB (77%)  ███████░░                     │  │
│  │  RAM: 12.3 GB / 16 GB (77%)  ███████░░                          │  │
│  │  Disk: 145 GB / 500 GB (29%)  ███░░░░░░░░░░░░░░░░░░░░░░░░░░░ │  │
│  │                                                                    │  │
│  │  Peak hours: 10-14:00 (high task load)                           │  │
│  │  Off hours: 18:00+ (repository scanning, optimization)            │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ CONFIDENCE CALIBRATION ───────────────────────────────────────────────┐  │
│  │                                                                    │  │
│  │  Claimed Confidence vs. Actual Success:                           │  │
│  │                                                                    │  │
│  │  > 90%: Claimed 28, Succeeded 26, Hit rate: 93%  ✓               │  │
│  │  80-90%: Claimed 15, Succeeded 14, Hit rate: 93%  ✓              │  │
│  │  70-80%: Claimed 8, Succeeded 7, Hit rate: 88%  ✓                │  │
│  │  < 70%: Claimed 3, Succeeded 2, Hit rate: 67%  ✓                │  │
│  │                                                                    │  │
│  │  Calibration score: 0.91 (near perfect)                           │  │
│  │                                                                    │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  [ Export metrics ] [ Reset data ] [ Configure alerts ]                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Interaction Flows

### Flow 1: User Asks Question (Non-Blocking)

```
┌─ TIMELINE ─────────────────────────────────────────────────────────────────┐
│                                                                             │
│ 10:30:00 Z  Pando: Question posed                                          │
│             "Should we use Redis or in-memory caching?"                    │
│             Status: feature/jwt-auth-20260112 [IN PROGRESS]               │
│             Assumed decision: "in-memory for now"                          │
│             Terminal 1: [CONTINUES WORKING]                               │
│                                                                             │
│ 10:30:05 Z  User (via GUI): Sees question in "Questions" tab              │
│             Examines Pando's reasoning                                     │
│             [NO RESPONSE YET]                                              │
│                                                                             │
│ 10:31:00 Z  Pando: Completes first draft of JWT code                      │
│             Creates local branch: feature/jwt-caching-redis                │
│             Tests with in-memory approach (assumption)                    │
│             Tests pass: ✓✓✓✓✓                                            │
│                                                                             │
│ 10:32:00 Z  Pando: Starts writing tests for JWT                           │
│             Terminal 1: [CONTINUES]                                        │
│             Terminal 2: [IDLE] → Assigned: code review scan                │
│                                                                             │
│ 10:35:00 Z  User (via GUI): Responds to question                          │
│             "Use Redis, better for distributed setup"                      │
│             [ Response submitted ]                                         │
│                                                                             │
│ 10:35:01 Z  Pando: Receives response via async_comm.py                    │
│             Logs decision in pando_state.jsonl                             │
│             Current assumption (in-memory) differs from decision (Redis)   │
│                                                                             │
│ 10:35:02 Z  Pando: Pivots strategy                                        │
│             Rebases feature/jwt-auth-20260112                             │
│             Updates caching implementation: in-memory → Redis              │
│             Preserves all other code                                       │
│             Adds Redis dependency                                          │
│             Updates test fixtures for Redis mock                           │
│             Re-runs tests: ✓✓✓✓✓ (all pass with Redis)                  │
│                                                                             │
│ 10:36:00 Z  Pando: Notifies user in GUI                                   │
│             "Question resolved. Switched to Redis caching."               │
│             "JWT feature still on track: 75% complete, ETA 30m"           │
│             Terminal 1: [STILL RUNNING]                                    │
│                                                                             │
│ 10:36:05 Z  User: Sees update in dashboard                                │
│             Question marked: ✓ RESOLVED                                    │
│             Work continues                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

KEY POINTS:
- Pando didn't wait for user response
- Used assumption to keep working
- Seamlessly switched strategies when user answered
- No blocking, no lost progress
- Full transparency of decision path
```

---

### Flow 2: Pando Proposes Enhancement

```
┌─ TIMELINE ─────────────────────────────────────────────────────────────────┐
│                                                                             │
│ 14:00:00 Z  Pando: Terminal 3 (background scan) discovers                 │
│             3 repos have duplicate utility functions                       │
│             Found: date_utils, string_utils, file_utils (repeated)        │
│             Code duplication: 340 lines across 3 repos                    │
│             Consolidation potential: 35% reduction                        │
│                                                                             │
│ 14:00:05 Z  Pando: Calculates confidence score                             │
│             confidence = 0.92                                              │
│             (high, clear consolidation, automated tests)                  │
│                                                                             │
│ 14:00:10 Z  Pando: Creates proposal                                        │
│             Type: PROPOSE (confidence 60-90%)                              │
│             Created branch: refactor/shared-utils-20260112                 │
│             Branch location: pando-dev repo                                │
│             Implementation: moves utils to shared location                 │
│             Impact: updates 3 repos to import from shared                 │
│             Work estimate: 1.5 hours total                                 │
│             Risk level: LOW (all tests included)                           │
│                                                                             │
│ 14:00:15 Z  Pando: Posts proposal to GUI                                   │
│             Dashboard: "Pending Decisions" shows:                          │
│             "[→] Consolidate 3 shared utilities                           │
│             └─ Branch: refactor/shared-utils-20260112                     │
│             └─ Improvement: Reduces duplication by 35%                    │
│             [ Approve ] [ Review code ] [ Defer ]"                        │
│                                                                             │
│ 14:00:20 Z  Pando: DOES NOT WAIT                                          │
│             Continues with primary task                                    │
│             Terminal 1: [WORKING ON JWT FEATURE]                           │
│             Terminal 2: [ASSIGNED NEW TASK: API rate limiting]             │
│             Terminal 3: [SCANNING CONTINUES]                               │
│                                                                             │
│ 14:30:00 Z  User (via GUI): Reviews proposal                               │
│             Clicks: [ Review code ]                                       │
│             Sees diff, implementation approach                             │
│             Examines test coverage                                         │
│             Confident in approach                                          │
│             Clicks: [ Approve ]                                            │
│                                                                             │
│ 14:30:01 Z  Pando: Receives approval                                       │
│             Marks proposal: APPROVED                                       │
│             Logs decision in pando_state.jsonl                             │
│             Queues branch for immediate merge                              │
│                                                                             │
│ 14:30:05 Z  Pando: Terminal 5 (available): Merges refactor branch          │
│             Runs final tests: ✓ (all 47 tests pass)                       │
│             Merges to main                                                 │
│             Cleans up feature branch                                       │
│             Updates pando_repos.json                                       │
│                                                                             │
│ 14:30:10 Z  Pando: Notifies user                                           │
│             "Consolidation complete. 340 lines removed from codebase."    │
│             "Updated 3 repos, all tests passing."                         │
│             Proposal marked: ✓ COMPLETED in GUI                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

KEY POINTS:
- Pando proposes without waiting for approval
- Continues other work in parallel
- User reviews at leisure
- Approval triggers immediate merge
- No bottlenecks, continuous progress
```

---

### Flow 3: Pando Encounters Issue, Branches with Assumption

```
┌─ TIMELINE ─────────────────────────────────────────────────────────────────┐
│                                                                             │
│ 15:45:00 Z  Pando: Working on feature/api-rate-limit-20260112             │
│             Discovers: What's the maximum requests per user per hour?     │
│             User spec doesn't clearly define this                          │
│             Confidence score: 0.62 (too low to autonomously decide)        │
│                                                                             │
│ 15:45:05 Z  Pando: Decision tree                                           │
│             confidence < 0.7 → Cannot execute autonomously                │
│             blocking task? → Yes (rate limiting depends on limit)          │
│             → BRANCH with assumption + ASK user                            │
│                                                                             │
│ 15:45:10 Z  Pando: Creates assumption branch                               │
│             Branch: assume/rate-limit-10k-20260112                         │
│             Assumption: "100 requests/hour per user"                       │
│             Reasoning: "Common for public APIs, we can adjust"            │
│             Updates config to use this value                               │
│             Terminal 1: [CONTINUES WORK ON THIS ASSUMPTION]                │
│                                                                             │
│ 15:45:15 Z  Pando: Posts question to user                                  │
│             Dashboard: Pending Questions shows:                            │
│             "[⚠] What should be the rate limit?                           │
│             └─ Currently assuming: 100 requests/hour per user             │
│             └─ Implementing on: assume/rate-limit-10k-20260112            │
│             [ 100/hour ] [ 1000/hour ] [ Other ] [ Discuss ]"            │
│                                                                             │
│ 15:45:20 Z  Pando: DOES NOT WAIT                                          │
│             Terminal 1: Implements rate limiting with assumption           │
│             Writes tests for 100/hour limit                                │
│             Writes integration tests                                       │
│             Code coverage: 98%                                             │
│             All tests passing with assumption                              │
│                                                                             │
│ 16:00:00 Z  User (via GUI): Responds to question                           │
│             "Use 1000/hour, more generous"                                │
│             [ 1000/hour ] submitted                                        │
│                                                                             │
│ 16:00:01 Z  Pando: Receives response                                       │
│             Assumption was: 100/hour                                       │
│             Decision is: 1000/hour                                         │
│             Difference: Configuration update only (no code change needed)  │
│                                                                             │
│ 16:00:02 Z  Pando: Updates branch                                          │
│             Commits: "Update rate limit config: 100 → 1000/hour"           │
│             Updates test assertions to match                               │
│             Re-runs tests: ✓ (all pass)                                    │
│             Continues feature branch work                                  │
│                                                                             │
│ 16:01:00 Z  Pando: Feature complete                                        │
│             feature/api-rate-limit-20260112 ready                          │
│             All tests passing                                              │
│             Creates PR, requests review                                    │
│                                                                             │
│ 16:05:00 Z  Reviewer Agent: Reviews PR                                     │
│             "Looks good. Rate limit correctly set to 1000/hour."          │
│             Approves PR                                                    │
│                                                                             │
│ 16:05:01 Z  Pando: Merges PR                                              │
│             Feature complete, deployed                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

KEY POINTS:
- Pando identifies decision point
- Creates assumption branch
- Continues working while waiting for clarification
- User can respond at any time
- Changes are isolated to assumption, seamless integration
- No blocking, continuous progress
```

---

## Key Design Principles

1. **Async First**: User input never blocks Pando's work
2. **Branch Isolation**: Assumptions are on separate branches, easy to pivot
3. **Transparency**: Every decision logged and visible to user
4. **Parallelism**: Multiple terminals working independently
5. **Quality Preservation**: Tests run before merge, static analysis continuous
6. **Escalation Clear**: When to ask vs. decide well-defined
7. **Real-time Updates**: WebSocket for live dashboard updates
8. **Continuity**: State persists, can resume after interruption

---

## Next: Implementation

Start with:
1. Flask backend skeleton
2. React frontend skeleton
3. WebSocket real-time updates
4. API endpoints for core flows
5. Integration with existing Pando systems
