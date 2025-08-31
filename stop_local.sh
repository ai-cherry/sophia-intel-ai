#!/bin/bash

# Stop all Sophia Intel AI local services

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping Sophia Intel AI services...${NC}"

# Stop API server
echo -n "Stopping API server..."
pkill -f "app.api.unified_server" 2>/dev/null && echo -e " ${GREEN}✓${NC}" || echo -e " ${YELLOW}not running${NC}"

# Stop UI
echo -n "Stopping UI dashboard..."
pkill -f "next dev" 2>/dev/null && echo -e " ${GREEN}✓${NC}" || echo -e " ${YELLOW}not running${NC}"

# Stop Weaviate if running
if command -v docker &> /dev/null; then
    echo -n "Stopping Weaviate..."
    docker stop weaviate 2>/dev/null && echo -e " ${GREEN}✓${NC}" || echo -e " ${YELLOW}not running${NC}"
fi

# Stop Redis if running
echo -n "Stopping Redis..."
pkill -x redis-server 2>/dev/null && echo -e " ${GREEN}✓${NC}" || echo -e " ${YELLOW}not running${NC}"

echo -e "${GREEN}All services stopped.${NC}"