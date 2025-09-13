#!/bin/bash
# Setup script for Personal API Token Optimizer

echo "Setting up Personal API Token Optimizer..."

# Install required dependencies
echo "Installing Python dependencies..."
pip install -r requirements_token_optimizer.txt

# Create cache directory
echo "Creating cache directory..."
mkdir -p ./cache

# Make the main script executable
chmod +x optimize_current_tokens.py

echo "Setup complete!"
echo ""
echo "Usage examples:"
echo "  # Extract all available data from all services"
echo "  python optimize_current_tokens.py --service all"
echo ""
echo "  # Extract only Linear data"
echo "  python optimize_current_tokens.py --service linear"
echo ""
echo "  # Extract only Asana data"
echo "  python optimize_current_tokens.py --service asana"
echo ""
echo "Make sure to set your environment variables:"
echo "  export LINEAR_API_TOKEN=your_token_here"
echo "  export ASANA_ACCESS_TOKEN=your_token_here"
