#!/bin/bash
# scripts/multi-agent-docker-env.sh
# Multi-agent environment manager
set -euo pipefail

COMPOSE_FILE="docker-compose.multi-agent.yml"
NETWORK_NAME="sophia-multi-agent-net"
PROJECT_NAME="sophia-intel-ai"

# Colors for output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running${NC}"
        echo "Please start Docker and try again"
        exit 1
    fi
}

# Function to check if compose file exists
check_compose_file() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo -e "${RED}❌ $COMPOSE_FILE not found${NC}"
        echo "Please run this script from the sophia-intel-ai root directory"
        exit 1
    fi
}

# Function to show help
show_help() {
    echo -e "${CYAN}Multi-Agent Development Environment Manager${NC}"
    echo ""
    echo "Usage: $0 {up|down|logs|shell|status|restart|clean}"
    echo ""
    echo "Commands:"
    echo "  up        Start multi-agent environment"
    echo "  down      Stop multi-agent environment"
    echo "  logs      View logs from all services (or specific service)"
    echo "  shell     Enter development shell"
    echo "  status    Show environment status"
    echo "  restart   Restart all services"
    echo "  clean     Clean up Docker resources"
    echo ""
    echo "Examples:"
    echo "  $0 up                    # Start all services"
    echo "  $0 logs redis            # Show Redis logs"
    echo "  $0 shell                 # Enter dev shell"
    echo "  $0 status                # Show service status"
}

# Function to start services
start_environment() {
    echo -e "${CYAN}🚀 Starting multi-agent environment...${NC}"
    
    check_docker
    check_compose_file
    
    # Check SSH agent
    if [ -z "${SSH_AUTH_SOCK:-}" ]; then
        echo -e "${YELLOW}⚠️  SSH_AUTH_SOCK not set. GitHub push may not work.${NC}"
        echo "To enable SSH agent forwarding, run: ssh-add -l"
    else
        echo -e "${GREEN}✅ SSH agent detected${NC}"
    fi
    
    # Check for .env file
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  .env file not found${NC}"
        if [ -f ".env.example" ]; then
            echo "Consider copying .env.example to .env and configuring your API keys"
        fi
    else
        echo -e "${GREEN}✅ .env file found${NC}"
    fi
    
    echo -e "${CYAN}🔧 Building and starting infrastructure services...${NC}"
    docker compose -f "$COMPOSE_FILE" build redis weaviate >/dev/null 2>&1 || true
    docker compose -f "$COMPOSE_FILE" up -d redis weaviate
    
    echo -e "${CYAN}⏳ Waiting for infrastructure to be healthy...${NC}"
    sleep 10
    
    # Check if we want MCP services
    read -p "Start MCP servers? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}🔧 Building and starting MCP servers...${NC}"
        docker compose -f "$COMPOSE_FILE" build mcp-memory mcp-filesystem-sophia mcp-filesystem-artemis mcp-git >/dev/null 2>&1 || true
        docker compose -f "$COMPOSE_FILE" up -d mcp-memory mcp-filesystem-sophia mcp-filesystem-artemis mcp-git
        sleep 5
    fi
    
    # Check if we want Web UI
    read -p "Start Web UI? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}🌐 Building and starting Web UI...${NC}"
        docker compose -f "$COMPOSE_FILE" build swarm-orchestrator webui >/dev/null 2>&1 || true
        docker compose -f "$COMPOSE_FILE" up -d swarm-orchestrator webui
        sleep 3
    fi
    
    # Check if we want indexer
    read -p "Start code indexer? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}🔍 Building and starting code indexer...${NC}"
        docker compose -f "$COMPOSE_FILE" build indexer >/dev/null 2>&1 || true
        docker compose -f "$COMPOSE_FILE" up -d indexer
    fi
    
    # Check if we want observability
    read -p "Start observability (Prometheus/Grafana)? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}📊 Building and starting observability stack...${NC}"
        docker compose -f "$COMPOSE_FILE" build prometheus grafana >/dev/null 2>&1 || true
        docker compose -f "$COMPOSE_FILE" up -d prometheus grafana
    fi
    
    echo ""
    echo -e "${GREEN}✅ Environment ready!${NC}"
    echo ""
    echo -e "${YELLOW}🌐 Available services:${NC}"
    echo "  Redis:     http://localhost:6379"
    echo "  Weaviate:  http://localhost:8080"
    
    if docker ps --format "table {{.Names}}" | grep -q "sophia-webui"; then
        echo "  Web UI:    http://localhost:3001"
    fi
    
    if docker ps --format "table {{.Names}}" | grep -q "sophia-grafana"; then
        echo "  Grafana:   http://localhost:3000 (admin/admin)"
        echo "  Prometheus: http://localhost:9090"
    fi
    
    echo ""
    echo -e "${YELLOW}📋 Quick commands:${NC}"
    echo "  $0 shell     # Enter development shell"
    echo "  $0 logs      # View all logs"
    echo "  $0 status    # Check service status"
}

