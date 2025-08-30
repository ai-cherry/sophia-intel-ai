# MCP Server Inventory

## Discovered Servers

| Server Name | Language | Path | Primary Tools | Startup Command |
|------------|----------|------|---------------|-----------------|
| Supermemory MCP | Python | `app/memory/supermemory_mcp.py` | add_to_memory, search_memory, get_stats | `python3 -m app.memory.supermemory_mcp` |
| Enhanced MCP Server | Python | `app/memory/enhanced_mcp_server.py` | initialize_pool, get_connection, health_check | `python3 -m app.memory.enhanced_mcp_server` |
| Filesystem MCP | Python | `app/tools/live_tools.py` | fs.read, fs.write, fs.list, fs.delete | Integrated |
| Git MCP | Python | `app/tools/live_tools.py` | git.status, git.diff, git.add, git.commit | Integrated |

## Selected Tools for UI Enhancement

### 1. Supermemory MCP
- **Control Panel**: Start/stop memory indexing, clear cache
- **Status Dashboard**: Memory stats, entry counts by type
- **Search Interface**: Interactive memory search with filters

### 2. Enhanced MCP Server  
- **Connection Pool Monitor**: Live pool status, connection health
- **Performance Dashboard**: Latency metrics, error rates
- **Configuration Panel**: Adjust pool size, timeouts

### 3. Filesystem MCP
- **File Browser**: Navigate and preview files
- **Safety Controls**: Enable/disable write operations
- **Activity Log**: Recent file operations

### 4. Git MCP
- **Repository Status**: Branch info, modified files
- **Commit Interface**: Stage files, create commits
- **History Viewer**: Recent commits with diffs

## UI Action Contracts

### Memory Operations
```json
{
  "actions": {
    "start_indexing": { "tool": "memory.index", "params": {"path": "string"} },
    "stop_indexing": { "tool": "memory.stop", "params": {} },
    "clear_memory": { "tool": "memory.clear", "params": {"type": "string"} },
    "search": { "tool": "memory.search", "params": {"query": "string", "top_k": "number"} }
  }
}
```

### Pool Management
```json
{
  "actions": {
    "resize_pool": { "tool": "pool.resize", "params": {"size": "number"} },
    "drain_pool": { "tool": "pool.drain", "params": {} },
    "health_check": { "tool": "pool.health", "params": {} }
  }
}
```