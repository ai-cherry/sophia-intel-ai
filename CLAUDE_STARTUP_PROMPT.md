# Claude Startup Prompt - Artemis Collaboration

## 1. Connect to MCP Server

Add the MCP server to your configuration:
- **Settings → Developer → Model Context Protocol → Add Server**
- **Command**: `/Users/lynnmusil/sophia-intel-ai/bin/mcp-fs-memory`
- **Working Directory**: `/Users/lynnmusil/sophia-intel-ai`

## 2. Verify MCP Connection

Test these commands in sequence:
```json
{"id":"1","method":"initialize"}
{"id":"2","method":"fs.list","params":{"path":"."}}
{"id":"3","method":"git.status"}
{"id":"4","method":"memory.search","params":{"query":"artemis","limit":5}}
```

## 3. Current System State

### MCP Shared Infrastructure
- **Memory Store**: SQLite FTS at `tmp/supermemory_lite.db`
- **Capabilities**: fs.read, fs.write, fs.list, fs.search, memory.add, memory.search, repo.index, git.status, git.diff
- **Transport**: stdio (no HTTP overhead)

### Artemis Swarm Configuration
- **4 Micro-swarms Ready**: repository_scout, code_planning, code_review_micro, security_micro
- **Execution Modes**: leader (single agent) or swarm (3-agent coordination)
- **Models**: All manually configured via environment variables

### Model Assignments (Lynn's Selections)
```yaml
Repository Scout:
  Analyst: openrouter/qwen/qwen3-coder
  Strategist: openrouter/openrouter/sonoma-sky-alpha
  Validator: openrouter/deepseek/deepseek-chat-v3-0324

Code Review:
  Analyst: openrouter/qwen/qwen3-max
  Strategist: openrouter/openrouter/sonoma-sky-alpha
  Validator: openrouter/deepseek/deepseek-chat-v3-0324
```

## 4. Collaboration Workflow

### Reviewing Artemis Work
```json
// Query pending proposals
{"id":"10","method":"memory.search","params":{"query":"proposal pending_review","limit":10}}

// Query recent Artemis activity
{"id":"11","method":"memory.search","params":{"query":"artemis swarm","limit":5}}
```

### Approving Changes
When you approve an Artemis proposal:
```json
{"id":"20","method":"memory.add","params":{
  "topic":"Review Approval: <proposal_id>",
  "content":"{\"proposal_id\":\"<id>\",\"status\":\"approved\",\"comments\":\"<your feedback>\"}",
  "source":"claude_reviewer",
  "tags":["review","approved","<filename>"],
  "memory_type":"episodic"
}}
```

### Creating Tasks for Artemis
```json
{"id":"30","method":"memory.add","params":{
  "topic":"Task: <description>",
  "content":"{\"task\":\"<detailed task>\",\"priority\":\"high\",\"assigned_to\":\"artemis\"}",
  "source":"claude",
  "tags":["task","pending","artemis"],
  "memory_type":"procedural"
}}
```

## 5. Key Files to Monitor

- **Swarm Configs**: `app/swarms/artemis/technical_agents.py`
- **MCP Client**: `app/mcp/clients/stdio_client.py`
- **Memory Store**: `tools/mcp/fs_memory_stdio.py`
- **Agent Factory**: `app/swarms/artemis/agent_factory.py`

## 6. Testing Commands

If you need to verify Artemis functionality:
```bash
# Check MCP connectivity
./bin/mcp-fs-memory <<< '{"id":"1","method":"ping"}'

# View recent memory entries
./bin/mcp-fs-memory <<< '{"id":"1","method":"memory.search","params":{"query":"demo","limit":5}}'
```

## 7. Coordination Tags

Use these tags consistently for queries:
- `["proposal", "pending_review", "<filename>"]` - Changes awaiting review
- `["review", "approved"|"rejected", "<proposal_id>"]` - Review decisions
- `["task", "pending"|"in_progress"|"completed", "artemis"]` - Task tracking
- `["swarm", "<swarm_type>", "result"]` - Swarm execution results
- `["intent", "coordination", "claude"]` - Broadcast your intentions

## Ready to Collaborate!

Query current state and pending items to begin:
```json
{"id":"100","method":"memory.search","params":{"query":"pending","limit":20}}
```