# Pando - Autonomous Development System

**Status**: Alpha (Production Ready)  
**Version**: 1.0  

## What is Pando?

Pando is an autonomous development team that runs continuously, makes intelligent decisions about code changes, works across multiple repositories simultaneously, and communicates with you asynchronously.

## Quick Start

```bash
python pando_gui/backend/app.py &  # Start API server
python agent.py                     # Start worker agent
curl -X POST http://localhost:5000/api/directions \
  -d "{`"text`": `"Review the auth module`", `"priority`": `"high`"}"
```

## How to Use

Submit **directions** (high-level tasks) via the API. Pando automatically parses them into concrete tasks, decides autonomously or asks for guidance, and reports progress in real-time.

**Learn more:** See [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) to get started.

## Key Features

 Autonomous decision making  
 Non-blocking user communication  
 Multi-repository management  
 Parallel task execution  
 Full audit trail  
 Real-time dashboard  

## Documentation

- [Getting Started](docs/GETTING_STARTED.md) - Quick start (5 min)
- [System Design](docs/architecture/SYSTEM_DESIGN.md) - Architecture (15 min)
- [Directions API](docs/api/DIRECTIONS_AND_TASKS.md) - API reference (10 min)
- [Key Answers](docs/ANSWERS.md) - FAQs on models, organization, GUI (10 min)

## Directory Structure

```
 docs/                           All documentation
    GETTING_STARTED.md
    ANSWERS.md
    architecture/SYSTEM_DESIGN.md
    api/DIRECTIONS_AND_TASKS.md
 pando_core/                     Core autonomy engine
 pando_gui/                      Web API and frontend
 agent.py                        Worker agent
 config.py                       Configuration
 [other core modules]
```

---

**Ready?** Start with [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)
