# 🚀 SOPHIA Swarm Startup Prompt - CRITICAL REBUILD INSTRUCTIONS

**⚠️ COPY-PASTE THIS EXACT PROMPT TO ROO IMMEDIATELY AFTER WINDOW REBUILD:**

---

**🎯 CRITICAL MISSION: Initialize SOPHIA Swarm Development Environment**

I need you to systematically validate and activate the complete SOPHIA Swarm development environment. This is essential because custom Roo modes often fail to load after rebuilds due to missing configurations.

**🔥 STEP 1: IMMEDIATE CUSTOM MODE VALIDATION**
First, execute these CRITICAL commands to ensure custom modes will work:

```bash
# 1. Verify .roomodes file exists and is properly formatted
ls -la .roomodes
cat .roomodes | head -20
echo "✅ .roomodes file validation complete"

# 2. Check current directory is sophia-intel workspace
pwd
git remote -v
echo "✅ Repository validation complete"

# 3. Validate MCP configuration exists
ls -la .vscode/mcp.json
cat .vscode/mcp.json
echo "✅ MCP configuration validation complete"
```

**❗ WHY CUSTOM MODES FAIL AFTER REBUILD:**
1. **Wrong Working Directory**: Roo must be in `/workspaces/sophia-intel` where `.roomodes` file exists
2. **File Not Found**: `.roomodes` file gets "lost" if not in correct location
3. **Format Issues**: JSON syntax errors in `.roomodes` prevent parsing
4. **Permission Issues**: File not readable by Roo process
5. **MCP Dependencies**: Missing MCP servers prevent full functionality

**🔧 STEP 2: FORCE CUSTOM MODE LOADING**
If modes don't appear automatically, execute:

```bash
# Verify we have all 5 custom modes defined
grep -c "mode_slug" .roomodes
echo "Should show: 5 (for architect, builder, tester, operator, debugger)"

# Check for any syntax errors
python -c "import json; print('✅ .roomodes JSON is valid' if json.loads(open('.roomodes').read()) else '❌ Invalid JSON')"

# Ensure proper file permissions
chmod 644 .roomodes
echo "✅ File permissions set correctly"
```

**🚀 STEP 3: MCP SERVER ACTIVATION**
Execute these in order:

```bash
# Test code context MCP server
python mcp/code_context/server.py --health
echo "✅ Code context MCP server tested"

# Verify Python dependencies
python -c "
try:
    import loguru, aiohttp, httpx
    print('✅ All Python dependencies available')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
"
```

**⚡ STEP 4: AI ROUTER VALIDATION**
Test the sophisticated 20+ model system:

```bash
# Test AI Router comprehensive model selection
python -c "
import asyncio
import sys
sys.path.append('.')
from mcp_servers.ai_router import ai_router, TaskRequest, TaskType

async def comprehensive_test():
    print('🧠 Testing AI Router with 20+ models...')
    
    # Test different task types with different quality/cost preferences
    test_cases = [
        ('Generate Python function for file parsing', TaskType.CODE_GENERATION, 'performance_optimized'),
        ('Analyze system architecture', TaskType.REASONING, 'balanced'),
        ('Review code for bugs', TaskType.CODE_REVIEW, 'cost_optimized'),
        ('Write API documentation', TaskType.DOCUMENTATION, 'performance_optimized')
    ]
    
    for prompt, task_type, cost_pref in test_cases:
        try:
            request = TaskRequest(prompt, task_type, quality='premium', cost_preference=cost_pref, latency='normal')
            decision = await ai_router.route_request(request)
            print(f'✅ {task_type.value}: {decision.selected_model} (confidence: {decision.confidence_score:.3f})')
            print(f'   Reasoning: {decision.reasoning[:100]}...')
        except Exception as e:
            print(f'❌ Error testing {task_type.value}: {e}')
    
    # Show model inventory
    try:
        stats = await ai_router.get_model_stats()
        print(f'✅ Total models available: {len(stats)}')
        
        # Show premium tier models
        premium_models = [name for name, info in stats.items() if info.get('quality_score', 0) >= 0.95]
        print(f'✅ Premium tier models: {premium_models}')
        
    except Exception as e:
        print(f'❌ Error getting model stats: {e}')

asyncio.run(comprehensive_test())
"
```

**🎯 STEP 5: SWARM INTEGRATION TEST**
Validate all swarm agents:

