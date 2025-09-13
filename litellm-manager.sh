#!/bin/bash
# Manage LiteLLM proxy

case "$1" in
    start)
        if [ -f ~/sophia-intel-ai/litellm.pid ]; then
            echo "LiteLLM already running"
        else
            echo "Starting LiteLLM..."
            nohup litellm --config ~/sophia-intel-ai/litellm-complete.yaml --port 4000 > ~/sophia-intel-ai/logs/litellm.log 2>&1 &
            echo $! > ~/sophia-intel-ai/litellm.pid
            echo "Started with PID: $(cat ~/sophia-intel-ai/litellm.pid)"
        fi
        ;;
    stop)
        if [ -f ~/sophia-intel-ai/litellm.pid ]; then
            kill $(cat ~/sophia-intel-ai/litellm.pid)
            rm ~/sophia-intel-ai/litellm.pid
            echo "LiteLLM stopped"
        else
            echo "LiteLLM not running"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if [ -f ~/sophia-intel-ai/litellm.pid ]; then
            PID=$(cat ~/sophia-intel-ai/litellm.pid)
            if ps -p $PID > /dev/null; then
                echo "LiteLLM running (PID: $PID)"
                echo "Health: $(curl -s http://localhost:4000/health)"
            else
                echo "LiteLLM PID file exists but process not running"
            fi
        else
            echo "LiteLLM not running"
        fi
        ;;
    logs)
        tail -f ~/sophia-intel-ai/logs/litellm.log
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        ;;
esac
