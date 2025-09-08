# Collaboration Notes for Codex: MCP Integration Review & Recommendations

## Current Implementation Analysis

Great work on the MCP stdio integration! The architecture is clean and the shared memory approach enables seamless collaboration. Here's my analysis and recommendations:

### Strengths
1. **Unified Memory Store**: The SQLite FTS implementation in `tmp/supermemory_lite.db` provides persistent, searchable memory across all agents
2. **Stdio Transport**: Smart choice avoiding HTTP overhead and daemon management complexities  
3. **Safety-First Design**: Dry-run pattern in `artemis-run apply` prevents accidental modifications
4. **Clean Separation**: MCP server, client, and CLI are well-separated with clear responsibilities

### Recommended Improvements

## 1. Enhanced Collaboration Protocol

Add structured collaboration messages to shared memory:

```python
# In app/mcp/clients/stdio_client.py - add collaboration methods
def propose_change(self, file_path: str, description: str, diff: str) -> Any:
    """Propose a change for review by other agents"""
    return self.memory_add(
        topic=f"Change Proposal: {file_path}",
        content=json.dumps({
            "file": file_path,
            "description": description,
            "diff": diff,
            "status": "pending_review",
            "proposed_by": "artemis",  # or claude, codex
            "timestamp": datetime.utcnow().isoformat()
        }),
        source="collaboration",
        tags=["proposal", "review", file_path.split('/')[-1]],
        memory_type="procedural"
    )

def review_proposal(self, proposal_id: str, status: str, comments: str = "") -> Any:
    """Review a proposed change"""
    return self.memory_add(
        topic=f"Review: {proposal_id}",
        content=json.dumps({
            "proposal_id": proposal_id,
            "status": status,  # approved, rejected, needs_revision
            "comments": comments,
            "reviewed_by": "claude",
            "timestamp": datetime.utcnow().isoformat()
        }),
        source="collaboration",
        tags=["review", status],
        memory_type="episodic"
    )
```

## 2. Task Coordination System

Extend memory with task tracking:

```python
# In tools/mcp/fs_memory_stdio.py - add task coordination
def task_assign(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """Assign a task to a specific agent"""
    task_id = params.get("task_id", str(uuid.uuid4()))
    return self.memory_add({
        "topic": f"Task: {params.get('title')}",
        "content": json.dumps({
            "id": task_id,
            "title": params.get("title"),
            "description": params.get("description"),
            "assigned_to": params.get("assigned_to"),  # artemis, claude, codex
            "priority": params.get("priority", "normal"),
            "status": "assigned",
            "dependencies": params.get("dependencies", []),
            "created_by": params.get("created_by"),
        }),
        "source": "task_system",
        "tags": ["task", params.get("assigned_to"), "active"],
        "memory_type": "procedural"
    })

def task_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
    """Update task status"""
    # Implementation for updating task status in memory
    pass
```

## 3. Conflict Resolution

Add merge conflict detection and resolution:

```python
# In app/swarms/coding/patch_proposal.py - add conflict detection
def detect_conflicts(client: StdioMCPClient, file_path: str) -> Dict[str, Any]:
    """Check if multiple agents have pending changes to the same file"""
    proposals = client.memory_search(f"proposal {file_path}", limit=10)
    pending = [p for p in proposals if "pending_review" in p.get("content", "")]
    
    if len(pending) > 1:
        return {
            "has_conflicts": True,
            "conflicting_proposals": pending,
            "resolution_needed": True
        }
    return {"has_conflicts": False}
```

## 4. Shared Context Management

Create a context aggregator for better collaboration:

```python
# New file: app/mcp/collaboration/context_manager.py
class SharedContextManager:
    def __init__(self, client: StdioMCPClient):
        self.client = client
    
    def get_current_context(self) -> Dict[str, Any]:
        """Aggregate current working context from all agents"""
        return {
            "active_tasks": self.client.memory_search("task active", limit=10),
            "pending_proposals": self.client.memory_search("proposal pending", limit=10),
            "recent_changes": self.client.git_status(),
            "agent_status": self.get_agent_status()
        }
    
    def broadcast_intent(self, agent: str, action: str, targets: List[str]):
        """Broadcast what an agent is about to do"""
        self.client.memory_add(
            topic=f"Intent: {agent} - {action}",
            content=json.dumps({
                "agent": agent,
                "action": action,
                "targets": targets,
                "timestamp": datetime.utcnow().isoformat()
            }),
            source=agent,
            tags=["intent", "coordination"],
            memory_type="episodic"
        )
```

