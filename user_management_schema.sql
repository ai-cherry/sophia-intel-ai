-- User Management Database Schema
-- Extends existing SQLite audit database with user management tables

-- Core Users table
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_login TEXT,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'active', 'suspended', 'deactivated'
    invite_token TEXT UNIQUE,
    invite_expires TEXT,
    password_hash TEXT, -- For local auth (development)
    metadata TEXT -- JSON for additional user data
);

-- Platform-level roles (owner, admin, member, viewer)
CREATE TABLE IF NOT EXISTS platform_roles (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL, -- 'owner', 'admin', 'member', 'viewer'
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    level INTEGER NOT NULL, -- Hierarchy: 1=owner, 2=admin, 3=member, 4=viewer
    permissions TEXT NOT NULL, -- JSON array of platform permissions
    created_at TEXT NOT NULL
);

-- Domain-level access (Artemis, Sophia)
CREATE TABLE IF NOT EXISTS domain_access (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    domain TEXT NOT NULL, -- 'artemis', 'sophia'
    access_level TEXT NOT NULL, -- 'full', 'read_only', 'restricted', 'none'
    granted_at TEXT NOT NULL,
    granted_by TEXT NOT NULL,
    expires_at TEXT, -- Optional expiration
    metadata TEXT, -- JSON for domain-specific settings
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, domain)
);

-- Service-level permissions (specific business services)
CREATE TABLE IF NOT EXISTS service_permissions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    service_name TEXT NOT NULL, -- 'crm', 'call_analysis', 'project_management', 'agent_factory'
    permission_type TEXT NOT NULL, -- 'read', 'write', 'admin', 'execute'
    resource_filter TEXT, -- JSON for filtered access (e.g., specific CRM accounts)
    granted_at TEXT NOT NULL,
    granted_by TEXT NOT NULL,
    expires_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Data-level access controls (proprietary/sensitive data)
CREATE TABLE IF NOT EXISTS data_access (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    data_category TEXT NOT NULL, -- 'financial', 'employee_data', 'customer_pii', 'api_keys'
    access_level TEXT NOT NULL, -- 'full', 'anonymized', 'aggregated_only', 'none'
    conditions TEXT, -- JSON for conditional access rules
    granted_at TEXT NOT NULL,
    granted_by TEXT NOT NULL,
    audit_required BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- User role assignments (links users to platform roles)
CREATE TABLE IF NOT EXISTS user_roles (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    assigned_at TEXT NOT NULL,
    assigned_by TEXT NOT NULL,
    expires_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES platform_roles(id) ON DELETE CASCADE,
    UNIQUE(user_id, role_id)
);

-- Invitation system
CREATE TABLE IF NOT EXISTS invitations (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    invited_by TEXT NOT NULL,
    role_id TEXT NOT NULL,
    domain_access TEXT, -- JSON: {"artemis": "full", "sophia": "read_only"}
    service_permissions TEXT, -- JSON array of initial service permissions
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    accepted_at TEXT,
    status TEXT DEFAULT 'pending', -- 'pending', 'accepted', 'expired', 'revoked'
    metadata TEXT, -- JSON for invite-specific data
    FOREIGN KEY (role_id) REFERENCES platform_roles(id)
);

-- Audit trail for user management actions
CREATE TABLE IF NOT EXISTS user_audit (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    action TEXT NOT NULL, -- 'invite_sent', 'user_created', 'permission_granted', 'access_denied'
    target_user_id TEXT,
    actor_user_id TEXT NOT NULL,
    resource_type TEXT, -- 'user', 'role', 'permission', 'invitation'
    resource_id TEXT,
    old_value TEXT, -- JSON of previous state
    new_value TEXT, -- JSON of new state
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY (target_user_id) REFERENCES users(id),
    FOREIGN KEY (actor_user_id) REFERENCES users(id)
);

-- Session management
CREATE TABLE IF NOT EXISTS user_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    last_accessed TEXT,
    ip_address TEXT,
    user_agent TEXT,
    active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Insert default platform roles
INSERT OR REPLACE INTO platform_roles (id, name, display_name, description, level, permissions, created_at) VALUES
('role_owner', 'owner', 'Platform Owner', 'Full system access and user management', 1,
 '["user_management", "platform_admin", "domain_admin", "service_admin", "data_admin", "audit_access"]',
 datetime('now')),
('role_admin', 'admin', 'Administrator', 'Platform administration and user management', 2,
 '["user_management", "domain_admin", "service_admin", "audit_access"]',
 datetime('now')),
('role_member', 'member', 'Member', 'Standard platform access', 3,
 '["domain_access", "service_access"]',
 datetime('now')),
('role_viewer', 'viewer', 'Viewer', 'Read-only platform access', 4,
 '["domain_read", "service_read"]',
 datetime('now'));

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_domain_access_user ON domain_access(user_id);
CREATE INDEX IF NOT EXISTS idx_service_permissions_user ON service_permissions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_audit_timestamp ON user_audit(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_invitations_email ON invitations(email);
CREATE INDEX IF NOT EXISTS idx_invitations_status ON invitations(status);
