"""
RBAC Foundation Migration - Database Agnostic
Supports both SQLite (development) and PostgreSQL (production)
"""
from __future__ import annotations

import os
import sqlite3
import psycopg2
from typing import Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MigrationConfig:
    """Database migration configuration"""
    db_type: str  # 'sqlite' or 'postgresql'
    db_path: Optional[str] = None  # For SQLite
    db_host: Optional[str] = None  # For PostgreSQL
    db_port: Optional[int] = None
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None


class DatabaseMigrator:
    """Database-agnostic migration runner"""
    
    def __init__(self, config: MigrationConfig):
        self.config = config
        
    def get_connection(self):
        """Get database connection based on configuration"""
        if self.config.db_type == 'sqlite':
            return sqlite3.connect(self.config.db_path or 'sophia.db')
        elif self.config.db_type == 'postgresql':
            return psycopg2.connect(
                host=self.config.db_host,
                port=self.config.db_port or 5432,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password
            )
        else:
            raise ValueError(f"Unsupported database type: {self.config.db_type}")
            
    def execute_sql(self, conn: Any, sql: str, params: tuple = ()):
        """Execute SQL with database-specific handling"""
        cursor = conn.cursor()
        cursor.execute(sql, params)
        
        if self.config.db_type == 'postgresql':
            conn.commit()
        
    def table_exists(self, conn: Any, table_name: str) -> bool:
        """Check if table exists"""
        if self.config.db_type == 'sqlite':
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            return cursor.fetchone() is not None
        elif self.config.db_type == 'postgresql':
            cursor = conn.cursor()
            cursor.execute(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)",
                (table_name,)
            )
            return cursor.fetchone()[0]
            
    def get_primary_key_type(self) -> str:
        """Get appropriate primary key type for database"""
        if self.config.db_type == 'sqlite':
            return 'TEXT PRIMARY KEY'
        elif self.config.db_type == 'postgresql':
            return 'UUID PRIMARY KEY DEFAULT gen_random_uuid()'
            
    def get_timestamp_type(self) -> str:
        """Get appropriate timestamp type for database"""
        if self.config.db_type == 'sqlite':
            return 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        elif self.config.db_type == 'postgresql':
            return 'TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP'
            
    def get_boolean_type(self) -> str:
        """Get appropriate boolean type for database"""
        if self.config.db_type == 'sqlite':
            return 'BOOLEAN DEFAULT TRUE'
        elif self.config.db_type == 'postgresql':
            return 'BOOLEAN DEFAULT TRUE'


def migrate_up(migrator: DatabaseMigrator):
    """Create RBAC tables"""
    conn = migrator.get_connection()
    
    try:
        # Create migration tracking table
        if not migrator.table_exists(conn, 'schema_migrations'):
            create_migrations_table = f"""
                CREATE TABLE schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at {migrator.get_timestamp_type()}
                )
            """
            migrator.execute_sql(conn, create_migrations_table)
            
        # Create users table
        create_users_table = f"""
            CREATE TABLE IF NOT EXISTS users (
                user_id {migrator.get_primary_key_type()},
                email VARCHAR(255) UNIQUE NOT NULL,
                role VARCHAR(50) NOT NULL,
                created_at {migrator.get_timestamp_type()},
                is_active {migrator.get_boolean_type()}
            )
        """
        migrator.execute_sql(conn, create_users_table)
        
        # Create user_permissions table
        create_permissions_table = f"""
            CREATE TABLE IF NOT EXISTS user_permissions (
                user_id VARCHAR(255),
                permission VARCHAR(255),
                granted_at {migrator.get_timestamp_type()},
                FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                PRIMARY KEY (user_id, permission)
            )
        """
        migrator.execute_sql(conn, create_permissions_table)
        
        # Create audit_log table for tracking changes
        create_audit_table = f"""
            CREATE TABLE IF NOT EXISTS audit_log (
                id {migrator.get_primary_key_type()},
                user_id VARCHAR(255),
                action VARCHAR(100) NOT NULL,
                resource_type VARCHAR(100),
                resource_id VARCHAR(255),
                details TEXT,
                timestamp {migrator.get_timestamp_type()},
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """
        migrator.execute_sql(conn, create_audit_table)
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
            "CREATE INDEX IF NOT EXISTS idx_user_permissions_user ON user_permissions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)"
        ]
        
        for index_sql in indexes:
            migrator.execute_sql(conn, index_sql)
            
        # Insert default owner user if running fresh
        if migrator.config.db_type == 'sqlite':
            default_owner_sql = """
                INSERT OR IGNORE INTO users (user_id, email, role) 
                VALUES ('owner-default-id', 'owner@sophia.ai', 'owner')
            """
        else:  # PostgreSQL
            default_owner_sql = """
                INSERT INTO users (user_id, email, role) 
                VALUES ('owner-default-id', 'owner@sophia.ai', 'owner')
                ON CONFLICT (email) DO NOTHING
            """
            
        migrator.execute_sql(conn, default_owner_sql)
        
        # Record migration
        migrator.execute_sql(
            conn,
            "INSERT OR IGNORE INTO schema_migrations (version) VALUES (?)" if migrator.config.db_type == 'sqlite' 
            else "INSERT INTO schema_migrations (version) VALUES (%s) ON CONFLICT (version) DO NOTHING",
            ('001_rbac_foundation',)
        )
        
        conn.commit()
        print("✅ RBAC foundation migration completed successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


def migrate_down(migrator: DatabaseMigrator):
    """Rollback RBAC tables"""
    conn = migrator.get_connection()
    
    try:
        # Drop tables in reverse order
        drop_statements = [
            "DROP TABLE IF EXISTS audit_log",
            "DROP TABLE IF EXISTS user_permissions", 
            "DROP TABLE IF EXISTS users"
        ]
        
        for drop_sql in drop_statements:
            migrator.execute_sql(conn, drop_sql)
            
        # Remove migration record
        migrator.execute_sql(
            conn,
            "DELETE FROM schema_migrations WHERE version = ?" if migrator.config.db_type == 'sqlite'
            else "DELETE FROM schema_migrations WHERE version = %s",
            ('001_rbac_foundation',)
        )
        
        conn.commit()
        print("✅ RBAC foundation rollback completed successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Rollback failed: {e}")
        raise
    finally:
        conn.close()


def get_config_from_env() -> MigrationConfig:
    """Load migration configuration from environment"""
    db_type = os.getenv('DB_TYPE', 'sqlite')
    
    if db_type == 'sqlite':
        return MigrationConfig(
            db_type='sqlite',
            db_path=os.getenv('DB_PATH', 'sophia.db')
        )
    elif db_type == 'postgresql':
        return MigrationConfig(
            db_type='postgresql',
            db_host=os.getenv('DB_HOST', 'localhost'),
            db_port=int(os.getenv('DB_PORT', '5432')),
            db_name=os.getenv('DB_NAME', 'sophia'),
            db_user=os.getenv('DB_USER', 'sophia'),
            db_password=os.getenv('DB_PASSWORD', '')
        )
    else:
        raise ValueError(f"Unsupported DB_TYPE: {db_type}")


if __name__ == "__main__":
    import sys
    
    config = get_config_from_env()
    migrator = DatabaseMigrator(config)
    
    command = sys.argv[1] if len(sys.argv) > 1 else 'up'
    
    if command == 'up':
        migrate_up(migrator)
    elif command == 'down':
        migrate_down(migrator)
    else:
        print("Usage: python 001_rbac_foundation.py [up|down]")
        sys.exit(1)