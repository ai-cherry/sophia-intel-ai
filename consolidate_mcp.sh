#!/bin/bash

echo "=========================================="
echo "🔧 MCP CONSOLIDATION SCRIPT"
echo "Consolidating all MCP implementations into mcp-unified"
echo "=========================================="

# Check if mcp-unified exists
if [ ! -d "mcp-unified" ]; then
    echo "Creating mcp-unified directory structure..."
    mkdir -p mcp-unified/{servers,gateway,clients,shared,config}
fi

# Create the unified MCP configuration
cat > mcp-unified/config/mcp_config.yaml << 'EOF'
# Unified MCP Configuration
servers:
  memory:
    port: 8081
    host: localhost
    database: postgresql://localhost/mcp_memory
    
  git:
    port: 8082
    host: localhost
    
  context:
    port: 8083
    host: localhost
    
  index:
    port: 8084
    host: localhost

gateway:
  port: 8080
  host: localhost
  
agents:
  - id: claude-cli
    permissions: [read, write, memory, index]
  - id: builder-agno
    permissions: [read, write, memory, index]
  - id: sophia-intel
    permissions: [read, memory]
  - id: codex
    permissions: [read, write, memory, index]
  - id: cursor
    permissions: [read, write, memory, index]
    
meta_tags:
  domains: [builder, sophia, business, code]
  actions: [create, modify, delete, read]
  entities: [file, function, api, component]
  quality: [production, test, experimental]
  impact: [high, medium, low]
EOF

# Create the gateway router
cat > mcp-unified/gateway/router.py << 'EOF'
"""
MCP Gateway Router - Central hub for all MCP traffic
"""
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class MCPRequest(BaseModel):
    agent_id: str
    operation: str
    data: Dict[str, Any]
    meta_tags: Optional[Dict[str, Any]] = None

class MCPGateway:
    """Central router for all MCP traffic"""
    
    def __init__(self):
        self.servers = {
            'memory': 'http://localhost:8081',
            'git': 'http://localhost:8082',
            'context': 'http://localhost:8083',
            'index': 'http://localhost:8084'
        }
        self.connected_agents = {}
        
    async def route_request(self, request: MCPRequest) -> Dict[str, Any]:
        """Route request to appropriate MCP server"""
        # Validate agent permissions
        if not self.check_permissions(request.agent_id, request.operation):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Auto-generate meta tags if not provided
        if not request.meta_tags:
            request.meta_tags = self.generate_meta_tags(request)
        
        # Route based on operation type
        if request.operation.startswith('memory.'):
            return await self.route_to_memory(request)
        elif request.operation.startswith('git.'):
            return await self.route_to_git(request)
        elif request.operation.startswith('context.'):
            return await self.route_to_context(request)
        elif request.operation.startswith('index.'):
            return await self.route_to_index(request)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation: {request.operation}")
    
    def check_permissions(self, agent_id: str, operation: str) -> bool:
        """Check if agent has permission for operation"""
        # Implementation based on config
        return True  # Placeholder
    
    def generate_meta_tags(self, request: MCPRequest) -> Dict[str, Any]:
        """Auto-generate meta tags for request"""
        tags = {
            'agent': request.agent_id,
            'timestamp': asyncio.get_event_loop().time(),
            'operation': request.operation
        }
        
        # Analyze operation to add domain tags
        if 'builder' in request.agent_id.lower():
            tags['domain'] = 'builder'
        elif 'sophia' in request.agent_id.lower():
            tags['domain'] = 'sophia'
            
        return tags
    
    async def route_to_memory(self, request: MCPRequest):
        """Route to memory server"""
        # Implementation
        pass
    
    async def route_to_git(self, request: MCPRequest):
        """Route to git server"""
        # Implementation
        pass
    
    async def route_to_context(self, request: MCPRequest):
        """Route to context server"""
        # Implementation
        pass
    
    async def route_to_index(self, request: MCPRequest):
        """Route to index server"""
        # Implementation
        pass

# FastAPI app
app = FastAPI(title="MCP Gateway", version="1.0.0")
gateway = MCPGateway()

@app.post("/mcp/request")
async def handle_request(request: MCPRequest):
    """Main endpoint for all MCP requests"""
    return await gateway.route_request(request)

