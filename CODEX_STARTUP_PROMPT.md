# Codex Startup Prompt - Artemis System Status

## System Health Check

### 1. MCP Server Status
```bash
# Test MCP connectivity
./bin/mcp-fs-memory <<< '{"id":"1","method":"initialize"}'

# Should return:
# {"id":"1","result":{"server":"fs-memory-stdio","cwd":"...","capabilities":[...]}}
```

### 2. Environment Configuration
All models configured in `.env.artemis.local`:
- ✅ Manual-only policy enforced (`LLM_SELECTION_MODE=manual`)
- ✅ Model approval strict mode (`LLM_APPROVAL_STRICT=true`)
- ✅ Per-role assignments set for all swarms

### 3. Current Issues to Fix

#### Import Error in swarm_integration.py
```python
# Line 14: Missing module
from app.integrations.connectors.gong_pipeline.gong_brain_training_adapter import GongBrainTrainingAdapter
# This module doesn't exist - needs to be removed or mocked
```

## Artemis Swarm Status

### Ready Swarms (4)
1. **repository_scout** - Maps integrations, hotspots, improvements
2. **code_planning** - Architecture and implementation planning
3. **code_review_micro** - Code quality and standards review
4. **security_micro** - Security vulnerability assessment

### Execution Modes
- **Leader Mode**: Single strategist agent for quick synthesis
- **Swarm Mode**: Full 3-agent coordination (Analyst → Strategist → Validator)

### Model Mapping
```python
# Repository Scout
LLM_ANALYST_PROVIDER=openrouter
LLM_ANALYST_MODEL=qwen/qwen3-coder
LLM_STRATEGIST_PROVIDER=openrouter  
LLM_STRATEGIST_MODEL=openrouter/sonoma-sky-alpha
LLM_VALIDATOR_PROVIDER=openrouter
LLM_VALIDATOR_MODEL=deepseek/deepseek-chat-v3-0324
```

## Quick Test Commands

### 1. Test MCP Operations
```bash
# Initialize and index
./bin/mcp-fs-memory <<< '{"id":"1","method":"repo.index","params":{"root":".","max_bytes_per_file":20000}}'

# Store a test entry
./bin/mcp-fs-memory <<< '{"id":"2","method":"memory.add","params":{"topic":"System Test","content":"Codex startup test","source":"codex","tags":["test","startup"],"memory_type":"episodic"}}'

# Search memory
./bin/mcp-fs-memory <<< '{"id":"3","method":"memory.search","params":{"query":"test","limit":5}}'
```

### 2. Test Agent Creation (No Network Required)
```bash
python3 scripts/test_artemis_agents.py
# Should show all 6 agents configured successfully
```

### 3. Test Swarm Execution (Requires Network)
```bash
# Leader-only test
./bin/artemis-run swarm --type repository_scout --mode leader --task "List main components"

# Full swarm test  
./bin/artemis-run swarm --type code_review_micro --mode swarm --task "Review app/swarms/artemis/agent_factory.py"
```

## Collaboration Protocol with Claude

### 1. Proposal Creation
When Artemis creates proposals, store them as:
```python
client.memory_add(
    topic=f"Proposal: {file_path}",
    content=json.dumps({
        "proposal_id": unique_id,
        "file": file_path,
        "changes": proposed_changes,
        "diff": unified_diff,
        "status": "pending_review",
        "confidence": confidence_score
    }),
    source="artemis",
    tags=["proposal", "pending_review", filename],
    memory_type="procedural"
)
```

### 2. Claude Reviews
Claude queries and reviews:
```json
// Claude searches for pending
{"method":"memory.search","params":{"query":"proposal pending_review"}}

// Claude approves/rejects
{"method":"memory.add","params":{
  "topic":"Review: <proposal_id>",
  "content":"{\"status\":\"approved\",\"comments\":\"...\"}",
  "tags":["review","approved"]
}}
```

### 3. Artemis Applies
After approval, Artemis:
1. Queries approved proposals
2. Applies changes via `fs.write`
3. Stores completion status
4. Runs tests if configured

## Next Actions

### Immediate Fixes Needed
1. **Fix import error** in `app/swarms/core/swarm_integration.py`
   - Either mock the missing module or remove the import
   
2. **Add model approval list** if using strict mode:
   ```python
   # app/models/approved_models.py
   APPROVED_MODELS = {
       "openrouter": ["qwen/qwen3-coder", "qwen/qwen3-max", ...],
       # Add all Lynn's selected models
   }
   ```

### Testing Priority
1. Fix the import issue first
2. Run `./bin/artemis-run smoke` to verify basic MCP operations
3. Test leader mode with simple tasks
4. Progress to full swarm tests
5. Create sample proposals for Claude to review

## Memory Query Shortcuts

```bash
# Recent Artemis activity
./bin/mcp-fs-memory <<< '{"id":"1","method":"memory.search","params":{"query":"artemis","limit":10}}'

# Pending proposals
./bin/mcp-fs-memory <<< '{"id":"1","method":"memory.search","params":{"query":"pending_review","limit":10}}'

# Completed tasks
./bin/mcp-fs-memory <<< '{"id":"1","method":"memory.search","params":{"query":"completed","limit":10}}'
```

## Ready State Checklist

- [x] MCP stdio server functional
- [x] Models configured in environment
- [x] Agent factory creates agents correctly
- [ ] Fix import error in swarm_integration.py
- [ ] Add approved_models.py if strict mode enabled
- [ ] Test leader mode execution
- [ ] Test full swarm execution
- [ ] Create initial proposals for review

Once the import is fixed, the system is ready for collaborative work!