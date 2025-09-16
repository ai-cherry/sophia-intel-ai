"""
Slack Token Validation Script for CI/E2E Tests

This script validates Slack tokens and scopes before running E2E tests.
Run this before E2E test suites to ensure proper configuration.
"""
import os
import sys
import asyncio
from typing import Dict, List, Optional
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError


class SlackTokenValidator:
    """Validates Slack tokens and required scopes"""
    
    REQUIRED_BOT_SCOPES = [
        "chat:write",           # Send messages
        "channels:read",        # List public channels
        "groups:read",          # List private channels  
        "im:read",              # List DMs
        "users:read",           # List workspace users
        "app_mentions:read",    # Receive mentions
        "commands",             # Handle slash commands
        "chat:write.public",    # Write to public channels bot isn't in
    ]
    
    OPTIONAL_BOT_SCOPES = [
        "chat:write.customize", # Custom username/icon
        "files:read",           # Read file info
        "reactions:read",       # Read reactions
        "channels:history",     # Read channel history
        "groups:history",       # Read private channel history
        "im:history",           # Read DM history
    ]
    
    REQUIRED_USER_SCOPES = [
        "search:read",          # Search messages (user token only)
    ]
    
    def __init__(self):
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.user_token = os.getenv("SLACK_USER_TOKEN")
        self.signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        self.app_token = os.getenv("SLACK_APP_TOKEN")
        self.test_channel = os.getenv("SLACK_TEST_CHANNEL", "#ci-slack-tests")
        
        self.issues = []
        self.warnings = []
    
    async def validate_all(self) -> Dict[str, any]:
        """Validate all tokens and return comprehensive report"""
        print("🔍 Validating Slack tokens and configuration...")
        
        # Check token presence
        self._check_token_presence()
        
        # Validate bot token
        if self.bot_token:
            await self._validate_bot_token()
        
        # Validate user token (optional)
        if self.user_token:
            await self._validate_user_token()
        
        # Validate app token for Socket Mode (optional)
        if self.app_token:
            await self._validate_app_token()
        
        # Check test channel accessibility
        if self.bot_token and self.test_channel:
            await self._check_test_channel()
        
        return self._generate_report()
    
    def _check_token_presence(self):
        """Check which tokens are configured"""
        if not self.bot_token:
            self.issues.append("❌ SLACK_BOT_TOKEN not configured")
        else:
            print(f"✅ Bot token configured ({self.bot_token[:12]}...)")
        
        if not self.signing_secret:
            self.issues.append("❌ SLACK_SIGNING_SECRET not configured")
        else:
            print(f"✅ Signing secret configured ({self.signing_secret[:8]}...)")
        
        if not self.user_token:
            self.warnings.append("⚠️  SLACK_USER_TOKEN not configured (search functionality limited)")
        else:
            print(f"✅ User token configured ({self.user_token[:12]}...)")
        
        if not self.app_token:
            self.warnings.append("⚠️  SLACK_APP_TOKEN not configured (Socket Mode unavailable)")
        else:
            print(f"✅ App token configured ({self.app_token[:12]}...)")
    
    async def _validate_bot_token(self):
        """Validate bot token and scopes"""
        print("\n🤖 Validating bot token...")
        
        try:
            client = AsyncWebClient(token=self.bot_token)
            
            # Test basic API call
            auth_response = await client.auth_test()
            if not auth_response["ok"]:
                self.issues.append(f"❌ Bot token invalid: {auth_response.get('error')}")
                return
            
            print(f"✅ Bot token valid - User: {auth_response['user']}, Team: {auth_response['team']}")
            
            # Check scopes
            await self._check_bot_scopes(client)
            
            # Test basic functionality
            await self._test_bot_functionality(client)
            
        except SlackApiError as e:
            self.issues.append(f"❌ Bot token error: {e.response['error']}")
        except Exception as e:
            self.issues.append(f"❌ Bot token validation failed: {str(e)}")
    
    async def _check_bot_scopes(self, client: AsyncWebClient):
        """Check bot token scopes"""
        try:
            # Get bot info to check scopes
            auth_response = await client.auth_test()
            bot_id = auth_response.get("bot_id")
            
            if bot_id:
                # Try to get bot info (requires users:read scope)
                try:
                    await client.users_info(user=bot_id)
                    print("✅ users:read scope verified")
                except SlackApiError as e:
                    if e.response["error"] == "missing_scope":
                        self.issues.append("❌ Missing required scope: users:read")
            
            # Test channels:read
            try:
                await client.conversations_list(types="public_channel", limit=1)
                print("✅ channels:read scope verified")
            except SlackApiError as e:
                if e.response["error"] == "missing_scope":
                    self.issues.append("❌ Missing required scope: channels:read")
            
            # Test chat:write by checking if we can prepare to send (don't actually send)
            # This is tricky to test without actually sending, so we'll note it as a requirement
            print("ℹ️  chat:write scope required for message sending (will be tested in E2E)")
            
        except Exception as e:
            self.warnings.append(f"⚠️  Could not fully validate bot scopes: {str(e)}")
    
    async def _test_bot_functionality(self, client: AsyncWebClient):
        """Test basic bot functionality"""
        try:
            # Test getting user list
            users_response = await client.users_list(limit=10)
            if users_response["ok"]:
                user_count = len(users_response["members"])
                print(f"✅ Retrieved {user_count} users")
            
            # Test getting conversations
            convs_response = await client.conversations_list(types="public_channel", limit=10)
            if convs_response["ok"]:
                channel_count = len(convs_response["channels"])
                print(f"✅ Retrieved {channel_count} channels")
                
        except SlackApiError as e:
            self.warnings.append(f"⚠️  Bot functionality test failed: {e.response['error']}")
    
    async def _validate_user_token(self):
        """Validate user token (if provided)"""
        print("\n👤 Validating user token...")
        
        try:
            client = AsyncWebClient(token=self.user_token)
            
            auth_response = await client.auth_test()
            if not auth_response["ok"]:
                self.issues.append(f"❌ User token invalid: {auth_response.get('error')}")
                return
            
            print(f"✅ User token valid - User: {auth_response['user']}")
            
            # Test search functionality (main use case for user token)
            try:
                search_response = await client.search_messages(query="test", count=1)
                if search_response["ok"]:
                    print("✅ Message search functionality verified")
                else:
                    self.warnings.append("⚠️  Message search not working")
            except SlackApiError as e:
                if e.response["error"] == "missing_scope":
                    self.issues.append("❌ User token missing search:read scope")
                else:
                    self.warnings.append(f"⚠️  Search test failed: {e.response['error']}")
                    
        except Exception as e:
            self.issues.append(f"❌ User token validation failed: {str(e)}")
    
    async def _validate_app_token(self):
        """Validate app token for Socket Mode"""
        print("\n🔌 Validating app token...")
        
        if not self.app_token.startswith("xapp-"):
            self.issues.append("❌ App token should start with 'xapp-'")
            return
        
        # Socket Mode validation would require actually connecting
        # For now, just verify the token format
        print("✅ App token format valid")
        print("ℹ️  Socket Mode connection will be tested in E2E tests")
    
    async def _check_test_channel(self):
        """Check if test channel is accessible"""
        print(f"\n📺 Checking test channel: {self.test_channel}")
        
        try:
            client = AsyncWebClient(token=self.bot_token)
            
            # Get all conversations
            convs_response = await client.conversations_list(
                types="public_channel,private_channel"
            )
            
            if not convs_response["ok"]:
                self.warnings.append("⚠️  Could not list channels to verify test channel")
                return
            
            # Look for test channel
            channel_name = self.test_channel.lstrip("#")
            test_channel = None
            
            for channel in convs_response["channels"]:
                if channel["name"] == channel_name:
                    test_channel = channel
                    break
            
            if test_channel:
                print(f"✅ Test channel found: {test_channel['name']} ({test_channel['id']})")
                
                # Check if bot is member
                if test_channel.get("is_member", False):
                    print("✅ Bot is member of test channel")
                else:
                    self.warnings.append(f"⚠️  Bot not a member of {self.test_channel} - may not be able to post")
            else:
                self.warnings.append(f"⚠️  Test channel {self.test_channel} not found")
                
        except Exception as e:
            self.warnings.append(f"⚠️  Could not check test channel: {str(e)}")
    
    def _generate_report(self) -> Dict[str, any]:
        """Generate validation report"""
        success = len(self.issues) == 0
        
        print(f"\n{'='*60}")
        print("📋 SLACK TOKEN VALIDATION REPORT")
        print(f"{'='*60}")
        
        if success:
            print("🎉 All validations passed!")
        else:
            print(f"❌ {len(self.issues)} issue(s) found:")
            for issue in self.issues:
                print(f"   {issue}")
        
        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                print(f"   {warning}")
        
        print(f"\n{'='*60}")
        
        report = {
            "success": success,
            "issues": self.issues,
            "warnings": self.warnings,
            "tokens": {
                "bot_token": bool(self.bot_token),
                "user_token": bool(self.user_token),
                "app_token": bool(self.app_token),
                "signing_secret": bool(self.signing_secret)
            },
            "test_channel": self.test_channel
        }
        
        return report


async def main():
    """Main validation function"""
    validator = SlackTokenValidator()
    report = await validator.validate_all()
    
    if not report["success"]:
        print("\n💡 To fix issues:")
        print("   1. Set required environment variables:")
        print("      - SLACK_BOT_TOKEN (required)")
        print("      - SLACK_SIGNING_SECRET (required)")
        print("      - SLACK_USER_TOKEN (optional, for search)")
        print("      - SLACK_APP_TOKEN (optional, for Socket Mode)")
        print("   2. Ensure bot has required scopes in Slack app settings")
        print("   3. Invite bot to test channel if specified")
        print("   4. Re-run this script to verify fixes")
        
        sys.exit(1)
    
    print("\n✅ Ready for Slack E2E tests!")
    return report


if __name__ == "__main__":
    asyncio.run(main())
