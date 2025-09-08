# NetSuite Integration Setup Guide

## Your NetSuite Sandbox Information

- **Account ID**: `7616750_SB1`
- **Application ID**: `82329689-C871-456F-8AA0-96DBDF5B0275`
- **Script ID**: `custinteg_0667f9a7dbc6`
- **Data Center**: US Phoenix 7
- **Username**: lynn@payready.com

## Setup Steps

### Step 1: Log into NetSuite Sandbox

1. Go to: `https://7616750-sb1.app.netsuite.com`
2. Login with your credentials

### Step 2: Enable REST Web Services

1. Navigate to: **Setup → Company → Enable Features**
2. Click the **SuiteCloud** tab
3. Check these options:
   - ✅ REST Web Services
   - ✅ OAuth 2.0
   - ✅ Token-Based Authentication (if you prefer TBA over OAuth 2.0)
4. Click **Save**

### Step 3: Create Integration Record

1. Navigate to: **Setup → Integrations → Manage Integrations**
2. Click **New**
3. Fill in:
   - **Name**: Sophia Integration
   - **State**: Enabled
   - **Application ID**: `82329689-C871-456F-8AA0-96DBDF5B0275`
   
4. Choose Authentication Method:

#### Option A: OAuth 2.0 (Recommended)
- Check: ✅ OAuth 2.0
- Check: ✅ REST Web Services
- **Redirect URI**: `https://localhost:8080/callback`
- **Scope**: Select "REST Web Services"

#### Option B: Token-Based Authentication (TBA)
- Check: ✅ Token-Based Authentication
- Check: ✅ REST Web Services

5. Click **Save**

### Step 4: Get Your Credentials

After saving, NetSuite will show you:

#### For OAuth 2.0:
- **Client ID**: (Copy this)
- **Client Secret**: (Copy this - shown only once!)
- **Certificate ID**: (If using certificate-based auth)

#### For TBA:
- **Consumer Key**: (Copy this)
- **Consumer Secret**: (Copy this - shown only once!)

### Step 5: Create Access Token (For TBA only)

If using Token-Based Authentication:

1. Navigate to: **Setup → Users/Roles → Access Tokens**
2. Click **New**
3. Select:
   - **Application Name**: Sophia Integration
   - **User**: lynn@payready.com
   - **Role**: Administrator (or appropriate role)
4. Click **Save**
5. Copy:
   - **Token ID**
   - **Token Secret** (shown only once!)

### Step 6: Configure Permissions

1. Navigate to: **Setup → Users/Roles → Manage Roles**
2. Create or edit a role with these permissions:
   - **Permissions → Setup → REST Web Services** (Full)
   - **Permissions → Setup → SuiteAnalytics Connect** (Full)
   - **Permissions → Lists → Customers** (View)
   - **Permissions → Transactions → Sales Order** (View)
   - Add other permissions as needed

### Step 7: Update Your .env File

Create or update your `.env` file with:

```bash
# NetSuite Configuration
NETSUITE_AUTH_METHOD=oauth2  # or token_based

# Account Configuration
NETSUITE_ACCOUNT_ID=7616750_SB1
NETSUITE_APPLICATION_ID=82329689-C871-456F-8AA0-96DBDF5B0275

# For OAuth 2.0
NETSUITE_CLIENT_ID=your_client_id_from_step_4
NETSUITE_CLIENT_SECRET=your_client_secret_from_step_4
NETSUITE_REDIRECT_URI=https://localhost:8080/callback
NETSUITE_SCOPE=rest_webservices

# For Token-Based Authentication
NETSUITE_CONSUMER_KEY=your_consumer_key_from_step_4
NETSUITE_CONSUMER_SECRET=your_consumer_secret_from_step_4
NETSUITE_TOKEN_ID=your_token_id_from_step_5
NETSUITE_TOKEN_SECRET=your_token_secret_from_step_5

# Features
NETSUITE_SUITEQL_ENABLED=true
NETSUITE_RESTLET_ENABLED=false
NETSUITE_WEBHOOK_ENABLED=false
```

### Step 8: Test the Connection

```bash
python app/integrations/test_netsuite.py
```

## API Endpoints

Your NetSuite REST API base URL:
```
https://7616750-sb1.suitetalk.api.netsuite.com/services/rest
```

## Common Issues & Solutions

### Issue: "Invalid Login Attempt"
- Ensure REST Web Services is enabled
- Check that your role has REST Web Services permission
- Verify credentials are copied correctly

### Issue: "Permission Violation"
- Check role permissions for the records you're trying to access
- Ensure the user has the correct role assigned

### Issue: "Invalid OAuth Token"
- OAuth 2.0 tokens expire after 1 hour
- The connector will auto-refresh, but check client credentials

## Next Steps

1. Complete the setup in NetSuite following the steps above
2. Copy the credentials to your .env file
3. Run the test script to verify connection
4. Start syncing data from NetSuite to Sophia

## Security Notes

- **NEVER** commit credentials to git
- Store production credentials in a secure secrets manager
- Use different credentials for sandbox vs production
- Rotate tokens regularly