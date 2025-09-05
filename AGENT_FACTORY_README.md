# 🏗️ Agent Factory - Dynamic AI Swarm Creation System

## Overview

The Agent Factory is a sophisticated system for creating, configuring, and executing custom AI agent swarms. Built on the existing MCP server infrastructure, it provides both a visual interface and robust API for dynamic agent orchestration.

## 🎯 Key Features

### ✅ **Completed (Phase 1)**

- **Visual Swarm Builder**: Drag-and-drop interface for creating agent swarms
- **Pre-built Templates**: Ready-to-use swarm patterns (Coding, Debate, Consensus)
- **Real-time Cost Estimation**: Track estimated costs before execution
- **Live Testing Sandbox**: Test swarms with sample tasks
- **Multi-Agent Coordination**: Coordinated execution with different patterns
- **Code Quality Integration**: Enhanced with dedicated code quality reviewer agent
- **Accessibility Support**: ARIA labels, keyboard navigation, screen reader support
- **Security Hardening**: XSS prevention, input validation, safe DOM manipulation

### 🚀 **Available Swarm Templates**

1. **Coding Swarm** (4 agents)

   - Code Planner → Code Generator → Security Reviewer → **Quality Reviewer**
   - Pattern: Hierarchical execution
   - Best for: Code generation, review, and optimization

2. **Debate Swarm** (3 agents)

   - Advocate ↔ Critic → Judge
   - Pattern: Adversarial debate
   - Best for: Decision making, risk assessment

3. **Consensus Swarm** (4 agents)
   - Technical Analyst + Business Analyst + UX Analyst → Synthesizer
   - Pattern: Consensus building
   - Best for: Complex decisions, strategic planning

### 🔧 **Technical Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Browser UI    │    │   MCP Server    │    │  OpenRouter     │
│                 │    │   Port 3333     │    │     API         │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Tab Interface │    │ • Factory API   │    │ • Model Access  │
│ • Agent Builder │◄──►│ • Swarm Storage │◄──►│ • Execution     │
│ • Cost Display  │    │ • Pattern Logic │    │ • Token Usage   │
│ • Test Sandbox  │    │ • Integration   │    │ • Rate Limits   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📚 **API Endpoints**

### Core Factory Operations

- `GET /api/factory/health` - Service health check
- `GET /api/factory/templates` - Available swarm templates
- `GET /api/factory/patterns` - Execution patterns
- `POST /api/factory/create` - Create new swarm
- `GET /api/factory/swarms` - List all swarms
- `GET /api/factory/swarms/{id}` - Get swarm details
- `POST /api/factory/swarms/{id}/execute` - Execute swarm
- `DELETE /api/factory/swarms/{id}` - Delete swarm

### Example Usage

```bash
# Create a swarm
curl -X POST http://127.0.0.1:3333/api/factory/create \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "My Custom Swarm",
    "agents": [
      {
        "name": "Planner",
        "role": "planner",
        "model": "qwen/qwen3-30b-a3b",
        "temperature": 0.3,
        "instructions": "Create implementation plan",
        "capabilities": ["planning"]
      }
    ]
  }'

# Execute the swarm
curl -X POST http://127.0.0.1:3333/api/factory/swarms/{swarm_id}/execute \\
  -H "Content-Type: application/json" \\
  -d '{"task": "Create a Python function for file processing"}'
```

## 🎨 **User Interface**

### Access the Factory

**Primary Interface**: `file:///Users/lynnmusil/sophia-intel-ai/dev-mcp-unified/ui/multi-chat-artemis.html`

### Navigation

- **Artemis Coding**: Multi-model chat interface
- **Agent Factory**: Swarm builder (current focus)
- **Sophia Business**: Business automation (Phase 2)
- **Analytics**: Performance metrics (Phase 2)

### Factory Workflow

1. **Select Template**: Choose from Coding, Debate, or Consensus patterns
2. **Configure Agents**: Set names, roles, models, temperatures, instructions
3. **Choose Pattern**: Hierarchical, debate, consensus, sequential, parallel
4. **Test & Iterate**: Use sandbox to test with sample tasks
5. **Deploy**: Create production-ready swarm

## 🧩 **Agent Roles**

| Role                 | Purpose                                | Typical Models            |
| -------------------- | -------------------------------------- | ------------------------- |
| **planner**          | Requirements analysis, architecture    | qwen/qwen3-30b-a3b        |
| **generator**        | Content/code creation                  | x-ai/grok-code-fast-1     |
| **critic**           | Bug detection, security review         | openai/gpt-5-chat         |
| **quality_reviewer** | 🆕 Code quality, style, best practices | anthropic/claude-sonnet-4 |
| **judge**            | Final decisions, synthesis             | openai/gpt-5-chat         |
| **runner**           | Task execution, coordination           | google/gemini-2.5-flash   |

