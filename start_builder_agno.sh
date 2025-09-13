#!/bin/bash

echo "=========================================="
echo "🔨 BUILDER AGNO SYSTEM"
echo "Port: 8005"
echo "Purpose: Code generation & agent swarms"
echo "=========================================="

# Check if builder-agno-system exists
if [ ! -d "builder-agno-system" ]; then
    echo "❌ Error: builder-agno-system directory not found!"
    echo "Please run the setup script first."
    exit 1
fi

# Navigate to Builder Agno System
cd builder-agno-system

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Builder Agno dependencies..."
    npm install
fi

# Start the Builder Agno System
echo "🚀 Starting Builder Agno System on http://localhost:8005"
npm run dev