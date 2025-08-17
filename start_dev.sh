#!/bin/bash
# SOPHIA Intel Development Startup Script

echo "🚀 Starting SOPHIA Intel Development Environment"

# Start PostgreSQL
sudo systemctl start postgresql
echo "✅ PostgreSQL started"

# Start Redis
sudo systemctl start redis-server
echo "✅ Redis started"

# Load environment
export $(cat .env.local | xargs)
echo "✅ Environment loaded"

echo "🎉 SOPHIA Intel development environment ready!"
echo "Database URL: $DATABASE_URL"
echo "Redis: localhost:6379"
