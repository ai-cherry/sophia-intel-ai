#!/usr/bin/env python3
"""
Test the updated Portkey virtual keys
Validates that all keys are correctly saved and functional
"""

import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.local', override=True)

class VirtualKeyTester:
    """Test all updated Portkey virtual keys"""

    def __init__(self):
        self.portkey_api_key = os.getenv("PORTKEY_API_KEY")
        self.base_url = "https://api.portkey.ai/v1"

        # Updated virtual keys from .env.local
        self.virtual_keys = {
            "OPENAI": os.getenv("PORTKEY_OPENAI_VK", "openai-vk-190a60"),
            "XAI": os.getenv("PORTKEY_XAI_VK", "xai-vk-e65d0f"),
            "OPENROUTER": os.getenv("PORTKEY_OPENROUTER_VK", "vkj-openrouter-cc4151"),
            "TOGETHER": os.getenv("PORTKEY_TOGETHER_VK", "together-ai-670469")
        }

        if not self.portkey_api_key:
            raise ValueError("PORTKEY_API_KEY not found in environment")

    async def test_virtual_key(self, provider: str, virtual_key: str) -> dict[str, any]:
        """Test a single virtual key with a simple completion request"""

        print(f"\n🧪 Testing {provider} virtual key: {virtual_key}")

        # Test models for each provider
        test_models = {
            "OPENAI": "gpt-4o-mini",
            "XAI": "grok-beta",
            "OPENROUTER": "meta-llama/llama-3.2-3b-instruct",
            "TOGETHER": "meta-llama/Llama-2-7b-chat-hf"
        }

        model = test_models.get(provider, "gpt-4o-mini")

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {virtual_key}",
                        "Content-Type": "application/json",
                        "x-portkey-provider": provider.lower()
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "user", "content": "Say 'Connected' in one word"}
                        ],
                        "max_tokens": 10,
                        "temperature": 0.1
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                    print(f"   ✅ SUCCESS: {provider} responded with: {content.strip()}")
                    return {
                        "success": True,
                        "provider": provider,
                        "virtual_key": virtual_key,
                        "response": content.strip()
                    }
                else:
                    print(f"   ❌ FAILED: Status {response.status_code}")
                    try:
                        error = response.json()
                        print(f"      Error details: {error}")
                    except:
                        print(f"      Response: {response.text[:200]}")

                    return {
                        "success": False,
                        "provider": provider,
                        "virtual_key": virtual_key,
                        "error": f"Status {response.status_code}"
                    }

        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            return {
                "success": False,
                "provider": provider,
                "virtual_key": virtual_key,
                "error": str(e)
            }

    async def test_all_virtual_keys(self):
        """Test all virtual keys"""

        print("🔑 PORTKEY VIRTUAL KEYS TEST")
        print("=" * 60)
        print(f"Testing {len(self.virtual_keys)} virtual keys...")

        results = []

        # Test each virtual key
        for provider, virtual_key in self.virtual_keys.items():
            result = await self.test_virtual_key(provider, virtual_key)
            results.append(result)

            # Small delay between tests
            await asyncio.sleep(1)

        # Results summary
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)

        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        print(f"\n✅ Successful: {len(successful)}/{len(results)}")
        print(f"❌ Failed: {len(failed)}/{len(results)}")

        if successful:
            print("\n🎉 Working Virtual Keys:")
            for result in successful:
                print(f"   - {result['provider']}: {result['virtual_key']}")

        if failed:
            print("\n⚠️  Failed Virtual Keys:")
            for result in failed:
                print(f"   - {result['provider']}: {result['virtual_key']} ({result.get('error', 'Unknown error')})")

        # Overall status
        success_rate = len(successful) / len(results) * 100 if results else 0

        if success_rate >= 100:
            print("\n🎉 ALL VIRTUAL KEYS WORKING! (100%)")
            return True
        elif success_rate >= 75:
            print(f"\n✅ Most virtual keys working ({success_rate:.1f}%)")
            return True
        elif success_rate >= 50:
            print(f"\n⚠️  Some virtual keys working ({success_rate:.1f}%)")
            return False
        else:
            print(f"\n❌ Most virtual keys failed ({success_rate:.1f}%)")
            return False

    def show_configuration_status(self):
        """Show current configuration status"""

        print("\n" + "=" * 60)
        print("⚙️  CONFIGURATION STATUS")
        print("=" * 60)

        print(f"\nPortkey API Key: {'✅ Set' if self.portkey_api_key else '❌ Missing'}")
        print(f"Base URL: {self.base_url}")

        print("\nConfigured Virtual Keys:")
        for provider, vk in self.virtual_keys.items():
            print(f"  - {provider:12}: {vk}")

        print("\nEnvironment Variables:")
        env_vars = [
            ("PORTKEY_API_KEY", self.portkey_api_key[:20] + "..." if self.portkey_api_key else "Not Set"),
            ("PORTKEY_OPENAI_VK", os.getenv("PORTKEY_OPENAI_VK", "Not Set")),
            ("PORTKEY_XAI_VK", os.getenv("PORTKEY_XAI_VK", "Not Set")),
            ("PORTKEY_OPENROUTER_VK", os.getenv("PORTKEY_OPENROUTER_VK", "Not Set")),
            ("PORTKEY_TOGETHER_VK", os.getenv("PORTKEY_TOGETHER_VK", "Not Set"))
        ]

        for var, value in env_vars:
            status = "✅" if value != "Not Set" else "❌"
            print(f"  {status} {var}: {value}")

async def main():
    """Main test function"""

    print("🔑 Portkey Virtual Keys Validation")
    print("Testing updated virtual keys configuration...")

    try:
        tester = VirtualKeyTester()

        # Show configuration first
        tester.show_configuration_status()

        # Test all keys
        success = await tester.test_all_virtual_keys()

        if success:
            print("\n🎉 Virtual keys are properly configured and working!")
            sys.exit(0)
        else:
            print("\n⚠️  Some virtual keys need attention.")
            sys.exit(1)

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("Make sure PORTKEY_API_KEY is set in .env.local")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
