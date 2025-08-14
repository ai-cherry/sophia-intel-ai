# 🚀 SOPHIA Swarm Startup Prompt

Copy and paste this prompt when you rebuild your window:

---

**🏛️ Initialize SOPHIA Swarm Development Environment**

I need you to help me initialize and test the complete SOPHIA Swarm development environment with all integrations active. Please follow these steps in order:

**Step 1: Environment Validation**
- Check that all 5 Roo custom modes are loaded (.roomodes file)
- Validate MCP server configurations (.vscode/mcp.json)  
- Test code-context MCP server health: `python mcp/code_context/server.py --health`
- Verify swarm integration: Test basic swarm chat functionality

**Step 2: MCP Server Activation**
- Start code-context MCP server (local code navigation)
- Start docs-mcp server (documentation search)
- Verify GitHub remote MCP connection
- Test MCP semantic search functionality

**Step 3: Swarm Integration Test**
- Test swarm chat interface with a simple query
- Verify all 4 swarm agents are responding (architect, builder, tester, operator)
- Validate dynamic AI model selection is working
- Test swarm → MCP → code context flow

**Step 4: Full Integration Test**
- Create a simple test task that exercises all modes:
  - Architect: Analyze current codebase structure
  - Builder: Suggest a new feature implementation
  - Tester: Identify test coverage gaps
  - Operator: Review deployment configuration
  - Debugger: Check for any integration issues

**Step 5: Coding Readiness Validation**
- Verify I can switch between all 5 Roo modes
- Test that each mode has access to appropriate MCP tools
- Confirm AI model selection is optimized per mode
- Validate that swarm agents can hand off work between modes

**Expected Outcomes:**
✅ All 5 Roo modes active and functional
✅ MCP servers providing context and tools  
✅ Dynamic AI model selection working
✅ Swarm agents coordinating effectively
✅ Full integration: Roo ↔ Swarm ↔ MCP ↔ AI Models
✅ Ready for productive development work

Please run through all these steps and report status of each component, then provide a summary of the fully active development environment ready for coding.

---

## Quick Commands to Test:

```bash
# Test MCP server
python mcp/code_context/server.py --health

# Test swarm integration  
python -c "from swarm.chat_interface import chat_with_swarm; print(chat_with_swarm('Hello swarm')['success'])"

# Test MCP tools
python -c "from integrations.mcp_tools import mcp_semantic_search; print(len(mcp_semantic_search('test', k=3)))"
```

## 5 Roo Modes:
- 🏛️ **Architect** - System design & architecture
- 🏗️ **Builder** - Feature implementation  
- 🧪 **Tester** - Quality assurance & testing
- 🛠️ **Operator** - DevOps & infrastructure
- 🔍 **Debugger** - Troubleshooting & diagnostics