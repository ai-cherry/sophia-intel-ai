#!/usr/bin/env python3
"""
Portkey Virtual Keys Setup Verification
Helps verify and configure Portkey virtual keys for the enhanced agent system
"""

import os
import sys
import json
import httpx
import asyncio
from typing import Dict, Any

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env.local')

class PortkeySetupVerifier:
    """Verify and guide Portkey virtual keys setup"""
    
    def __init__(self):
        self.api_key = os.getenv("PORTKEY_API_KEY")
        self.base_url = "https://api.portkey.ai/v1"
        
        # Virtual keys from environment
        self.virtual_keys = {
            "openai": os.getenv("PORTKEY_OPENAI_VK", "openai-vk-190a60"),
            "xai": os.getenv("PORTKEY_XAI_VK", "xai-vk-e65d0f"),
            "openrouter": os.getenv("PORTKEY_OPENROUTER_VK", "vkj-openrouter-cc4151"),
            "together": os.getenv("PORTKEY_TOGETHER_VK", "together-ai-670469")
        }
        
        # Provider API keys available
        self.provider_keys = {
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "xai": bool(os.getenv("XAI_API_KEY")),
            "openrouter": bool(os.getenv("OPENROUTER_API_KEY")),
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
            "groq": bool(os.getenv("GROQ_API_KEY"))
        }
        
    def print_header(self):
        """Print setup verification header"""
        print("=" * 70)
        print("🔧 PORTKEY VIRTUAL KEYS SETUP VERIFICATION")
        print("=" * 70)
        print()
        
    def check_api_key(self):
        """Check if Portkey API key is configured"""
        print("1️⃣ Checking Portkey API Key...")
        
        if not self.api_key:
            print("   ❌ PORTKEY_API_KEY not found in environment")
            print("   📝 Add to .env.local: PORTKEY_API_KEY=your_key_here")
            return False
            
        print(f"   ✅ API Key found: {self.api_key[:20]}...")
        return True
        
    def check_provider_keys(self):
        """Check which provider API keys are available"""
        print("\n2️⃣ Checking Provider API Keys...")
        
        for provider, available in self.provider_keys.items():
            status = "✅" if available else "❌"
            print(f"   {status} {provider.upper()}_API_KEY: {'Available' if available else 'Not found'}")
            
        available_count = sum(self.provider_keys.values())
        print(f"\n   📊 {available_count}/{len(self.provider_keys)} provider keys available")
        
        return available_count > 0
        
    def display_virtual_keys(self):
        """Display configured virtual keys"""
        print("\n3️⃣ Configured Virtual Keys...")
        
        for provider, vk_id in self.virtual_keys.items():
            print(f"   • {provider.upper()}: {vk_id}")
            
    async def test_virtual_key(self, provider: str, vk_id: str) -> Dict[str, Any]:
        """Test a virtual key with a simple request"""
        
        headers = {
            "x-portkey-api-key": self.api_key,
            "x-portkey-virtual-key": vk_id,
            "Content-Type": "application/json"
        }
        
        # Simple test payload
        data = {
            "model": self.get_test_model(provider),
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    return {"success": True, "status": "Active"}
                elif response.status_code == 401:
                    return {"success": False, "status": "Not Activated", "error": "Virtual key not activated in dashboard"}
                elif response.status_code == 400:
                    error_data = response.json()
                    return {"success": False, "status": "Config Error", "error": error_data.get("message", "Invalid configuration")}
                else:
                    return {"success": False, "status": f"Error {response.status_code}", "error": response.text}
                    
        except Exception as e:
            return {"success": False, "status": "Connection Error", "error": str(e)}
            
    def get_test_model(self, provider: str) -> str:
        """Get appropriate test model for provider"""
        models = {
            "openai": "gpt-3.5-turbo",
            "xai": "grok-beta",
            "openrouter": "openai/gpt-3.5-turbo",
            "together": "meta-llama/Llama-2-7b-chat-hf"
        }
        return models.get(provider, "gpt-3.5-turbo")
        
    async def test_all_virtual_keys(self):
        """Test all configured virtual keys"""
        print("\n4️⃣ Testing Virtual Keys...")
        print("   (This will make test API calls to verify activation)")
        print()
        
        results = {}
        for provider, vk_id in self.virtual_keys.items():
            print(f"   Testing {provider.upper()} ({vk_id})...")
            result = await self.test_virtual_key(provider, vk_id)
            results[provider] = result
            
            if result["success"]:
                print(f"   ✅ {provider.upper()}: {result['status']}")
            else:
                print(f"   ❌ {provider.upper()}: {result['status']}")
                if "error" in result:
                    print(f"      → {result['error']}")
                    
        return results
        
    def print_setup_instructions(self, test_results: Dict[str, Any]):
        """Print setup instructions based on test results"""
        print("\n" + "=" * 70)
        print("📋 SETUP INSTRUCTIONS")
        print("=" * 70)
        
        inactive_keys = [p for p, r in test_results.items() if not r["success"]]
        
        if not inactive_keys:
            print("\n🎉 All virtual keys are active and working!")
            print("The enhanced agent system is ready to use.")
            
        else:
            print("\n⚠️  Some virtual keys need activation:")
            print("\n1. Go to https://app.portkey.ai/virtual-keys")
            print("2. Sign in with your Portkey account")
            print("3. For each virtual key that needs activation:\n")
            
            for provider in inactive_keys:
                vk_id = self.virtual_keys[provider]
                print(f"   📍 {provider.upper()} Virtual Key: {vk_id}")
                print(f"      a) Click 'Create Virtual Key' or find existing key")
                print(f"      b) Set the Virtual Key ID to: {vk_id}")
                
                if provider == "openai" and self.provider_keys["openai"]:
                    print(f"      c) Add your OpenAI API key from .env.local")
                elif provider == "xai" and self.provider_keys["xai"]:
                    print(f"      c) Add your xAI API key from .env.local")
                elif provider == "openrouter" and self.provider_keys["openrouter"]:
                    print(f"      c) Add your OpenRouter API key from .env.local")
                    
                print(f"      d) Save and activate the virtual key")
                print()
                
            print("4. After activation, run this script again to verify")
            
        print("\n" + "=" * 70)
        print("💡 NEXT STEPS")
        print("=" * 70)
        
        if not inactive_keys:
            print("\n✅ Your enhanced agent system is ready!")
            print("\nTest it with:")
            print("   python3 test_agent_direct.py")
            print("   python3 test_enhanced_agent_system.py")
            
        else:
            print("\n1. Activate virtual keys in Portkey dashboard")
            print("2. Run this script again to verify: python3 verify_portkey_setup.py")
            print("3. Test the agent system: python3 test_agent_direct.py")
            
    async def run_verification(self):
        """Run complete verification process"""
        self.print_header()
        
        # Check API key
        if not self.check_api_key():
            print("\n❌ Please configure PORTKEY_API_KEY first")
            return
            
        # Check provider keys
        self.check_provider_keys()
        
        # Display virtual keys
        self.display_virtual_keys()
        
        # Test virtual keys
        print("\n" + "-" * 70)
        input("Press Enter to test virtual keys (this will make API calls)...")
        
        test_results = await self.test_all_virtual_keys()
        
        # Print instructions
        self.print_setup_instructions(test_results)
        
        # Summary
        active_count = sum(1 for r in test_results.values() if r["success"])
        total_count = len(test_results)
        
        print("\n" + "=" * 70)
        print(f"📊 SUMMARY: {active_count}/{total_count} virtual keys active")
        print("=" * 70)


async def main():
    """Main verification function"""
    verifier = PortkeySetupVerifier()
    await verifier.run_verification()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification cancelled by user")
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        sys.exit(1)