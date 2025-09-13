"""
NetSuite OAuth 2.0 Callback Server
Simple server to handle OAuth 2.0 callbacks for testing
"""
import asyncio
import logging
import webbrowser
from aiohttp import web
logger = logging.getLogger(__name__)
# Global variable to store the authorization code
auth_code = None
auth_state = None
async def handle_callback(request):
    """Handle OAuth 2.0 callback from NetSuite"""
    global auth_code, auth_state
    # Extract code and state from query parameters
    auth_code = request.query.get("code")
    auth_state = request.query.get("state")
    error = request.query.get("error")
    if error:
        html = f"""
        <html>
        <body>
        <h1>OAuth Error</h1>
        <p>Error: {error}</p>
        <p>Description: {request.query.get('error_description', 'Unknown error')}</p>
        </body>
        </html>
        """
    elif auth_code:
        html = f"""
        <html>
        <body>
        <h1>Authorization Successful!</h1>
        <p>Authorization code received: {auth_code[:20]}...</p>
        <p>You can close this window and return to your terminal.</p>
        <script>
            setTimeout(function() {{
                window.close();
            }}, 3000);
        </script>
        </body>
        </html>
        """
        logger.info(f"Received authorization code: {auth_code}")
    else:
        html = """
        <html>
        <body>
        <h1>Invalid Request</h1>
        <p>No authorization code received.</p>
        </body>
        </html>
        """
    return web.Response(text=html, content_type="text/html")
async def start_oauth_flow(client_id, redirect_uri, account_id):
    """Start OAuth 2.0 authorization flow"""
    # Build authorization URL
    auth_url = (
        f"https://{account_id}.app.netsuite.com/app/login/oauth2/authorize.nl"
        f"?client_id={client_id}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&scope=rest_webservices"
        f"&state=your_state_value"
    )
    print("\n=== NetSuite OAuth 2.0 Authorization ===\n")
    print("Opening browser for authorization...")
    print(f"Authorization URL: {auth_url}\n")
    # Open browser
    webbrowser.open(auth_url)
    # Start callback server
    app = web.Application()
    app.router.add_get("/callback", handle_callback)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8080)
    print("Callback server running on http://localhost:8080")
    print("Waiting for authorization callback...")
    await site.start()
    # Wait for callback (timeout after 5 minutes)
    for _ in range(300):  # 5 minutes
        if auth_code:
            print("\n✅ Authorization code received!")
            print(f"Code: {auth_code}")
            await runner.cleanup()
            return auth_code
        await asyncio.sleep(1)
    print("\n❌ Timeout waiting for authorization")
    await runner.cleanup()
    return None
async def exchange_code_for_token(
    code, client_id, client_secret, redirect_uri, account_id
):
    """Exchange authorization code for access token"""
    import aiohttp
    token_url = f"https://{account_id}.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(token_url, data=data) as response:
            if response.status == 200:
                token_data = await response.json()
                print("\n✅ Access token obtained!")
                print(f"Access Token: {token_data.get('access_token', 'N/A')[:50]}...")
                print(f"Expires In: {token_data.get('expires_in', 'N/A')} seconds")
                print(
                    f"Refresh Token: {token_data.get('refresh_token', 'N/A')[:20]}..."
                    if token_data.get("refresh_token")
                    else "No refresh token"
                )
                return token_data
            else:
                error = await response.text()
                print(f"\n❌ Failed to get token: {error}")
                return None
async def main():
    """Run OAuth 2.0 flow"""
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    # Load environment
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_path)
    # Get configuration
    client_id = os.getenv("NETSUITE_CLIENT_ID")
    client_secret = os.getenv("NETSUITE_CLIENT_SECRET")
    account_id = os.getenv("NETSUITE_ACCOUNT_ID")
    redirect_uri = "http://localhost:8080/callback"
    if not all([client_id, client_secret, account_id]):
        print("❌ Missing NetSuite OAuth 2.0 credentials in .env")
        print(
            "Required: NETSUITE_CLIENT_ID, NETSUITE_CLIENT_SECRET, NETSUITE_ACCOUNT_ID"
        )
        return
    print("=== NetSuite OAuth 2.0 Setup ===")
    print(f"Account ID: {account_id}")
    print(f"Client ID: {client_id[:20]}...")
    print(f"Redirect URI: {redirect_uri}\n")
    # Start OAuth flow
    code = await start_oauth_flow(client_id, redirect_uri, account_id)
    if code:
        # Exchange code for token
        token_data = await exchange_code_for_token(
            code, client_id, client_secret, redirect_uri, account_id
        )
        if token_data:
            print("\n=== Next Steps ===")
            print("1. Save the access token to your .env file")
            print("2. Use the token for API calls")
            print("3. Implement token refresh before expiration")
    else:
        print("\n❌ OAuth flow failed")
if __name__ == "__main__":
    asyncio.run(main())
