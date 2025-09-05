"""
Foundational Knowledge Migration
Creates tables for CEO Knowledge Base sync, versioning, and audit trail
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from backup_configs.database_configs.migrations.migration_base import DatabaseMigrator, MigrationConfig


def migrate_up(migrator: DatabaseMigrator):
    """Create foundational knowledge tables"""
    conn = migrator.get_connection()

    try:
        # Main foundational knowledge table
        create_knowledge_table = f"""
            CREATE TABLE IF NOT EXISTS foundational_knowledge (
                id {migrator.get_primary_key_type()},
                source_id VARCHAR(255) NOT NULL,
                source_table VARCHAR(100) NOT NULL,
                source_platform VARCHAR(50) DEFAULT 'airtable',
                
                -- Content fields
                title VARCHAR(500) NOT NULL,
                content TEXT,
                category VARCHAR(100),
                tags TEXT,
                
                -- Classification
                data_classification VARCHAR(50) DEFAULT 'proprietary',
                sensitivity_level VARCHAR(20) DEFAULT 'high',
                access_level VARCHAR(50) DEFAULT 'executive',
                
                -- Metadata
                metadata JSON,
                embeddings TEXT,
                
                -- Tracking
                version INTEGER DEFAULT 1,
                is_current {migrator.get_boolean_type()},
                created_at {migrator.get_timestamp_type()},
                updated_at {migrator.get_timestamp_type()},
                last_synced_at {migrator.get_timestamp_type()},
                
                -- Unique constraint on source
                UNIQUE(source_id, source_table, source_platform)
            )
        """
        migrator.execute_sql(conn, create_knowledge_table)

        # Version history table
        create_version_table = f"""
            CREATE TABLE IF NOT EXISTS knowledge_versions (
                id {migrator.get_primary_key_type()},
                knowledge_id VARCHAR(255) NOT NULL,
                version_number INTEGER NOT NULL,
                
                -- Snapshot of data at this version
                title VARCHAR(500),
                content TEXT,
                category VARCHAR(100),
                tags TEXT,
                metadata JSON,
                
                -- Change tracking
                change_type VARCHAR(50),  -- 'create', 'update', 'delete'
                change_summary TEXT,
                changed_fields TEXT,
                previous_version_id VARCHAR(255),
                
                -- Who and when
                changed_by VARCHAR(255),
                changed_at {migrator.get_timestamp_type()},
                change_source VARCHAR(100),  -- 'sync', 'manual', 'api'
                
                FOREIGN KEY (knowledge_id) REFERENCES foundational_knowledge(id) ON DELETE CASCADE,
                UNIQUE(knowledge_id, version_number)
            )
        """
        migrator.execute_sql(conn, create_version_table)

        # Sync operations tracking
        create_sync_log_table = f"""
            CREATE TABLE IF NOT EXISTS sync_operations (
                id {migrator.get_primary_key_type()},
                sync_type VARCHAR(50) NOT NULL,  -- 'full', 'incremental', 'manual'
                source_platform VARCHAR(50) DEFAULT 'airtable',
                source_base VARCHAR(255),
                source_table VARCHAR(100),
                
                -- Sync results
                status VARCHAR(50) NOT NULL,  -- 'pending', 'running', 'completed', 'failed'
                records_processed INTEGER DEFAULT 0,
                records_created INTEGER DEFAULT 0,
                records_updated INTEGER DEFAULT 0,
                records_deleted INTEGER DEFAULT 0,
                records_failed INTEGER DEFAULT 0,
                
                -- Timing
                started_at {migrator.get_timestamp_type()},
                completed_at TIMESTAMP,
                duration_seconds INTEGER,
                
                -- Error tracking
                error_message TEXT,
                error_details JSON,
                
                -- Metadata
                triggered_by VARCHAR(255),
                sync_metadata JSON
            )
        """
        migrator.execute_sql(conn, create_sync_log_table)

        # Knowledge relationships table (for linking related knowledge)
        create_relationships_table = f"""
            CREATE TABLE IF NOT EXISTS knowledge_relationships (
                id {migrator.get_primary_key_type()},
                source_knowledge_id VARCHAR(255) NOT NULL,
                target_knowledge_id VARCHAR(255) NOT NULL,
                relationship_type VARCHAR(100) NOT NULL,  -- 'relates_to', 'depends_on', 'supersedes'
                strength FLOAT DEFAULT 1.0,
                metadata JSON,
                created_at {migrator.get_timestamp_type()},
                
                FOREIGN KEY (source_knowledge_id) REFERENCES foundational_knowledge(id) ON DELETE CASCADE,
                FOREIGN KEY (target_knowledge_id) REFERENCES foundational_knowledge(id) ON DELETE CASCADE,
                UNIQUE(source_knowledge_id, target_knowledge_id, relationship_type)
            )
        """
        migrator.execute_sql(conn, create_relationships_table)

        # Access log for audit trail
        create_access_log_table = f"""
            CREATE TABLE IF NOT EXISTS knowledge_access_log (
                id {migrator.get_primary_key_type()},
                knowledge_id VARCHAR(255),
                accessed_by VARCHAR(255),
                access_type VARCHAR(50),  -- 'read', 'update', 'delete', 'export'
                access_context TEXT,
                accessed_at {migrator.get_timestamp_type()},
                session_id VARCHAR(255),
                ip_address VARCHAR(45),
                user_agent TEXT,
                
                FOREIGN KEY (knowledge_id) REFERENCES foundational_knowledge(id) ON DELETE SET NULL
            )
        """
        migrator.execute_sql(conn, create_access_log_table)

        # Cache metadata table
        create_cache_table = f"""
            CREATE TABLE IF NOT EXISTS knowledge_cache_metadata (
                cache_key VARCHAR(500) PRIMARY KEY,
                knowledge_ids TEXT,  -- JSON array of knowledge IDs
                query_hash VARCHAR(255),
                created_at {migrator.get_timestamp_type()},
                expires_at TIMESTAMP,
                hit_count INTEGER DEFAULT 0,
                last_accessed_at TIMESTAMP,
                cache_size_bytes INTEGER
            )
        """
        migrator.execute_sql(conn, create_cache_table)

        # Create indexes for performance
        indexes = [
            # Foundational knowledge indexes
            "CREATE INDEX IF NOT EXISTS idx_fk_source ON foundational_knowledge(source_id, source_table)",
            "CREATE INDEX IF NOT EXISTS idx_fk_category ON foundational_knowledge(category)",
            "CREATE INDEX IF NOT EXISTS idx_fk_classification ON foundational_knowledge(data_classification)",
            "CREATE INDEX IF NOT EXISTS idx_fk_current ON foundational_knowledge(is_current)",
            "CREATE INDEX IF NOT EXISTS idx_fk_updated ON foundational_knowledge(updated_at)",
            
            # Version history indexes
            "CREATE INDEX IF NOT EXISTS idx_kv_knowledge ON knowledge_versions(knowledge_id)",
            "CREATE INDEX IF NOT EXISTS idx_kv_version ON knowledge_versions(version_number)",
            "CREATE INDEX IF NOT EXISTS idx_kv_changed ON knowledge_versions(changed_at)",
            
            # Sync operations indexes
            "CREATE INDEX IF NOT EXISTS idx_so_status ON sync_operations(status)",
            "CREATE INDEX IF NOT EXISTS idx_so_started ON sync_operations(started_at)",
            
            # Relationships indexes
            "CREATE INDEX IF NOT EXISTS idx_kr_source ON knowledge_relationships(source_knowledge_id)",
            "CREATE INDEX IF NOT EXISTS idx_kr_target ON knowledge_relationships(target_knowledge_id)",
            
            # Access log indexes
            "CREATE INDEX IF NOT EXISTS idx_kal_knowledge ON knowledge_access_log(knowledge_id)",
            "CREATE INDEX IF NOT EXISTS idx_kal_accessed ON knowledge_access_log(accessed_at)",
            "CREATE INDEX IF NOT EXISTS idx_kal_user ON knowledge_access_log(accessed_by)",
            
            # Cache indexes
            "CREATE INDEX IF NOT EXISTS idx_kcm_expires ON knowledge_cache_metadata(expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_kcm_accessed ON knowledge_cache_metadata(last_accessed_at)",
        ]

        for index_sql in indexes:
            migrator.execute_sql(conn, index_sql)

        # Create full-text search index if PostgreSQL
        if migrator.config.db_type == "postgresql":
            fts_index = """
                CREATE INDEX IF NOT EXISTS idx_fk_fts 
                ON foundational_knowledge 
                USING gin(to_tsvector('english', title || ' ' || COALESCE(content, '') || ' ' || COALESCE(tags, '')))
            """
            migrator.execute_sql(conn, fts_index)

        # Record migration
        migrator.execute_sql(
            conn,
            "INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)"
            if migrator.config.db_type == "sqlite"
            else "INSERT INTO schema_migrations (version) VALUES (%s) ON CONFLICT (version) DO NOTHING",
            ("002_foundational_knowledge",),
        )

        conn.commit()
        print("✅ Foundational knowledge migration completed successfully")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


def migrate_down(migrator: DatabaseMigrator):
    """Rollback foundational knowledge tables"""
    conn = migrator.get_connection()

    try:
        # Drop tables in reverse order of dependencies
        drop_statements = [
            "DROP TABLE IF EXISTS knowledge_cache_metadata",
            "DROP TABLE IF EXISTS knowledge_access_log",
            "DROP TABLE IF EXISTS knowledge_relationships",
            "DROP TABLE IF EXISTS sync_operations",
            "DROP TABLE IF EXISTS knowledge_versions",
            "DROP TABLE IF EXISTS foundational_knowledge",
        ]

        for drop_sql in drop_statements:
            migrator.execute_sql(conn, drop_sql)

        # Remove migration record
        migrator.execute_sql(
            conn,
            "DELETE FROM schema_migrations WHERE version = ?"
            if migrator.config.db_type == "sqlite"
            else "DELETE FROM schema_migrations WHERE version = %s",
            ("002_foundational_knowledge",),
        )

        conn.commit()
        print("✅ Foundational knowledge rollback completed successfully")

    except Exception as e:
        conn.rollback()
        print(f"❌ Rollback failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    from backup_configs.database_configs.migrations.migration_base import get_config_from_env
    
    config = get_config_from_env()
    migrator = DatabaseMigrator(config)
    
    command = sys.argv[1] if len(sys.argv) > 1 else "up"
    
    if command == "up":
        migrate_up(migrator)
    elif command == "down":
        migrate_down(migrator)
    else:
        print("Usage: python 002_foundational_knowledge.py [up|down]")
        sys.exit(1)