#!/usr/bin/env python3
"""
LLM providers testing and validation script
Tests OpenRouter, Portkey, Lambda Labs, and other AI service providers
"""

import os
import sys
import json
import time
import requests
from typing import Dict, Any, Optional

def load_environment():
    """Load environment variables from .env file"""
    env_vars = {}
    try:
        with open('.env.remediation', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
                    os.environ[key] = value
    except FileNotFoundError:
        print("Warning: .env.remediation file not found")
    return env_vars

def test_openrouter():
    """Test OpenRouter API connectivity and functionality"""
    print("\n=== Testing OpenRouter API ===")
    
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        return {"status": "NOT_CONFIGURED", "message": "No API key found"}
    
    print(f"API Key: {api_key[:20]}..." if len(api_key) > 20 else api_key)
    
    # Test API connectivity
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://sophia-intel.ai",
        "X-Title": "Sophia AI Platform"
    }
    
    try:
        # Test 1: Get available models
        print("Testing models endpoint...")
        models_response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers=headers,
            timeout=30
        )
        
        print(f"Models endpoint status: {models_response.status_code}")
        
        if models_response.status_code == 200:
            models_data = models_response.json()
            model_count = len(models_data.get('data', []))
            print(f"✅ Available models: {model_count}")
            
            # Test 2: Simple chat completion
            print("Testing chat completion...")
            chat_data = {
                "model": "openai/gpt-3.5-turbo",
                "messages": [
                    {"role": "user", "content": "Hello! This is a test from Sophia AI platform."}
                ],
                "max_tokens": 50
            }
            
            chat_response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=chat_data,
                timeout=30
            )
            
            print(f"Chat completion status: {chat_response.status_code}")
            
            if chat_response.status_code == 200:
                chat_result = chat_response.json()
                message = chat_result['choices'][0]['message']['content']
                usage = chat_result.get('usage', {})
                
                print(f"✅ Chat completion successful")
                print(f"Response: {message[:100]}...")
                print(f"Tokens used: {usage.get('total_tokens', 'unknown')}")
                
                return {
                    "status": "OK",
                    "models_available": model_count,
                    "chat_test": "successful",
                    "response_preview": message[:100],
                    "tokens_used": usage.get('total_tokens', 0)
                }
            else:
                print(f"❌ Chat completion failed: {chat_response.text}")
                return {
                    "status": "PARTIAL",
                    "models_available": model_count,
                    "chat_test": "failed",
                    "error": chat_response.text
                }
        else:
            print(f"❌ Models endpoint failed: {models_response.text}")
            return {
                "status": "ERROR",
                "message": f"API access failed: {models_response.text}"
            }
            
    except Exception as e:
        print(f"❌ OpenRouter test failed: {str(e)}")
        return {"status": "ERROR", "message": str(e)}

def test_portkey():
    """Test Portkey AI gateway functionality"""
    print("\n=== Testing Portkey AI Gateway ===")
    
    api_key = os.environ.get('PORTKEY_API_KEY')
    config = os.environ.get('PORTKEY_CONFIG')
    
    if not api_key:
        return {"status": "NOT_CONFIGURED", "message": "No API key found"}
    
    print(f"API Key: {api_key[:20]}..." if len(api_key) > 20 else api_key)
    print(f"Config: {config[:50]}..." if config and len(config) > 50 else config or "Not set")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    if config:
        headers["x-portkey-config"] = config
    
    try:
        # Test Portkey gateway
        print("Testing Portkey gateway...")
        
        # Try different Portkey endpoints
        endpoints_to_test = [
            "https://api.portkey.ai/v1/chat/completions",
            "https://api.portkey.ai/v1/models"
        ]
        
        for endpoint in endpoints_to_test:
            print(f"Testing endpoint: {endpoint}")
            
            if "models" in endpoint:
                response = requests.get(endpoint, headers=headers, timeout=30)
            else:
                # Chat completion test
                chat_data = {
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "user", "content": "Hello from Sophia AI via Portkey!"}
                    ],
                    "max_tokens": 50
                }
                response = requests.post(endpoint, headers=headers, json=chat_data, timeout=30)
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Portkey endpoint working: {endpoint}")
                
                if "chat/completions" in endpoint:
                    message = result['choices'][0]['message']['content']
                    print(f"Response: {message[:100]}...")
                    
                    return {
                        "status": "OK",
                        "endpoint": endpoint,
                        "response_preview": message[:100],
                        "config_used": bool(config)
                    }
                else:
                    models = result.get('data', [])
                    print(f"Models available: {len(models)}")
                    
                    return {
                        "status": "OK",
                        "endpoint": endpoint,
                        "models_count": len(models),
                        "config_used": bool(config)
                    }
            else:
                print(f"❌ Failed: {response.text[:200]}")
        
        return {"status": "ERROR", "message": "All Portkey endpoints failed"}
        
    except Exception as e:
        print(f"❌ Portkey test failed: {str(e)}")
        return {"status": "ERROR", "message": str(e)}

