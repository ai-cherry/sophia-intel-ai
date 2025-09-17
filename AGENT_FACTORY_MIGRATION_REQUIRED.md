# Agent Factory Migration Required

## Issue
Agent Factory components found in sophia-intel-ai repository.
This violates the repository separation principle.

## Required Action
Move the following files to workbench-ui:
- app/factory/ui/AgentFactoryComponents.jsx

## Repository Separation Principle
- **workbench-ui**: Agent development, testing, optimization
- **sophia-intel-ai**: Agent deployment, business operations, monitoring

## Migration Command
```bash
# Move to workbench-ui
mv ~/sophia-intel-ai/app/factory/ui/AgentFactoryComponents.jsx ~/workbench-ui/src/components/factory/
```
