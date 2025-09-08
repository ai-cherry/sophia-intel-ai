#!/usr/bin/env python3
"""
Script to update all Claude references to Claude Opus 4.1 via Portkey/OpenRouter
"""

import os
import re
import json
from pathlib import Path

def update_claude_references():
    """Update all Claude model references to Opus 4.1"""

    # Model mapping for updates
    model_updates = {
        # Direct Claude API references
        r'"claude-3\.5-sonnet[^"]*"': '"anthropic/claude-3.5-sonnet"',
        r'"anthropic/claude-3-sonnet"]*"': '"anthropic/claude-3-sonnet"',
        r'"anthropic/claude-3-opus"]*"': '"anthropic/claude-3-opus"',
        r'"anthropic/claude-opus-4-1-20250805"]*"': '"anthropic/claude-opus-4-1-20250805"',
        r'"anthropic/claude-opus-4-1-20250805"]*"': '"anthropic/claude-opus-4-1-20250805"',

        # Python string references
        r"'claude-3\.5-sonnet[^']*'": "'anthropic/claude-3.5-sonnet'",
        r"'anthropic/claude-3-sonnet']*'": "'anthropic/claude-3-sonnet'",
        r"'anthropic/claude-3-opus']*'": "'anthropic/claude-3-opus'",
        r"'anthropic/claude-opus-4-1-20250805']*'": "'anthropic/claude-opus-4-1-20250805'",
        r"'anthropic/claude-opus-4-1-20250805']*'": "'anthropic/claude-opus-4-1-20250805'",

        # Configuration references
        r'model:\s*claude-[^\s\n]+': 'model: anthropic/claude-opus-4-1-20250805',
        r'MODEL:\s*claude-[^\s\n]+': 'MODEL: anthropic/claude-opus-4-1-20250805',

        # API endpoint updates
        r'https://api\.anthropic\.com': 'https://openrouter.ai/api',
        r'anthropic\.com/v1': 'openrouter.ai/api/v1',

        # Header updates for OpenRouter
        r'"Authorization"': '"Authorization"',
        r"'Authorization'": "'Authorization'",

        # Environment variable references
        r'OPENROUTER_API_KEY': 'OPENROUTER_API_KEY',
        r'OPENROUTER_API_KEY': 'OPENROUTER_API_KEY',
    }

    # Files to update
    file_patterns = [
        "**/*.py",
        "**/*.js", 
        "**/*.ts",
        "**/*.tsx",
        "**/*.json",
        "**/*.yaml",
        "**/*.yml",
        "**/*.md",
        "**/*.env*",
        "**/*.sh"
    ]

    updated_files = []

    for pattern in file_patterns:
        for file_path in Path(".").glob(pattern):
            if file_path.is_file() and not any(skip in str(file_path) for skip in ['.git', 'node_modules', '__pycache__', '.venv']):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    original_content = content

                    # Apply all model updates
                    for pattern, replacement in model_updates.items():
                        content = re.sub(pattern, replacement, content)

                    # Special handling for specific files
                    if file_path.name.endswith('.json'):
                        content = update_json_config(content)
                    elif file_path.name.endswith(('.py', '.js', '.ts', '.tsx')):
                        content = update_code_files(content)
                    elif file_path.name.endswith(('.yaml', '.yml')):
                        content = update_yaml_config(content)

                    # Write back if changed
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        updated_files.append(str(file_path))
                        print(f"✅ Updated: {file_path}")

                except Exception as e:
                    print(f"❌ Error updating {file_path}: {e}")

    return updated_files

def update_json_config(content):
    """Update JSON configuration files"""
    try:
        # Parse and update JSON
        if content.strip():
            data = json.loads(content)

            # Update model configurations
            def update_models_recursive(obj):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key in ['model', 'MODEL', 'default_model'] and isinstance(value, str):
                            if 'claude' in value.lower():
                                obj[key] = 'anthropic/claude-opus-4-1-20250805'
                        elif isinstance(value, (dict, list)):
                            update_models_recursive(value)
                elif isinstance(obj, list):
                    for item in obj:
                        update_models_recursive(item)

            update_models_recursive(data)
            return json.dumps(data, indent=2)
    except json.JSONDecodeError:

    return content