def test_lambda_labs_llm():
    """Test Lambda Labs LLM API if available"""
    print("\n=== Testing Lambda Labs LLM API ===")
    
    api_key = os.environ.get('LAMBDA_CLOUD_API_KEY') or os.environ.get('LAMBDA_CLOUD_API_KEY')
    
    if not api_key:
        return {"status": "NOT_CONFIGURED", "message": "No Lambda Labs API key found"}
    
    print(f"API Key: {api_key[:20]}..." if len(api_key) > 20 else api_key)
    
    # Lambda Labs primarily provides compute, not direct LLM API
    # But let's check if they have any inference endpoints
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # Test Lambda Labs API endpoints
        endpoints_to_test = [
            "https://cloud.lambdalabs.com/api/v1/instances",
            "https://cloud.lambdalabs.com/api/v1/instance-types"
        ]
        
        for endpoint in endpoints_to_test:
            print(f"Testing endpoint: {endpoint}")
            
            response = requests.get(endpoint, headers=headers, timeout=30)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Lambda Labs API accessible: {endpoint}")
                
                if "instances" in endpoint:
                    instances = result.get('data', [])
                    print(f"Active instances: {len(instances)}")
                    
                    return {
                        "status": "OK",
                        "service": "compute",
                        "instances_count": len(instances),
                        "note": "Lambda Labs provides compute, not direct LLM API"
                    }
                elif "instance-types" in endpoint:
                    instance_types = result.get('data', {})
                    gpu_types = list(instance_types.keys()) if instance_types else []
                    print(f"Available GPU types: {gpu_types[:3]}...")
                    
                    return {
                        "status": "OK", 
                        "service": "compute",
                        "gpu_types_available": len(gpu_types),
                        "note": "Lambda Labs provides GPU compute for model inference"
                    }
            else:
                print(f"❌ Failed: {response.text[:200]}")
        
        return {"status": "ERROR", "message": "Lambda Labs API endpoints failed"}
        
    except Exception as e:
        print(f"❌ Lambda Labs test failed: {str(e)}")
        return {"status": "ERROR", "message": str(e)}

def test_other_providers():
    """Test other AI service providers"""
    print("\n=== Testing Other AI Providers ===")
    
    providers_to_test = {
        "TOGETHER_AI_API_KEY": "https://api.together.xyz/v1/models",
        "HUGGINGFACE_API_TOKEN": "https://huggingface.co/api/whoami",
        "TAVILY_API_KEY": None,  # Search API, different endpoint structure
        "ARIZE_API_KEY": None    # Monitoring API, different structure
    }
    
    results = {}
    
    for env_key, test_endpoint in providers_to_test.items():
        api_key = os.environ.get(env_key)
        provider_name = env_key.replace('_API_KEY', '').replace('_API_TOKEN', '').lower()
        
        print(f"\nTesting {provider_name}...")
        
        if not api_key:
            results[provider_name] = {"status": "NOT_CONFIGURED", "message": "No API key found"}
            print(f"❌ {provider_name}: No API key")
            continue
        
        print(f"API Key: {api_key[:20]}..." if len(api_key) > 20 else api_key)
        
        if not test_endpoint:
            results[provider_name] = {"status": "CONFIGURED", "message": "API key present, endpoint testing not implemented"}
            print(f"⚠️ {provider_name}: API key present, no test endpoint")
            continue
        
        try:
            headers = {"Authorization": f"Bearer {api_key}"}
            
            response = requests.get(test_endpoint, headers=headers, timeout=30)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ {provider_name}: API accessible")
                results[provider_name] = {"status": "OK", "endpoint": test_endpoint}
            else:
                print(f"❌ {provider_name}: {response.text[:100]}")
                results[provider_name] = {"status": "ERROR", "message": response.text[:100]}
                
        except Exception as e:
            print(f"❌ {provider_name}: {str(e)}")
            results[provider_name] = {"status": "ERROR", "message": str(e)}
    
    return results

