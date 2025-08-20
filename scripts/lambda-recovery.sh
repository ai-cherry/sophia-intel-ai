#!/bin/bash
# 🤠 SOPHIA AI Swarm Lambda Auto-Recovery Script
# Auto-restart Lambda servers if Uvicorn dies

LAMBDA_SERVERS=("192.222.51.223" "192.222.50.242")
SSH_KEY="sophia_production_key.pem"

echo "🤠 SOPHIA AI Swarm Lambda Recovery Check"
echo "Timestamp: $(date)"

for server in "${LAMBDA_SERVERS[@]}"; do
    echo "Checking Lambda server: $server"
    
    # Check if server is responding
    if curl -s --connect-timeout 5 "http://$server:8000/health" > /dev/null; then
        echo "✅ $server is healthy"
    else
        echo "❌ $server is down - initiating recovery"
        
        # Restart the service (kill and restart in separate commands)
        ssh -i "$SSH_KEY" -o ConnectTimeout=10 "ubuntu@$server" "killall uvicorn" 2>/dev/null || true
        sleep 2
        ssh -i "$SSH_KEY" -o ConnectTimeout=10 "ubuntu@$server" "cd /home/ubuntu && nohup python3 -m uvicorn ml_task:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &" 2>/dev/null
        
        # Wait and verify
        sleep 5
        if curl -s --connect-timeout 5 "http://$server:8000/health" > /dev/null; then
            echo "✅ $server recovered successfully"
        else
            echo "❌ $server recovery failed - manual intervention needed"
        fi
    fi
done

echo "✅ Lambda recovery check complete"
