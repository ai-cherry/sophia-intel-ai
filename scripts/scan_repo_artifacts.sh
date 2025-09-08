#!/bin/bash
# Repository Artifact Scanner - Generate audit report for cleanup
# Part of Sophia Intel AI standardized tooling

set -e

echo "📊 Sophia Intel AI - Repository Artifact Scanner"
echo "=============================================="

# Ensure we're in the right directory
EXPECTED_DIR="/Users/lynnmusil/sophia-intel-ai"
if [ "$(pwd)" != "$EXPECTED_DIR" ]; then
    cd "$EXPECTED_DIR" || { echo "❌ Cannot change to $EXPECTED_DIR"; exit 1; }
fi

REPORT_FILE="repo_audit_report.json"
TEMP_FILE="/tmp/repo_scan_$$.tmp"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

# Initialize JSON report
cat > "$TEMP_FILE" << 'EOF'
{
  "scan_timestamp": "TIMESTAMP_PLACEHOLDER",
  "repository": "ai-cherry/sophia-intel-ai",
  "local_path": "/Users/lynnmusil/sophia-intel-ai",
  "findings": {
    "backup_archive_files": [],
    "temporary_databases": [],
    "large_files": [],
    "duplicate_configs": [],
    "one_time_scripts": [],
    "cache_directories": []
  },
  "recommendations": {
    "delete": [],
    "move_to_gitignore": [],
    "archive": [],
    "consolidate": []
  },
  "summary": {
    "total_issues": 0,
    "space_reclaimable": "0MB",
    "action_required": false
  }
}
EOF

# Replace timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
sed -i.bak "s/TIMESTAMP_PLACEHOLDER/$TIMESTAMP/" "$TEMP_FILE" && rm "$TEMP_FILE.bak"

echo "1. Scanning for backup and archive files..."

# Find backup/archive files
BACKUP_FILES=$(mktemp)
find . -name "*backup*" -o -name "*archive*" -o -name "*old*" -o -name "*_bak" -o -name "*.bak" -o -name "*_old*" 2>/dev/null > "$BACKUP_FILES"

BACKUP_COUNT=$(wc -l < "$BACKUP_FILES")
if [ "$BACKUP_COUNT" -gt 0 ]; then
    warning "Found $BACKUP_COUNT backup/archive files"
    
    # Add to JSON (simplified - would need jq for proper JSON manipulation)
    echo "   Examples:"
    head -5 "$BACKUP_FILES" | while read -r file; do
        echo "   - $file"
    done
fi

echo ""
echo "2. Scanning for temporary databases and dumps..."

# Find database files and dumps in tmp/
DB_FILES=$(mktemp)
find tmp/ -name "*.db" -o -name "*.dump" -o -name "dump.*" 2>/dev/null > "$DB_FILES" || true
find . -name "dump.rdb" 2>/dev/null >> "$DB_FILES" || true

DB_COUNT=$(wc -l < "$DB_FILES")
if [ "$DB_COUNT" -gt 0 ]; then
    warning "Found $DB_COUNT database/dump files"
    echo "   Files found:"
    cat "$DB_FILES" | while read -r file; do
        if [ -n "$file" ]; then
            SIZE=$(du -h "$file" 2>/dev/null | cut -f1 || echo "?")
            echo "   - $file ($SIZE)"
        fi
    done
fi

echo ""
echo "3. Scanning for large files (>10MB)..."

LARGE_FILES=$(mktemp)
find . -size +10M -not -path "./.git/*" 2>/dev/null > "$LARGE_FILES"

LARGE_COUNT=$(wc -l < "$LARGE_FILES")
if [ "$LARGE_COUNT" -gt 0 ]; then
    warning "Found $LARGE_COUNT large files (>10MB)"
    echo "   Files:"
    cat "$LARGE_FILES" | while read -r file; do
        if [ -n "$file" ]; then
            SIZE=$(du -h "$file" 2>/dev/null | cut -f1 || echo "?")
            echo "   - $file ($SIZE)"
        fi
    done
fi

echo ""
echo "4. Checking for duplicate configuration files..."

# Look for multiple docker-compose files
DOCKER_COMPOSE_COUNT=$(find . -name "docker-compose*.yml" -o -name "docker-compose*.yaml" | wc -l)
if [ "$DOCKER_COMPOSE_COUNT" -gt 1 ]; then
    warning "Found $DOCKER_COMPOSE_COUNT docker-compose files - consider consolidation"
    find . -name "docker-compose*.yml" -o -name "docker-compose*.yaml" | head -5
