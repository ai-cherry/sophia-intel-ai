# 🎯 Artemis Scout Swarm Enhancement Plan
*Unified strategy based on Claude & Codex analysis*

## 📊 Current State Summary

### ✅ Operational Components
- **API Keys**: Fully configured (OpenRouter, DeepSeek, Weaviate, Portkey)
- **MCP stdio**: Working for fs/git/memory operations
- **Agent Factory**: Task-specific routing with manual LLM selection
- **Collaboration**: Schema v2 with multi-agent approval workflow

### ⚠️ Critical Gaps
1. **No Code Indexing Pipeline**: Scouts run blind without pre-indexed repository
2. **Weaviate Not Active**: Vector DB configured but not running
3. **No Agent Tool Use**: Agents can't directly request file reads via MCP
4. **Generic Prompts**: Missing scout-specific heuristics and output schemas

## 🚀 Near-Term Plan (Days 1-3)

### Day 1: Foundation & Readiness
```bash
# 1. Start required services
docker-compose up -d weaviate redis

# 2. Load environment variables
source .env.artemis.local

# 3. Test basic connectivity
./bin/artemis-run smoke  # Verify stdio MCP works
```

### Day 2: Scout Prefetch & Index
Create prefetch step in scout execution:

```python
# Add to scout execution flow
async def prefetch_and_index_repository(client, path: Path):
    """Pre-index repository for scout context"""
    # 1. Use stdio MCP to get repo summary
    repo_index = await client.repo_index(max_files=100)
    
    # 2. Sample key files (200-500KB max)
    key_files = select_hotspot_files(repo_index)
    
    # 3. Generate embeddings and store
    chunks = create_code_chunks(key_files)
    await memory_router.upsert_chunks(chunks, domain="artemis")
    
    return {"indexed_files": len(key_files), "chunks": len(chunks)}
```

### Day 3: Enhanced Scout Prompts
Upgrade scout personas with specific output schemas:

```python
SCOUT_OUTPUT_SCHEMA = """
## FINDINGS
- Key patterns and architecture insights
- Integration points and dependencies
- Performance bottlenecks

## INTEGRATIONS
- External service connections
- API surface area
- Data flow mappings

## RISKS
- Security vulnerabilities
- Scalability concerns
- Technical debt hotspots

## RECOMMENDATIONS
- Priority improvements (1-3)
- Quick wins
- Long-term refactoring needs

## METRICS
- Code complexity scores
- Test coverage gaps
- Dependency health
"""
```

## 📅 Mid-Term Plan (Week 1-2)

### Week 1: Agent Tool Affordances

#### Enable MCP Tool Calls in Agent Loop
```python
class ToolAwareAgent(MicroSwarmAgent):
    async def process_with_tools(self, task, context):
        # Allow agents to request file samples
        response = await self.llm_complete(task, context)
        
        if "REQUEST_FS_READ:" in response:
            file_path = extract_path(response)
            content = await self.mcp_client.read_file(file_path, max_bytes=5000)
            # Re-invoke with file content
            return await self.llm_complete(task, context + content)
        
        return response
```

#### Implement Code-Aware Indexing
- Language-specific chunking (Python/TS/JS/Go)
- Maintain path metadata and import graphs
- Delta indexing based on git diff
- Store in Weaviate with hybrid search

### Week 2: Production Readiness

#### Structured Scout Reports
```markdown
# Scout Report - {timestamp}
Repository: {repo_name}
Scout Team: Tag Hunter, Integration Stalker, Scale Assassin

## Executive Summary
{high_level_findings}

## Detailed Analysis
{per_agent_insights}

## Action Items
- [ ] Priority 1: {action}
- [ ] Priority 2: {action}
- [ ] Priority 3: {action}

## Metrics Dashboard
- Files Analyzed: {count}
- Patterns Detected: {count}
- Risk Score: {score}/10
```

#### Evaluation Harness
- Synthetic test repositories with known issues
- Measure scout accuracy and coverage
- Track performance metrics

## 🛠️ Implementation Checklist

### Immediate Actions (Today)
- [ ] Start Weaviate container
- [ ] Verify all API keys loaded from .env.artemis.local
- [ ] Run `./bin/artemis-run smoke` to verify base functionality
- [ ] Test scout with simple task (no index required)

### Quick Wins (This Week)
- [ ] Add `--check` flag to scout command for readiness verification
- [ ] Implement basic prefetch for top 10 changed files
- [ ] Add scout-specific output schema to prompts
- [ ] Create SCOUT_REPORT.md template

### Infrastructure (Next Sprint)
- [ ] Deploy code indexing daemon
- [ ] Setup hybrid search (keywords + vectors)
- [ ] Add metrics collection and dashboard
- [ ] Create scout performance benchmarks

## 🎯 Success Metrics

### Phase 1 (Days 1-3)
- Scout runs successfully with basic context
- Weaviate stores and retrieves embeddings
- Structured output from all three agents

### Phase 2 (Week 1-2)
- 80% of integration points identified
- <30 second response time for scout analysis
- Actionable recommendations in every report

### Phase 3 (Sprint 2)
- Fully automated code indexing pipeline
- Agent tool use for targeted file analysis
- Scout accuracy >85% on test repositories

## 🔧 Environment Configuration

### Required Environment Variables
```bash
# Core Services
WEAVIATE_URL=https://w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud
WEAVIATE_API_KEY=VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf

# Embeddings
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-ada-002
OPENAI_API_KEY=sk-svcacct-...

# Scout Swarm LLMs
LLM_ANALYST_PROVIDER=openrouter
LLM_ANALYST_MODEL=qwen/qwen3-coder
LLM_STRATEGIST_PROVIDER=openrouter
LLM_STRATEGIST_MODEL=openrouter/sonoma-sky-alpha
LLM_VALIDATOR_PROVIDER=openrouter
LLM_VALIDATOR_MODEL=deepseek/deepseek-chat-v3-0324

# Portkey
PORTKEY_API_KEY=nYraiE8dOR9A1gDwaRNpSSXRkXBc
```

### Service Dependencies
```yaml
# docker-compose.yml additions
services:
  weaviate:
    image: semitechnologies/weaviate:latest
    ports:
      - "8080:8080"
    environment:
      AUTHENTICATION_APIKEY_ENABLED: 'true'
      AUTHENTICATION_APIKEY_ALLOWED_KEYS: ${WEAVIATE_API_KEY}
      
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

## 📝 Next Concrete Actions

1. **Lynn to approve**: This enhancement plan and priority order
2. **Codex to emit**: Schema v2 proposal with scout enhancements
3. **Implementation**:
   - Add readiness check to scout command
   - Create prefetch/index integration
   - Enhance scout prompts with schemas
   - Add smoke test for offline validation

## 🎉 Expected Outcomes

### Immediate (24 hours)
- Scout swarm runs with real repository context
- Structured, actionable output from analysis
- Clear visibility into what's working/missing

### Short-term (1 week)
- Automated code indexing before scout runs
- Agents can request specific file contents
- Reproducible scout reports with metrics

### Long-term (2 weeks)
- Production-ready scout with <1 minute analysis
- 85%+ accuracy on detecting integration points
- Scalable to 1M+ LOC repositories

---

*This plan synthesizes insights from both Claude and Codex analyses, leveraging existing API keys and infrastructure while addressing critical gaps in the scout swarm implementation.*