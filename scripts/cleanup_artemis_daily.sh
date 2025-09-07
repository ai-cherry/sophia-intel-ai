#!/bin/bash
# Daily cleanup script for Artemis collaboration system
# Prevents AI confusion from stale data, duplicates, and conflicts

set -e

# Configuration
BASE_DIR="/Users/lynnmusil/sophia-intel-ai"
LOG_DIR="${BASE_DIR}/logs/cleanup"
ARCHIVE_DIR="${BASE_DIR}/archive"
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/cleanup_${DATE}.log"

# Create directories if needed
mkdir -p "${LOG_DIR}" "${ARCHIVE_DIR}"

# Logging function
log() {
    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] $1" | tee -a "${LOG_FILE}"
}

log "Starting Artemis daily cleanup"

# 1. Clean old collaboration proposals (>7 days)
log "Cleaning old collaboration proposals..."
cd "${BASE_DIR}"
python3 -c "
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
sys.path.insert(0, '${BASE_DIR}')

try:
    from app.mcp.clients.stdio_client import StdioMCPClient

    client = StdioMCPClient(Path.cwd())
    cutoff = (datetime.now() - timedelta(days=7)).isoformat()

    # Search for old proposals
    old_items = client.memory_search('collab', limit=1000)

    archived = 0
    for item in old_items:
        if item.get('timestamp', '') < cutoff:
            # Archive to file
            archive_file = Path('${ARCHIVE_DIR}/collab_archive_${DATE}.jsonl')
            with open(archive_file, 'a') as f:
                f.write(json.dumps(item) + '\\n')
            archived += 1

    print(f'Archived {archived} old collaboration items')
except Exception as e:
    print(f'Error archiving collaborations: {e}')
    sys.exit(1)
" || log "Warning: Collaboration cleanup failed"

# 2. Clean duplicate memory entries
log "Removing duplicate memory entries..."
python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, '${BASE_DIR}')

try:
    from app.memory.unified_memory_router import UnifiedMemoryRouter
    import asyncio

    async def cleanup_duplicates():
        router = UnifiedMemoryRouter()
        stats = await router.cleanup_duplicates()
        return stats

    stats = asyncio.run(cleanup_duplicates())
    print(f'Removed {stats.get(\"duplicates_removed\", 0)} duplicate entries')
except Exception as e:
    print(f'Error cleaning duplicates: {e}')
" || log "Warning: Duplicate cleanup failed"

# 3. Clean old test artifacts
log "Cleaning old test artifacts..."
find "${BASE_DIR}" -name "*.pyc" -type f -mtime +7 -delete
find "${BASE_DIR}" -name "__pycache__" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
find "${BASE_DIR}" -name ".pytest_cache" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
find "${BASE_DIR}" -name "*.coverage" -type f -mtime +7 -delete

# 4. Rotate logs
log "Rotating logs..."
find "${LOG_DIR}" -name "*.log" -type f -mtime +30 -exec gzip {} \;
find "${LOG_DIR}" -name "*.log.gz" -type f -mtime +90 -delete

# 5. Clean temporary files
log "Cleaning temporary files..."
find "${BASE_DIR}/tmp" -type f -mtime +3 -delete 2>/dev/null || true
find /tmp -name "artemis_*" -type f -mtime +1 -delete 2>/dev/null || true

# 6. Optimize databases
log "Optimizing databases..."
if [ -f "${BASE_DIR}/tmp/supermemory_lite.db" ]; then
    sqlite3 "${BASE_DIR}/tmp/supermemory_lite.db" "VACUUM;" || log "Warning: SQLite vacuum failed"
fi

# 7. Clean old MCP status files
log "Cleaning old MCP status files..."
find "${BASE_DIR}" -name "mcp_status_*.json" -type f -mtime +7 -delete
find "${BASE_DIR}" -name "mcp_validation_*.json" -type f -mtime +7 -delete

# 8. Archive old swarm execution results
log "Archiving old swarm results..."
find "${BASE_DIR}" -name "artemis_*_test_*.json" -type f -mtime +14 -exec mv {} "${ARCHIVE_DIR}/" \;

# 9. Clean Redis if running
if command -v redis-cli &> /dev/null; then
    log "Cleaning Redis expired keys..."
    redis-cli --scan --pattern "artemis:*" | while read key; do
        ttl=$(redis-cli TTL "$key")
        if [ "$ttl" -eq "-1" ]; then
            # No TTL set, check age and set TTL
            redis-cli EXPIRE "$key" 604800  # 7 days
        fi
    done 2>/dev/null || log "Warning: Redis cleanup failed"
fi

# 10. Report disk usage
log "Disk usage report:"
du -sh "${BASE_DIR}" | tee -a "${LOG_FILE}"
du -sh "${BASE_DIR}/tmp" 2>/dev/null | tee -a "${LOG_FILE}"
du -sh "${ARCHIVE_DIR}" | tee -a "${LOG_FILE}"

log "Cleanup completed successfully"

# Send summary if notification system is configured
if [ -n "${SLACK_WEBHOOK_URL}" ]; then
    SUMMARY=$(tail -20 "${LOG_FILE}")
    curl -X POST "${SLACK_WEBHOOK_URL}" \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"Artemis cleanup completed:\\n\\`\\`\\`${SUMMARY}\\`\\`\\`\"}" \
        2>/dev/null || true
fi

exit 0
