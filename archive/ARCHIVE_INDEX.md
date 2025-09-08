# Archive Index

**Created**: September 8, 2024  
**Purpose**: Consolidated archive of backup configurations and deprecated files

## 📁 Directory Structure

```
archive/
├── ARCHIVE_INDEX.md (this file)
├── backups/
│   ├── backup_configs_20240908/     # Configuration backups
│   ├── tests_backup_20240908/       # Test file backups  
│   └── backup_hybrid_20240905/      # Hybrid system backup
└── docker-compose/                 # Old compose files (existing)
```

## 📋 Contents

### backup_configs_20240908/
- **Source**: Root `backup_configs/` directory
- **Contents**: Database configs, integration configs, port configs, portkey configs
- **Date Archived**: 2024-09-08
- **Reason**: Consolidation cleanup - moved to centralized archive

### tests_backup_20240908/
- **Source**: Root `tests_backup/` directory  
- **Contents**: `test_artemis_swarm_orchestrator.py`
- **Date Archived**: 2024-09-08
- **Reason**: Consolidation cleanup - moved to centralized archive

### backup_hybrid_20240905/
- **Source**: Root `backup_hybrid_20250905_183452/` directory
- **Contents**: `artemis_unified.py` and related files
- **Date Archived**: 2024-09-08 (originally created 2024-09-05)
- **Reason**: Consolidation cleanup - moved to centralized archive

## 🔄 Retention Policy

- **Active Archives**: Keep for 6 months minimum
- **Configuration Backups**: Keep indefinitely (small size, high value)
- **Code Backups**: Review quarterly, keep if historically significant
- **Review Date**: March 8, 2025

## 🔍 Recovery Instructions

To restore any archived content:

1. **Locate** the archived directory above
2. **Copy** (don't move) files back to original location
3. **Test** functionality before removing from archive
4. **Update** this index if permanent restoration

## 📝 Notes

- All moves preserve original timestamps
- Git history remains intact for all archived files
- Archives are read-only - modify copies, not originals
- Large archives may be moved to external storage in future