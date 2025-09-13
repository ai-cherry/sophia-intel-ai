#!/bin/bash
# Comprehensive endpoint testing

echo "🧪 Sophia AI Endpoint Testing"
echo "============================="

# Test main site
echo "Testing main site..."
curl -I https://www.sophia-intel.ai

# Test API endpoints
echo -e "\nTesting API endpoints..."
curl -X GET http://104.171.202.103:8080/api/health
curl -X GET http://104.171.202.103:8080/api/status

# Test MCP endpoints
echo -e "\nTesting MCP endpoints..."
curl -X GET https://mcp.sophia-intel.ai/health
curl -X GET https://mcp.sophia-intel.ai/status

# Test ML endpoints
echo -e "\nTesting ML endpoints..."
curl -X GET https://ml.sophia-intel.ai/health
curl -X GET https://ml.sophia-intel.ai/models

echo -e "\nEndpoint testing complete"
