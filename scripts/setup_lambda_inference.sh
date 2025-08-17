#!/bin/bash
# SOPHIA Intel Lambda Labs GH200 Setup Script
# Configures inference servers for production deployment

set -e

SERVER_NAME=$1
if [ -z "$SERVER_NAME" ]; then
    echo "Usage: $0 <server_name>"
    echo "Example: $0 sophia-inference-01"
    exit 1
fi

echo "🚀 Setting up $SERVER_NAME for SOPHIA Intel inference..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    htop \
    nvtop \
    tmux \
    docker.io \
    docker-compose

# Add user to docker group
sudo usermod -aG docker ubuntu

# Install Python packages for inference
pip3 install --upgrade pip
pip3 install \
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
    pandas

# Create SOPHIA Intel directory structure
mkdir -p ~/sophia-intel/{models,logs,config,scripts}

# Clone SOPHIA Intel repository
cd ~/sophia-intel
if [ ! -d ".git" ]; then
    git clone https://github.com/ai-cherry/sophia-intel.git .
fi

# Create inference service configuration
cat > ~/sophia-intel/config/inference_config.yaml << EOF
server:
  host: "0.0.0.0"
  port: 8000
  workers: 1

models:
  default_model: "meta-llama/Llama-3.1-405B-Instruct"
  model_cache_dir: "/home/ubuntu/sophia-intel/models"
  max_model_len: 32768
  gpu_memory_utilization: 0.9

inference:
  max_concurrent_requests: 10
  request_timeout: 300
  enable_streaming: true

logging:
  level: "INFO"
  file: "/home/ubuntu/sophia-intel/logs/inference.log"
EOF

# Create systemd service for inference server
sudo tee /etc/systemd/system/sophia-inference.service > /dev/null << EOF
[Unit]
Description=SOPHIA Intel Inference Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/sophia-intel
Environment=CUDA_VISIBLE_DEVICES=0
ExecStart=/usr/bin/python3 -m vllm.entrypoints.api_server \\
    --model meta-llama/Llama-3.1-405B-Instruct \\
    --host 0.0.0.0 \\
    --port 8000 \\
    --gpu-memory-utilization 0.9 \\
    --max-model-len 32768 \\
    --disable-log-requests
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable sophia-inference.service

# Create health check script
cat > ~/sophia-intel/scripts/health_check.sh << 'EOF'
#!/bin/bash
# Health check for SOPHIA Intel inference server

HEALTH_URL="http://localhost:8000/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ "$RESPONSE" = "200" ]; then
    echo "✅ SOPHIA Intel inference server is healthy"
    exit 0
else
    echo "❌ SOPHIA Intel inference server is not responding (HTTP $RESPONSE)"
    exit 1
fi
EOF

chmod +x ~/sophia-intel/scripts/health_check.sh

# Create monitoring script
cat > ~/sophia-intel/scripts/monitor.sh << 'EOF'
#!/bin/bash
# Monitoring script for SOPHIA Intel inference server

echo "=== SOPHIA Intel Inference Server Status ==="
echo "Server: $(hostname)"
echo "Date: $(date)"
echo ""

echo "=== GPU Status ==="
nvidia-smi --query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits

echo ""
echo "=== Service Status ==="
systemctl status sophia-inference.service --no-pager -l

echo ""
echo "=== Recent Logs ==="
journalctl -u sophia-inference.service --no-pager -n 10

echo ""
echo "=== System Resources ==="
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)% usage"
echo "Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
echo "Disk: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 " used)"}')"
EOF

chmod +x ~/sophia-intel/scripts/monitor.sh

echo "✅ $SERVER_NAME setup complete!"
echo ""
echo "Next steps:"
echo "1. Start the inference service: sudo systemctl start sophia-inference.service"
echo "2. Check status: ~/sophia-intel/scripts/monitor.sh"
echo "3. Test health: ~/sophia-intel/scripts/health_check.sh"

