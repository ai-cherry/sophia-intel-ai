#!/bin/bash

# Sophia AI Services Startup Script for Codespaces
# This script starts both backend and frontend services

set -e

echo "🚀 Starting Sophia AI Services..."

# Function to check if a port is in use
check_port() {
    local port=$1
    if netstat -tlnp | grep ":$port " > /dev/null; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ $service_name failed to start after $max_attempts attempts"
    return 1
}

# Start Backend
echo "🐍 Starting Backend API..."
if check_port 8000; then
    echo "✅ Backend already running on port 8000"
else
    cd backend
    echo "   Installing Python dependencies..."
    pip install -r ../requirements.txt > /dev/null 2>&1 || echo "   Warning: Some dependencies may have failed to install"
    
    echo "   Starting backend server..."
    nohup python main.py > ../backend.log 2>&1 &
    cd ..
    
    # Wait for backend to be ready
    wait_for_service "http://localhost:8000/health" "Backend API"
fi

# Start Frontend
echo "⚛️ Starting Frontend..."
if check_port 3000; then
    echo "✅ Frontend already running on port 3000"
else
    cd frontend
    echo "   Installing Node.js dependencies..."
    npm install --silent > /dev/null 2>&1 || echo "   Warning: Some dependencies may have failed to install"
    
    echo "   Starting frontend server..."
    nohup npm run dev -- --host ${BIND_IP} --port 3000 > ../frontend.log 2>&1 &
    cd ..
    
    # Wait for frontend to be ready
    wait_for_service "${SOPHIA_FRONTEND_ENDPOINT}" "Frontend"
fi

echo ""
echo "🎉 Sophia AI Services Started Successfully!"
echo ""
echo "📊 Available Services:"
echo "   • Backend API: http://localhost:8000"
echo "   • Frontend: ${SOPHIA_FRONTEND_ENDPOINT}"
echo "   • API Documentation: http://localhost:8000/docs"
echo ""
echo "📝 Logs:"
echo "   • Backend: backend.log"
echo "   • Frontend: frontend.log"
echo ""
echo "🔗 In Codespaces, these will be available as:"
echo "   • Backend: https://CODESPACE-NAME-8000.app.github.dev/"
echo "   • Frontend: https://CODESPACE-NAME-3000.app.github.dev/"
echo ""
echo "✅ Ready for development!"

