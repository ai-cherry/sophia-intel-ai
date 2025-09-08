#!/bin/bash

echo "🚀 Starting Sophia AI Essential Services..."

# Check if Docker is running
docker info >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check and start Redis
if ! docker ps --filter "name=redis" --format "{{.Names}}" | grep -q "redis"; then
    echo "🔄 Starting Redis container..."
    docker stop redis >/dev/null 2>&1
    docker rm redis >/dev/null 2>&1
    docker run -d --name redis --network host redis:latest
    if [ $? -eq 0 ]; then
        echo "✅ Redis container started successfully"
    else
        echo "❌ Failed to start Redis container"
        exit 1
    fi
else
    echo "✅ Redis container is already running"
fi

# Check and start Qdrant
if ! docker ps --filter "name=qdrant" --format "{{.Names}}" | grep -q "qdrant"; then
    echo "🔄 Starting Qdrant container..."
    docker stop qdrant >/dev/null 2>&1
    docker rm qdrant >/dev/null 2>&1
    docker run -d --name qdrant --network host qdrant/qdrant:latest
    if [ $? -eq 0 ]; then
        echo "✅ Qdrant container started successfully"
    else
        echo "❌ Failed to start Qdrant container"
        exit 1
    fi
else
    echo "✅ Qdrant container is already running"
fi

# Start MCP Memory Server
echo "🔄 Starting MCP Memory Server..."
cd /workspace/mcp_memory_server
nohup ./start_mcp_memory.sh > ../mcp_memory.log 2>&1 &
echo "✅ MCP Memory Server started (check mcp_memory.log for details)"

# Check if services are healthy
echo -e "\n🔍 Checking service health..."
sleep 5

# Check Redis
REDIS_CHECK=$(redis-cli ping 2>/dev/null)
if [[ "$REDIS_CHECK" == "PONG" ]]; then
    echo "✅ Redis health check: PASSED"
else
    echo "⚠️ Redis health check: FAILED"
fi

# Check Qdrant
QDRANT_CHECK=$(curl -s http://localhost:6333/collections)
if [[ "$QDRANT_CHECK" == *"status"*"ok"* ]]; then
    echo "✅ Qdrant health check: PASSED"
else
    echo "⚠️ Qdrant health check: FAILED"
fi

# Check MCP Memory Server
MCP_CHECK=$(curl -s http://localhost:8001/health)
if [[ "$MCP_CHECK" == *"operational"* ]]; then
    echo "✅ MCP Memory Server health check: PASSED"
else
    echo "⚠️ MCP Memory Server health check: FAILED"
fi

echo -e "\n🎉 Sophia AI Essential Services startup completed!"
echo "📊 Service summary:"
echo "  - Redis: Port 6379" 
echo "  - Qdrant: Port 6333"
echo "  - MCP Memory Server: Port 8001"
