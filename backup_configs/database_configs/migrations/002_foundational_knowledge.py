"""
Foundational Knowledge Migration - Database Agnostic
Adds tables for foundational knowledge management, versioning, and sync tracking
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from backup_configs.database_configs.migrations.migration_base import (
    DatabaseMigrator,
    MigrationConfig,
)


def migrate_up(migrator: DatabaseMigrator):
    """Create foundational knowledge tables"""
    conn = migrator.get_connection()

    try:
        # Create foundational_knowledge table
        create_foundational_knowledge = f"""
            CREATE TABLE IF NOT EXISTS foundational_knowledge (
                id {migrator.get_primary_key_type()},
                name VARCHAR(255) NOT NULL,
                category VARCHAR(100) NOT NULL,
                classification VARCHAR(50) DEFAULT 'foundational',
                priority INTEGER CHECK (priority BETWEEN 1 AND 5),
                content TEXT NOT NULL,
                pay_ready_context TEXT,
                metadata TEXT DEFAULT '{{}}',
                source VARCHAR(50) DEFAULT 'airtable',
                source_id VARCHAR(255),
                is_active {migrator.get_boolean_type()},
                created_at {migrator.get_timestamp_type()},
                updated_at {migrator.get_timestamp_type()},
                synced_at {migrator.get_timestamp_type()}
            )
        """
        migrator.execute_sql(conn, create_foundational_knowledge)

        # Create knowledge_versions table
        create_versions_table = f"""
            CREATE TABLE IF NOT EXISTS knowledge_versions (
                version_id {migrator.get_primary_key_type()},
                knowledge_id VARCHAR(255) NOT NULL,
                version_number INTEGER NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                change_summary TEXT,
                changed_by VARCHAR(255),
                created_at {migrator.get_timestamp_type()},
                FOREIGN KEY (knowledge_id) REFERENCES foundational_knowledge (id) ON DELETE CASCADE,
                UNIQUE (knowledge_id, version_number)
            )
        """
        migrator.execute_sql(conn, create_versions_table)

        # Create sync_operations table
        create_sync_table = f"""
            CREATE TABLE IF NOT EXISTS sync_operations (
                id {migrator.get_primary_key_type()},
                operation_type VARCHAR(50),
                source VARCHAR(50),
                status VARCHAR(50),
                started_at {migrator.get_timestamp_type()},
                completed_at {migrator.get_timestamp_type()},
                records_processed INTEGER DEFAULT 0,
                conflicts_detected INTEGER DEFAULT 0,
                error_details TEXT
            )
        """
        migrator.execute_sql(conn, create_sync_table)

        # Create sync_conflicts table
        create_conflicts_table = f"""
            CREATE TABLE IF NOT EXISTS sync_conflicts (
                id {migrator.get_primary_key_type()},
                knowledge_id VARCHAR(255),
                sync_operation_id VARCHAR(255),
                local_version TEXT,
                remote_version TEXT,
                conflict_type VARCHAR(50),
                resolution_status VARCHAR(50) DEFAULT 'pending',
                resolved_by VARCHAR(255),
                resolved_at {migrator.get_timestamp_type()},
                created_at {migrator.get_timestamp_type()},
                FOREIGN KEY (knowledge_id) REFERENCES foundational_knowledge (id),
                FOREIGN KEY (sync_operation_id) REFERENCES sync_operations (id)
            )
        """
        migrator.execute_sql(conn, create_conflicts_table)

        # Create knowledge_tags table for extensibility
        create_tags_table = f"""
            CREATE TABLE IF NOT EXISTS knowledge_tags (
                id {migrator.get_primary_key_type()},
                knowledge_id VARCHAR(255) NOT NULL,
                tag_name VARCHAR(100) NOT NULL,
                tag_value TEXT,
                tag_type VARCHAR(50) DEFAULT 'custom',
                created_at {migrator.get_timestamp_type()},
                FOREIGN KEY (knowledge_id) REFERENCES foundational_knowledge (id) ON DELETE CASCADE,
                UNIQUE (knowledge_id, tag_name)
            )
        """
        migrator.execute_sql(conn, create_tags_table)

        # Create knowledge_relationships table for connections
        create_relationships_table = f"""
            CREATE TABLE IF NOT EXISTS knowledge_relationships (
                id {migrator.get_primary_key_type()},
                source_id VARCHAR(255) NOT NULL,
                target_id VARCHAR(255) NOT NULL,
                relationship_type VARCHAR(100) NOT NULL,
                strength REAL DEFAULT 1.0,
                metadata TEXT,
                created_at {migrator.get_timestamp_type()},
                FOREIGN KEY (source_id) REFERENCES foundational_knowledge (id) ON DELETE CASCADE,
                FOREIGN KEY (target_id) REFERENCES foundational_knowledge (id) ON DELETE CASCADE,
                UNIQUE (source_id, target_id, relationship_type)
            )
        """
        migrator.execute_sql(conn, create_relationships_table)

        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_foundational_knowledge_category ON foundational_knowledge(category)",
            "CREATE INDEX IF NOT EXISTS idx_foundational_knowledge_classification ON foundational_knowledge(classification)",
            "CREATE INDEX IF NOT EXISTS idx_foundational_knowledge_priority ON foundational_knowledge(priority)",
            "CREATE INDEX IF NOT EXISTS idx_foundational_knowledge_source ON foundational_knowledge(source, source_id)",
            "CREATE INDEX IF NOT EXISTS idx_foundational_knowledge_active ON foundational_knowledge(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_versions_knowledge ON knowledge_versions(knowledge_id)",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_versions_number ON knowledge_versions(knowledge_id, version_number)",
            "CREATE INDEX IF NOT EXISTS idx_sync_operations_status ON sync_operations(status)",
            "CREATE INDEX IF NOT EXISTS idx_sync_operations_time ON sync_operations(started_at, completed_at)",
            "CREATE INDEX IF NOT EXISTS idx_sync_conflicts_status ON sync_conflicts(resolution_status)",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_tags_knowledge ON knowledge_tags(knowledge_id)",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_tags_name ON knowledge_tags(tag_name)",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_relationships_source ON knowledge_relationships(source_id)",
            "CREATE INDEX IF NOT EXISTS idx_knowledge_relationships_target ON knowledge_relationships(target_id)",
        ]

        for index_sql in indexes:
            migrator.execute_sql(conn, index_sql)

        # Insert default foundational knowledge categories
        default_categories = [
            ("company_overview", "foundational", 5, "Core company information and mission"),
            ("strategic_initiatives", "foundational", 5, "CEO-level strategic initiatives"),
            ("executive_decisions", "foundational", 5, "Critical executive decisions and rationale"),
            ("market_intelligence", "strategic", 4, "Market analysis and competitive intelligence"),
            ("operational_metrics", "operational", 3, "Key operational metrics and KPIs"),
        ]

        for name, classification, priority, description in default_categories:
            if migrator.config.db_type == "sqlite":
                insert_sql = """
                    INSERT OR IGNORE INTO foundational_knowledge 
                    (id, name, category, classification, priority, content, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
            else:  # PostgreSQL
                insert_sql = """
                    INSERT INTO foundational_knowledge 
                    (id, name, category, classification, priority, content, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """
            
            import json
            migrator.execute_sql(
                conn,
                insert_sql,
                (
                    f"default-{name}",
                    name.replace("_", " ").title(),
                    "system",
                    classification,
                    priority,
                    json.dumps({"description": description, "is_template": True}),
                    json.dumps({"created_by": "system", "is_default": True})
                ),
            )

        # Record migration
        migrator.execute_sql(
            conn,
            "INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)"
            if migrator.config.db_type == "sqlite"
            else "INSERT INTO schema_migrations (version) VALUES (%s) ON CONFLICT (version) DO NOTHING",
            ("002_foundational_knowledge",),
        )

        conn.commit()
        print("✅ Foundational Knowledge migration completed successfully")

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
        # Drop tables in reverse order
        drop_statements = [
            "DROP TABLE IF EXISTS knowledge_relationships",
            "DROP TABLE IF EXISTS knowledge_tags",
            "DROP TABLE IF EXISTS sync_conflicts",
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
        print("✅ Foundational Knowledge rollback completed successfully")

    except Exception as e:
        conn.rollback()
        print(f"❌ Rollback failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    from backup_configs.database_configs.migrations.migration_base import (
        get_config_from_env,
    )

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