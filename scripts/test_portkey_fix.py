#!/usr/bin/env python3
"""
Test Portkey with different configuration approaches
"""

import os
import json
import requests

def load_environment():
    """Load environment variables"""
    try:
        with open('.env.remediation', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        pass

def test_portkey_with_provider():
    """Test Portkey with provider header"""
    print("Testing Portkey with provider header...")
    
    api_key = os.environ.get('PORTKEY_API_KEY')
    if not api_key:
        print("❌ No Portkey API key found")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "x-portkey-provider": "openrouter",
        "x-portkey-api-key": os.environ.get('OPENROUTER_API_KEY', '')
    }
    
    chat_data = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Hello from Sophia AI via Portkey with provider!"}
        ],
        "max_tokens": 50
    }
    
    try:
        response = requests.post(
            "https://api.portkey.ai/v1/chat/completions",
            headers=headers,
            json=chat_data,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content']
            print(f"✅ Portkey with provider working!")
            print(f"Response: {message}")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_portkey_with_config():
    """Test Portkey with config"""
    print("\nTesting Portkey with config...")
    
    api_key = os.environ.get('PORTKEY_API_KEY')
    if not api_key:
        print("❌ No Portkey API key found")
        return False
    
    # Load config
    try:
        with open('config/portkey_config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ No Portkey config file found")
        return False
    
    # Replace placeholder with actual API key
    config_str = json.dumps(config).replace('{{OPENAI_API_KEY}}', os.environ.get('OPENROUTER_API_KEY', ''))
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "x-portkey-config": config_str
    }
    
    chat_data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Hello from Sophia AI via Portkey with config!"}
        ],
        "max_tokens": 50
    }
    
    try:
        response = requests.post(
            "https://api.portkey.ai/v1/chat/completions",
            headers=headers,
            json=chat_data,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content']
            print(f"✅ Portkey with config working!")
            print(f"Response: {message}")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    load_environment()
    
    print("Portkey Configuration Testing")
    print("="*40)
    
    # Test with provider header
    provider_works = test_portkey_with_provider()
    
    # Test with config
    config_works = test_portkey_with_config()
    
    print(f"\nResults:")
    print(f"Provider approach: {'✅ Working' if provider_works else '❌ Failed'}")
    print(f"Config approach: {'✅ Working' if config_works else '❌ Failed'}")
    
    if provider_works or config_works:
        print("\n✅ Portkey can be configured successfully!")
        if provider_works:
            print("Recommended: Use x-portkey-provider header approach")
        else:
            print("Recommended: Use x-portkey-config approach")
    else:
        print("\n❌ Portkey configuration needs investigation")

if __name__ == "__main__":
    main()

