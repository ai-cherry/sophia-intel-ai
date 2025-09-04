#!/usr/bin/env python3
"""
Individual Virtual Key Testing Suite
Tests each Portkey virtual key to verify it's active and measure performance
"""

import asyncio
import time
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portkey_ai import Portkey
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.portkey')

# Virtual key to provider/model mapping
KEY_CONFIG = {
    "deepseek-vk-24102f": {
        "provider": "DeepSeek",
        "test_model": "deepseek-chat",
        "test_prompt": "Return 'OK' if working",
        "expected_tpm": 100000
    },
    "openai-vk-190a60": {
        "provider": "OpenAI",
        "test_model": "gpt-3.5-turbo",  # Start with cheaper model for testing
        "test_prompt": "Return 'OK' if working",
        "expected_tpm": 150000
    },
    "anthropic-vk-b42804": {
        "provider": "Anthropic",
        "test_model": "claude-3-haiku-20240307",  # Cheaper for testing
        "test_prompt": "Return 'OK' if working",
        "expected_tpm": 100000
    },
    "vkj-openrouter-cc4151": {
        "provider": "OpenRouter",
        "test_model": "openai/gpt-3.5-turbo",  # Via OpenRouter
        "test_prompt": "Return 'OK' if working",
        "expected_tpm": 200000
    },
    "perplexity-vk-56c172": {
        "provider": "Perplexity",
        "test_model": "llama-3.1-sonar-small-128k-online",
        "test_prompt": "Return 'OK' if working",
        "expected_tpm": 50000
    },
    "groq-vk-6b9b52": {
        "provider": "Groq",
        "test_model": "llama3-8b-8192",  # Fast model
        "test_prompt": "Return 'OK' if working",
        "expected_tpm": 500000
    },
    "mistral-vk-f92861": {
        "provider": "Mistral",
        "test_model": "mistral-tiny",  # Cheapest for testing
        "test_prompt": "Return 'OK' if working",
        "expected_tpm": 100000
    },
    "xai-vk-e65d0f": {
        "provider": "X.AI",
        "test_model": "grok-beta",
        "test_prompt": "Return 'OK' if working",
        "expected_tpm": 100000
    },
    "together-ai-670469": {
        "provider": "Together",
        "test_model": "meta-llama/Llama-3-8b-chat-hf",
        "test_prompt": "Return 'OK' if working",
        "expected_tpm": 200000
    },
    "cohere-vk-496fa9": {
        "provider": "Cohere",
        "test_model": "command-r",
        "test_prompt": "Return 'OK' if working",
        "expected_tpm": 100000
    }
}


