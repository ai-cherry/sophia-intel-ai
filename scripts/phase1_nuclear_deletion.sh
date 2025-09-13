#!/bin/bash
# ============================================================================
# PHASE 1: NUCLEAR DELETION SCRIPT
# Sophia AI Platform - Technical Debt Elimination
# WARNING: This script will DELETE 92% of the codebase
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║     🔥 NUCLEAR DELETION PHASE - SOPHIA AI V2.0 🔥           ║${NC}"
echo -e "${RED}║     WARNING: This will DELETE 92% of the codebase!          ║${NC}"
echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the right directory
if [ ! -d "asip" ] || [ ! -d "mcp_servers" ] || [ ! -d "agents" ]; then
    echo -e "${RED}ERROR: Must run from Sophia AI root directory${NC}"
    exit 1
fi

# Confirmation prompt
read -p "Are you ABSOLUTELY SURE you want to proceed? Type 'DELETE EVERYTHING' to confirm: " confirmation
if [ "$confirmation" != "DELETE EVERYTHING" ]; then
    echo -e "${YELLOW}Deletion cancelled. Wise choice to think twice!${NC}"
    exit 0
fi

echo -e "${YELLOW}Creating backup archives before deletion...${NC}"

# Create backup directory with timestamp
BACKUP_DIR="nuclear_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Statistics tracking
total_deleted_files=0
total_deleted_dirs=0
total_deleted_lines=0

# Function to count lines in a directory
count_lines() {
    find "$1" -type f -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}'
}

# ============================================================================
# PHASE 1: MCP SERVER MASSACRE (Delete 26+ out of 30+ servers)
# ============================================================================

echo ""
echo -e "${RED}═══════════════════════════════════════════════════════${NC}"
echo -e "${RED}PHASE 1: MCP SERVER MASSACRE${NC}"
echo -e "${RED}═══════════════════════════════════════════════════════${NC}"

if [ -d "mcp_servers" ]; then
    echo "Backing up MCP servers..."
    tar -czf "$BACKUP_DIR/mcp_servers_backup.tar.gz" mcp_servers/ 2>/dev/null || true
    
    # List of MCP servers to DELETE
    MCP_TO_DELETE=(
        "agent_frameworks"
        "ai_providers"
        "enhanced_enterprise"
        "enhanced_framework"
        "hyper_hub"
        "graph_rag"
        "super_memory"
        "vector_databases"
        "research"
        "reliability"
        "performance"
        "notion"
        "slack"
        "gong"
        "huggingface"
        "marketing"
        "monitor"
        "infrastructure"
        "enterprise"
        "data"
        "hubspot"
        "github"
        "kb"
        "shared"
    )
    
    deleted_count=0
    for server in "${MCP_TO_DELETE[@]}"; do
        if [ -d "mcp_servers/$server" ]; then
            lines=$(count_lines "mcp_servers/$server")
            echo -e "${RED}  ✗ Deleting mcp_servers/$server (~$lines lines)${NC}"
            rm -rf "mcp_servers/$server"
            ((deleted_count++))
            ((total_deleted_dirs++))
            ((total_deleted_lines+=lines))
        fi
    done
    
    echo -e "${GREEN}✅ Deleted $deleted_count MCP servers${NC}"
fi

# ============================================================================
# PHASE 2: AGENT SYSTEM ANNIHILATION (Delete 10+ out of 12)
# ============================================================================

echo ""
echo -e "${RED}═══════════════════════════════════════════════════════${NC}"
echo -e "${RED}PHASE 2: AGENT SYSTEM ANNIHILATION${NC}"
echo -e "${RED}═══════════════════════════════════════════════════════${NC}"

