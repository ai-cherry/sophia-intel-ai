#!/bin/bash
echo "🎯 ACTIVATING SOPHIA MODES..."

# Set environment variables that extensions might check
export ROO_CUSTOM_MODES_ENABLED=true
export ROO_MODES_FILE=".roomodes"
export SOPHIA_MODES_ACTIVE=true

# Touch files to trigger watchers
touch .roomodes
touch .roomodes.json
touch .roo/config.json

echo "✅ SOPHIA modes environment activated"
echo "Please restart VSCode now..."
        