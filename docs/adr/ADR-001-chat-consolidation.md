# ADR-001: Chat Endpoint Consolidation

## Status
Accepted

## Context
The SOPHIA Intel platform had multiple chat implementations scattered across different files:
- `backend/chat_proxy.py` - FastAPI streaming chat with MCP integration
- `backend/main.py` - Unified backend with chat, research, web scraping
- `swarm/chat_interface.py` - Direct Swarm system integration

This fragmentation led to:
- Duplicate code and inconsistent behavior
- Maintenance overhead across multiple implementations
- Confusion about which endpoint to use for different scenarios
- Inconsistent feature flags and request models

## Decision
Consolidate all chat functionality into a unified domain-driven architecture:
- Single chat service in `backend/domains/chat/service.py`
- Unified request/response models in `backend/domains/chat/models.py`
- Intelligent routing logic to determine backend (Orchestrator vs Swarm)
- Consistent feature flags across all chat operations

## Consequences

### Positive
- Single source of truth for chat functionality
- Consistent API interface and behavior
- Easier maintenance and feature development
- Intelligent routing based on message analysis
- Unified session management and memory integration

### Negative
- Requires migration of existing integrations
- Temporary disruption during consolidation
- Need to update documentation and client code

### Neutral
- Code complexity moves from distribution to centralization
- Testing focus shifts to single comprehensive test suite

## Implementation
1. Create unified chat domain structure
2. Migrate functionality from existing implementations
3. Implement intelligent routing logic
4. Update all client integrations
5. Remove deprecated chat endpoints
6. Update documentation and tests

## Alternatives Considered
- Keep separate implementations with shared libraries
- Create a chat gateway that routes to existing services
- Gradual migration with feature flags

## References
- COMPREHENSIVE_PRE_DEPLOYMENT_REPORT.md
- Backend domain architecture design
- Chat routing intelligence requirements