class VirtualKeyTester:
    """Test individual virtual keys"""
    
    def __init__(self):
        self.portkey_api_key = os.getenv("PORTKEY_API_KEY")
        if not self.portkey_api_key:
            raise ValueError("PORTKEY_API_KEY not set")
        
        self.results = {}
        self.rate_limit_tests = {}
    
    async def test_single_key(self, virtual_key: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single virtual key"""
        
        print(f"\n🔑 Testing {config['provider']} ({virtual_key})")
        print(f"   Model: {config['test_model']}")
        
        try:
            # Create Portkey client
            client = Portkey(
                api_key=self.portkey_api_key,
                virtual_key=virtual_key
            )
            
            # Test 1: Basic connectivity
            start_time = time.time()
            
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=config['test_model'],
                messages=[
                    {"role": "user", "content": config['test_prompt']}
                ],
                max_tokens=10,
                temperature=0
            )
            
            latency = time.time() - start_time
            response_text = response.choices[0].message.content
            
            # Test 2: Measure tokens used
            tokens_used = 0
            if hasattr(response, 'usage'):
                tokens_used = response.usage.total_tokens
            
            result = {
                "virtual_key": virtual_key,
                "provider": config['provider'],
                "model": config['test_model'],
                "status": "✅ ACTIVE",
                "latency": round(latency, 3),
                "response": response_text[:50],
                "tokens_used": tokens_used,
                "expected_tpm": config['expected_tpm'],
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"   ✅ SUCCESS - Latency: {latency:.3f}s")
            return result
            
        except Exception as e:
            error_msg = str(e)
            
            # Parse error for useful info
            status = "❌ FAILED"
            if "rate limit" in error_msg.lower():
                status = "⚠️ RATE LIMITED"
            elif "authentication" in error_msg.lower():
                status = "🔒 AUTH FAILED"
            elif "model not found" in error_msg.lower():
                status = "❓ MODEL ISSUE"
            
            result = {
                "virtual_key": virtual_key,
                "provider": config['provider'],
                "model": config['test_model'],
                "status": status,
                "error": error_msg[:200],
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"   {status} - {error_msg[:100]}")
            return result
    
    async def test_rate_limits(self, virtual_key: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test actual rate limits by sending burst requests"""
        
        print(f"\n📊 Testing rate limits for {config['provider']}")
        
        try:
            client = Portkey(
                api_key=self.portkey_api_key,
                virtual_key=virtual_key
            )
            
            # Send 10 rapid requests
            burst_size = 10
            tasks = []
            
            for i in range(burst_size):
                task = asyncio.to_thread(
                    client.chat.completions.create,
                    model=config['test_model'],
                    messages=[{"role": "user", "content": f"Test {i}"}],
                    max_tokens=5,
                    temperature=0
                )
                tasks.append(task)
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            burst_time = time.time() - start_time
            
            # Count successes and failures
            successes = sum(1 for r in results if not isinstance(r, Exception))
            rate_limited = sum(1 for r in results if isinstance(r, Exception) and "rate" in str(r).lower())
            
            rpm_estimate = (successes / burst_time) * 60 if burst_time > 0 else 0
            
            return {
                "provider": config['provider'],
                "burst_size": burst_size,
                "successes": successes,
                "rate_limited": rate_limited,
                "burst_time": round(burst_time, 2),
                "estimated_rpm": round(rpm_estimate),
                "status": "✅ Good" if successes == burst_size else "⚠️ Limited" if rate_limited > 0 else "❌ Failed"
            }
            
        except Exception as e:
            return {
                "provider": config['provider'],
                "error": str(e),
                "status": "❌ Failed to test"
            }
    
    async def test_all_keys(self):
        """Test all configured virtual keys"""
        
        print("="*70)
        print("TESTING ALL VIRTUAL KEYS")
        print("="*70)
        
        # Test each key
        test_tasks = []
        for virtual_key, config in KEY_CONFIG.items():
            test_tasks.append(self.test_single_key(virtual_key, config))
        
        results = await asyncio.gather(*test_tasks)
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        active_keys = []
        failed_keys = []
        rate_limited = []
        
        for result in results:
            self.results[result['provider']] = result
            
            if "✅" in result['status']:
                active_keys.append(result)
            elif "⚠️" in result['status']:
                rate_limited.append(result)
            else:
                failed_keys.append(result)
        
        # Print active keys
        if active_keys:
            print(f"\n✅ ACTIVE KEYS ({len(active_keys)}):")
            for key in active_keys:
                print(f"   {key['provider']:12} - Latency: {key.get('latency', 'N/A')}s - TPM: {key['expected_tpm']:,}")
        
        # Print rate limited
        if rate_limited:
            print(f"\n⚠️ RATE LIMITED ({len(rate_limited)}):")
            for key in rate_limited:
                print(f"   {key['provider']:12} - {key.get('error', '')[:60]}")
        
        # Print failed keys
        if failed_keys:
            print(f"\n❌ FAILED KEYS ({len(failed_keys)}):")
            for key in failed_keys:
                print(f"   {key['provider']:12} - {key.get('error', '')[:60]}")
        
        # Calculate total capacity
        total_tpm = sum(k['expected_tpm'] for k in active_keys)
        print(f"\n💪 TOTAL ACTIVE CAPACITY: {total_tpm:,} TPM")
        
        return self.results
    
    async def test_rate_limits_all(self):
        """Test rate limits for all active keys"""
        
        print("\n" + "="*70)
        print("RATE LIMIT TESTING")
        print("="*70)
        
        # Only test keys that were active
        active_keys = [(k, c) for k, c in KEY_CONFIG.items() 
                      if c['provider'] in self.results and "✅" in self.results[c['provider']].get('status', '')]
        
        if not active_keys:
            print("No active keys to test rate limits")
            return
        
        rate_tasks = []
        for virtual_key, config in active_keys:
            rate_tasks.append(self.test_rate_limits(virtual_key, config))
        
        rate_results = await asyncio.gather(*rate_tasks)
        
        print("\n📊 RATE LIMIT RESULTS:")
        for result in rate_results:
            if result['status'] == "✅ Good":
                print(f"   {result['provider']:12} - ✅ No limits hit - Est. RPM: {result.get('estimated_rpm', 'N/A')}")
            elif "⚠️" in result['status']:
                print(f"   {result['provider']:12} - ⚠️ Hit limit after {result.get('successes', 0)}/{result.get('burst_size', 0)} requests")
            else:
                print(f"   {result['provider']:12} - ❌ {result.get('error', 'Failed')[:50]}")
        
        self.rate_limit_tests = {r['provider']: r for r in rate_results}
        return rate_results
    
    def save_results(self, filename: str = "virtual_key_test_results.json"):
        """Save test results to file"""
        
        output = {
            "test_time": datetime.now().isoformat(),
            "key_tests": self.results,
            "rate_tests": self.rate_limit_tests,
            "summary": {
                "total_keys": len(KEY_CONFIG),
                "active_keys": len([r for r in self.results.values() if "✅" in r.get('status', '')]),
                "failed_keys": len([r for r in self.results.values() if "❌" in r.get('status', '')]),
                "total_tpm_capacity": sum(
                    r['expected_tpm'] for r in self.results.values() 
                    if "✅" in r.get('status', '')
                )
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n📄 Results saved to {filename}")
        return filename


async def main():
    """Run the complete test suite"""
    
    print("\n" + "="*70)
    print("VIRTUAL KEY INDIVIDUAL TESTING SUITE")
    print("="*70)
    print("This will test each virtual key to verify:")
    print("  1. Key is active and authenticated")
    print("  2. Model is accessible")
    print("  3. Response latency")
    print("  4. Rate limit behavior")
    print("="*70)
    
    tester = VirtualKeyTester()
    
    # Step 1: Test all keys
    await tester.test_all_keys()
    
    # Step 2: Test rate limits for active keys
    await asyncio.sleep(2)  # Brief pause
    await tester.test_rate_limits_all()
    
    # Step 3: Save results
    tester.save_results()
    
    print("\n" + "="*70)
    print("TESTING COMPLETE")
    print("="*70)
    
    # Recommendations
    print("\n📋 RECOMMENDATIONS:")
    
    # Find fastest providers
    active = [r for r in tester.results.values() if "✅" in r.get('status', '')]
    if active:
        active.sort(key=lambda x: x.get('latency', 999))
        print("\n⚡ FASTEST PROVIDERS (for time-critical tasks):")
        for provider in active[:3]:
            print(f"   1. {provider['provider']:12} - {provider['latency']}s")
    
    # Find highest capacity
    active.sort(key=lambda x: x.get('expected_tpm', 0), reverse=True)
    print("\n💪 HIGHEST CAPACITY (for parallel workloads):")
    for provider in active[:3]:
        print(f"   1. {provider['provider']:12} - {provider['expected_tpm']:,} TPM")
    
    print("\n✅ Use these results to configure your swarm routing!")


if __name__ == "__main__":
    asyncio.run(main())