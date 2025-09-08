# Repository Cleanup Recommendations

## Immediate Actions Required

### 1. Database files in repository
**Issue**: Database files found in tmp/ directory
**Action**: Move to data/ (gitignored) or delete if recreatable
**Files**:
- tmp/supermemory.db
- tmp/embedding_cache.db
- tmp/knowledge_graph.db
- ./dump.rdb

### 2. Backup/Archive files
**Issue**: Backup and archive files cluttering repository
**Action**: Move to archive/ directory with date stamps
**Files**:
- ./backup_configs
- ./app/scaffolding
- ./app/scaffolding/ai_scaffolding_config.yaml
- ./archive
- ./config/scaffolding_config.yaml
- ./tests_backup
- ./backup_hybrid_20250905_183452
- ./scripts/init_ai_scaffolding.py
- ./scripts/redis-backup.sh
- ./scripts/backup-all.sh
- ./scripts/cleanup_old_mcp.sh
- ./.git/logs/refs/remotes/origin/prod-backup-20250817
- ./.git/logs/refs/remotes/origin/backup-updated
- ./.git/logs/refs/remotes/origin/backup-current-main
- ./.git/logs/refs/remotes/origin/manual-task-priority-backup
- ./.git/logs/refs/remotes/origin/sophia-v4-minimal-backup
- ./.git/logs/refs/remotes/origin/sophia-v4-production-backup
- ./.git/logs/refs/remotes/origin/backup-before-testing
- ./.git/logs/refs/remotes/origin/pre-cleanup-backup-20250817-171731
- ./.git/refs/tags/backup

### 3. One-time scripts
**Issue**: Migration and cleanup scripts no longer needed
**Action**: Move to scripts/archive/ with README explaining purpose
**Scripts**:
- scripts/weaviate_migration.py
- scripts/final_validation.py
- scripts/phase1_nuclear_deletion.sh
- scripts/cleanup_artemis_daily.sh
- scripts/final_cleanup_optimization.py
- scripts/cleanup_docs.sh
- scripts/test_final_model_architecture.py
- scripts/execute_cleanup_and_optimization.sh
- scripts/cleanup_obsolete_code.sh
- scripts/phase1_asip_rebuild.sh
- scripts/cleanup.py
- scripts/emergency_cleanup.sh
- scripts/artemis_final_working_swarm.py
- scripts/artemis_swarm_final.py
- scripts/setup_cleanup_cron.sh
- scripts/migration
- scripts/migration/validate_migration.py
- scripts/migration/rollback_migration.py
- scripts/execute_phase1_complete.sh
- scripts/cleanup_old_mcp.sh

### 4. Large files
**Issue**: Large files may not belong in git repository
**Action**: Review each file, move to LFS or external storage if needed
**Files**:
- ./tmp/supermemory.db ( 62M)

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
