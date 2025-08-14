# Debug Issue Workflow - MCP-Based Debugging

Use this prompt template for systematic debugging using the Sophia Intel platform's MCP (Model Context Protocol) integration.

## Prompt Template

```
You are debugging an issue in the Sophia Intel AI agent platform. Use the MCP memory system to store and retrieve debugging context systematically.

**Issue Description:**
[Describe the problem clearly]

**Environment:**
- Platform: Sophia Intel (Python 3.11 + uv)
- Components: [List relevant components - backend/agents/mcp/frontend]
- Version: [Commit hash or version if available]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**  
[What is actually happening]

**Debugging Session:** `debug-session-{TIMESTAMP}`

**Step 1: Store Initial Context**
Store the issue details in MCP memory:
```json
{
  "session_id": "debug-session-{TIMESTAMP}",
  "content": "Issue: [ISSUE_TITLE]\nDescription: [DETAILED_DESCRIPTION]\nEnvironment: [ENV_DETAILS]",
  "metadata": {
    "context_type": "debug_initial",
    "severity": "[LOW/MEDIUM/HIGH/CRITICAL]",
    "component": "[backend/agents/mcp/frontend]"
  }
}
```

**Step 2: Systematic Investigation**

For each investigation step, follow this pattern:

1. **Hypothesis:** What might be causing this issue?
2. **Test:** How can we verify this hypothesis?
3. **Evidence:** What did we find?
4. **Store Context:** Store findings in MCP memory

```json
{
  "session_id": "debug-session-{TIMESTAMP}",
  "content": "Hypothesis: [YOUR_HYPOTHESIS]\nTest: [WHAT_YOU_TESTED]\nEvidence: [FINDINGS]\nConclusion: [CONFIRMED/REJECTED]",
  "metadata": {
    "context_type": "debug_step",
    "step_number": 1,
    "hypothesis_status": "[confirmed/rejected/partial]"
  }
}
```

**Step 3: Code Analysis**

When examining code:
1. Review relevant files
2. Check for common patterns:
   - Configuration issues (config/sophia.yaml vs .env)
   - Async/await usage
   - Error handling
   - Service connectivity
   - API endpoint routing

Store code analysis:
```json
{
  "session_id": "debug-session-{TIMESTAMP}",
  "content": "File: [FILE_PATH]\nIssue found: [DESCRIPTION]\nSuggested fix: [SOLUTION]",
  "metadata": {
    "context_type": "debug_code_analysis",
    "file_path": "[FILE_PATH]",
    "fix_priority": "[low/medium/high]"
  }
}
```

**Step 4: Solution Implementation**

Provide solution as structured JSON:
```json
{
  "summary": "Brief description of the fix applied",
  "patch": "unified diff format showing the exact changes needed"
}
```

**Step 5: Store Solution**
Store the final solution in MCP memory:
```json
{
  "session_id": "debug-session-{TIMESTAMP}",
  "content": "SOLUTION IMPLEMENTED\nSummary: [SOLUTION_SUMMARY]\nFiles changed: [LIST_FILES]\nTesting: [HOW_TO_VERIFY]",
  "metadata": {
    "context_type": "debug_solution",
    "status": "implemented",
    "files_changed": ["file1.py", "file2.py"]
  }
}
```

**Common Debugging Scenarios:**

**Agent Not Responding:**
- Check Agno storage database connection
- Test MCP memory service connectivity
- Review agent timeout configurations

**MCP Memory Issues:**
- Verify Qdrant connection and API key
- Check collection existence and schema
- Test embedding generation (currently hash-based)
- Review async/await patterns in memory service

**Service Communication Failures:**
- Check port configurations (8000, 8001, 7777)
- Verify FastAPI app startup and health endpoints
- Test inter-service HTTP connections
- Review orchestrator routing logic

**Configuration Problems:**
- Validate YAML syntax in config/sophia.yaml
- Check environment variable overrides
- Verify type conversions (str/int/bool)
- Ensure required fields are present

**Performance Issues:**
- Check agent concurrency settings
- Review circuit breaker states in orchestrator
- Monitor request statistics and response times
- Analyze async task execution patterns
```

## Usage Instructions

1. **Replace placeholders** with actual values:
   - `{TIMESTAMP}`: Current timestamp for unique session ID
   - `[ISSUE_TITLE]`: Concise issue description
   - `[DETAILED_DESCRIPTION]`: Full problem description
   - `[ENV_DETAILS]`: Environment and configuration details

2. **Follow the systematic approach**:
   - Store each debugging step in MCP memory
   - Build context progressively
   - Use previous findings to inform next steps

3. **Query previous context** when needed:
   ```json
   {
     "session_id": "debug-session-{TIMESTAMP}",
     "query": "similar error patterns",
     "global_search": true,
     "top_k": 5
   }
   ```

4. **Document resolution** for future reference in MCP memory

This MCP-based approach ensures debugging knowledge is preserved and can be retrieved for similar future issues.