fi

# Look for multiple prometheus configs
PROMETHEUS_COUNT=$(find . -name "prometheus*.yml" -o -name "prometheus*.yaml" | wc -l)
if [ "$PROMETHEUS_COUNT" -gt 1 ]; then
    warning "Found $PROMETHEUS_COUNT prometheus config files - consider consolidation"
fi

echo ""
echo "5. Identifying one-time/migration scripts..."

ONE_TIME_SCRIPTS=$(mktemp)
find scripts/ -name "*phase*" -o -name "*final*" -o -name "*emergency*" -o -name "*nuclear*" -o -name "*migration*" -o -name "*cleanup*" 2>/dev/null > "$ONE_TIME_SCRIPTS"

SCRIPT_COUNT=$(wc -l < "$ONE_TIME_SCRIPTS")
if [ "$SCRIPT_COUNT" -gt 0 ]; then
    warning "Found $SCRIPT_COUNT potential one-time scripts"
    echo "   Examples:"
    head -10 "$ONE_TIME_SCRIPTS" | while read -r file; do
        echo "   - $file"
    done
fi

echo ""
echo "6. Checking for cache directories and temporary files..."

CACHE_DIRS=$(find . -type d -name "*cache*" -o -name "__pycache__" -o -name ".pytest_cache" 2>/dev/null | wc -l)
if [ "$CACHE_DIRS" -gt 0 ]; then
    success "Found $CACHE_DIRS cache directories (normal, should be in .gitignore)"
fi

echo ""
echo "=============================================="

# Generate recommendations
echo "7. Generating recommendations..."

# Create simplified recommendations (in practice, would use proper JSON tools)
cat >> recommendations.md << 'EOF'
# Repository Cleanup Recommendations

## Immediate Actions Required

### 1. Database files in repository
**Issue**: Database files found in tmp/ directory
**Action**: Move to data/ (gitignored) or delete if recreatable
**Files**:
EOF

if [ -s "$DB_FILES" ]; then
    cat "$DB_FILES" | while read -r file; do
        if [ -n "$file" ]; then
            echo "- $file" >> recommendations.md
        fi
    done
else
    echo "- None found" >> recommendations.md
fi

cat >> recommendations.md << 'EOF'

### 2. Backup/Archive files
**Issue**: Backup and archive files cluttering repository
**Action**: Move to archive/ directory with date stamps
**Files**:
EOF

if [ -s "$BACKUP_FILES" ]; then
    head -20 "$BACKUP_FILES" | while read -r file; do
        echo "- $file" >> recommendations.md
    done
else
    echo "- None found" >> recommendations.md
fi

cat >> recommendations.md << 'EOF'

### 3. One-time scripts
**Issue**: Migration and cleanup scripts no longer needed
**Action**: Move to scripts/archive/ with README explaining purpose
**Scripts**:
EOF

if [ -s "$ONE_TIME_SCRIPTS" ]; then
    head -20 "$ONE_TIME_SCRIPTS" | while read -r file; do
        echo "- $file" >> recommendations.md
    done
else
    echo "- None found" >> recommendations.md
fi

cat >> recommendations.md << 'EOF'

### 4. Large files
**Issue**: Large files may not belong in git repository
**Action**: Review each file, move to LFS or external storage if needed
**Files**:
EOF

if [ -s "$LARGE_FILES" ]; then
    cat "$LARGE_FILES" | while read -r file; do
        if [ -n "$file" ]; then
            SIZE=$(du -h "$file" 2>/dev/null | cut -f1 || echo "?")
            echo "- $file ($SIZE)" >> recommendations.md
        fi
    done
else
    echo "- None found" >> recommendations.md
fi

cat >> recommendations.md << 'EOF'

## .gitignore Updates Needed

Add these patterns to .gitignore:
```
# Temporary databases and caches
*.db
dump.rdb
tmp/*.db
data/

# Cache directories
*cache*/
__pycache__/
.pytest_cache/

# IDE and OS files
.DS_Store
Thumbs.db
*.swp
*.swo

# Virtual environments (critical)
venv/
.venv/
env/
.env/
pyvenv.cfg
```

## Configuration Consolidation

Consider consolidating duplicate configuration files:
- Multiple docker-compose files found
- Multiple prometheus configurations
- Choose one canonical version per service

## Next Steps

1. Run `make clean-artifacts` to remove safe-to-delete items
2. Review recommendations.md and manually handle remaining items  
3. Update
