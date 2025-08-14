# MCP Integration Activation Roadmap
## Getting Roo (SOPHIA) to Actively Use MCP Integration

## 🎯 **Current State vs. Target State**

**Current**: Roo uses built-in tools, no persistence, no learning
**Target**: Roo uses MCP-enhanced tools with memory, context, and learning

## 🚀 **Activation Steps Required**

### **Phase 1: MCP Server Deployment (Required)**

#### **1.1 Deploy Enhanced MCP Server**
```bash
# Start the enhanced unified MCP server with memory service
cd /workspaces/sophia-intel
python -m uvicorn mcp_servers.enhanced_unified_server:app --host 0.0.0.0 --port 8000
```

#### **1.2 Verify Server Health**
```bash
# Test the HTTP endpoint
curl http://localhost:8000/health
# Should return: {"status": "healthy", ...}
```

### **Phase 2: SOPHIA System Integration (Required)**

#### **2.1 Create MCP-Enhanced Tool Registry**
```python
# File: agents/mcp_enhanced_registry.py
import asyncio
from libs.mcp_client import SophiaMCPClient, SophiaSessionManager, ContextAwareToolWrapper

class MCPEnhancedToolRegistry:
    def __init__(self):
        self.session_manager = None
        self.mcp_client = None
        self.enhanced_tools = {}
    
    async def initialize(self, session_id: str = None):
        """Initialize MCP-enhanced tools"""
        self.session_manager = SophiaSessionManager()
        session_id = await self.session_manager.start_session(session_id)
        self.mcp_client = self.session_manager.mcp_client
        
        # Wrap all tools with MCP enhancement
        await self._wrap_existing_tools()
        
        return session_id
    
    async def _wrap_existing_tools(self):
        """Replace built-in tools with MCP-enhanced versions"""
        wrapper = ContextAwareToolWrapper(self.mcp_client)
        
        # Enhanced read_file
        self.enhanced_tools['read_file'] = await wrapper.wrap_tool(
            self._enhanced_read_file, 'read_file'
        )
        
        # Enhanced search_files  
        self.enhanced_tools['search_files'] = await wrapper.wrap_tool(
            self._enhanced_search_files, 'search_files'
        )
        
        # Enhanced apply_diff
        self.enhanced_tools['apply_diff'] = await wrapper.wrap_tool(
            self._enhanced_apply_diff, 'apply_diff'
        )
```

#### **2.2 Modify SOPHIA Core to Use MCP Tools**
```python
# File: agents/base_agent.py - Add MCP integration
from agents.mcp_enhanced_registry import MCPEnhancedToolRegistry

class BaseAgent:
    def __init__(self):
        self.mcp_registry = None
        self.use_mcp = True  # Feature flag
        
    async def initialize_mcp(self):
        if self.use_mcp:
            self.mcp_registry = MCPEnhancedToolRegistry()
            await self.mcp_registry.initialize()
    
    async def read_file(self, path: str):
        if self.mcp_registry:
            return await self.mcp_registry.enhanced_tools['read_file'](path)
        else:
            # Fallback to built-in tool
            return self._builtin_read_file(path)
```

### **Phase 3: Configuration Integration (Required)**

#### **3.1 Update SOPHIA Configuration**
```python
# File: config/sophia.yaml - Add MCP settings
mcp:
  enabled: true
  server_url: "http://localhost:8000"
  session_persistence: true
  context_awareness: true
  predictive_assistance: true
  performance_monitoring: true
```

#### **3.2 Environment Setup**
```bash
# Add to .env or environment
export SOPHIA_MCP_ENABLED=true
export SOPHIA_MCP_SERVER_URL=http://localhost:8000
export SOPHIA_SESSION_DIR=.sophia_sessions
```

### **Phase 4: Integration Activation (The Key Step)**

