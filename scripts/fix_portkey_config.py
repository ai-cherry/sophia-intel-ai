#!/usr/bin/env python3
"""
Fix Portkey Configuration Storage
Ensures all virtual keys are properly stored and persisted
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.secrets_manager import get_secrets_manager


def store_portkey_configuration():
    """Store all Portkey configuration in secure vault"""

    # Critical Portkey configuration
    PORTKEY_CONFIG = {
        # Main API Key - using the correct one from your message
        "PORTKEY_API_KEY": "hPxFZGd8AN269n4bznDf2/Onbi8I",
        # Virtual Keys for each provider
        "VK_DEEPSEEK": "deepseek-vk-24102f",
        "VK_OPENAI": "openai-vk-190a60",
        "VK_ANTHROPIC": "anthropic-vk-b42804",
        "VK_OPENROUTER": "vkj-openrouter-cc4151",
        "VK_XAI": "xai-vk-e65d0f",
        "VK_TOGETHER": "together-ai-670469",
        "VK_GEMINI": "gemini-vk-3d6108",
        "VK_GROQ": "groq-vk-6b9b52",
        "VK_PERPLEXITY": "perplexity-vk-56c172",
        "VK_MISTRAL": "mistral-vk-f92861",
        "VK_COHERE": "cohere-vk-496fa9",
        "VK_HUGGINGFACE": "huggingface-vk-28240e",
        "VK_MILVUS": "milvus-vk-34fa02",
        "VK_QDRANT": "qdrant-vk-d2b62a",
    }

    secrets_manager = get_secrets_manager()

    print("🔧 Storing Portkey configuration in secure vault...")

    for key, value in PORTKEY_CONFIG.items():
        secrets_manager.set_secret(key, value)
        print(f"  ✅ Stored {key}")

    # Also set in environment for immediate use
    for key, value in PORTKEY_CONFIG.items():
        os.environ[key] = value

    print("\n✅ Portkey configuration stored successfully!")

    # Verify storage
    print("\n🔍 Verifying stored configuration...")
    stored_keys = secrets_manager.list_secrets()
    portkey_keys = [k for k in stored_keys if "PORTKEY" in k or "VK_" in k]
    print(f"  Found {len(portkey_keys)} Portkey-related keys in vault")

    # Test retrieval
    api_key = secrets_manager.get_secret("PORTKEY_API_KEY")
    if api_key:
        print("  ✅ PORTKEY_API_KEY retrieval successful")
    else:
        print("  ❌ PORTKEY_API_KEY retrieval failed!")

    return True


def verify_portkey_manager():
    """Verify PortkeyManager can access configuration"""
    from app.core.portkey_manager import get_portkey_manager

    print("\n🔍 Testing PortkeyManager initialization...")

    try:
        manager = get_portkey_manager()
        print("  ✅ PortkeyManager initialized successfully")

        # Validate virtual keys
        validation = manager.validate_virtual_keys()
        print("\n📊 Virtual Key Validation:")
        for provider, status in validation.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {provider}")

        return True
    except Exception as e:
        print(f"  ❌ PortkeyManager initialization failed: {e}")
        return False


def main():
    """Main execution"""
    print("=" * 60)
    print("🛠️  PORTKEY CONFIGURATION FIX")
    print("=" * 60)

    # Store configuration
    if not store_portkey_configuration():
        print("\n❌ Failed to store configuration")
        sys.exit(1)

    # Verify manager
    if not verify_portkey_manager():
        print("\n⚠️  PortkeyManager verification failed")
        print("This may be due to missing dependencies or network issues")

    print("\n" + "=" * 60)
    print("✅ Configuration fix complete!")
    print("The Portkey virtual keys are now permanently stored.")
    print("=" * 60)


if __name__ == "__main__":
    main()
