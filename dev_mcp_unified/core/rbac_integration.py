"""
RBAC Integration Module
Minimal integration of user management with existing MCP server
"""
from __future__ import annotations

import os
from typing import Optional
from fastapi import FastAPI, HTTPException

def integrate_rbac_with_mcp_server(app: FastAPI) -> None:
    """
    Integrate RBAC system with existing MCP server
    This function is called from mcp_server.py to add user management
    """
    try:
        # Only import and integrate if RBAC is enabled
        rbac_enabled = os.getenv('RBAC_ENABLED', 'false').lower() == 'true'
        
        if not rbac_enabled:
            print("ℹ️  RBAC integration disabled (set RBAC_ENABLED=true to enable)")
            return
            
        # Import user management router
        from dev_mcp_unified.routers.user_management import router as user_management_router
        
        # Add user management routes with /api prefix to match existing patterns
        app.include_router(user_management_router, prefix="/api")
        
        print("✅ RBAC user management integrated successfully")
        
        # Initialize RBAC database if needed
        _initialize_rbac_database()
        
    except ImportError as e:
        print(f"⚠️  RBAC integration skipped due to missing dependencies: {e}")
    except Exception as e:
        print(f"❌ RBAC integration failed: {e}")
        # Don't crash the server, just log the error


def _initialize_rbac_database():
    """Initialize RBAC database using migration system"""
    try:
        import sys
        sys.path.append('migrations')
        from importlib import import_module
        rbac_migration = import_module('001_rbac_foundation')
        get_config_from_env = rbac_migration.get_config_from_env
        DatabaseMigrator = rbac_migration.DatabaseMigrator
        migrate_up = rbac_migration.migrate_up
        
        config = get_config_from_env()
        migrator = DatabaseMigrator(config)
        
        # Check if migration is needed
        conn = migrator.get_connection()
        try:
            if migrator.config.db_type == 'sqlite':
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
                )
                table_exists = cursor.fetchone() is not None
            else:  # PostgreSQL
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
                )
                table_exists = cursor.fetchone()[0]
                
            if not table_exists:
                print("🔄 Running RBAC database migration...")
                migrate_up(migrator)
            else:
                print("✅ RBAC database already initialized")
                
        finally:
            conn.close()
            
    except Exception as e:
        print(f"⚠️  RBAC database initialization failed: {e}")


def add_rbac_middleware(app: FastAPI) -> None:
    """
    Add RBAC middleware to existing endpoints
    This can be called to progressively add permissions to existing routes
    """
    rbac_enabled = os.getenv('RBAC_ENABLED', 'false').lower() == 'true'
    
    if not rbac_enabled:
        return
        
    try:
        from dev_mcp_unified.auth.rbac_manager import verify_token_with_permissions
        
        @app.middleware("http")
        async def rbac_middleware(request, call_next):
            """Optional RBAC middleware for existing endpoints"""
            
            # Skip middleware for public endpoints
            public_paths = ["/", "/healthz", "/models", "/api/admin/system/health"]
            if request.url.path in public_paths:
                return await call_next(request)
                
            # Skip middleware for new user management endpoints (they handle auth internally)
            if request.url.path.startswith("/api/admin"):
                return await call_next(request)
                
            # For now, just pass through - can add permission checks later
            response = await call_next(request)
            return response
            
        print("✅ RBAC middleware added (pass-through mode)")
        
    except Exception as e:
        print(f"⚠️  RBAC middleware setup failed: {e}")