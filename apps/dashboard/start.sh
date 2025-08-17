#!/bin/bash

# Set default port if not provided
export PORT=${PORT:-80}

echo "Starting nginx on port $PORT"

# Create nginx configuration with substituted PORT
envsubst '$$PORT' < /etc/nginx/nginx.conf > /tmp/nginx.conf

# Start nginx with the processed configuration
exec nginx -c /tmp/nginx.conf -g 'daemon off;'

