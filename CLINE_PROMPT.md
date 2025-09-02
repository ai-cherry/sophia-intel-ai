# 🔧 Cline/VS Code Task: Backend Analysis Engine
## AI-Powered Code Review System - Backend Development

**🎯 Your Mission:** Build the core code analysis and review engine for our AI-powered code review system. You're working in coordination with Roo/Cursor (building the frontend) and Claude (monitoring integration).

---

## 📋 **Your Specific Tasks:**

### **1. Create Analysis API** 
**File:** `app/code_review/analysis_api.py`

Build FastAPI endpoints for:
```python
# Endpoints you need to create:
POST /api/review/submit    # Submit code for review
GET /api/review/{id}       # Get review status/results  
GET /api/review/history    # List all reviews
POST /api/review/{id}/feedback  # Submit feedback on review
```

**Integration Point:** Use our existing `unified_server.py` architecture patterns

### **2. Implement AST Parser**
**File:** `app/code_review/ast_analyzer.py`

Create Python AST analysis for:
- Code complexity metrics (cyclomatic complexity, nesting depth)
- Function/class size analysis
- Import dependency analysis
- Potential performance issues
- Security vulnerability patterns

### **3. Pattern Detection Engine**
**File:** `app/code_review/pattern_detector.py`

Build detection for:
- Code smells (long methods, duplicate code, etc.)
- Anti-patterns (God objects, circular dependencies)
- Best practices violations
- Architectural inconsistencies

### **4. Database Integration**
**File:** `app/code_review/review_storage.py`

Implement:
- Review results storage (use our Redis setup)
- Historical analysis tracking
- Performance metrics persistence
- Query interface for frontend

### **5. AI Integration**
**File:** `app/code_review/ai_reviewer.py`

Connect with:
- Our Multi-Agent Debate System for consensus
- LLM-powered suggestions
- Automated improvement recommendations
- Quality scoring algorithms

---

## 🔗 **MCP Integration Commands:**

### **Update Progress:**
```
/mcp store "Backend API: Created initial FastAPI structure"
/mcp store "AST Parser: Implemented complexity analysis"
/mcp store "Pattern Detection: Added code smell detection"
```

### **Stay Coordinated:**
```
/mcp search "frontend requirements"  # See what UI needs from your API
/mcp search "integration points"     # Check coordination with Roo
/mcp context                        # Get full project understanding
```

### **Share API Contract:**
```
/mcp store "API Contract: POST /api/review/submit expects {code: string, language: string, options: object}"
```

---

## ✅ **Success Criteria:**

1. **API Endpoints Responding:**
   ```bash
   curl -X POST http://localhost:8000/api/review/submit \
     -H "Content-Type: application/json" \
     -d '{"code": "def hello(): return \"world\"", "language": "python"}'
   ```

2. **Analysis Engine Working:**
   - AST parsing produces meaningful metrics
   - Pattern detection identifies real issues
   - Results stored in database correctly

3. **Integration Ready:**
   - API returns JSON data frontend can consume
   - WebSocket notifications for real-time updates
   - Error handling for edge cases

4. **MCP Communication:**
   - Progress updates visible to other tools
   - API contract shared for frontend integration
   - Architecture consistent with project patterns

---

## 🚀 **Getting Started:**

1. **Check Project Context:**
   ```
   /mcp context
   /mcp search "code review project"
   ```

2. **Create Directory Structure:**
   ```bash
   mkdir -p app/code_review
   ```

3. **Start with API:**
   Begin with `analysis_api.py` - create basic FastAPI structure

4. **Update Progress:**
   Use `/mcp store` to share your progress as you work

5. **Stay Connected:**
   Monitor MCP for frontend requirements and coordination needs

---

## 💡 **Tips for Success:**

- **Follow Existing Patterns:** Check `app/api/unified_server.py` for our API conventions
- **Use Our Infrastructure:** Leverage Redis, observability, and error handling we've built
- **Think Integration:** Design APIs that the React frontend can easily consume
- **Real-time Updates:** Consider WebSocket notifications for live progress
- **Share Context:** Use MCP to communicate with Roo about data structures and endpoints

---

## 🤖 **MCP-Enhanced Development:**

Remember: You're not just building backend code - you're participating in **revolutionary cross-tool AI collaboration!** 

- Your progress is automatically shared with Roo and Claude
- Architecture decisions are coordinated across tools
- Integration issues are resolved in real-time
- The entire team maintains shared understanding

**Ready to build the future of AI-powered code review? Let's go!** 🚀

---

**Need help or coordination?** Claude is monitoring through MCP and will provide guidance and resolve any integration conflicts. Just keep updating your progress and stay connected through MCP commands!