def generate_llm_fixes(results: Dict[str, Any]):
    """Generate fixes for LLM provider issues"""
    print("\n" + "="*60)
    print("LLM PROVIDERS REMEDIATION RECOMMENDATIONS")
    print("="*60)
    
    fixes = []
    
    # OpenRouter fixes
    if results['openrouter']['status'] != 'OK':
        fixes.append({
            "service": "OpenRouter",
            "issue": f"OpenRouter API {results['openrouter']['status'].lower()}",
            "fix": "Verify API key at https://openrouter.ai/keys and check billing",
            "priority": "HIGH"
        })
    
    # Portkey fixes
    if results['portkey']['status'] != 'OK':
        fixes.append({
            "service": "Portkey",
            "issue": f"Portkey gateway {results['portkey']['status'].lower()}",
            "fix": "Verify API key and config at https://portkey.ai/",
            "priority": "HIGH"
        })
    
    # Lambda Labs fixes
    if results['lambda_labs']['status'] != 'OK':
        fixes.append({
            "service": "Lambda Labs",
            "issue": f"Lambda Labs API {results['lambda_labs']['status'].lower()}",
            "fix": "Verify API key at https://cloud.lambdalabs.com/api-keys",
            "priority": "MEDIUM"
        })
    
    # Other providers fixes
    for provider, result in results.get('other_providers', {}).items():
        if result['status'] not in ['OK', 'CONFIGURED']:
            fixes.append({
                "service": provider.title(),
                "issue": f"{provider} API {result['status'].lower()}",
                "fix": f"Verify {provider} API key and account status",
                "priority": "LOW"
            })
    
    # Print fixes
    for fix in fixes:
        print(f"\n🔧 {fix['service']} ({fix['priority']} PRIORITY)")
        print(f"   Issue: {fix['issue']}")
        print(f"   Fix: {fix['fix']}")
    
    return fixes

def main():
    """Main test execution"""
    print("Sophia AI LLM Providers Testing")
    print("="*50)
    
    # Load environment
    env_vars = load_environment()
    print(f"Loaded {len(env_vars)} environment variables")
    
    # Run tests
    results = {
        'openrouter': test_openrouter(),
        'portkey': test_portkey(),
        'lambda_labs': test_lambda_labs_llm(),
        'other_providers': test_other_providers()
    }
    
    # Generate fixes
    fixes = generate_llm_fixes(results)
    
    # Save results
    with open('llm_providers_test_results.json', 'w') as f:
        json.dump({
            'timestamp': time.time(),
            'results': results,
            'fixes': fixes
        }, f, indent=2)
    
    print(f"\n📊 Results saved to llm_providers_test_results.json")
    
    # Summary
    print(f"\n📋 SUMMARY")
    print(f"="*20)
    for service, result in results.items():
        if service == 'other_providers':
            continue  # Skip other providers in main summary
        status_emoji = "✅" if result['status'] == 'OK' else "⚠️" if result['status'] in ['PARTIAL', 'CONFIGURED'] else "❌"
        print(f"{status_emoji} {service.upper()}: {result['status']}")
    
    # Other providers summary
    if results.get('other_providers'):
        print(f"\nOTHER PROVIDERS:")
        for provider, result in results['other_providers'].items():
            status_emoji = "✅" if result['status'] == 'OK' else "⚠️" if result['status'] == 'CONFIGURED' else "❌"
            print(f"{status_emoji} {provider.upper()}: {result['status']}")

if __name__ == "__main__":
    main()