if [ -d "agents" ]; then
    echo "Backing up agent systems..."
    tar -czf "$BACKUP_DIR/agents_backup.tar.gz" agents/ 2>/dev/null || true
    
    # List of agent systems to DELETE
    AGENTS_TO_DELETE=(
        "enhanced_framework"
        "meta_learning"
        "production_goals"
        "resilient"
        "conflict_resolution"
        "dependency_management"
        "performance"
        "architect"
        "coder"
        "registry"
    )
    
    deleted_count=0
    for agent in "${AGENTS_TO_DELETE[@]}"; do
        if [ -d "agents/$agent" ]; then
            lines=$(count_lines "agents/$agent")
            echo -e "${RED}  ✗ Deleting agents/$agent (~$lines lines)${NC}"
            rm -rf "agents/$agent"
            ((deleted_count++))
            ((total_deleted_dirs++))
            ((total_deleted_lines+=lines))
        fi
    done
    
    # Also delete standalone agent files if not needed
    if [ -f "agents/performance_optimizer.py" ]; then
        echo -e "${RED}  ✗ Deleting agents/performance_optimizer.py${NC}"
        rm -f "agents/performance_optimizer.py"
        ((total_deleted_files++))
    fi
    
    echo -e "${GREEN}✅ Deleted $deleted_count agent systems${NC}"
fi

# ============================================================================
# PHASE 3: BACKEND SERVICE GENOCIDE (Delete 32+ services)
# ============================================================================

echo ""
echo -e "${RED}═══════════════════════════════════════════════════════${NC}"
echo -e "${RED}PHASE 3: BACKEND SERVICE GENOCIDE${NC}"
echo -e "${RED}═══════════════════════════════════════════════════════${NC}"

if [ -d "backend/services" ]; then
    echo "Backing up backend services..."
    tar -czf "$BACKUP_DIR/backend_services_backup.tar.gz" backend/services/ 2>/dev/null || true
    
    # List of backend services to DELETE
    SERVICES_TO_DELETE=(
        "optimized_agno_swarm.py"
        "langgraph_granular_durability.py"
        "flashrag_speculative_engine.py"
        "zero_downtime_orchestrator.py"
        "hr_business_intelligence_orchestrator.py"
        "mcp_consolidation_engine.py"
        "opus41_service.py"
        "performance_optimization_engine.py"
        "langgraph_haystack_fusion.py"
        "aiac_agent.py"
        "iac_gen.py"
        "lambda_inference_service.py"
        "lambda_labs_manager.py"
        "openrouter_service.py"
        "web_search_service.py"
        "unified_estuary_service.py"
        "real_time_sync_manager.py"
        "mcp_rag_enhanced.py"
        "mcp_rag_service.py"
        "estuary_cdc_pool.py"
        "feature_flags.py"
        "github_service.py"
        "enterprise_security_service.py"
        "database_connection_manager.py"
        "service_discovery.py"
        "memory_optimizer.py"
        "file_operations_service.py"
    )
    
    deleted_count=0
    for service in "${SERVICES_TO_DELETE[@]}"; do
        if [ -f "backend/services/$service" ]; then
            echo -e "${RED}  ✗ Deleting backend/services/$service${NC}"
            rm -f "backend/services/$service"
            ((deleted_count++))
            ((total_deleted_files++))
        fi
    done
    
    # Delete entire subdirectories
    SERVICE_DIRS_TO_DELETE=(
        "business"
        "cache"
        "coding"
        "embeddings"
        "events"
        "integration"
        "integrations"
        "knowledge"
        "orchestration"
        "project_management"
        "query"
        "rag"
        "ranking"
        "realtime"
        "retrieval"
        "shared"
        "text"
        "vector"
    )
    
    for dir in "${SERVICE_DIRS_TO_DELETE[@]}"; do
        if [ -d "backend/services/$dir" ]; then
            lines=$(count_lines "backend/services/$dir")
            echo -e "${RED}  ✗ Deleting backend/services/$dir/ (~$lines lines)${NC}"
            rm -rf "backend/services/$dir"
            ((deleted_count++))
            ((total_deleted_dirs++))
            ((total_deleted_lines+=lines))
        fi
    done
    
    echo -e "${GREEN}✅ Deleted $deleted_count backend services/directories${NC}"
fi

# ============================================================================
# PHASE 4: CONFIGURATION CONSOLIDATION (Delete 49+ config files)
# ============================================================================

