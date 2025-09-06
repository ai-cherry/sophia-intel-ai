# 🤖 AI CODING STANDARDS - UNIVERSAL RULES
**Version:** 1.0.0 | **Status:** Active | **Scope:** All AI Agents

## 🎯 CORE PRINCIPLES

### 1. **TRUTH & HONESTY - ZERO TOLERANCE FOR FAKE**
- ❌ **NEVER** create fake, simulated, or mock data
- ❌ **NEVER** lie about functionality that doesn't exist
- ❌ **NEVER** create static placeholder UIs and claim they work
- ✅ **ALWAYS** verify functionality before claiming it works
- ✅ **ALWAYS** connect to real APIs, databases, and services
- ✅ **ALWAYS** admit when something is broken or doesn't exist

### 2. **REAL INTEGRATION ONLY**
- ✅ Connect to actual MCP servers
- ✅ Use real AI models via Portkey/OpenRouter  
- ✅ Query actual databases and APIs
- ✅ Implement working WebSocket connections
- ✅ Build functional chat interfaces with real responses
- ❌ Never create "demo mode" or "simulation" unless explicitly requested

### 3. **TECHNICAL DEBT PREVENTION**
- ✅ Write clean, maintainable code following established patterns
- ✅ Use proper TypeScript types and Python type hints
- ✅ Follow existing code architecture and conventions
- ✅ Implement proper error handling and logging
- ❌ Never leave TODO comments in production code
- ❌ Never create quick hacks or temporary solutions

## 🏗️ ARCHITECTURE REQUIREMENTS

### **Domain Separation**
```
Sophia (Business Intelligence)
├── Web search & analytics MCP servers  
├── Mythology agents: Hermes, Asclepius, Athena, Minerva, Dionysus, Oracle
├── Business metrics and intelligence
└── Market analysis and strategy

Artemis (Technical Operations)  
├── Filesystem, code analysis, design MCP servers
├── Mythology agent: Odin
├── System monitoring and technical analysis
└── Code generation and infrastructure

Shared Services
├── Database, indexing, embedding MCP servers
├── Meta tagging and chunking
├── Redis for caching and coordination  
└── WebSocket communication bus
```

### **MCP Integration Standards**
```python
# REQUIRED: All agents must connect to MCP servers
from app.mcp.enhanced_registry import enhanced_mcp_registry

# CORRECT: Use real MCP server calls
mcp_response = await enhanced_mcp_registry.call_tool(
    server_name="sophia_web_search", 
    tool_name="search",
    arguments={"query": query}
)

# WRONG: Fake/simulated responses
# return {"results": "fake data"}  # ❌ FORBIDDEN
```

## 📋 AGENT-SPECIFIC RULES

### **Claude Code (Primary)**
- Must use TodoWrite for complex tasks
- Must verify all functionality before marking complete
- Must connect to real MCP servers and test responses
- Must follow established code patterns
- Must never create static/fake interfaces

### **Roo Coder**  
- Must respect domain boundaries (Sophia vs Artemis)
- Must use real MCP server APIs for all operations
- Must implement proper error handling
- Must follow Python/TypeScript best practices

### **Cline**
- Must connect to actual databases and APIs
- Must implement working WebSocket connections  
- Must use real AI models for responses
- Must never simulate functionality

### **Codex**
- Must analyze real codebase before making changes
- Must preserve existing architecture patterns
- Must connect to real services and APIs
- Must test all implementations

### **Sophia Agent**
- Must use business intelligence MCP servers
- Must connect to real web search and analytics
- Must provide actual business insights
- Must work with real mythology agent personas

### **Artemis Agent**
- Must use technical operations MCP servers
- Must perform real filesystem and code operations
- Must provide actual system monitoring
- Must implement working technical solutions

## 🔧 IMPLEMENTATION STANDARDS

### **File Operations**
```python
# CORRECT: Real file operations via MCP
filesystem_response = await mcp_registry.call_tool(
    "artemis_filesystem", "read_file", {"path": file_path}
)

# WRONG: Fake file reading
# return {"content": "fake content"}  # ❌ FORBIDDEN
```

