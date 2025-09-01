# Fly.io Machine Inventory - Sophia Intel AI Enterprise Infrastructure

**🚨 ENTERPRISE AI INFRASTRUCTURE - COMPLEX MACHINE ALLOCATION**  
**Account**: musillynn@gmail.com | **Organization**: personal | **Total Machines**: 7-58

## 🏗️ **REAL Machine Allocation (vs Simple Demo Apps)**

### **Why We Need More Machines Than Hello-Fly:**

**Hello-Fly Demo**: 2 machines (simple NodeJS app)  
**Sophia Intel AI**: **7-58 machines** (enterprise AI with agent swarms, MCP servers, multi-tier embeddings)

---

## 🤖 **ENTERPRISE AI MACHINE SPECIFICATIONS**

### **1. sophia-api (Main Orchestrator) 🔥 CRITICAL**
```yaml
Purpose: "Agent Swarms + Multi-LLM Orchestration + Consensus Systems"
Configuration:
  min_machines: 2           # High availability baseline
  max_machines: 20          # Enterprise scaling for agent swarms
  cpus: 4                   # High CPU for agent coordination
  memory_mb: 4096          # 4GB for complex swarm operations
  storage: "15GB"          # Main data storage
  
Auto-scaling Triggers:
  - CPU > 60% (earlier scaling for agents)
  - Memory > 70%
  - Requests > 150/min
  - Response time > 200ms
  
Workloads:
  - Multi-agent swarm coordination
  - Consensus decision making
  - LLM gateway management (Portkey)
  - GPU task orchestration (Lambda Labs)
  - Real-time agent communication
```

### **2. sophia-vector (3-Tier Embedding Engine)**
```yaml
Purpose: "Voyage + Cohere + BGE Multi-Model Embedding Processing"
Configuration:
  min_machines: 1
  max_machines: 12          # High scaling for embedding workloads
  cpus: 2
  memory_mb: 2048
  storage: "10GB"          # Embedding cache
  
Auto-scaling Triggers:
  - CPU > 65% (lower threshold for embeddings)
  - Memory > 70%
  - Requests > 80/min (embedding requests are intensive)
  
Workloads:
  - Voyage API embedding processing
  - Cohere multilingual embeddings  
  - BGE model inference
  - Embedding similarity search
  - Vector cache management
```

### **3. sophia-mcp (Memory Management Protocol)**
```yaml
Purpose: "MCP Server + Unified Memory + Agent State Management"
Configuration:
  min_machines: 1
  max_machines: 8           # Scaling for memory operations
  cpus: 2
  memory_mb: 2048
  storage: "5GB"           # Memory state storage
  
Auto-scaling Triggers:
  - CPU > 70%
  - Memory > 75%
  - Requests > 100/min
  
Workloads:
  - MCP protocol server
  - Unified memory management
  - Agent state persistence
  - Memory deduplication
  - Cross-agent memory sharing
```

### **4. sophia-weaviate (Vector Database)**
```yaml
Purpose: "Weaviate v1.32 + Vector Storage + Knowledge Graph"
Configuration:
  min_machines: 1
  max_machines: 4           # Database scaling
  cpus: 2
  memory_mb: 2048
  storage: "20GB"          # Largest storage for vectors
  
Auto-scaling Triggers:
  - CPU > 70%
  - Memory > 75%
  
Workloads:
  - Vector similarity search
  - Knowledge graph storage
  - Multi-tenancy support
  - RQ compression (75% memory reduction)
  - Cluster coordination
```

### **5. sophia-bridge (UI Compatibility Bridge)**
```yaml
Purpose: "Agent-UI Communication + Legacy API Support"
Configuration:
  min_machines: 1
  max_machines: 8           # UI scaling
  cpus: 1
  memory_mb: 1024
  storage: "2GB"
  
Auto-scaling Triggers:
  - CPU > 70%
  - Memory > 75%
  
Workloads:
  - Agent-UI communication bridge
  - Legacy API compatibility
  - WebSocket connections
  - Real-time agent updates
```

### **6. sophia-ui (Next.js Frontend)**
```yaml
Purpose: "Agent Interface + Real-time Dashboard + User Interaction"
Configuration:
  min_machines: 1
  max_machines: 6           # Frontend scaling
  cpus: 1
  memory_mb: 1024
  storage: "1GB"
  
Auto-scaling Triggers:
  - CPU > 70%
  - Memory > 75%
  
Workloads:
  - Next.js frontend serving
  - Real-time agent dashboard
  - User interaction handling
  - Static asset serving
```

---

## 📊 **TOTAL MACHINE CAPACITY**