def update_code_files(content):
    """Update Python/JavaScript/TypeScript files"""

    if 'claude' in content.lower() and 'import' in content:
        if 'from openai import' in content and 'openrouter' not in content.lower():
            content = content.replace(
                'from openai import OpenAI',
                '''from openai import OpenAI
import os

# Configure for OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)'''
            )

    # Update API client initialization
    content = re.sub(
        r'anthropic\.Anthropic\([^)]*\)',
        '''OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)''',
        content
    )

    # Update message format for OpenRouter
    content = re.sub(
        r'client\.messages\.create\(',
        'client.chat.completions.create(',
        content
    )

    return content

def update_yaml_config(content):
    """Update YAML configuration files"""

    # Update model references in YAML
    content = re.sub(
        r'model:\s*claude[^\n]*',
        'model: anthropic/claude-opus-4-1-20250805',
        content
    )

    # Update API endpoints
    content = re.sub(
        r'base_url:\s*https://api\.anthropic\.com[^\n]*',
        'base_url: https://openrouter.ai/api/v1',
        content
    )

    return content

def create_portkey_config():
    """Create Portkey configuration for enhanced routing"""

    portkey_config = {
        "strategy": {
            "mode": "loadbalance"
        },
        "targets": [
            {
                "name": "anthropic/claude-opus-4-1-20250805",
                "provider": "anthropic",
                "api_key": "{{OPENROUTER_API_KEY}}",
                "model": "anthropic/claude-opus-4-1-20250805",
                "weight": 0.8
            },
            {
                "name": "anthropic/claude-opus-4-1-20250805",
                "provider": "openrouter", 
                "api_key": "{{OPENROUTER_API_KEY}}",
                "model": "anthropic/claude-opus-4-1-20250805",
                "weight": 0.2
            }
        ]
    }

    with open('config/portkey_opus41.json', 'w') as f:
        json.dump(portkey_config, f, indent=2)

    print("✅ Created Portkey configuration for Opus 4.1")

def update_environment_files():
    """Update environment configuration files"""

    env_updates = {
        '.env.example': [
            '# Claude Opus 4.1 via OpenRouter/Portkey',
            'OPENROUTER_API_KEY=your_openrouter_api_key_here',
            'PORTKEY_API_KEY=your_portkey_api_key_here',
            'PORTKEY_CONFIG=config/portkey_opus41.json',
            '',
            '# Fallback direct Anthropic API',
            'OPENROUTER_API_KEY=your_anthropic_api_key_here',
            '',
            '# Model Configuration',
            'DEFAULT_MODEL=anthropic/claude-opus-4-1-20250805',
            'CLAUDE_MODEL=anthropic/claude-opus-4-1-20250805',
        ],
        '.env.production': [
            '# Production Claude Opus 4.1 Configuration',
            'OPENROUTER_API_KEY=${OPENROUTER_API_KEY}',
            'PORTKEY_API_KEY=${PORTKEY_API_KEY}',
            'PORTKEY_CONFIG=config/portkey_opus41.json',
            'DEFAULT_MODEL=anthropic/claude-opus-4-1-20250805',
        ]
    }

    for filename, lines in env_updates.items():
        with open(filename, 'w') as f:
            f.write('\n'.join(lines) + '\n')
        print(f"✅ Updated {filename}")

def main():
    """Main execution function"""
    print("🚀 Updating all Claude references to Opus 4.1 via Portkey/OpenRouter...")

    # Change to sophia-main directory
    os.chdir('/app')

    # Update all files
    updated_files = update_claude_references()

    # Create Portkey configuration
    os.makedirs('config', exist_ok=True)
    create_portkey_config()

    # Update environment files
    update_environment_files()

    print(f"\n✅ Update complete! Modified {len(updated_files)} files:")
    for file_path in updated_files[:10]:  # Show first 10
        print(f"  - {file_path}")

    if len(updated_files) > 10:
        print(f"  ... and {len(updated_files) - 10} more files")

    print("\n🎯 Key Changes Made:")
    print("  - All Claude models updated to claude-opus-4-1-20250805")
    print("  - API endpoints switched to OpenRouter")
    print("  - Environment variables updated for OpenRouter/Portkey")
    print("  - Portkey configuration created for load balancing")
    print("  - Headers updated for OpenRouter authentication")

    print("\n📋 Next Steps:")
    print("  1. Set OPENROUTER_API_KEY in your environment")
    print("  2. Set PORTKEY_API_KEY for enhanced routing (optional)")
    print("  3. Test the integration with the new model")
    print("  4. Update any remaining manual references")

if __name__ == "__main__":
    main()