#### **4.1 Modify SOPHIA Startup Sequence**
```python
# File: main SOPHIA entry point (wherever Roo is initialized)
async def initialize_sophia():
    # ... existing initialization ...
    
    # NEW: Initialize MCP integration
    if config.mcp.enabled:
        logger.info("Initializing MCP integration...")
        
        # Start MCP-enhanced agent
        agent = BaseAgent()
        await agent.initialize_mcp()
        
        logger.info(f"MCP integration active - Session: {agent.mcp_registry.session_manager.current_session}")
        return agent
    else:
        # Fallback to standard agent
        return BaseAgent()
```

## 🔧 **Technical Implementation Details**

### **Required Code Changes**

#### **1. Tool System Replacement**
- Replace direct tool calls with MCP-enhanced versions
- Add automatic context storage for all operations
- Enable predictive suggestions based on usage patterns

#### **2. Session Management Integration**
- Initialize persistent sessions on startup
- Restore context from previous sessions
- Store interaction patterns for learning

#### **3. Memory Integration**
- Connect to Qdrant vector database
- Store and retrieve semantic context
- Enable cross-session learning

## 🚦 **Deployment Scenarios**

### **Scenario A: Full Integration (Recommended)**
1. Deploy enhanced MCP server on persistent infrastructure
2. Modify SOPHIA core to use MCP tools by default
3. Enable persistent sessions and context storage
4. **Result**: Roo has full memory, learning, and predictive capabilities

### **Scenario B: Gradual Integration**
1. Deploy MCP server with feature flag (disabled by default)
2. Enable MCP for specific modes or operations
3. Gradually expand MCP usage based on performance
4. **Result**: Controlled rollout with fallback options

### **Scenario C: Development Integration**
1. Run MCP server locally during development
2. Use MCP tools only in specific development contexts
3. Test and validate before production deployment
4. **Result**: Safe testing environment for MCP capabilities

## 🎯 **Immediate Next Steps to Activate**

### **Option 1: Quick Local Activation (30 minutes)**
```bash
# 1. Start the MCP server
python -m uvicorn mcp_servers.enhanced_unified_server:app --port 8000 &

# 2. Create a simple MCP-enabled session test
python examples/mcp_integration_example.py

# 3. Verify it's working with persistent memory
```

### **Option 2: Full System Integration (2-4 hours)**
1. **Deploy MCP Server**: Set up persistent MCP server infrastructure
2. **Modify Agent System**: Update base agent to use MCP tools
3. **Update Configuration**: Enable MCP in SOPHIA config
4. **Test Integration**: Verify all tools work with memory/learning
5. **Deploy**: Roll out to production with monitoring

### **Option 3: VS Code Extension Integration (1-2 hours)**
```bash
# The VS Code MCP config is already set up
# Just need to enable the MCP extension and connect

# 1. Install VS Code MCP extension
# 2. The .vscode/mcp.json is already configured
# 3. VS Code will automatically connect to MCP servers
# 4. Roo would then have access through VS Code's MCP interface
```

## 📊 **Success Metrics**

When successfully activated, you'll see:
- ✅ Persistent memory across Roo sessions
- ✅ Context-aware tool suggestions
- ✅ Learning from previous interactions
- ✅ Semantic code search capabilities
- ✅ Predictive next-action suggestions

## ⚠️ **Prerequisites for Activation**

1. **MCP Server Running**: HTTP endpoint accessible
2. **Database Available**: Qdrant for vector storage (or fallback to file storage)
3. **SOPHIA Core Access**: Ability to modify the core agent system
4. **Configuration Control**: Access to SOPHIA configuration files
5. **Deployment Capability**: Ability to restart/redeploy SOPHIA with changes

## 🔥 **The Simplest Path to Activation**

**If you want to see this working immediately:**

1. **Start MCP Server**: `python -m uvicorn mcp_servers.enhanced_unified_server:app --port 8000`
2. **Run Demo**: `python examples/mcp_integration_example.py`
3. **See Memory in Action**: The demo shows persistent sessions and context awareness

**For full Roo integration**: The SOPHIA core system needs to be modified to use the MCP client instead of built-in tools.