## 📊 **Quality Improvements**

### Security Enhancements

- ✅ **XSS Prevention**: Safe DOM manipulation without innerHTML
- ✅ **Input Validation**: Server-side validation for all inputs
- ✅ **Rate Limiting**: Prevent API abuse (planned)
- ✅ **Secure Headers**: CORS, CSP headers configured

### Accessibility (WCAG 2.1 AA)

- ✅ **ARIA Labels**: Screen reader support
- ✅ **Keyboard Navigation**: Full keyboard accessibility
- ✅ **Focus Management**: Proper focus indicators
- ✅ **Color Contrast**: Sufficient contrast ratios
- 🔄 **Screen Reader Announcements**: Dynamic content changes (in progress)

### Performance

- ✅ **Lazy Loading**: Factory components load on-demand
- ✅ **Request Optimization**: Efficient API calls with caching
- ✅ **Memory Management**: Proper cleanup of agent instances
- 🔄 **Bundle Optimization**: Code splitting (planned)

## 🧪 **Testing & Quality Assurance**

### Automated Testing (Recommended)

```python
# Example test structure
def test_agent_creation():
    factory = AgentFactory()
    agent_config = AgentConfig(
        name="Test Agent",
        role="planner",
        model="qwen/qwen3-30b-a3b",
        instructions="Test instructions"
    )
    agent = await factory.create_agent(agent_config)
    assert agent.id is not None
    assert agent.config.name == "Test Agent"

def test_swarm_execution():
    # Test end-to-end swarm execution
    pass
```

### Manual Testing Checklist

- [ ] Template loading works correctly
- [ ] Agent configuration updates properly
- [ ] Cost estimation displays accurately
- [ ] Swarm creation succeeds
- [ ] Swarm execution returns results
- [ ] Error handling displays helpful messages
- [ ] Accessibility features function properly

## 🔮 **Roadmap**

### Phase 2: Sophia Business Integration (4-6 weeks)

- **Business Templates**: Sales, Support, Analytics swarms
- **CRM Integration**: HubSpot, Salesforce connectivity
- **Workflow Automation**: Business process orchestration
- **Multi-tenancy**: Client data isolation
- **Role-based Access**: Business user vs developer permissions

### Phase 3: Advanced Features (8-10 weeks)

- **Meta-Factory**: AI that creates better factories
- **Auto-optimization**: Performance-based agent tuning
- **Pattern Learning**: Discover optimal swarm configurations
- **Advanced Analytics**: Performance dashboards, cost analysis
- **Template Marketplace**: Share and discover swarm patterns

## 🛠️ **Development Setup**

### Prerequisites

- Python 3.11+
- Node.js 18+ (for UI development)
- OpenRouter API key
- MCP server running on port 3333

### Quick Start

```bash
# 1. Start MCP server
cd ~/sophia-intel-ai
python3 -m uvicorn dev_mcp_unified.core.mcp_server:app --host 127.0.0.1 --port 3333 --reload

# 2. Open factory interface
open "file:///Users/lynnmusil/sophia-intel-ai/dev-mcp-unified/ui/multi-chat-artemis.html"

# 3. Test API endpoints
curl http://127.0.0.1:3333/api/factory/health
```

## 📋 **Contributing**

### Code Quality Standards

- **Security**: All inputs validated, XSS prevention required
- **Accessibility**: WCAG 2.1 AA compliance mandatory
- **Performance**: < 3s page load, < 5s API responses
- **Testing**: Unit tests for all new functionality
- **Documentation**: Inline comments and README updates

### Review Process

1. **UX Review**: Ensure usability and accessibility
2. **Code Review**: Security, performance, maintainability
3. **Testing**: Manual and automated test coverage
4. **Integration**: Verify MCP server compatibility

## 🎯 **Key Insights & Observations**

1. **🧬 Multi-Agent Synergy**: The enhanced swarm with 4 agents (Planner → Generator → Security Reviewer → Quality Reviewer) demonstrates true AI collaboration, with each agent building on the previous work.

2. **⚡ Performance-First Design**: Real-time cost estimation and live testing sandbox make the Factory immediately practical rather than just experimental.

3. **🌉 Bridge to Business**: The namespace architecture (`artemis:*` vs `sophia:*`) and tab-based UI create clear separation while sharing infrastructure, enabling smooth expansion to business use cases.

The Agent Factory represents a significant advancement in making AI swarm orchestration accessible and practical for both technical and business users. The foundation is solid for continued evolution into a comprehensive AI automation platform.
