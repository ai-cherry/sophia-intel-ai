#!/bin/bash
# Build the sample Flask application into a Docker image

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Build the Docker image
echo "Building sample-flask-app image..."
docker build -t sample-flask-app .

echo "Image built successfully!"
echo "You can run this image using the container_manager.py tool:"
echo "python container_manager.py start sample-flask-app -p 5000:5000 -n flask-demo"
