"""
Database Migration Base Classes
Shared utilities for database-agnostic migrations
"""
from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from typing import Any

try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


@dataclass
class MigrationConfig:
    """Database migration configuration"""

    db_type: str  # 'sqlite' or 'postgresql'
    db_path: str | None = None  # For SQLite
    db_host: str | None = None  # For PostgreSQL
    db_port: int | None = None
    db_name: str | None = None
    db_user: str | None = None
    db_password: str | None = None


class DatabaseMigrator:
    """Database-agnostic migration runner"""

    def __init__(self, config: MigrationConfig):
        self.config = config

    def get_connection(self):
        """Get database connection based on configuration"""
        if self.config.db_type == "sqlite":
            return sqlite3.connect(self.config.db_path or "sophia.db")
        elif self.config.db_type == "postgresql":
            if not POSTGRES_AVAILABLE:
                raise ImportError("psycopg2 is required for PostgreSQL support. Install with: pip install psycopg2-binary")
            return psycopg2.connect(
                host=self.config.db_host,
                port=self.config.db_port or 5432,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password,
            )
        else:
            raise ValueError(f"Unsupported database type: {self.config.db_type}")

    def execute_sql(self, conn: Any, sql: str, params: tuple = ()):
        """Execute SQL with database-specific handling"""
        cursor = conn.cursor()
        cursor.execute(sql, params)

        if self.config.db_type == "postgresql":
            conn.commit()

    def table_exists(self, conn: Any, table_name: str) -> bool:
        """Check if table exists"""
        if self.config.db_type == "sqlite":
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
            )
            return cursor.fetchone() is not None
        elif self.config.db_type == "postgresql":
            cursor = conn.cursor()
            cursor.execute(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)",
                (table_name,),
            )
            return cursor.fetchone()[0]

    def get_primary_key_type(self) -> str:
        """Get appropriate primary key type for database"""
        if self.config.db_type == "sqlite":
            return "TEXT PRIMARY KEY"
        elif self.config.db_type == "postgresql":
            return "UUID PRIMARY KEY DEFAULT gen_random_uuid()"

    def get_timestamp_type(self) -> str:
        """Get appropriate timestamp type for database"""
        if self.config.db_type == "sqlite":
            return "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        elif self.config.db_type == "postgresql":
            return "TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"

    def get_boolean_type(self) -> str:
        """Get appropriate boolean type for database"""
        if self.config.db_type == "sqlite":
            return "INTEGER DEFAULT 1"  # SQLite uses 0/1 for boolean
        elif self.config.db_type == "postgresql":
            return "BOOLEAN DEFAULT TRUE"


def get_config_from_env() -> MigrationConfig:
    """Load migration configuration from environment"""
    db_type = os.getenv("DB_TYPE", "sqlite")

    if db_type == "sqlite":
        return MigrationConfig(db_type="sqlite", db_path=os.getenv("DB_PATH", "sophia.db"))
    elif db_type == "postgresql":
        return MigrationConfig(
            db_type="postgresql",
            db_host=os.getenv("DB_HOST", "localhost"),
            db_port=int(os.getenv("DB_PORT", "5432")),
            db_name=os.getenv("DB_NAME", "sophia"),
            db_user=os.getenv("DB_USER", "sophia"),
            db_password=os.getenv("DB_PASSWORD", ""),
        )
    else:
        raise ValueError(f"Unsupported DB_TYPE: {db_type}")