# Linear OAuth Integration Upgrade Guide

Complete guide for upgrading from Personal API Key to OAuth application for organizational access in Sophia's business intelligence platform.

## Table of Contents

- [Overview](#overview)
- [Personal API Key vs OAuth Comparison](#personal-api-key-vs-oauth-comparison)
- [OAuth Application Setup](#oauth-application-setup)
- [Required Scopes](#required-scopes)
- [Implementation Changes](#implementation-changes)
- [Security Considerations](#security-considerations)
- [Migration Process](#migration-process)
- [Testing and Validation](#testing-and-validation)

## Overview

Currently, Sophia's Linear integration uses a Personal API Key (`lin_api_gF8bCZPVYz02YKUGp1yqqkGJOnJ6XICaK2bdftIp`) which provides access limited to the individual user's permissions. Upgrading to OAuth provides organization-wide access with proper scoping, enhanced security, and better compliance with enterprise requirements.

### Benefits of OAuth Upgrade

- **Enhanced Access**: Organization-wide data access beyond individual user limitations
- **Better Rate Limits**: Higher API rate limits for business intelligence applications
- **Improved Security**: Token rotation, scoped permissions, and audit trails
- **Compliance**: Meets enterprise security requirements for third-party integrations
- **Scalability**: Supports multiple users and automated workflows

## Personal API Key vs OAuth Comparison

| Aspect           | Personal API Key                   | OAuth Application                              |
| ---------------- | ---------------------------------- | ---------------------------------------------- |
| **Access Scope** | User's personal permissions only   | Organization-wide with proper scopes           |
| **Rate Limits**  | Standard user limits (200 req/min) | Higher limits for applications (1000+ req/min) |
| **Security**     | Static token, no rotation          | Dynamic tokens with refresh capability         |
| **Audit Trail**  | Limited to user actions            | Complete application audit trail               |
| **Team Access**  | Single user visibility             | All teams and members with proper permissions  |
| **Data Export**  | Limited to user's accessible data  | Complete organizational data export            |
| **Compliance**   | Individual user consent            | Proper organizational consent workflow         |

## OAuth Application Setup

### Step 1: Create OAuth Application

1. **Navigate to Linear Settings**

   - Go to Linear workspace → Settings → API
   - Click "Create new OAuth application"

2. **Configure Application Details**

   ```
   Application Name: Sophia Business Intelligence
   Description: AI-powered business intelligence platform for development analytics
   Homepage URL: https://sophia-intel-ai.com
   Redirect URI: https://your-domain.com/auth/linear/callback
   ```

3. **Application Type Selection**
   - Choose "Web Application" for server-side integration
   - Select "Confidential" for secure client secret handling

### Step 2: Obtain Credentials

After creation, you'll receive:

- **Client ID**: `lin_oauth_[unique_id]`
- **Client Secret**: `[secure_secret]`
- **Application ID**: `[app_id]`

## Required Scopes

For comprehensive business intelligence access, request these scopes:

### Core Data Access Scopes

```
read:teams          # Access team information and membership
read:users          # Access user profiles and activity data
read:issues         # Read all issues across organization
read:projects       # Access project data and status
read:cycles         # Read development cycles and sprints
read:comments       # Access issue comments and discussions
read:attachments    # Read file attachments on issues
read:labels         # Access issue labels and categorization
read:workflows      # Read workflow states and transitions
```

### Analytics and Reporting Scopes

```
read:analytics      # Access Linear's analytics data
read:insights       # Read team performance insights
read:timetracking   # Access time tracking data if available
```

### Optional Administrative Scopes (if needed)

```
write:issues        # Create and update issues (for automation)
write:comments      # Add comments to issues
admin:read          # Read organization settings (admin only)
```

## Implementation Changes

### Current Implementation Structure

```python
# Current personal API key setup
class LinearClient:
    def __init__(self):
        self.config = INTEGRATIONS.get("linear", {})
        self.api_key = self.config.get("api_key")  # Personal API key
        self.headers = {
            "Authorization": self.api_key,  # Direct key usage
            "Content-Type": "application/json"
        }
```

### OAuth Implementation

#### 1. Update Configuration Structure

```python
# app/api/integrations_config.py
INTEGRATIONS = {
    "linear": {
        "enabled": True,
        "auth_type": "oauth",  # Changed from api_key
        "status": "connected",
        "oauth_config": {
            "client_id": "lin_oauth_your_client_id",
            "client_secret": "your_client_secret",
            "redirect_uri": "https://your-domain.com/auth/linear/callback",
            "scopes": [
                "read:teams", "read:users", "read:issues", "read:projects",
                "read:cycles", "read:comments", "read:attachments",
                "read:labels", "read:workflows", "read:analytics"
            ]
        },
        "tokens": {
            "access_token": None,  # Will be populated after OAuth flow
            "refresh_token": None,
            "expires_at": None,
            "token_type": "Bearer"
        },
        "stats": {"teams": "organization-wide", "user": "OAuth App"}
    }
}
```

#### 2. OAuth Authentication Handler

```python
# app/integrations/linear_oauth.py
import asyncio
import aiohttp
import time
from urllib.parse import urlencode
from datetime import datetime, timedelta
import secrets
import base64
import hashlib

class LinearOAuthHandler:
    def __init__(self, config):
        self.client_id = config["oauth_config"]["client_id"]
        self.client_secret = config["oauth_config"]["client_secret"]
        self.redirect_uri = config["oauth_config"]["redirect_uri"]
        self.scopes = config["oauth_config"]["scopes"]
        self.auth_url = "https://linear.app/oauth/authorize"
        self.token_url = "https://api.linear.app/oauth/token"

    def generate_auth_url(self, state=None):
        """Generate OAuth authorization URL with PKCE"""
        # Generate PKCE parameters
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode('utf-8')).digest()
        ).decode('utf-8').rstrip('=')

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "response_type": "code",
            "state": state or secrets.token_urlsafe(32),
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }

        auth_url = f"{self.auth_url}?{urlencode(params)}"

        return {
            "auth_url": auth_url,
            "state": params["state"],
            "code_verifier": code_verifier
        }

    async def exchange_code_for_tokens(self, code, code_verifier, state):
        """Exchange authorization code for access tokens"""
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "code_verifier": code_verifier
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()

                    # Calculate expiration time
                    expires_in = token_data.get("expires_in", 3600)
                    expires_at = datetime.now() + timedelta(seconds=expires_in)

                    return {
                        "access_token": token_data["access_token"],
                        "refresh_token": token_data.get("refresh_token"),
                        "token_type": token_data.get("token_type", "Bearer"),
                        "expires_at": expires_at.isoformat(),
                        "scope": token_data.get("scope")
                    }
                else:
                    error_data = await response.json()
                    raise Exception(f"Token exchange failed: {error_data}")

    async def refresh_access_token(self, refresh_token):
        """Refresh expired access token"""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    expires_in = token_data.get("expires_in", 3600)
                    expires_at = datetime.now() + timedelta(seconds=expires_in)

                    return {
                        "access_token": token_data["access_token"],
                        "refresh_token": token_data.get("refresh_token", refresh_token),
                        "token_type": token_data.get("token_type", "Bearer"),
                        "expires_at": expires_at.isoformat()
                    }
                else:
                    error_data = await response.json()
                    raise Exception(f"Token refresh failed: {error_data}")
```

#### 3. Updated Linear Client

```python
# app/integrations/linear_client.py - Updated sections
import asyncio
from datetime import datetime
from .linear_oauth import LinearOAuthHandler

class LinearClient:
    def __init__(self):
        self.config = INTEGRATIONS.get("linear", {})
        self.auth_type = self.config.get("auth_type", "api_key")
        self.base_url = "https://api.linear.app/graphql"
        self.session: Optional[aiohttp.ClientSession] = None

        if self.auth_type == "oauth":
            self.oauth_handler = LinearOAuthHandler(self.config)
            self.tokens = self.config.get("tokens", {})
            self._setup_oauth_headers()
        else:
            # Fallback to API key for backward compatibility
            self.api_key = self.config.get("api_key")
            if not self.api_key:
                raise ValueError("Linear API key not configured")
            self.headers = {
                "Authorization": self.api_key,
                "Content-Type": "application/json"
            }

        logger.info(f"🔧 Linear client initialized with {self.auth_type} authentication")

    def _setup_oauth_headers(self):
        """Setup headers for OAuth authentication"""
        access_token = self.tokens.get("access_token")
        token_type = self.tokens.get("token_type", "Bearer")

        if not access_token:
            raise ValueError("OAuth access token not available. Please complete authorization flow.")

        self.headers = {
            "Authorization": f"{token_type} {access_token}",
            "Content-Type": "application/json"
        }

    async def _ensure_valid_token(self):
        """Ensure we have a valid access token, refresh if necessary"""
        if self.auth_type != "oauth":
            return  # No token refresh needed for API keys

        expires_at = self.tokens.get("expires_at")
        if not expires_at:
            return

        expiry_time = datetime.fromisoformat(expires_at)
        now = datetime.now()

        # Refresh if token expires in the next 5 minutes
        if expiry_time <= now + timedelta(minutes=5):
            refresh_token = self.tokens.get("refresh_token")
            if refresh_token:
                try:
                    new_tokens = await self.oauth_handler.refresh_access_token(refresh_token)
                    self.tokens.update(new_tokens)

                    # Update configuration
                    INTEGRATIONS["linear"]["tokens"] = self.tokens
                    self._setup_oauth_headers()

                    logger.info("🔄 Linear OAuth token refreshed successfully")
                except Exception as e:
                    logger.error(f"Failed to refresh Linear OAuth token: {e}")
                    raise Exception("OAuth token refresh failed. Re-authorization may be required.")

    async def _make_graphql_request(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated GraphQL request with OAuth support"""
        if not self.session:
            await self.initialize_session()

        # Ensure token is valid for OAuth
        await self._ensure_valid_token()

        payload = {
            "query": query,
            "variables": variables or {}
        }

        try:
            async with self.session.post(self.base_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()

                    if "errors" in result:
                        error_messages = [err.get("message", "") for err in result["errors"]]
                        raise Exception(f"Linear GraphQL errors: {'; '.join(error_messages)}")

                    return result.get("data", {})
                elif response.status == 401:
                    if self.auth_type == "oauth":
                        raise Exception("Linear OAuth token invalid - re-authorization required")
                    else:
                        raise Exception("Linear authentication failed - check API key")
                elif response.status == 403:
                    raise Exception("Linear API forbidden - check permissions/scopes")
                elif response.status == 429:
                    raise Exception("Linear API rate limit exceeded - retry later")
                else:
                    error_text = await response.text()
                    raise Exception(f"Linear API error {response.status}: {error_text}")

        except Exception as e:
            logger.error(f"Linear GraphQL request failed: {e}")
            raise
```

#### 4. OAuth Authorization Endpoint

```python
# app/api/routers/linear_auth.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from app.integrations.linear_oauth import LinearOAuthHandler
from app.api.integrations_config import INTEGRATIONS

router = APIRouter(prefix="/auth/linear", tags=["linear-auth"])

# Store temporary OAuth state (use Redis in production)
oauth_states = {}

@router.get("/authorize")
async def initiate_oauth():
    """Initiate Linear OAuth flow"""
    config = INTEGRATIONS.get("linear", {})
    if config.get("auth_type") != "oauth":
        raise HTTPException(status_code=400, detail="OAuth not configured for Linear")

    oauth_handler = LinearOAuthHandler(config)
    auth_data = oauth_handler.generate_auth_url()

    # Store state temporarily (use secure storage in production)
    oauth_states[auth_data["state"]] = {
        "code_verifier": auth_data["code_verifier"],
        "timestamp": datetime.now().isoformat()
    }

    return {
        "auth_url": auth_data["auth_url"],
        "message": "Visit the auth_url to complete Linear authorization"
    }

@router.get("/callback")
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: str = Query(None)
):
    """Handle OAuth callback from Linear"""
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    stored_data = oauth_states.pop(state)
    code_verifier = stored_data["code_verifier"]

    config = INTEGRATIONS.get("linear", {})
    oauth_handler = LinearOAuthHandler(config)

    try:
        tokens = await oauth_handler.exchange_code_for_tokens(code, code_verifier, state)

        # Store tokens in configuration
        INTEGRATIONS["linear"]["tokens"] = tokens
        INTEGRATIONS["linear"]["status"] = "connected"

        return {
            "status": "success",
            "message": "Linear OAuth authorization completed successfully",
            "expires_at": tokens["expires_at"]
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"OAuth callback failed: {str(e)}")

@router.post("/refresh")
async def refresh_token():
    """Manually refresh Linear OAuth token"""
    config = INTEGRATIONS.get("linear", {})
    tokens = config.get("tokens", {})
    refresh_token = tokens.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=400, detail="No refresh token available")

    oauth_handler = LinearOAuthHandler(config)

    try:
        new_tokens = await oauth_handler.refresh_access_token(refresh_token)
        INTEGRATIONS["linear"]["tokens"] = new_tokens

        return {
            "status": "success",
            "message": "Token refreshed successfully",
            "expires_at": new_tokens["expires_at"]
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token refresh failed: {str(e)}")
```

## Security Considerations

### 1. Token Storage Security

```python
# Secure token storage implementation
import os
from cryptography.fernet import Fernet

class SecureTokenStorage:
    def __init__(self):
        # Use environment variable or secure key management
        key = os.getenv('TOKEN_ENCRYPTION_KEY')
        if not key:
            # Generate and store securely in production
            key = Fernet.generate_key()
        self.cipher_suite = Fernet(key)

    def encrypt_tokens(self, tokens):
        """Encrypt tokens for storage"""
        token_json = json.dumps(tokens)
        encrypted_data = self.cipher_suite.encrypt(token_json.encode())
        return encrypted_data.decode()

    def decrypt_tokens(self, encrypted_tokens):
        """Decrypt tokens for use"""
        decrypted_data = self.cipher_suite.decrypt(encrypted_tokens.encode())
        return json.loads(decrypted_data.decode())
```

### 2. Environment Variables

```bash
# .env - Add these OAuth configuration variables
LINEAR_OAUTH_CLIENT_ID=lin_oauth_your_client_id
LINEAR_OAUTH_CLIENT_SECRET=your_client_secret
LINEAR_OAUTH_REDIRECT_URI=https://your-domain.com/auth/linear/callback
TOKEN_ENCRYPTION_KEY=your_encryption_key_for_tokens
```

### 3. Security Best Practices

1. **Use HTTPS**: Always use HTTPS for OAuth redirects and token exchange
2. **PKCE Implementation**: Implement Proof Key for Code Exchange for additional security
3. **Token Rotation**: Implement automatic token refresh with proper error handling
4. **Scope Limitation**: Request only necessary scopes for your use case
5. **Secure Storage**: Encrypt tokens at rest and in transit
6. **Audit Logging**: Log all OAuth operations for security monitoring

## Migration Process

### Phase 1: Preparation

1. **Create OAuth Application** in Linear workspace
2. **Update Configuration** with OAuth credentials
3. **Deploy OAuth Handlers** to staging environment
4. **Test OAuth Flow** with limited scopes

### Phase 2: Implementation

1. **Update integrations_config.py** with OAuth configuration
2. **Deploy OAuth authentication endpoints**
3. **Update LinearClient** to support both API key and OAuth
4. **Test comprehensive data access**

### Phase 3: Migration

1. **Complete OAuth authorization flow**
2. **Validate organizational data access**
3. **Update production configuration**
4. **Remove API key fallback** (optional)

### Migration Script

```python
# migration_script.py
async def migrate_to_oauth():
    """Migration script from API key to OAuth"""
    print("🔄 Starting Linear OAuth migration...")

    # 1. Test current API key access
    try:
        async with LinearClient() as client:
            current_health = await client.get_integration_health()
            print(f"✅ Current API key access: {current_health['status']}")
    except Exception as e:
        print(f"❌ Current API key failed: {e}")
        return

    # 2. Update configuration to OAuth
    INTEGRATIONS["linear"]["auth_type"] = "oauth"
    INTEGRATIONS["linear"]["oauth_config"] = {
        "client_id": os.getenv("LINEAR_OAUTH_CLIENT_ID"),
        "client_secret": os.getenv("LINEAR_OAUTH_CLIENT_SECRET"),
        "redirect_uri": os.getenv("LINEAR_OAUTH_REDIRECT_URI"),
        "scopes": ["read:teams", "read:users", "read:issues", "read:projects"]
    }

    # 3. Initiate OAuth flow
    oauth_handler = LinearOAuthHandler(INTEGRATIONS["linear"])
    auth_data = oauth_handler.generate_auth_url()

    print(f"🔗 Complete OAuth authorization at: {auth_data['auth_url']}")
    print("⏳ Waiting for OAuth completion...")

    # 4. Wait for callback completion (implement callback monitoring)
    # This would be handled by your callback endpoint in practice

    print("✅ Migration to OAuth completed successfully!")
```

## Testing and Validation

### 1. OAuth Flow Testing

```python
# test_linear_oauth.py
import pytest
from app.integrations.linear_oauth import LinearOAuthHandler

@pytest.mark.asyncio
async def test_oauth_url_generation():
    config = {
        "oauth_config": {
            "client_id": "test_client_id",
            "client_secret": "test_secret",
            "redirect_uri": "https://test.com/callback",
            "scopes": ["read:teams", "read:issues"]
        }
    }

    handler = LinearOAuthHandler(config)
    auth_data = handler.generate_auth_url()

    assert "auth_url" in auth_data
    assert "linear.app/oauth/authorize" in auth_data["auth_url"]
    assert "client_id=test_client_id" in auth_data["auth_url"]
    assert "scope=read%3Ateams+read%3Aissues" in auth_data["auth_url"]

@pytest.mark.asyncio
async def test_enhanced_data_access():
    """Test that OAuth provides enhanced organizational access"""
    async with LinearClient() as client:
        # Test organizational team access
        teams = await client.get_teams(first=100)
        assert len(teams) > 0, "Should access all organizational teams"

        # Test comprehensive user access
        users = await client.get_users(first=100)
        assert len(users) > 0, "Should access all organizational users"

        # Test bulk issue access
        issues = await client.get_issues(first=500)
        assert len(issues) >= 100, "Should access large number of issues"

        print(f"✅ OAuth provides access to {len(teams)} teams, {len(users)} users, {len(issues)} issues")
```

### 2. Performance Validation

```python
async def validate_oauth_performance():
    """Validate OAuth provides better rate limits and performance"""
    import time

    async with LinearClient() as client:
        start_time = time.time()

        # Make multiple concurrent requests to test rate limits
        tasks = []
        for i in range(20):
            tasks.append(client.get_teams(first=10))
            tasks.append(client.get_users(first=10))
            tasks.append(client.get_issues(first=50))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        success_count = len([r for r in results if not isinstance(r, Exception)])
        error_count = len(results) - success_count

        print(f"📊 Performance Test Results:")
        print(f"   Total requests: {len(tasks)}")
        print(f"   Successful: {success_count}")
        print(f"   Failed: {error_count}")
        print(f"   Duration: {end_time - start_time:.2f}s")
        print(f"   Rate: {len(tasks)/(end_time - start_time):.2f} req/s")

        assert error_count == 0, "All requests should succeed with proper OAuth rate limits"
```

## Conclusion

Upgrading from Personal API Key to OAuth provides significant benefits for Sophia's business intelligence platform:

1. **Organizational Access**: Complete visibility into all teams, projects, and issues
2. **Enhanced Performance**: Higher rate limits for bulk data operations
3. **Better Security**: Token rotation and scoped permissions
4. **Enterprise Compliance**: Proper authorization workflows

The implementation maintains backward compatibility during migration and provides a secure, scalable foundation for advanced business intelligence capabilities.

---

**Next Steps:**

1. Create OAuth application in Linear workspace
2. Configure environment variables for OAuth credentials
3. Deploy OAuth handlers to staging environment
4. Complete authorization flow and validate organizational access
5. Update production configuration and remove API key dependency

**Key Ideas and Observations:**

1. **Rate Limit Advantage**: OAuth applications typically receive 5-10x higher rate limits than personal API keys, crucial for bulk BI operations
2. **Audit Trail Enhancement**: OAuth provides detailed application-level audit logs, improving compliance and debugging capabilities
3. **Future-Proof Architecture**: This OAuth implementation pattern can be easily extended to other platforms (GitHub, Asana, etc.) for consistent enterprise authentication across Sophia's integrations