# Function to stop services
stop_environment() {
    echo -e "${RED}🛑 Stopping multi-agent environment...${NC}"
    check_compose_file
    
    docker compose -f "$COMPOSE_FILE" down
    
    echo -e "${GREEN}✅ Environment stopped${NC}"
}

# Function to show logs
show_logs() {
    check_compose_file
    
    if [ -n "${1:-}" ]; then
        echo -e "${CYAN}📋 Showing logs for $1...${NC}"
        docker compose -f "$COMPOSE_FILE" logs -f "$1"
    else
        echo -e "${CYAN}📋 Showing all logs...${NC}"
        docker compose -f "$COMPOSE_FILE" logs -f
    fi
}

# Function to enter shell
enter_shell() {
    echo -e "${CYAN}🐚 Entering development shell...${NC}"
    check_docker
    check_compose_file
    
    # Start agent-dev service if not running
    if ! docker ps --format "table {{.Names}}" | grep -q "sophia-agent-dev"; then
        echo -e "${YELLOW}⚠️  Development container not running, starting...${NC}"
        docker compose -f "$COMPOSE_FILE" up -d agent-dev
        sleep 2
    fi
    
    docker compose -f "$COMPOSE_FILE" exec agent-dev bash -l
}

# Function to show status
show_status() {
    echo -e "${CYAN}📊 Multi-agent environment status:${NC}"
    check_compose_file
    
    echo ""
    docker compose -f "$COMPOSE_FILE" ps
    
    echo ""
    echo -e "${YELLOW}🔗 Network status:${NC}"
    if docker network ls | grep -q "$NETWORK_NAME"; then
        echo -e "${GREEN}✅ Network $NETWORK_NAME exists${NC}"
    else
        echo -e "${RED}❌ Network $NETWORK_NAME not found${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}💾 Volume status:${NC}"
    docker volume ls | grep "$PROJECT_NAME" || echo "No project volumes found"
    
    echo ""
    echo -e "${YELLOW}🏥 Health checks:${NC}"
    docker compose -f "$COMPOSE_FILE" ps --format "table {{.Service}}\t{{.Status}}"
}

# Function to restart services
restart_environment() {
    echo -e "${YELLOW}🔄 Restarting multi-agent environment...${NC}"
    check_compose_file
    
    docker compose -f "$COMPOSE_FILE" restart
    
    echo -e "${GREEN}✅ Environment restarted${NC}"
}

# Function to clean resources
clean_resources() {
    echo -e "${RED}🧹 Cleaning Docker resources...${NC}"
    
    read -p "This will remove stopped containers, unused networks, and dangling images. Continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker system prune -f
        
        read -p "Also remove project volumes? This will delete all data. (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker volume prune -f
            echo -e "${GREEN}✅ Volumes cleaned${NC}"
        fi
        
        echo -e "${GREEN}✅ Docker resources cleaned${NC}"
    else
        echo "Cancelled"
    fi
}

# Main script logic
case "${1:-help}" in
    "up"|"start")
        start_environment
        ;;
        
    "down"|"stop")
        stop_environment
        ;;
        
    "logs")
        show_logs "${2:-}"
        ;;
        
    "shell"|"bash")
        enter_shell
        ;;
        
    "status"|"ps")
        show_status
        ;;
        
    "restart")
        restart_environment
        ;;
        
    "clean")
        clean_resources
        ;;
        
    "help"|"--help"|"-h")
        show_help
        ;;
        
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