echo ""
echo -e "${RED}═══════════════════════════════════════════════════════${NC}"
echo -e "${RED}PHASE 4: CONFIGURATION CONSOLIDATION${NC}"
echo -e "${RED}═══════════════════════════════════════════════════════${NC}"

if [ -d "config" ]; then
    echo "Backing up configurations..."
    tar -czf "$BACKUP_DIR/config_backup.tar.gz" config/ 2>/dev/null || true
    
    # Delete config subdirectories
    CONFIG_DIRS_TO_DELETE=(
        "environment"
        "estuary"
        "governance"
        "grafana"
        "monitoring"
        "openrouter"
        "performance"
        "prometheus"
        "pulumi"
        "qdrant"
        "redis"
        "security"
        "startup"
        "unified"
    )
    
    deleted_count=0
    for dir in "${CONFIG_DIRS_TO_DELETE[@]}"; do
        if [ -d "config/$dir" ]; then
            echo -e "${RED}  ✗ Deleting config/$dir/${NC}"
            rm -rf "config/$dir"
            ((deleted_count++))
            ((total_deleted_dirs++))
        fi
    done
    
    # Delete all config files except the one we'll create
    find config -maxdepth 1 -type f \( -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.py" -o -name "*.conf" -o -name "*.ini" \) -exec rm {} \; 2>/dev/null
    
    echo -e "${GREEN}✅ Deleted $deleted_count config directories and all config files${NC}"
fi

# ============================================================================
# PHASE 5: DOCUMENTATION DECIMATION (Delete 90+ docs)
# ============================================================================

echo ""
echo -e "${RED}═══════════════════════════════════════════════════════${NC}"
echo -e "${RED}PHASE 5: DOCUMENTATION DECIMATION${NC}"
echo -e "${RED}═══════════════════════════════════════════════════════${NC}"

# Create essential docs backup
mkdir -p "$BACKUP_DIR/docs_essential"
[ -f "README.md" ] && cp README.md "$BACKUP_DIR/docs_essential/"
[ -f "ASIP_IMPLEMENTATION_SUCCESS.md" ] && cp ASIP_IMPLEMENTATION_SUCCESS.md "$BACKUP_DIR/docs_essential/"
[ -f "LICENSE" ] && cp LICENSE "$BACKUP_DIR/docs_essential/"
[ -f "PHASE1_ULTIMATE_SLASH_BURN_PLAN.md" ] && cp PHASE1_ULTIMATE_SLASH_BURN_PLAN.md "$BACKUP_DIR/docs_essential/"

# Delete documentation noise
DOCS_TO_DELETE=(
    "MEGA_INTERROGATION_*.md"
    "SOPHIA_V*_*.md"
    "*_COMPREHENSIVE_*.md"
    "*_ULTIMATE_*.md"
    "*_ANALYSIS*.md"
    "*_AUDIT*.md"
    "*_REPORT*.md"
    "*_GUIDE*.md"
    "*_OVERVIEW*.md"
    "*_ROADMAP*.md"
    "*_STRATEGY*.md"
    "*_PROPOSAL*.md"
    "*_ASSESSMENT*.md"
    "CODESPACES_*.md"
    "ENHANCED_*.md"
    "FUSION_*.md"
    "CHAOS_*.md"
    "CONTINUE_*.md"
    "DEPENDENCY_*.md"
    "DEPLOYMENT*.md"
    "DEV*.md"
    "DOCUMENTATION_*.md"
    "EMERGENCY_*.md"
    "ENVIRONMENT_*.md"
    "ESTUARY_*.md"
    "FINAL_*.md"
    "INFRASTRUCTURE_*.md"
    "INTEGRATIONS_*.md"
    "LAMBDA_*.md"
    "PAY_READY_*.md"
    "PM_*.md"
    "PRODUCTION_*.md"
    "REPOSITORY_*.md"
    "SECURITY_*.md"
    "SERVICE_*.md"
    "STARTUP_*.md"
    "STRATEGIC_*.md"
    "SYSTEM_*.md"
    "TECH_*.md"
    "TOP_*.md"
    "UNIFIED_*.md"
    "V8_*.md"
)

deleted_docs=0
for pattern in "${DOCS_TO_DELETE[@]}"; do
    for file in $pattern; do
        if [ -f "$file" ] && [ "$file" != "PHASE1_ULTIMATE_SLASH_BURN_PLAN.md" ]; then
            echo -e "${RED}  ✗ Deleting $file${NC}"
            rm -f "$file"
            ((deleted_docs++))
            ((total_deleted_files++))
        fi
    done
done

# Delete docs directory if it exists
if [ -d "docs" ]; then
    echo -e "${RED}  ✗ Deleting docs/ directory${NC}"
    rm -rf "docs"
    ((total_deleted_dirs++))
fi

echo -e "${GREEN}✅ Deleted $deleted_docs documentation files${NC}"

# ============================================================================
# PHASE 6: ARCHIVE CLEANUP
# ============================================================================

echo ""
echo -e "${RED}═══════════════════════════════════════════════════════${NC}"
echo -e "${RED}PHASE 6: ARCHIVE CLEANUP${NC}"
echo -e "${RED}═══════════════════════════════════════════════════════${NC}"

# Keep the archive folder but note what's in it
if [ -d "archive" ]; then
    echo -e "${YELLOW}  ℹ Archive folder exists (contains Langroid legacy)${NC}"
    echo -e "${YELLOW}    Keeping for reference but excluding from active codebase${NC}"
fi

# ============================================================================
# SUMMARY REPORT
# ============================================================================

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}NUCLEAR DELETION COMPLETE - SUMMARY REPORT${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════${NC}"

echo -e "${GREEN}✅ Total Deleted:${NC}"
echo -e "   • Directories: $total_deleted_dirs"
echo -e "   • Files: $total_deleted_files"
echo -e "   • Estimated lines removed: ~$total_deleted_lines"

echo ""
echo -e "${YELLOW}📦 Backups created in: $BACKUP_DIR/${NC}"
echo -e "   • mcp_servers_backup.tar.gz"
echo -e "   • agents_backup.tar.gz"
echo -e "   • backend_services_backup.tar.gz"
echo -e "   • config_backup.tar.gz"
echo -e "   • docs_essential/"

echo ""
echo -e "${BLUE}🏗️ What remains (to be consolidated):${NC}"
echo -e "   • asip/ - Core ASIP platform"
echo -e "   • mcp_servers/sophia, base, security, mem0_server"
echo -e "   • agents/core, specialized"
echo -e "   • backend/services/ (minimal services)"
echo -e "   • config/ (awaiting single sophia.yaml)"

echo ""
echo -e "${MAGENTA}📊 Estimated code reduction: ~92%${NC}"
echo -e "${MAGENTA}🎯 Target: <8,000 lines of code${NC}"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     🎉 PHASE 1 DELETION COMPLETE - READY FOR REBUILD 🎉     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"

echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Create single config/sophia.yaml"
echo -e "2. Rebuild backend/main.py with ASIP"
echo -e "3. Write comprehensive tests"
echo -e "4. Validate <8,000 total lines"

# Create a deletion report
cat > "$BACKUP_DIR/deletion_report.txt" << EOF
NUCLEAR DELETION REPORT
Date: $(date)
Total Directories Deleted: $total_deleted_dirs
Total Files Deleted: $total_deleted_files
Estimated Lines Removed: ~$total_deleted_lines

MCP Servers Deleted:
$(for server in "${MCP_TO_DELETE[@]}"; do echo "  - $server"; done)

Agent Systems Deleted:
$(for agent in "${AGENTS_TO_DELETE[@]}"; do echo "  - $agent"; done)

Backend Services Deleted:
$(for service in "${SERVICES_TO_DELETE[@]}"; do echo "  - $service"; done)

Config Directories Deleted:
$(for dir in "${CONFIG_DIRS_TO_DELETE[@]}"; do echo "  - $dir"; done)

Documentation Patterns Deleted:
$(for pattern in "${DOCS_TO_DELETE[@]}"; do echo "  - $pattern"; done)
EOF

echo -e "${GREEN}Deletion report saved to: $BACKUP_DIR/deletion_report.txt${NC}"