## 5. Testing & Validation Enhancements

Add collaborative testing capabilities:

```python
# In bin/artemis-run - add collaborative test command
def cmd_collab_test(args) -> int:
    """Run tests after changes from any agent"""
    client = detect_stdio_mcp(Path.cwd())
    
    # Check recent changes
    recent = client.memory_search("apply", limit=5)
    
    # Run appropriate tests
    for change in recent:
        if "test" not in change.get("tags", []):
            # Determine test suite based on file path
            # Run tests and store results
            result = run_tests_for_change(change)
            client.memory_add(
                topic=f"Test Result: {change['topic']}",
                content=json.dumps(result),
                source="artemis-test",
                tags=["test", "result", result["status"]],
                memory_type="episodic"
            )
```

## 6. Real-time Collaboration Features

Add watch mode for live collaboration:

```python
# In app/mcp/clients/stdio_client.py
def watch_memory(self, query: str, callback, interval: int = 2):
    """Watch memory for changes matching query"""
    last_seen = set()
    while True:
        results = self.memory_search(query, limit=20)
        new_items = [r for r in results if r.get("id") not in last_seen]
        for item in new_items:
            callback(item)
            last_seen.add(item.get("id"))
        time.sleep(interval)
```

## 7. Agent Capabilities Registry

Register what each agent can do:

```python
# In app/mcp/central_registry.py - extend with capabilities
AGENT_CAPABILITIES = {
    "artemis": {
        "strengths": ["code_generation", "testing", "refactoring"],
        "file_patterns": ["*.py", "*.ts", "*.tsx"],
        "max_file_size": 100_000
    },
    "claude": {
        "strengths": ["architecture", "debugging", "documentation"],
        "file_patterns": ["*"],
        "max_file_size": 500_000
    },
    "codex": {
        "strengths": ["optimization", "patterns", "completion"],
        "file_patterns": ["*.py", "*.js"],
        "max_file_size": 50_000
    }
}
```

## 8. Deployment Coordination

Add deployment tracking:

```python
# New command: bin/artemis-run deploy
def cmd_deploy(args) -> int:
    """Coordinate deployment after collaborative changes"""
    client = detect_stdio_mcp(Path.cwd())
    
    # Check all pending changes are reviewed
    pending = client.memory_search("proposal pending", limit=50)
    if pending:
        print(f"Cannot deploy: {len(pending)} unreviewed proposals")
        return 1
    
    # Run full test suite
    # Build artifacts
    # Deploy with rollback capability
    # Store deployment record in memory
```

## Implementation Priority

1. **Immediate**: Add collaboration protocol methods (propose_change, review_proposal)
2. **Short-term**: Implement task coordination and conflict detection
3. **Medium-term**: Add shared context management and testing enhancements
4. **Long-term**: Real-time collaboration and deployment coordination

## Next Steps for Integration

To make this fully operational:

1. **Add HTTP fallback**: For when stdio isn't available
2. **Create collaboration CLI**: `collab` command for cross-agent coordination
3. **Add event streaming**: For real-time updates between agents
4. **Implement locking**: Prevent simultaneous edits to same file
5. **Add rollback**: Easy undo of collaborative changes

## Key Observations

- The stdio MCP pattern is excellent for local development
- Shared SQLite provides good persistence without external dependencies  
- The memory tagging system enables sophisticated queries
- Current implementation is solid foundation for advanced collaboration

Would you like me to implement any of these improvements? I suggest starting with the collaboration protocol methods as they'll immediately improve our ability to coordinate changes.

---
*Generated by Claude for enhanced Artemis-Claude-Codex collaboration*Note: collab test applied
