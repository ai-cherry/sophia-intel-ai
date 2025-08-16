#!/usr/bin/env python3
"""
SOPHIA Intel Environment Check Script
Fail-fast environment validation for CI/CD and local development
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.common.env_schema import load_and_validate, get_config_export

def main():
    """Main environment check function"""
    try:
        print("🔍 SOPHIA Intel Environment Validation")
        print("=" * 50)
        
        # Load and validate configuration
        config = load_and_validate()
        
        print(f"✅ Environment: {config.ENV}")
        print(f"✅ API Configuration: {config.API_HOST}:{config.API_PORT}")
        print(f"✅ Workers: {config.API_WORKERS}")
        print(f"✅ Debug Mode: {config.DEBUG}")
        print(f"✅ Log Level: {config.LOG_LEVEL}")
        
        # Check feature flags
        features = {
            "Voice": config.FEATURE_VOICE_ENABLED,
            "Research": config.FEATURE_RESEARCH_ENABLED,
            "Code Generation": config.FEATURE_CODE_GENERATION,
            "Memory": config.FEATURE_MEMORY_ENABLED,
            "Telemetry": config.FEATURE_TELEMETRY_ENABLED,
        }
        
        print("\n🎛️  Feature Flags:")
        for feature, enabled in features.items():
            status = "✅ Enabled" if enabled else "❌ Disabled"
            print(f"   {feature}: {status}")
        
        # Check service URLs
        print("\n🔗 Service URLs:")
        services = {
            "MCP Code": config.MCP_CODE_URL,
            "MCP Research": config.MCP_RESEARCH_URL,
            "MCP Embedding": config.MCP_EMBEDDING_URL,
            "MCP Telemetry": config.MCP_TELEMETRY_URL,
            "MCP Notion": config.MCP_NOTION_URL,
            "Qdrant": config.QDRANT_URL,
            "Database": config.DATABASE_URL,
            "Redis": config.REDIS_URL,
        }
        
        for service, url in services.items():
            print(f"   {service}: {url}")
        
        # Check API providers
        print("\n🤖 AI Providers:")
        print(f"   OpenRouter Model: {config.OPENROUTER_MODEL}")
        print(f"   TTS Provider: {config.TTS_PROVIDER}")
        print(f"   STT Provider: {config.STT_PROVIDER}")
        
        # Production guardrails check
        if config.ENV == "prod":
            print("\n🛡️  Production Guardrails:")
            guardrails = [
                ("Mock Services", config.MOCK_SERVICES, False),
                ("Mock Embeddings", config.MOCK_EMBEDDINGS, False),
                ("Hash Embeddings", config.ALLOW_HASH_EMBEDDINGS, False),
                ("Debug Mode", config.DEBUG, False),
            ]
            
            for name, value, expected in guardrails:
                if value == expected:
                    print(f"   ✅ {name}: {value} (correct)")
                else:
                    print(f"   ⚠️  {name}: {value} (should be {expected})")
        
        # Export configuration for debugging
        if "--export" in sys.argv:
            export_data = get_config_export(config)
            export_file = project_root / "config_export.json"
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            print(f"\n📄 Configuration exported to: {export_file}")
        
        print("\n✅ Environment validation PASSED")
        print("🚀 Ready for deployment!")
        
        return 0
        
    except SystemExit as e:
        print(f"\n❌ Environment validation FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

