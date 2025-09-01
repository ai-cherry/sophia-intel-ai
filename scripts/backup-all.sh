#!/bin/bash

# Sophia Intel AI - Complete System Backup Script
# Creates comprehensive backup before MCP migration

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
BACKUP_NAME="sophia-backup-$(date +%Y%m%d_%H%M%S)"

echo -e "${GREEN}🔒 Starting Sophia Intel AI Complete Backup${NC}"
echo "Backup directory: $BACKUP_DIR"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# 1. Backup PostgreSQL
echo -e "${YELLOW}📊 Backing up PostgreSQL...${NC}"
if docker exec sophia-postgres pg_dump -U sophia sophia_db > "$BACKUP_DIR/postgres_dump.sql" 2>/dev/null; then
    echo -e "${GREEN}✓ PostgreSQL backed up${NC}"
else
    echo -e "${YELLOW}⚠ PostgreSQL backup skipped (not running or no data)${NC}"
fi

# 2. Backup Redis
echo -e "${YELLOW}💾 Backing up Redis...${NC}"
if docker exec redis redis-cli --rdb "$BACKUP_DIR/redis_dump.rdb" 2>/dev/null; then
    echo -e "${GREEN}✓ Redis backed up${NC}"
else
    echo -e "${YELLOW}⚠ Redis backup skipped (not running or no data)${NC}"
fi

# 3. Backup Weaviate (export schema and data)
echo -e "${YELLOW}🔍 Backing up Weaviate...${NC}"
python3 - <<EOF
import weaviate
import json
import os

try:
    client = weaviate.Client("http://localhost:8080")
    
    # Export schema
    schema = client.schema.get()
    with open("$BACKUP_DIR/weaviate_schema.json", "w") as f:
        json.dump(schema, f, indent=2)
    
    # Export data (simplified - in production use batch export)
    print("✓ Weaviate schema exported")
except Exception as e:
    print(f"⚠ Weaviate backup skipped: {e}")
EOF

# 4. Backup configuration files
echo -e "${YELLOW}⚙️ Backing up configuration files...${NC}"
cp -r .env* "$BACKUP_DIR/" 2>/dev/null || true
cp -r config/ "$BACKUP_DIR/" 2>/dev/null || true
cp docker-compose*.yml "$BACKUP_DIR/" 2>/dev/null || true
cp fly*.toml "$BACKUP_DIR/" 2>/dev/null || true
echo -e "${GREEN}✓ Configuration files backed up${NC}"

# 5. Backup application code (git state)
echo -e "${YELLOW}📝 Saving git state...${NC}"
git rev-parse HEAD > "$BACKUP_DIR/git_commit.txt"
git status > "$BACKUP_DIR/git_status.txt"
git diff > "$BACKUP_DIR/git_diff.txt"
echo -e "${GREEN}✓ Git state saved${NC}"

# 6. Create manifest
echo -e "${YELLOW}📋 Creating backup manifest...${NC}"
cat > "$BACKUP_DIR/manifest.json" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "version": "1.0.0",
  "components": {
    "postgresql": $([ -f "$BACKUP_DIR/postgres_dump.sql" ] && echo "true" || echo "false"),
    "redis": $([ -f "$BACKUP_DIR/redis_dump.rdb" ] && echo "true" || echo "false"),
    "weaviate": $([ -f "$BACKUP_DIR/weaviate_schema.json" ] && echo "true" || echo "false"),
    "config": true,
    "git": true
  },
  "git_commit": "$(git rev-parse HEAD)",
  "backup_size": "$(du -sh "$BACKUP_DIR" | cut -f1)"
}
EOF

# 7. Compress backup
echo -e "${YELLOW}📦 Compressing backup...${NC}"
tar -czf "${BACKUP_NAME}.tar.gz" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")"

# 8. Calculate checksum
echo -e "${YELLOW}🔐 Calculating checksum...${NC}"
shasum -a 256 "${BACKUP_NAME}.tar.gz" > "${BACKUP_NAME}.tar.gz.sha256"

# Final summary
echo -e "${GREEN}✅ Backup Complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 Backup Location: ${BACKUP_NAME}.tar.gz"
echo "📊 Backup Size: $(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)"
echo "🔐 Checksum: $(cat "${BACKUP_NAME}.tar.gz.sha256" | cut -d' ' -f1)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To restore from this backup:"
echo "  tar -xzf ${BACKUP_NAME}.tar.gz"
echo "  ./scripts/restore-backup.sh $BACKUP_DIR"