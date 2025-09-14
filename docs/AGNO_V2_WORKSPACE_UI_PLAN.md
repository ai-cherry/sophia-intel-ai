# Agno AI v2 Setup Plan for workspace-ui
## Advanced Agent Framework with Portkey Gateway Integration

---

## 🎯 Overview
Implement the latest Agno AI v2 framework exclusively in workspace-ui repository with:
- **Portkey Gateway SDK** integration using virtual keys
- **MCP server connections** to sophia-intel-ai backend
- **Agent orchestration** with advanced workflows
- **Custom UI vs Agno UI** comparison and selection

---

## 🔥 Agno AI v2 Latest Features

### Core Improvements
1. **Agent Chains**: Sequential and parallel execution
2. **Memory Persistence**: Long-term context storage
3. **Tool Registry**: Dynamic tool loading
4. **Streaming Support**: Real-time agent responses
5. **Multi-Model Router**: Automatic model selection
6. **Observability**: Built-in tracing and metrics

### Architecture Components
```
workspace-ui/
├── agno/
│   ├── core/
│   │   ├── agent.ts          # Base agent class
│   │   ├── chain.ts          # Chain orchestration
│   │   ├── memory.ts         # Memory management
│   │   └── tools.ts          # Tool registry
│   ├── agents/
│   │   ├── architect.ts      # Planning agent
│   │   ├── coder.ts          # Implementation agent
│   │   ├── reviewer.ts       # Code review agent
│   │   └── tester.ts         # Testing agent
│   ├── providers/
│   │   ├── portkey.ts        # Portkey Gateway integration
│   │   └── mcp-client.ts     # MCP server connections
│   ├── ui/
│   │   ├── agno-ui.tsx       # Agno's built-in UI
│   │   └── custom-ui.tsx     # Custom UI implementation
│   └── config.yaml            # Configuration
```

---

## 🔑 Portkey Gateway SDK Integration

### Virtual Keys Configuration
```typescript
// agno/providers/portkey.ts
import { Portkey } from 'portkey-ai';

const portkey = new Portkey({
  apiKey: process.env.PORTKEY_API_KEY, // User key: p2pibAbU+7DU7fKTmUjfJ34qAZaz
  virtualKeys: {
    'anthropic-vk-b': process.env.ANTHROPIC_VK_B,
    'openai-vk-c': process.env.OPENAI_VK_C,
    'google-vk-d': process.env.GOOGLE_VK_D,
    'grok-vk-e': process.env.GROK_VK_E,
  },
  config: {
    retry: {
      attempts: 3,
      onFailedAttempt: (error) => {
        console.log(`Retry attempt ${error.attemptNumber}`);
      }
    },
    cache: {
      enabled: true,
      ttl: 300
    }
  }
});

// Model routing with virtual keys
export const modelRouter = {
  'claude-opus-4.1': 'anthropic-vk-b',
  'gpt-4-turbo': 'openai-vk-c',
  'gemini-pro': 'google-vk-d',
  'grok-2': 'grok-vk-e'
};
```

### Environment Setup
```bash
# workspace-ui/.env
PORTKEY_API_KEY=p2pibAbU+7DU7fKTmUjfJ34qAZaz
ANTHROPIC_VK_B=@anthropic-vk-b  # Virtual key with @ prefix for SDK
OPENAI_VK_C=@openai-vk-c
GOOGLE_VK_D=@google-vk-d
GROK_VK_E=@grok-vk-e
```

---

## 🎨 UI Comparison: Agno UI vs Custom UI

### Agno Built-in UI
**Pros:**
- Ready-to-use agent interface
- Built-in chat, workflow visualization
- Automatic tool rendering
- Real-time streaming support
- Dark/light theme included

**Cons:**
- Limited customization
- Fixed layout structure
- Opinionated design system

**Best for:** Rapid prototyping, standard agent interactions

