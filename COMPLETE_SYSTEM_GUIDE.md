# COMPLETE SYSTEM GUIDE - Two Separate Systems

## 🚨 CRITICAL DISTINCTION - READ FIRST

This repository contains **TWO COMPLETELY SEPARATE SYSTEMS**:

1. **SOPHIA INTEL APP** - Business Intelligence Platform (UI 3000, API 8003)
2. **BUILDER AGNO** - Code Generation System (Port 8005)

They serve different purposes, run on different ports, and should NEVER be mixed.

## Quick Reference

| System | Purpose | Port | Dashboard URL | For Who |
|--------|---------|------|---------------|---------|
| SOPHIA | Business Intelligence | 3000/8003 | http://localhost:3000 | Business Users |
| BUILDER | Code Generation | 8005 | http://localhost:8005 | Developers |

## Startup Commands

```bash
# For Business Intelligence (Sales, Analytics, Metrics)
./start_sophia_complete.sh

# For Code Generation (Development, Repository Management)
./builder-system/start_builder.sh
```

## Decision Tree

```
User asks about...
├── Sales/Revenue/Customers/Business
│   └── USE SOPHIA (UI 3000 / API 8003)
├── Code/Features/Tests/Repository
│   └── USE BUILDER (Port 8005)
└── Unclear?
    └── ASK FOR CLARIFICATION
```

For complete details, see:
- Sophia: docs/SOPHIA_ARCHITECTURE.md
- Builder: builder-system/README.md
- AI Instructions: AI_AGENT_INSTRUCTIONS.md