@app.get("/mcp/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "servers": gateway.servers}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
EOF

# Create memory server
cat > mcp-unified/servers/memory.py << 'EOF'
"""
MCP Memory Server - Centralized memory management for all AI agents
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI
import asyncpg
import numpy as np
from sentence_transformers import SentenceTransformer

class MemoryServer:
    """Unified memory system for all AI agents"""
    
    def __init__(self):
        self.db_pool = None
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
    async def initialize(self):
        """Initialize database connection"""
        self.db_pool = await asyncpg.create_pool(
            'postgresql://localhost/mcp_memory',
            min_size=10,
            max_size=20
        )
        await self.create_schema()
    
    async def create_schema(self):
        """Create memory schema if not exists"""
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS agent_memories (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    agent_id VARCHAR(50),
                    session_id UUID,
                    timestamp TIMESTAMP DEFAULT NOW(),
                    memory_type VARCHAR(20),
                    content JSONB,
                    embeddings FLOAT8[],
                    meta_tags JSONB,
                    relevance_score FLOAT
                );
                
                CREATE INDEX IF NOT EXISTS idx_agent_memories_agent 
                    ON agent_memories(agent_id);
                CREATE INDEX IF NOT EXISTS idx_agent_memories_session 
                    ON agent_memories(session_id);
            ''')
    
    async def store_memory(self, agent_id: str, memory: Dict[str, Any]):
        """Store a memory with embeddings"""
        # Generate embeddings
        content_text = json.dumps(memory.get('content', ''))
        embeddings = self.encoder.encode(content_text).tolist()
        
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO agent_memories 
                (agent_id, session_id, memory_type, content, embeddings, meta_tags)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', 
            agent_id, 
            memory.get('session_id'),
            memory.get('type', 'general'),
            json.dumps(memory.get('content')),
            embeddings,
            json.dumps(memory.get('meta_tags', {}))
            )
    
    async def retrieve_context(self, agent_id: str, query: str, limit: int = 10):
        """Retrieve relevant memories for context"""
        # Generate query embeddings
        query_embeddings = self.encoder.encode(query).tolist()
        
        async with self.db_pool.acquire() as conn:
            # Cosine similarity search
            rows = await conn.fetch('''
                SELECT content, meta_tags, relevance_score
                FROM agent_memories
                WHERE agent_id = $1
                ORDER BY embeddings <-> $2
                LIMIT $3
            ''', agent_id, query_embeddings, limit)
            
            return [dict(row) for row in rows]

# FastAPI app
app = FastAPI(title="MCP Memory Server", version="1.0.0")
memory_server = MemoryServer()

@app.on_event("startup")
async def startup_event():
    await memory_server.initialize()

@app.post("/memory/store")
async def store_memory(agent_id: str, memory: Dict[str, Any]):
    """Store a memory"""
    await memory_server.store_memory(agent_id, memory)
    return {"status": "stored"}

@app.get("/memory/retrieve")
async def retrieve_context(agent_id: str, query: str, limit: int = 10):
    """Retrieve context"""
    contexts = await memory_server.retrieve_context(agent_id, query, limit)
    return {"contexts": contexts}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
EOF

# Create startup script for MCP servers
cat > mcp-unified/start_mcp.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting Unified MCP System..."

# Start gateway
echo "Starting MCP Gateway on port 8080..."
python mcp-unified/gateway/router.py &
GATEWAY_PID=$!

# Start memory server
echo "Starting Memory Server on port 8081..."
python mcp-unified/servers/memory.py &
MEMORY_PID=$!

# Start git server (if exists)
if [ -f "mcp-unified/servers/git.py" ]; then
    echo "Starting Git Server on port 8082..."
    python mcp-unified/servers/git.py &
    GIT_PID=$!
fi

echo "✅ MCP System Started"
echo "Gateway: http://localhost:8080"
echo "Memory: http://localhost:8081"
echo "Git: http://localhost:8082"

# Wait for processes
wait $GATEWAY_PID $MEMORY_PID $GIT_PID
EOF

chmod +x mcp-unified/start_mcp.sh

echo "✅ MCP consolidation structure created"
echo ""
echo "Next steps:"
echo "1. Review mcp-unified/ structure"
echo "2. Migrate useful code from other MCP directories"
echo "3. Update agent configurations to use gateway at localhost:8080"
echo "4. Run: ./mcp-unified/start_mcp.sh to start the unified system"