### Custom UI Implementation
**Pros:**
- Full control over design
- Integration with existing design system
- Custom workflow builders
- Tailored user experience
- Brand consistency

**Cons:**
- More development time
- Need to implement streaming
- Manual tool UI creation

**Best for:** Production applications, specific UX requirements

### Recommendation: Hybrid Approach
```typescript
// Use Agno UI for agent interactions
import { AgnoChat } from '@agno/ui';

// Custom wrapper for branding
export const WorkspaceAgentUI = () => {
  return (
    <div className="workspace-ui-wrapper">
      <CustomHeader />
      <AgnoChat 
        agents={customAgents}
        theme={customTheme}
        onMessage={handleCustomLogic}
      />
      <CustomToolPanel />
    </div>
  );
};
```

---

## 📦 Implementation Steps

### Step 1: Install Agno v2 and Dependencies
```bash
cd workspace-ui
npm install @agno-agi/core@^2.0.0
npm install @agno-agi/ui@^2.0.0
npm install portkey-ai@latest
npm install @langchain/core@latest
```

### Step 2: Core Agent Implementation
```typescript
// agno/core/agent.ts
import { BaseAgent } from '@agno-agi/core';
import { portkey } from '../providers/portkey';

export class WorkspaceAgent extends BaseAgent {
  constructor(config: AgentConfig) {
    super({
      ...config,
      llm: portkey.completions,
      tools: this.registerTools(),
      memory: this.setupMemory()
    });
  }

  private registerTools() {
    return {
      mcp_memory: this.createMCPTool('memory', 8081),
      mcp_filesystem: this.createMCPTool('filesystem', 8082),
      mcp_git: this.createMCPTool('git', 8084),
      mcp_vector: this.createMCPTool('vector', 8085)
    };
  }

  private createMCPTool(name: string, port: number) {
    return {
      name: `mcp_${name}`,
      description: `Access MCP ${name} server`,
      execute: async (params: any) => {
        const response = await fetch(`http://localhost:${port}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(params)
        });
        return response.json();
      }
    };
  }
}
```

### Step 3: Agent Chain Configuration
```typescript
// agno/core/chain.ts
import { Chain } from '@agno-agi/core';

export const developmentChain = new Chain({
  name: 'Feature Development',
  agents: [
    { id: 'architect', model: 'claude-opus-4.1', virtualKey: 'anthropic-vk-b' },
    { id: 'coder', model: 'grok-2', virtualKey: 'grok-vk-e' },
    { id: 'tester', model: 'deepseek-v3', virtualKey: 'deepseek-vk-f' },
    { id: 'reviewer', model: 'claude-opus-4.1', virtualKey: 'anthropic-vk-b' }
  ],
  flow: {
    type: 'sequential',
    errorHandling: 'continue',
    timeout: 300
  }
});
```

### Step 4: Memory Integration with MCP
```typescript
// agno/core/memory.ts
export class MCPMemory {
  private memoryServer = 'http://localhost:8081';
  
  async store(key: string, value: any) {
    await fetch(`${this.memoryServer}/store`, {
      method: 'POST',
      body: JSON.stringify({ key, value })
    });
  }
  
  async retrieve(key: string) {
    const response = await fetch(`${this.memoryServer}/retrieve?key=${key}`);
    return response.json();
  }
  
  async search(query: string) {
    const response = await fetch(`${this.memoryServer}/search?query=${query}`);
    return response.json();
  }
}
```

---

## 🛠️ Advanced Tools and Features

### 1. Streaming Responses
```typescript
import { streamCompletion } from 'portkey-ai';

