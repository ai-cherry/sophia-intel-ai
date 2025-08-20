# Neon API Discovery Results

## API Configuration
- **Base URL**: `https://console.neon.tech/api/v2/`
- **Authentication**: Bearer Token (`Authorization: Bearer $NEON_API_TOKEN`)
- **API Token**: `napi_mr8himnznklsfgjpwb78w89q9eqfi0pb9ceg8y8y08a05v68vwrefcxg4gu82sg7`

## User Information
- **User ID**: `46f55f52-5aac-46b7-8c88-61c2349627c7`
- **Email**: `musillynn@gmail.com`
- **Name**: Lynn Musil
- **Login**: `musillynn`
- **Plan**: `free_v2`

## API Requirements
- Most endpoints require an `org_id` parameter
- Need to find organization ID from organization settings page
- Current API token appears to be organization-scoped

## Available Endpoints (from documentation)
- `/projects` - List projects (requires org_id)
- `/users/me` - Get current user info ✅ Working
- `/organizations` - List organizations (returned empty)
- `/projects/{project_id}/branches` - List branches
- `/projects/{project_id}/endpoints` - List compute endpoints

## Next Steps
1. Need to obtain org_id from Neon Console organization settings
2. Once org_id is available, can discover database endpoints
3. Can then configure connection strings for SOPHIA V4

## Connection String Format (typical)
```
postgresql://[user]:[password]@[endpoint]/[database]?sslmode=require
```

