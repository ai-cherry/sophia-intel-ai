#!/usr/bin/env python3
"""
Automatically create all Portkey virtual keys programmatically.
This will set up all 7 virtual keys with OpenRouter as the provider.
"""

import asyncio
import os
from typing import Any

import httpx
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.local', override=True)

class PortkeyVirtualKeyCreator:
    """Create virtual keys in Portkey programmatically."""

    def __init__(self):
        self.portkey_api_key = os.getenv("PORTKEY_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

        if not self.portkey_api_key:
            raise ValueError("PORTKEY_API_KEY not found in .env.local")
        if not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY not found in .env.local")

        self.base_url = "https://api.portkey.ai/v1"
        self.created_keys = {}

    async def create_virtual_key(self, name: str, description: str, default_model: str = None) -> dict[str, Any]:
        """Create a single virtual key in Portkey."""

        print(f"\n📝 Creating virtual key: {name}")

        # Virtual key configuration
        config = {
            "name": name,
            "provider": "openrouter",
            "api_key": self.openrouter_api_key,
            "description": description,
            "config": {
                "base_url": "https://openrouter.ai/api/v1",
                "headers": {
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Sophia Intel AI"
                }
            }
        }

        if default_model:
            config["default_model"] = default_model

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try to create virtual key using Portkey Admin API
                response = await client.post(
                    f"{self.base_url}/admin/virtual-keys",
                    headers={
                        "x-portkey-api-key": self.portkey_api_key,
                        "Content-Type": "application/json"
                    },
                    json=config
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    vk_id = result.get("id") or result.get("virtual_key_id")
                    print(f"   ✅ Created: {vk_id}")
                    self.created_keys[name] = vk_id
                    return {"success": True, "id": vk_id}
                else:
                    print(f"   ❌ Failed: Status {response.status_code}")
                    try:
                        error = response.json()
                        print(f"      Error: {error}")
                    except:
                        print(f"      Response: {response.text[:200]}")
                    return {"success": False, "error": f"Status {response.status_code}"}

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def create_all_virtual_keys(self):
        """Create all 7 virtual keys."""

        print("\n" + "="*60)
        print("🚀 CREATING PORTKEY VIRTUAL KEYS")
        print("="*60)

        # Define all virtual keys to create
        virtual_keys = [
            {
                "name": "openrouter-main",
                "description": "Main OpenRouter access for general purpose",
                "default_model": "openrouter/auto"
            },
            {
                "name": "gpt-models",
                "description": "GPT-4 and GPT-3.5 models via OpenRouter",
                "default_model": "openai/gpt-4o"
            },
            {
                "name": "claude-models",
                "description": "Claude models (Sonnet, Opus, Haiku) via OpenRouter",
                "default_model": "anthropic/claude-3.5-sonnet"
            },
            {
                "name": "qwen-coder",
                "description": "Qwen 2.5 Coder for primary code generation",
                "default_model": "qwen/qwen-2.5-coder-32b-instruct"
            },
            {
                "name": "deepseek-coder",
                "description": "DeepSeek Coder v2 for alternative code generation",
                "default_model": "deepseek/deepseek-coder-v2"
            },
            {
                "name": "fast-inference",
                "description": "Fast, cheap models for quick tasks",
                "default_model": "meta-llama/llama-3.2-3b-instruct"
            },
            {
                "name": "groq-speed",
                "description": "Groq for ultra-fast inference",
                "default_model": "groq/llama-3.1-70b-versatile"
            }
        ]

        # Create each virtual key
        results = []
        for vk in virtual_keys:
            result = await self.create_virtual_key(
                vk["name"],
                vk["description"],
                vk.get("default_model")
            )
            results.append((vk["name"], result))

        # Summary
        print("\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)

        successful = sum(1 for _, r in results if r.get("success"))
        total = len(results)

        print(f"\n✅ Successfully created: {successful}/{total}")

        if successful == total:
            print("\n🎉 All virtual keys created successfully!")

            # Update .env.local with the virtual key IDs
            await self.update_env_file()

        elif successful == 0:
            print("\n❌ No virtual keys were created")
            print("\nPossible issues:")
            print("  • Portkey API might not support programmatic virtual key creation")
            print("  • API key might not have admin permissions")
            print("  • You may need to create them manually in the dashboard")

            await self.provide_manual_instructions()
        else:
            print(f"\n⚠️  {total - successful} virtual keys failed to create")
            print("Check the errors above and try again")

    async def update_env_file(self):
        """Update .env.local with the created virtual key IDs."""

        if not self.created_keys:
            return

        print("\n📝 Updating .env.local with virtual key IDs...")

        # Read existing .env.local
        env_path = ".env.local"
        with open(env_path) as f:
            lines = f.readlines()

        # Add or update virtual key IDs
        vk_mapping = {
            "openrouter-main": "PORTKEY_VK_MAIN",
            "gpt-models": "PORTKEY_VK_GPT",
            "claude-models": "PORTKEY_VK_CLAUDE",
            "qwen-coder": "PORTKEY_VK_QWEN",
            "deepseek-coder": "PORTKEY_VK_DEEPSEEK",
            "fast-inference": "PORTKEY_VK_FAST",
            "groq-speed": "PORTKEY_VK_GROQ"
        }

        # Check if virtual key section exists
        has_vk_section = any("Portkey Virtual Key IDs" in line for line in lines)

        if not has_vk_section:
            lines.append("\n# Portkey Virtual Key IDs (auto-generated)\n")

        for key_name, vk_id in self.created_keys.items():
            env_var = vk_mapping.get(key_name)
            if env_var:
                # Check if this env var already exists
                found = False
                for i, line in enumerate(lines):
                    if line.startswith(f"{env_var}="):
                        lines[i] = f"{env_var}={vk_id}\n"
                        found = True
                        break

                if not found:
                    lines.append(f"{env_var}={vk_id}\n")

        # Write back to file
        with open(env_path, 'w') as f:
            f.writelines(lines)

        print("✅ .env.local updated with virtual key IDs")

    async def provide_manual_instructions(self):
        """Provide manual instructions if API creation fails."""

        print("\n" + "="*60)
        print("📋 MANUAL SETUP INSTRUCTIONS")
        print("="*60)

        print("""
Since programmatic creation didn't work, here's how to create them manually:

1. Go to https://app.portkey.ai
2. Click on "Virtual Keys" in the left sidebar
3. Click "+ Create Virtual Key" button

For EACH of these 7 keys, create with:
  • Provider: OpenRouter
  • API Key: Your OpenRouter key (already in clipboard if you copy from .env.local)

Virtual Keys to Create:
1. openrouter-main (default model: openrouter/auto)
2. gpt-models (default model: openai/gpt-4o)
3. claude-models (default model: anthropic/claude-3.5-sonnet)
4. qwen-coder (default model: qwen/qwen-2.5-coder-32b-instruct)
5. deepseek-coder (default model: deepseek/deepseek-coder-v2)
6. fast-inference (default model: meta-llama/llama-3.2-3b-instruct)
7. groq-speed (default model: groq/llama-3.1-70b-versatile)

After creating, add the virtual key IDs to .env.local:
PORTKEY_VK_MAIN=<id>
PORTKEY_VK_GPT=<id>
PORTKEY_VK_CLAUDE=<id>
PORTKEY_VK_QWEN=<id>
PORTKEY_VK_DEEPSEEK=<id>
PORTKEY_VK_FAST=<id>
PORTKEY_VK_GROQ=<id>
        """)

    async def test_virtual_keys(self):
        """Test if virtual keys are working."""

        print("\n" + "="*60)
        print("🧪 TESTING VIRTUAL KEYS")
        print("="*60)

        if not self.created_keys:
            print("No keys to test (none were created)")
            return

        # Test one of the created keys
        test_key = list(self.created_keys.values())[0]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {test_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "meta-llama/llama-3.2-3b-instruct",
                        "messages": [{"role": "user", "content": "Say 'working' in one word"}],
                        "max_tokens": 5
                    }
                )

                if response.status_code == 200:
                    print("✅ Virtual keys are working!")
                else:
                    print(f"❌ Test failed: Status {response.status_code}")

        except Exception as e:
            print(f"❌ Test error: {e}")


async def main():
    """Main function to create all virtual keys."""

    print("🔐 Portkey Virtual Key Automation")
    print("This will attempt to create all virtual keys programmatically.")

    try:
        creator = PortkeyVirtualKeyCreator()
        await creator.create_all_virtual_keys()

        if creator.created_keys:
            await creator.test_virtual_keys()

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("Make sure PORTKEY_API_KEY and OPENROUTER_API_KEY are set in .env.local")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
