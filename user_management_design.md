# User Management System Architecture

## Overview

Hierarchical access control system for Sophia Intelligence AI platform with email invitations and granular permissions.

## User Hierarchy

### 1. Platform Level Access

- **Owner** (you): Full access to everything
- **Admin**: Full access to assigned domains
- **Manager**: Limited management within domains
- **Member**: Standard user access
- **Viewer**: Read-only access

### 2. Domain Level Access

- **Sophia Domain**: Business intelligence and operations
- **Artemis Domain**: Development and technical systems

### 3. Service Level Access

#### Sophia Services

- CRM Integration (HubSpot, Salesforce)
- Call Analysis (Gong)
- Project Management (Asana, Linear, Notion)
- Business Analytics & Reporting

#### Artemis Services

- Agent Factory
- Swarm Orchestration
- Code Management
- System Monitoring

### 4. Data Classification Levels

- **Public**: General business information
- **Internal**: Company operational data
- **Confidential**: Financial reports, contracts
- **Restricted**: Employee PII, sensitive financial data
- **Proprietary**: Trade secrets, strategic plans

## Technical Implementation

### Database Schema

```sql
-- User management tables
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    status ENUM('pending', 'active', 'suspended'),
    created_at TIMESTAMP,
    invited_by UUID REFERENCES users(id)
);

CREATE TABLE roles (
    id UUID PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    level ENUM('platform', 'domain', 'service', 'data')
);

CREATE TABLE permissions (
    id UUID PRIMARY KEY,
    resource VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    data_classification VARCHAR(50)
);

CREATE TABLE user_role_assignments (
    user_id UUID REFERENCES users(id),
    role_id UUID REFERENCES roles(id),
    scope VARCHAR(255), -- 'sophia', 'artemis', 'sophia.crm', etc.
    granted_by UUID REFERENCES users(id),
    expires_at TIMESTAMP
);
```

### API Endpoints

```
POST /api/admin/users/invite
GET  /api/admin/users
PUT  /api/admin/users/{id}/permissions
DELETE /api/admin/users/{id}
POST /api/admin/roles
GET  /api/auth/permissions/check
```

### UI Components

- User Management Tab in unified dashboard
- Email invitation workflow
- Permission matrix interface
- Role assignment wizard
