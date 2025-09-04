"""
RBAC Integration Tests
Validates user management functionality across existing MCP server endpoints
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
import pytest
import asyncio
from typing import Dict, Any
from fastapi.testclient import TestClient
from unittest.mock import patch

# Set up test environment before imports
os.environ['RBAC_ENABLED'] = 'true'
os.environ['DB_TYPE'] = 'sqlite'
os.environ['DB_PATH'] = ':memory:'  # Use in-memory database for testing

from dev_mcp_unified.core.mcp_server import app
from dev_mcp_unified.auth.rbac_manager import rbac_manager, UserRole, Permission
from migrations.001_rbac_foundation import get_config_from_env, DatabaseMigrator, migrate_up


class TestRBACIntegration:
    """Test suite for RBAC integration with MCP server"""
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        """Set up test database for each test"""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Update environment for this test
        os.environ['DB_PATH'] = self.temp_db.name
        
        # Run migration
        config = get_config_from_env()
        migrator = DatabaseMigrator(config)
        migrate_up(migrator)
        
        # Recreate RBAC manager with test database
        global rbac_manager
        rbac_manager.__init__(self.temp_db.name)
        
        # Create test client
        self.client = TestClient(app)
        
        yield
        
        # Cleanup
        os.unlink(self.temp_db.name)
    
    def create_test_user(self, email: str, role: UserRole) -> str:
        """Helper to create test user"""
        return rbac_manager.create_user(email, role)
    
    def get_auth_headers(self, user_email: str) -> Dict[str, str]:
        """Helper to get authentication headers for user"""
        # Mock JWT token creation (in real implementation, use proper JWT)
        import jwt
        from dev_mcp_unified.core.mcp_server import SECRET_KEY
        
        token = jwt.encode(
            {"user": user_email, "exp": 9999999999},  # Far future expiry
            SECRET_KEY,
            algorithm="HS256"
        )
        
        return {"Authorization": f"Bearer {token}"}
    
    def test_server_starts_with_rbac_disabled(self):
        """Test that server starts normally when RBAC is disabled"""
        with patch.dict(os.environ, {'RBAC_ENABLED': 'false'}):
            response = self.client.get("/")
            assert response.status_code == 200
    
    def test_server_starts_with_rbac_enabled(self):
        """Test that server starts with RBAC integration enabled"""
        response = self.client.get("/")
        assert response.status_code == 200
    
    def test_rbac_endpoints_available(self):
        """Test that RBAC endpoints are available when enabled"""
        # Create owner user for authentication
        owner_id = self.create_test_user("owner@test.com", UserRole.OWNER)
        headers = self.get_auth_headers("owner@test.com")
        
        # Test user management endpoints
        response = self.client.get("/api/admin/users", headers=headers)
        assert response.status_code == 200
        
        response = self.client.get("/api/admin/me", headers=headers)
        assert response.status_code == 200
    
    def test_permission_enforcement(self):
        """Test that permissions are properly enforced"""
        # Create users with different roles
        owner_id = self.create_test_user("owner@test.com", UserRole.OWNER)
        viewer_id = self.create_test_user("viewer@test.com", UserRole.VIEWER)
        
        owner_headers = self.get_auth_headers("owner@test.com")
        viewer_headers = self.get_auth_headers("viewer@test.com")
        
        # Owner can access user management
        response = self.client.get("/api/admin/users", headers=owner_headers)
        assert response.status_code == 200
        
        # Viewer cannot access user management
        response = self.client.get("/api/admin/users", headers=viewer_headers)
        assert response.status_code == 403
    
    def test_user_crud_operations(self):
        """Test complete user CRUD operations"""
        # Create owner user
        owner_id = self.create_test_user("owner@test.com", UserRole.OWNER)
        headers = self.get_auth_headers("owner@test.com")
        
        # Create user via API
        create_data = {
            "email": "newuser@test.com",
            "role": "member"
        }
        response = self.client.post("/api/admin/users", json=create_data, headers=headers)
        assert response.status_code == 200
        new_user = response.json()
        assert new_user["email"] == "newuser@test.com"
        assert new_user["role"] == "member"
        
        # Read user
        response = self.client.get(f"/api/admin/users/{new_user['user_id']}", headers=headers)
        assert response.status_code == 200
        
        # Update user
        update_data = {"role": "admin"}
        response = self.client.put(
            f"/api/admin/users/{new_user['user_id']}", 
            json=update_data, 
            headers=headers
        )
        assert response.status_code == 200
        updated_user = response.json()
        assert updated_user["role"] == "admin"
        
        # List users
        response = self.client.get("/api/admin/users", headers=headers)
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 2  # owner + new user
    
    def test_permission_checking(self):
        """Test permission checking endpoints"""
        member_id = self.create_test_user("member@test.com", UserRole.MEMBER)
        headers = self.get_auth_headers("member@test.com")
        
        # Check valid permission
        response = self.client.get(
            "/api/admin/permissions/check?permission=sophia.read",
            headers=headers
        )
        assert response.status_code == 200
        assert response.json()["has_permission"] is True
        
        # Check invalid permission
        response = self.client.get(
            "/api/admin/permissions/check?permission=user.manage",
            headers=headers
        )
        assert response.status_code == 200
        assert response.json()["has_permission"] is False
        
        # List user permissions
        response = self.client.get("/api/admin/permissions/list", headers=headers)
        assert response.status_code == 200
        perms = response.json()
        assert "sophia.read" in perms["permissions"]
        assert "user.manage" not in perms["permissions"]
    
    def test_authentication_required(self):
        """Test that authentication is required for protected endpoints"""
        # Try accessing protected endpoint without auth
        response = self.client.get("/api/admin/users")
        assert response.status_code == 401
        
        # Try with invalid token
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        response = self.client.get("/api/admin/users", headers=invalid_headers)
        assert response.status_code == 401
    
    def test_database_migration_integration(self):
        """Test that database migration works correctly"""
        # Check that required tables exist
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            
            # Check users table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            assert cursor.fetchone() is not None
            
            # Check user_permissions table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_permissions'")
            assert cursor.fetchone() is not None
            
            # Check audit_log table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log'")
            assert cursor.fetchone() is not None
            
            # Check default owner user exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'owner'")
            count = cursor.fetchone()[0]
            assert count >= 1
    
    def test_existing_endpoints_unaffected(self):
        """Test that existing MCP server endpoints continue to work"""
        # Test public endpoints still work
        response = self.client.get("/")
        assert response.status_code == 200
        
        response = self.client.get("/healthz")
        assert response.status_code == 200
        
        response = self.client.get("/models")
        assert response.status_code == 200
        
        # Test that existing authenticated endpoints accept the new auth format
        # (This would need to be expanded based on which endpoints require auth)
    
    def test_role_hierarchy(self):
        """Test that role hierarchy works correctly"""
        # Create users with different roles
        owner_id = self.create_test_user("owner@test.com", UserRole.OWNER)
        admin_id = self.create_test_user("admin@test.com", UserRole.ADMIN)
        member_id = self.create_test_user("member@test.com", UserRole.MEMBER)
        viewer_id = self.create_test_user("viewer@test.com", UserRole.VIEWER)
        
        # Test permission inheritance
        owner = rbac_manager.get_user(owner_id)
        admin = rbac_manager.get_user(admin_id)
        member = rbac_manager.get_user(member_id)
        viewer = rbac_manager.get_user(viewer_id)
        
        # Owner has all permissions
        assert Permission.USER_MANAGE.value in owner.permissions
        assert Permission.SOPHIA_READ.value in owner.permissions
        assert Permission.BI_WRITE.value in owner.permissions
        
        # Admin has most permissions but not system config
        assert Permission.USER_INVITE.value in admin.permissions
        assert Permission.SOPHIA_WRITE.value in admin.permissions
        assert Permission.USER_MANAGE.value not in admin.permissions
        
        # Member has read permissions and some execute
        assert Permission.SOPHIA_READ.value in member.permissions
        assert Permission.AGENT_EXECUTE.value in member.permissions
        assert Permission.SOPHIA_WRITE.value not in member.permissions
        
        # Viewer only has read permissions
        assert Permission.SOPHIA_READ.value in viewer.permissions
        assert Permission.BI_READ.value in viewer.permissions
        assert Permission.AGENT_EXECUTE.value not in viewer.permissions
    
    def test_error_handling(self):
        """Test proper error handling in RBAC system"""
        owner_id = self.create_test_user("owner@test.com", UserRole.OWNER)
        headers = self.get_auth_headers("owner@test.com")
        
        # Test duplicate user creation
        create_data = {
            "email": "duplicate@test.com",
            "role": "member"
        }
        response1 = self.client.post("/api/admin/users", json=create_data, headers=headers)
        assert response1.status_code == 200
        
        response2 = self.client.post("/api/admin/users", json=create_data, headers=headers)
        assert response2.status_code == 409  # Conflict
        
        # Test invalid user ID
        response = self.client.get("/api/admin/users/invalid-id", headers=headers)
        assert response.status_code == 404
        
        # Test invalid permission
        response = self.client.get(
            "/api/admin/permissions/check?permission=invalid.permission",
            headers=headers
        )
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])