### **Machine Count Summary**
```
Minimum Configuration (Low Load):     7 machines
Maximum Configuration (Peak Load):   58 machines

Service Breakdown:
  sophia-api (Main):      2-20 machines  (🔥 CRITICAL - Agent Swarms)
  sophia-vector:          1-12 machines  (3-Tier Embeddings)
  sophia-mcp:             1-8 machines   (MCP + Memory)
  sophia-weaviate:        1-4 machines   (Vector Database)
  sophia-bridge:          1-8 machines   (UI Bridge)
  sophia-ui:              1-6 machines   (Frontend)
```

### **Why This is NOT Like Hello-Fly**
| Aspect | Hello-Fly Demo | Sophia Intel AI Enterprise |
|--------|----------------|----------------------------|
| **Purpose** | Simple web demo | Enterprise AI with agent swarms |
| **Machines** | 2 static | 7-58 auto-scaling |
| **CPU** | 1 CPU shared | 4-15 CPUs distributed |
| **Memory** | 1GB total | 8-29GB distributed |
| **Storage** | None | 53GB persistent volumes |
| **Services** | 1 simple app | 6 microservices |
| **Workloads** | Static content | AI agents, embeddings, memory, vectors |
| **Scaling** | Manual | Intelligent auto-scaling |

## 🚀 **Machine Addition Commands for AI Workloads**

### **Add Machines for Agent Swarms**
```bash
# Scale main API for agent swarm operations
flyctl machines create --app sophia-api --region sjc --cpu-kind shared --cpus 4 --memory 4096
flyctl machines create --app sophia-api --region iad --cpu-kind shared --cpus 4 --memory 4096

# Scale embedding processing for multi-tier workloads
flyctl machines create --app sophia-vector --region sjc --cpu-kind shared --cpus 2 --memory 2048
flyctl machines create --app sophia-vector --region iad --cpu-kind shared --cpus 2 --memory 2048

# Scale MCP servers for memory management
flyctl machines create --app sophia-mcp --region sjc --cpu-kind shared --cpus 2 --memory 2048
```

### **High-Load Scaling (Agent Swarm Peak Usage)**
```bash
# Scale to handle multiple concurrent agent swarms
flyctl scale count 15 --app sophia-api      # 15 main orchestrator machines
flyctl scale count 8 --app sophia-vector    # 8 embedding machines  
flyctl scale count 6 --app sophia-mcp       # 6 memory management machines
flyctl scale count 3 --app sophia-weaviate  # 3 vector database machines

# Total: 32 machines for peak AI workloads
```

## 🔧 **Current Applications & Machine Status**

### **✅ Created Applications (Ready for Complex Deployment)**
```
sophia-weaviate    → Vector Database (Foundation)
sophia-mcp         → MCP Memory Protocol Server  
sophia-vector      → 3-Tier Embedding Engine
sophia-api         → Agent Swarm Orchestrator 🔥 CRITICAL
sophia-bridge      → UI Compatibility Bridge
sophia-ui          → Agent Dashboard Frontend
```

### **🔄 Current Deployment Status**
```
sophia-weaviate:  🔄 DEPLOYING (20GB vector storage + Weaviate 1.32)
sophia-mcp:       ⏳ PENDING   (MCP protocol + unified memory)
sophia-vector:    ⏳ PENDING   (Voyage/Cohere/BGE embeddings)
sophia-api:       ⏳ PENDING   (Main agent orchestrator)
sophia-bridge:    ⏳ PENDING   (Agent-UI bridge)
sophia-ui:        ⏳ PENDING   (Agent dashboard frontend)
```

## 💡 **Enterprise AI Scaling Strategy**

### **Intelligent Auto-scaling for AI Workloads**
```bash
# Agent Swarm Scaling Triggers:
CPU > 60%     → Add sophia-api machines (agent coordination)
Memory > 70%  → Add sophia-mcp machines (memory management)
Requests > 80 → Add sophia-vector machines (embedding processing)

# Peak Load Response:
Agent Swarms Active    → Scale sophia-api to 15-20 machines
Embedding Requests     → Scale sophia-vector to 8-12 machines  
Memory Operations      → Scale sophia-mcp to 6-8 machines
Vector Queries         → Scale sophia-weaviate to 3-4 machines
```

### **Production Workload Expectations**
- **Concurrent Agent Swarms**: 5-20 simultaneous swarms
- **Embedding Requests**: 1000+ requests/minute (3 models)
- **Memory Operations**: Complex unified memory with deduplication
- **Vector Queries**: High-dimensional similarity search
- **Real-time Dashboard**: Live agent monitoring and control

---

**🎯 ENTERPRISE SCALE**: This is **NOT a simple web app** - it's a **sophisticated AI infrastructure** requiring **intelligent machine allocation** for **agent swarms, multi-tier embeddings, and complex memory management**.

**Machine Philosophy**: **Auto-scale from 7→58 machines** based on **AI workload demands**, not static allocation like simple demos.