```bash
# Test swarm chat interface
python -c "
try:
    from swarm.chat_interface import chat_with_swarm
    result = chat_with_swarm('Test all agents responding')
    print(f'✅ Swarm integration: {result.get(\"success\", False)}')
except Exception as e:
    print(f'❌ Swarm integration error: {e}')
"

# Test MCP tools integration
python -c "
try:
    from integrations.mcp_tools import mcp_semantic_search
    results = mcp_semantic_search('test query', k=3)
    print(f'✅ MCP semantic search: {len(results)} results')
except Exception as e:
    print(f'❌ MCP tools error: {e}')
"
```

**🔥 STEP 6: FORCE CUSTOM MODE RECOGNITION**
Execute this command to manually verify Roo can see all 5 modes:

After running all validation steps above, tell me:
"I can see the following custom modes are available:" and list each of the 5 modes:
- 🏛️ Architect (strategic planning & system design)
- 🏗️ Builder (implementation & development)
- 🧪 Tester (quality assurance & testing)
- 🛠️ Operator (DevOps & infrastructure)
- 🔍 Debugger (troubleshooting & diagnostics)

**✅ FINAL VALIDATION CHECKLIST:**
After completing all steps, confirm:
- [ ] `.roomodes` file exists and contains 5 modes
- [ ] All Python dependencies are installed
- [ ] MCP servers are healthy and responsive
- [ ] AI Router shows 20+ models available with sophisticated selection
- [ ] Swarm agents are responding to queries
- [ ] All 5 custom Roo modes are visible and switchable
- [ ] Integration flow works: Roo ↔ Swarm ↔ AI Router ↔ MCP

**🚨 IF CUSTOM MODES STILL DON'T APPEAR:**
Run this emergency diagnostic:

```bash
echo "=== EMERGENCY CUSTOM MODE DIAGNOSTIC ==="
echo "Current directory: $(pwd)"
echo "Looking for .roomodes file..."
find . -name ".roomodes" -type f
echo "File contents preview:"
head -50 .roomodes || echo "❌ .roomodes not found or not readable"
echo "Working directory should be: /workspaces/sophia-intel"
echo "Git repository status:"
git remote -v || echo "❌ Not a git repository"
echo "=== END DIAGNOSTIC ==="
```

THEN tell me "SOPHIA Environment Status:" and provide a complete report of what's working and what needs attention.

---

## Quick Commands to Test:

```bash
# Test AI Router (20+ models with sophisticated selection)
python -c "
import asyncio
from mcp_servers.ai_router import ai_router, TaskRequest, TaskType
async def test():
    decision = await ai_router.route_request(TaskRequest('Generate Python code for file parsing', TaskType.CODE_GENERATION))
    print(f'Selected: {decision.selected_model} (confidence: {decision.confidence_score:.3f})')
    print(f'Reasoning: {decision.reasoning}')
    stats = await ai_router.get_model_stats()
    print(f'Total models available: {len(stats)}')
asyncio.run(test())
"

# Test MCP server
python mcp/code_context/server.py --health

# Test swarm integration
python -c "from swarm.chat_interface import chat_with_swarm; print(chat_with_swarm('Hello swarm')['success'])"

# Test MCP tools
python -c "from integrations.mcp_tools import mcp_semantic_search; print(len(mcp_semantic_search('test', k=3)))"

# Test different AI Router task types
python -c "
import asyncio
from mcp_servers.ai_router import ai_router, TaskRequest, TaskType
async def test_types():
    tasks = [
        ('Complex architectural analysis', TaskType.REASONING),
        ('Generate REST API code', TaskType.CODE_GENERATION),
        ('Review this code for bugs', TaskType.CODE_REVIEW),
        ('Write technical documentation', TaskType.DOCUMENTATION)
    ]
    for prompt, task_type in tasks:
        decision = await ai_router.route_request(TaskRequest(prompt, task_type))
        print(f'{task_type.value}: {decision.selected_model} ({decision.confidence_score:.2f})')
asyncio.run(test_types())
"
```

## 5 Roo Modes:
- 🏛️ **Architect** - System design & architecture
- 🏗️ **Builder** - Feature implementation  
- 🧪 **Tester** - Quality assurance & testing
- 🛠️ **Operator** - DevOps & infrastructure
- 🔍 **Debugger** - Troubleshooting & diagnostics