#!/bin/bash
echo "Checking Airbyte services startup..."
for i in {1..30}; do
    echo "Attempt $i/30..."
    if curl -f http://localhost:8001/api/v1/health >/dev/null 2>&1; then
        echo "✅ Airbyte API is healthy!"
        curl http://localhost:8001/api/v1/health
        exit 0
    fi
    sleep 10
done
echo "❌ Airbyte failed to start within 5 minutes"
exit 1
