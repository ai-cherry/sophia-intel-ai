# SOPHIA Swarm Integration Guide

## 🏗️ Roo Modes ↔ Swarm Agent Architecture

Your `.roomodes` file defines 5 custom modes that directly integrate with the SOPHIA Swarm system:

### 🏛️ **SOPHIA Architect** (slug: `architect`)
**Swarm Agent**: Primary reasoning and design agent  
**AI Model**: GPT-5 / Claude Opus 4.1 (latest reasoning models)  
**Purpose**: System architecture, code reviews, refactoring  
**MCP Tools**: Full repo context, documentation search, design patterns  
**Usage**: Complex architectural decisions, code quality analysis

### 🏗️ **Feature Builder** (slug: `builder`) 
**Swarm Agent**: Implementation and construction agent  
**AI Model**: GPT-5 / DeepSeek Coder V2 (code generation specialists)  
**Purpose**: New features, components, API implementation  
**MCP Tools**: Code context, GitHub integration, file operations  
**Usage**: Building new functionality, API endpoints, components

### 🧪 **Test Engineer** (slug: `tester`)
**Swarm Agent**: Quality assurance and validation agent  
**AI Model**: GPT-5 Turbo / Claude Sonnet 3.5 (fast analysis)  
**Purpose**: Test creation, coverage analysis, quality metrics  
**MCP Tools**: Test frameworks, coverage reports, CI integration  
**Usage**: Writing tests, finding edge cases, QA validation

### 🛠️ **Operator** (slug: `operator`)
**Swarm Agent**: Infrastructure and deployment agent  
**AI Model**: GPT-4o Omni / Gemini Pro 1.5 (efficient operations)  
**Purpose**: DevOps, infrastructure, deployment, monitoring  
**MCP Tools**: Infrastructure tools, deployment scripts, monitoring  
**Usage**: CI/CD, infrastructure management, deployment

### 🔍 **Debugger** (slug: `debugger`)
**Swarm Agent**: Diagnostic and troubleshooting agent  
**AI Model**: GPT-5 / Claude Opus 4.1 (deep analysis)  
**Purpose**: Issue diagnosis, error analysis, system debugging  
**MCP Tools**: Logs, error tracking, system diagnostics  
**Usage**: Troubleshooting, error resolution, system analysis

## 🤖 Dynamic LLM Model Selection

Based on `swarm/ai_integration.py`, your system includes:

### **Tier 1 Models** (Latest & Most Capable)
- **GPT-5** - Primary reasoning, architecture
- **GPT-5 Turbo** - Fast analysis, testing  
- **Claude Opus 4.1** - Complex reasoning, debugging
- **Claude Sonnet 3.5** - Balanced performance

### **Tier 2 Models** (Specialized)
- **DeepSeek Coder V2** - Code generation specialist
- **Gemini Pro 1.5** - Long context, operations
- **Groq Llama 3.1 70B** - Fast inference

### **Model Selection Logic**
```python
# Stage-specific optimization
architect → GPT-5/Claude Opus (complex reasoning)
builder → GPT-5/DeepSeek Coder (code generation) 
tester → GPT-5 Turbo (fast analysis)
operator → GPT-4o/Gemini Pro (efficient docs)
debugger → GPT-5/Claude Opus (deep analysis)
```

## 🔌 MCP Server Integration

### **Active MCP Servers**
1. **code-context** - Local code navigation and search
2. **docs-mcp** - Documentation and knowledge search  
3. **github-remote** - GitHub integration via Copilot API

### **Swarm-MCP Integration Flow**
```
Roo Mode → Swarm Agent → AI Model → MCP Tools → Code Action
```

## 🚀 COMPLETE STARTUP PROMPT

Use this prompt when you rebuild the window to get everything active:

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

## 🎯 Quick Mode Usage Examples

### **Architectural Review**
*Switch to Architect mode*: `"Analyze the swarm integration architecture and suggest improvements"`

### **Feature Development** 
*Switch to Builder mode*: `"Implement a new MCP tool for database operations"`

### **Quality Assurance**
*Switch to Tester mode*: `"Create comprehensive tests for the swarm chat interface"`

### **Infrastructure Management**
*Switch to Operator mode*: `"Review and optimize the MCP server deployment configuration"`

### **Issue Resolution**
*Switch to Debugger mode*: `"Investigate why MCP server connections are timing out"`

## 🔄 Swarm Workflow Integration

When you use any mode, the system:
1. **Selects optimal AI model** based on task type
2. **Activates relevant MCP tools** for context
3. **Coordinates with other swarm agents** if needed
4. **Provides cross-mode handoffs** for complex tasks
5. **Maintains context** across mode switches

This creates a powerful development environment where each mode specializes but they all work together through the swarm coordination system.