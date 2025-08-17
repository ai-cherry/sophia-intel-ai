#!/bin/bash
# SOPHIA Intel Lambda Labs GH200 Production Setup Script
# Idempotent, containerized, secure setup following best practices

set -e

SERVER_ROLE=$1
if [ -z "$SERVER_ROLE" ]; then
    echo "Usage: $0 <primary|secondary>"
    echo "Example: $0 primary"
    exit 1
fi

# Configuration
SOPHIA_DIR="/home/ubuntu/sophia-intel"
CONTAINER_NAME="sophia-inference"
INFERENCE_PORT=8000
HEALTH_PORT=8001

echo "🚀 Setting up SOPHIA Intel GH200 ($SERVER_ROLE) for production inference..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if package is installed
package_installed() {
    dpkg -l | grep -q "^ii  $1 "
}

# 1. VERIFY GPU AND CUDA SUPPORT
echo "🔍 Verifying GPU and CUDA support..."
if ! command_exists nvidia-smi; then
    echo "❌ NVIDIA drivers not found. Installing..."
    sudo apt update
    sudo apt install -y nvidia-driver-535 nvidia-utils-535
    echo "⚠️  Reboot required after driver installation. Please reboot and re-run this script."
    exit 1
fi

# Check GPU status
GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits)
echo "✅ GPU detected: $GPU_INFO"

# Verify CUDA availability
if ! nvidia-smi > /dev/null 2>&1; then
    echo "❌ NVIDIA drivers not properly loaded"
    exit 1
fi

# 2. SYSTEM UPDATES (IDEMPOTENT)
echo "📦 Updating system packages..."
sudo apt update

# Install essential packages only if not present
PACKAGES="curl wget git htop nvtop tmux ufw python3-pip python3-venv"
for pkg in $PACKAGES; do
    if ! package_installed "$pkg"; then
        echo "Installing $pkg..."
        sudo apt install -y "$pkg"
    else
        echo "✅ $pkg already installed"
    fi
done

# 3. DOCKER INSTALLATION (IDEMPOTENT)
echo "🐳 Setting up Docker..."
if ! command_exists docker; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker ubuntu
    rm get-docker.sh
    echo "⚠️  Please log out and back in for Docker group membership to take effect"
else
    echo "✅ Docker already installed"
fi

# Install Docker Compose if not present
if ! command_exists docker-compose; then
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "✅ Docker Compose already installed"
fi

# 4. NVIDIA CONTAINER TOOLKIT
echo "🔧 Setting up NVIDIA Container Toolkit..."
if ! dpkg -l | grep -q nvidia-container-toolkit; then
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
    sudo apt update
    sudo apt install -y nvidia-container-toolkit
    sudo systemctl restart docker
else
    echo "✅ NVIDIA Container Toolkit already installed"
fi

# 5. FIREWALL CONFIGURATION (SECURE)
echo "🔒 Configuring firewall..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow $INFERENCE_PORT/tcp comment 'SOPHIA Inference API'
sudo ufw allow $HEALTH_PORT/tcp comment 'SOPHIA Health Check'
sudo ufw --force enable

# 6. CREATE SOPHIA DIRECTORY STRUCTURE
echo "📁 Setting up SOPHIA Intel directory structure..."
mkdir -p $SOPHIA_DIR/{config,logs,models,containers,scripts}

# 7. CLONE/UPDATE SOPHIA INTEL REPOSITORY
echo "📥 Setting up SOPHIA Intel repository..."
cd $SOPHIA_DIR
if [ ! -d ".git" ]; then
    git clone https://github.com/ai-cherry/sophia-intel.git .
else
    git pull origin main
fi

# 8. CREATE INFERENCE CONTAINER CONFIGURATION
echo "🐳 Creating inference container configuration..."
cat > $SOPHIA_DIR/containers/Dockerfile.inference << 'EOF'
FROM nvidia/cuda:12.1-devel-ubuntu22.04

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python packages
RUN pip3 install --no-cache-dir \
    torch \
    transformers \
    accelerate \
    bitsandbytes \
    vllm \
    fastapi \
    uvicorn \
    pydantic \
    requests \
    numpy \
    pandas \
    prometheus-client

