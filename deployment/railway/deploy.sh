#!/bin/bash
set -e

echo "🚀 SOPHIA Intel Railway Deployment Script"
echo "========================================="

# Set environment variables
export RAILWAY_TOKEN="32f097ac-7c3a-4a81-8385-b4ce98a2ca1f"

echo "1. Deploying Backend API..."
cd ../../backend
railway login --token $RAILWAY_TOKEN
railway project create sophia-intel-api || railway link sophia-intel-api
railway up --detach

echo "2. Deploying Frontend Dashboard..."  
cd ../apps/dashboard
railway project create sophia-intel-frontend || railway link sophia-intel-frontend
railway up --detach

echo "3. Deployment completed!"
railway status