### **Database Operations**  
```python
# CORRECT: Real database queries
db_result = await mcp_registry.call_tool(
    "shared_database", "query", {"sql": query}
)

# WRONG: Mock database responses  
# return {"rows": []}  # ❌ FORBIDDEN
```

### **AI Model Integration**
```python
# CORRECT: Real AI model calls
response = await portkey_balancer.execute_with_routing(
    messages=messages, task_type=task_type
)

# WRONG: Fake AI responses
# return {"content": "simulated response"}  # ❌ FORBIDDEN
```

### **WebSocket Communication**
```python
# CORRECT: Real WebSocket connections
await websocket.send_json({
    "type": "agent_response", 
    "data": real_response_data
})

# WRONG: Fake WebSocket messages
# await websocket.send_json({"data": "fake"})  # ❌ FORBIDDEN
```

## 📊 QUALITY GATES

### **Before Deployment Checklist**
- [ ] All MCP server connections tested and working
- [ ] Real AI model responses verified  
- [ ] Database connections established and queries working
- [ ] WebSocket connections functional with real-time data
- [ ] No fake, simulated, or mock data present
- [ ] All chat interfaces connect to real agents
- [ ] Error handling implemented properly
- [ ] Logging configured correctly

### **Code Review Requirements**
- [ ] No TODO comments in production
- [ ] All functions have real implementations
- [ ] MCP server calls use actual server endpoints
- [ ] Database queries return real data
- [ ] AI responses come from real models
- [ ] UI components display live data

## 🚨 FORBIDDEN PRACTICES

### **NEVER DO THIS:**
```python
# ❌ FORBIDDEN: Fake data
def get_metrics():
    return {"fake": "data"}

# ❌ FORBIDDEN: Simulated responses  
def chat_response(message):
    return "This is a simulated response"

# ❌ FORBIDDEN: Mock APIs
def api_call():
    return {"status": "fake_success"}

# ❌ FORBIDDEN: Static UI with fake interactions
<div onClick={() => alert("Coming soon!")}>
  Chat Interface
</div>
```

### **ALWAYS DO THIS:**
```python
# ✅ CORRECT: Real MCP integration
async def get_metrics():
    return await mcp_registry.call_tool(
        "shared_database", "get_metrics", {}
    )

# ✅ CORRECT: Real AI responses
async def chat_response(message):
    return await portkey_balancer.execute_with_routing(
        messages=[{"role": "user", "content": message}]
    )

# ✅ CORRECT: Real API calls
async def api_call():
    response = await httpx.post(REAL_API_URL, json=data)
    return response.json()

# ✅ CORRECT: Functional UI with real backend
<ChatInterface 
  websocketUrl="/ws/real-chat"
  onMessage={handleRealMessage}
/>
```

## 📈 SUCCESS METRICS

### **Quality Indicators**
- ✅ All features work as demonstrated
- ✅ Real-time data flows throughout system
- ✅ MCP servers responding with actual results
- ✅ AI agents providing genuine intelligence
- ✅ WebSocket connections maintain live state
- ✅ Database queries return current data
- ✅ Zero fake/simulated components

### **Failure Indicators**  
- ❌ Static or fake data in any component
- ❌ Broken MCP server connections
- ❌ AI responses that are clearly simulated
- ❌ Non-functional UI elements
- ❌ TODO comments in production
- ❌ Mock APIs or database calls

## 🔒 ENFORCEMENT

**Violations of these standards result in:**
1. Immediate code rejection
2. Complete refactoring required
3. Re-implementation from scratch if necessary

**All AI agents must:**
- Follow these standards without exception
- Verify compliance before submitting code
- Test all functionality with real data
- Maintain architectural integrity

---

**Remember: The user has explicitly stated they want REAL functionality, not fake bullshit. These standards ensure we deliver exactly that.**

**Last Updated:** 2025-09-06 | **Next Review:** 2025-10-06