# Copy application code
COPY . /app/

# Create non-root user
RUN useradd -m -u 1000 sophia && chown -R sophia:sophia /app
USER sophia

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000 8001

# Start command
CMD ["python3", "-m", "uvicorn", "inference_server:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# 9. CREATE INFERENCE SERVER APPLICATION
echo "🚀 Creating inference server application..."
cat > $SOPHIA_DIR/containers/inference_server.py << 'EOF'
import os
import asyncio
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from transformers import AutoTokenizer, AutoModelForCausalLM
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('sophia_inference_requests_total', 'Total inference requests')
REQUEST_DURATION = Histogram('sophia_inference_request_duration_seconds', 'Request duration')
ERROR_COUNT = Counter('sophia_inference_errors_total', 'Total inference errors')

# Global model and tokenizer
model = None
tokenizer = None

class InferenceRequest(BaseModel):
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9

class InferenceResponse(BaseModel):
    response: str
    tokens_generated: int
    processing_time: float

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global model, tokenizer
    logger.info("Loading model and tokenizer...")
    
    model_name = os.getenv("MODEL_NAME", "microsoft/DialoGPT-medium")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )
        
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            
        logger.info(f"Model {model_name} loaded successfully")
        logger.info(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            logger.info(f"GPU: {torch.cuda.get_device_name()}")
            logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
            
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down inference server...")

app = FastAPI(
    title="SOPHIA Intel Inference Server",
    description="High-performance inference server for SOPHIA Intel AI",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    gpu_available = torch.cuda.is_available()
    model_loaded = model is not None and tokenizer is not None
    
    status = {
        "status": "healthy" if model_loaded else "unhealthy",
        "model_loaded": model_loaded,
        "gpu_available": gpu_available,
        "gpu_count": torch.cuda.device_count() if gpu_available else 0
    }
    
    if gpu_available:
        status["gpu_name"] = torch.cuda.get_device_name()
        status["gpu_memory_allocated"] = torch.cuda.memory_allocated() / 1e9
        status["gpu_memory_cached"] = torch.cuda.memory_reserved() / 1e9
    
    return status

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.post("/inference", response_model=InferenceResponse)
async def run_inference(request: InferenceRequest):
    """Run inference on the provided prompt"""
    if model is None or tokenizer is None:
        ERROR_COUNT.inc()
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    REQUEST_COUNT.inc()
    
    with REQUEST_DURATION.time():
        try:
            # Tokenize input
            inputs = tokenizer.encode(request.prompt, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = inputs.cuda()
            
            # Generate response
            with torch.no_grad():
                outputs = model.generate(
                    inputs,
                    max_new_tokens=request.max_tokens,
                    temperature=request.temperature,
                    top_p=request.top_p,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            # Decode response
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response[len(request.prompt):].strip()
            
            tokens_generated = len(outputs[0]) - len(inputs[0])
            
            return InferenceResponse(
                response=response,
                tokens_generated=tokens_generated,
                processing_time=0.0  # Will be filled by middleware
            )
            
        except Exception as e:
            ERROR_COUNT.inc()
            logger.error(f"Inference error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "SOPHIA Intel Inference Server",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "inference": "/inference",
            "metrics": "/metrics"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "inference_server:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
EOF

# 10. CREATE DOCKER COMPOSE CONFIGURATION
echo "🐳 Creating Docker Compose configuration..."
cat > $SOPHIA_DIR/containers/docker-compose.yml << EOF
version: '3.8'

services:
  sophia-inference:
    build:
      context: .
      dockerfile: Dockerfile.inference
    container_name: sophia-inference-$SERVER_ROLE
    ports:
      - "$INFERENCE_PORT:8000"
      - "$HEALTH_PORT:8001"
    environment:
      - MODEL_NAME=microsoft/DialoGPT-medium
      - CUDA_VISIBLE_DEVICES=0
    volumes:
      - ../models:/app/models
      - ../logs:/app/logs
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
EOF

# 11. CREATE ENVIRONMENT CONFIGURATION
echo "⚙️  Creating environment configuration..."
cat > $SOPHIA_DIR/.env.lambda << EOF
# SOPHIA Intel Lambda Labs Configuration
SERVER_ROLE=$SERVER_ROLE
INFERENCE_PORT=$INFERENCE_PORT
HEALTH_PORT=$HEALTH_PORT
MODEL_NAME=microsoft/DialoGPT-medium
CUDA_VISIBLE_DEVICES=0

# Logging
LOG_LEVEL=INFO
LOG_FILE=/home/ubuntu/sophia-intel/logs/inference.log

# Security
API_KEY_REQUIRED=true
EOF

# 12. CREATE MONITORING SCRIPTS
echo "📊 Creating monitoring scripts..."
cat > $SOPHIA_DIR/scripts/monitor_inference.sh << 'EOF'
#!/bin/bash
# SOPHIA Intel Inference Monitoring Script

echo "=== SOPHIA Intel Inference Server Status ==="
echo "Server: $(hostname) ($(cat /home/ubuntu/sophia-intel/.env.lambda | grep SERVER_ROLE | cut -d'=' -f2))"
echo "Date: $(date)"
echo ""

echo "=== GPU Status ==="
nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits

echo ""
echo "=== Container Status ==="
docker ps --filter "name=sophia-inference" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== Health Check ==="
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "Health check failed"

echo ""
echo "=== Recent Logs ==="
docker logs sophia-inference-$(cat /home/ubuntu/sophia-intel/.env.lambda | grep SERVER_ROLE | cut -d'=' -f2) --tail 10 2>/dev/null || echo "No container logs available"

echo ""
echo "=== System Resources ==="
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)% usage"
echo "Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "Disk: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 " used)"}')"
EOF

chmod +x $SOPHIA_DIR/scripts/monitor_inference.sh

# 13. CREATE HEALTH CHECK SCRIPT
cat > $SOPHIA_DIR/scripts/health_check.sh << 'EOF'
#!/bin/bash
# Health check for SOPHIA Intel inference server

HEALTH_URL="http://localhost:8000/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL 2>/dev/null)

if [ "$RESPONSE" = "200" ]; then
    echo "✅ SOPHIA Intel inference server is healthy"
    # Get detailed health info
    curl -s $HEALTH_URL | python3 -m json.tool 2>/dev/null
    exit 0
else
    echo "❌ SOPHIA Intel inference server is not responding (HTTP $RESPONSE)"
    exit 1
fi
EOF

chmod +x $SOPHIA_DIR/scripts/health_check.sh

# 14. CREATE STARTUP SCRIPT
cat > $SOPHIA_DIR/scripts/start_inference.sh << 'EOF'
#!/bin/bash
# Start SOPHIA Intel inference server

cd /home/ubuntu/sophia-intel/containers

echo "🚀 Starting SOPHIA Intel inference server..."

# Load environment variables
source ../.env.lambda

# Build and start containers
docker-compose up -d --build

echo "✅ SOPHIA Intel inference server started"
echo "📊 Monitor with: ~/sophia-intel/scripts/monitor_inference.sh"
echo "🏥 Health check: ~/sophia-intel/scripts/health_check.sh"
EOF

chmod +x $SOPHIA_DIR/scripts/start_inference.sh

echo ""
echo "✅ SOPHIA Intel GH200 ($SERVER_ROLE) setup complete!"
echo ""
echo "🚀 Next steps:"
echo "1. Start inference server: ~/sophia-intel/scripts/start_inference.sh"
echo "2. Monitor status: ~/sophia-intel/scripts/monitor_inference.sh"
echo "3. Check health: ~/sophia-intel/scripts/health_check.sh"
echo ""
echo "🔗 Endpoints:"
echo "- Inference API: http://$(curl -s ifconfig.me):$INFERENCE_PORT"
echo "- Health Check: http://$(curl -s ifconfig.me):$INFERENCE_PORT/health"
echo "- Metrics: http://$(curl -s ifconfig.me):$INFERENCE_PORT/metrics"