const stream = await portkey.completions.create({
  messages: [{ role: 'user', content: prompt }],
  model: 'claude-3-opus',
  virtualKey: 'anthropic-vk-b',
  stream: true
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || '');
}
```

### 2. Observability with Portkey
```typescript
// Enable tracing
portkey.config.tracing = {
  enabled: true,
  provider: 'portkey',
  tags: {
    environment: 'development',
    repository: 'workspace-ui'
  }
};
```

### 3. Cost Optimization
```typescript
// Automatic fallback to cheaper models
const costOptimizedRouter = {
  primary: { model: 'claude-opus', virtualKey: 'anthropic-vk-b' },
  fallback: { model: 'gpt-3.5-turbo', virtualKey: 'openai-vk-c' },
  conditions: {
    maxCost: 0.10,  // Switch to fallback if cost exceeds
    maxLatency: 5000 // Switch if response time exceeds
  }
};
```

### 4. Caching Strategy
```typescript
// Semantic caching for similar queries
const cacheConfig = {
  semantic: true,
  similarity_threshold: 0.95,
  ttl: 3600,
  max_size: 1000
};
```

---

## 🚀 CLI Commands for Agno

### Package.json Scripts
```json
{
  "scripts": {
    "agno:init": "agno init --config ./agno/config.yaml",
    "agno:dev": "agno dev --port 3202",
    "agno:agents": "agno agents list",
    "agno:chain": "agno chain run development",
    "agno:ui": "agno ui --mode hybrid",
    "agno:test": "agno test --coverage",
    "agno:deploy": "agno deploy --env production"
  }
}
```

---

## 📊 Monitoring Dashboard

### Metrics to Track
1. **Agent Performance**
   - Response times per agent
   - Token usage per model
   - Cost per operation
   - Success/failure rates

2. **Portkey Analytics**
   - Virtual key usage
   - Model distribution
   - Latency patterns
   - Error rates

3. **MCP Health**
   - Server availability
   - Response times
   - Memory usage
   - Connection pool status

---

## 🔒 Security Best Practices

1. **Virtual Key Rotation**
   - Rotate keys monthly
   - Use different keys per environment
   - Monitor key usage

2. **Rate Limiting**
   - Per-agent limits
   - Per-user quotas
   - Burst protection

3. **Audit Logging**
   - All agent actions
   - Model selections
   - Tool executions
   - Cost tracking

---

## 📝 Configuration Templates

### Complete agno/config.yaml
```yaml
version: "2.0"
name: "Workspace UI Agents"

providers:
  portkey:
    api_key: ${PORTKEY_API_KEY}
    virtual_keys:
      anthropic: ${ANTHROPIC_VK_B}
      openai: ${OPENAI_VK_C}
      google: ${GOOGLE_VK_D}
      grok: ${GROK_VK_E}

agents:
  - id: architect
    model: claude-opus-4.1
    provider: portkey
    virtual_key: anthropic
    temperature: 0.2
    max_tokens: 4096
    
  - id: coder
    model: grok-2
    provider: portkey
    virtual_key: grok
    temperature: 0.3
    max_tokens: 8192

chains:
  development:
    agents: [architect, coder, tester, reviewer]
    type: sequential
    
  debug:
    agents: [coder, tester]
    type: parallel

ui:
  mode: hybrid  # agno|custom|hybrid
  port: 3202
  theme: dark
  
monitoring:
  enabled: true
  metrics_port: 9091
  
security:
  rate_limit: 100
  audit_log: true
```

---

## ✅ Validation Checklist

- [ ] Agno v2 installed and configured
- [ ] Portkey SDK integrated with virtual keys
- [ ] All agents defined and tested
- [ ] MCP connections verified
- [ ] UI mode selected and implemented
- [ ] Streaming responses working
- [ ] Caching configured
- [ ] Monitoring dashboard accessible
- [ ] Security measures in place
- [ ] Documentation complete

---

## 🎯 Next Steps

1. **Immediate Actions**
   - Install Agno v2 packages
   - Configure Portkey with virtual keys
   - Set up agent definitions

2. **Testing Phase**
   - Test each agent individually
   - Verify chain execution
   - Validate MCP connections

3. **Production Readiness**
   - Performance optimization
   - Error handling
   - Deployment configuration