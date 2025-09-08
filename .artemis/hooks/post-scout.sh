#!/bin/bash
echo "✅ Scout completed!"
if [ -n "$1" ]; then
    echo "Received JSON output:"
    cat | jq '.metrics'
fi
echo "Time: $(date)"
