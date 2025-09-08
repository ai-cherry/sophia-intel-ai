#!/usr/bin/env python3
"""
Troubleshoot ALL LLM Connections - Portkey AND Direct APIs
If Portkey fails, try direct API keys
"""
import asyncio
import json
import os
import time
from datetime import datetime
from typing import Any, Dict

# Set up environment
os.environ["PORTKEY_API_KEY"] = "hPxFZGd8AN269n4bznDf2/Onbi8I"

# Direct API keys (you'll need to add these)
DIRECT_API_KEYS = {
    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", ""),
    "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
    "GROQ_API_KEY": os.environ.get("GROQ_API_KEY", ""),
    "TOGETHER_API_KEY": os.environ.get("TOGETHER_API_KEY", ""),
    "MISTRAL_API_KEY": os.environ.get("MISTRAL_API_KEY", ""),
    "COHERE_API_KEY": os.environ.get("COHERE_API_KEY", ""),
    "DEEPSEEK_API_KEY": os.environ.get("DEEPSEEK_API_KEY", ""),
}

print("\n🔍 Checking for API keys in environment...")
for key_name, key_value in DIRECT_API_KEYS.items():
    if key_value:
        print(f"  ✅ {key_name}: Found (length: {len(key_value)})")
    else:
        print(f"  ❌ {key_name}: Not found")

# Portkey virtual keys
PORTKEY_CONFIGS = {
    "openai": {"vk": "openai-vk-190a60", "model": "gpt-3.5-turbo"},
    "anthropic": {"vk": "anthropic-vk-b42804", "model": "claude-3-haiku-20240307"},
    "groq": {"vk": "groq-vk-6b9b52", "model": "llama-3.1-8b-instant"},
    "deepseek": {"vk": "deepseek-vk-24102f", "model": "deepseek-chat"},
    "together": {
        "vk": "together-ai-670469",
        "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    },
    "mistral": {"vk": "mistral-vk-f92861", "model": "mistral-small-latest"},
    "cohere": {"vk": "cohere-vk-496fa9", "model": "command-r"},
}


class ConnectionTester:
    """Test both Portkey and direct API connections"""

    def __init__(self):
        self.results = {}
        self.working_providers = []
        self.test_prompt = "Respond with just 'OK' if you're working"

    async def test_portkey(self, provider: str, config: Dict) -> Dict[str, Any]:
        """Test connection via Portkey"""
        try:
            from portkey_ai import Portkey

            client = Portkey(api_key=os.environ["PORTKEY_API_KEY"], virtual_key=config["vk"])

            start = time.time()
            response = client.chat.completions.create(
                model=config["model"],
                messages=[{"role": "user", "content": self.test_prompt}],
                max_tokens=10,
                temperature=0,
            )
            latency = int((time.time() - start) * 1000)

            return {
                "method": "portkey",
                "status": "success",
                "response": (
                    response.choices[0].message.content if response.choices else "No response"
                ),
                "latency_ms": latency,
                "model": config["model"],
            }

        except Exception as e:
            return {"method": "portkey", "status": "failed", "error": str(e)[:200]}

    async def test_openai_direct(self) -> Dict[str, Any]:
        """Test OpenAI direct API"""
        if not DIRECT_API_KEYS["OPENAI_API_KEY"]:
            return {"method": "direct", "status": "skipped", "reason": "No API key"}

        try:
            import openai

            client = openai.OpenAI(api_key=DIRECT_API_KEYS["OPENAI_API_KEY"])

            start = time.time()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": self.test_prompt}],
                max_tokens=10,
                temperature=0,
            )
            latency = int((time.time() - start) * 1000)

            return {
                "method": "direct",
                "status": "success",
                "response": response.choices[0].message.content,
                "latency_ms": latency,
            }

        except Exception as e:
            return {"method": "direct", "status": "failed", "error": str(e)[:200]}

    async def test_anthropic_direct(self) -> Dict[str, Any]:
        """Test Anthropic direct API"""
        if not DIRECT_API_KEYS["ANTHROPIC_API_KEY"]:
            return {"method": "direct", "status": "skipped", "reason": "No API key"}

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=DIRECT_API_KEYS["ANTHROPIC_API_KEY"])

            start = time.time()
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": self.test_prompt}],
                max_tokens=10,
                temperature=0,
            )
            latency = int((time.time() - start) * 1000)

            return {
                "method": "direct",
                "status": "success",
                "response": response.content[0].text if response.content else "No response",
                "latency_ms": latency,
            }

        except Exception as e:
            return {"method": "direct", "status": "failed", "error": str(e)[:200]}

    async def test_groq_direct(self) -> Dict[str, Any]:
        """Test Groq direct API"""
        if not DIRECT_API_KEYS["GROQ_API_KEY"]:
            return {"method": "direct", "status": "skipped", "reason": "No API key"}

        try:
            from groq import Groq

            client = Groq(api_key=DIRECT_API_KEYS["GROQ_API_KEY"])

            start = time.time()
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": self.test_prompt}],
                max_tokens=10,
                temperature=0,
            )
            latency = int((time.time() - start) * 1000)

            return {
                "method": "direct",
                "status": "success",
                "response": response.choices[0].message.content,
                "latency_ms": latency,
            }

        except Exception as e:
            return {"method": "direct", "status": "failed", "error": str(e)[:200]}

    async def test_together_direct(self) -> Dict[str, Any]:
        """Test Together AI direct API"""
        if not DIRECT_API_KEYS["TOGETHER_API_KEY"]:
            return {"method": "direct", "status": "skipped", "reason": "No API key"}

        try:
            import requests

            headers = {
                "Authorization": f"Bearer {DIRECT_API_KEYS['TOGETHER_API_KEY']}",
                "Content-Type": "application/json",
            }

            data = {
                "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                "messages": [{"role": "user", "content": self.test_prompt}],
                "max_tokens": 10,
                "temperature": 0,
            }

            start = time.time()
            response = requests.post(
                "https://api.together.xyz/v1/chat/completions", headers=headers, json=data
            )
            latency = int((time.time() - start) * 1000)

            if response.status_code == 200:
                result = response.json()
                return {
                    "method": "direct",
                    "status": "success",
                    "response": result["choices"][0]["message"]["content"],
                    "latency_ms": latency,
                }
            else:
                return {
                    "method": "direct",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}: {response.text[:200]}",
                }

        except Exception as e:
            return {"method": "direct", "status": "failed", "error": str(e)[:200]}

    async def test_provider(self, provider: str) -> Dict[str, Any]:
        """Test a provider via both Portkey and direct API"""
        print(f"\n🧪 Testing {provider.upper()}...")

        results = {"provider": provider}

        # Test Portkey
        if provider in PORTKEY_CONFIGS:
            print("  📡 Testing via Portkey...")
            portkey_result = await self.test_portkey(provider, PORTKEY_CONFIGS[provider])
            results["portkey"] = portkey_result

            if portkey_result["status"] == "success":
                print(f"    ✅ Portkey works! ({portkey_result['latency_ms']}ms)")
            else:
                print(f"    ❌ Portkey failed: {portkey_result.get('error', 'Unknown')[:100]}")

        # Test direct API
        print("  🔌 Testing direct API...")

        if provider == "openai":
            direct_result = await self.test_openai_direct()
        elif provider == "anthropic":
            direct_result = await self.test_anthropic_direct()
        elif provider == "groq":
            direct_result = await self.test_groq_direct()
        elif provider == "together":
            direct_result = await self.test_together_direct()
        else:
            direct_result = {"method": "direct", "status": "not_implemented"}

        results["direct"] = direct_result

        if direct_result["status"] == "success":
            print(f"    ✅ Direct API works! ({direct_result['latency_ms']}ms)")
        elif direct_result["status"] == "skipped":
            print(f"    ⏭️  Direct API skipped: {direct_result['reason']}")
        elif direct_result["status"] == "not_implemented":
            print(f"    ⏭️  Direct API not implemented for {provider}")
        else:
            print(f"    ❌ Direct API failed: {direct_result.get('error', 'Unknown')[:100]}")

        # Determine best method
        if portkey_result.get("status") == "success" and direct_result.get("status") == "success":
            # Both work, choose faster
            if portkey_result["latency_ms"] < direct_result["latency_ms"]:
                results["recommendation"] = "use_portkey"
            else:
                results["recommendation"] = "use_direct"
        elif portkey_result.get("status") == "success":
            results["recommendation"] = "use_portkey"
        elif direct_result.get("status") == "success":
            results["recommendation"] = "use_direct"
        else:
            results["recommendation"] = "provider_broken"

        return results

    async def test_all(self):
        """Test all providers"""
        print("=" * 60)
        print("🔧 COMPREHENSIVE CONNECTION TROUBLESHOOTING")
        print("=" * 60)

        providers_to_test = [
            "openai",
            "anthropic",
            "groq",
            "together",
            "deepseek",
            "mistral",
            "cohere",
        ]

        for provider in providers_to_test:
            result = await self.test_provider(provider)
            self.results[provider] = result

            if result.get("recommendation") != "provider_broken":
                self.working_providers.append(provider)

        return self.results

    def generate_recommendations(self) -> Dict[str, Any]:
        """Generate recommendations based on test results"""
        recommendations = {"use_portkey": [], "use_direct": [], "broken": [], "config_needed": []}

        for provider, result in self.results.items():
            recommendation = result.get("recommendation", "unknown")

            if recommendation == "use_portkey":
                recommendations["use_portkey"].append(provider)
            elif recommendation == "use_direct":
                recommendations["use_direct"].append(provider)
                # Check if we have the API key
                key_name = f"{provider.upper()}_API_KEY"
                if not DIRECT_API_KEYS.get(key_name):
                    recommendations["config_needed"].append(f"Add {key_name} to environment")
            elif recommendation == "provider_broken":
                recommendations["broken"].append(provider)

        return recommendations


async def main():
    tester = ConnectionTester()
    results = await tester.test_all()

    print("\n" + "=" * 60)
    print("📊 RESULTS SUMMARY")
    print("=" * 60)

    # Show working providers
    print(f"\n✅ Working Providers: {len(tester.working_providers)}")
    for provider in tester.working_providers:
        result = results[provider]
        methods = []
        if result.get("portkey", {}).get("status") == "success":
            methods.append(f"Portkey ({result['portkey']['latency_ms']}ms)")
        if result.get("direct", {}).get("status") == "success":
            methods.append(f"Direct ({result['direct']['latency_ms']}ms)")
        print(f"  • {provider}: {', '.join(methods)}")

    # Show broken providers
    broken = [p for p in results if results[p].get("recommendation") == "provider_broken"]
    if broken:
        print(f"\n❌ Broken Providers: {len(broken)}")
        for provider in broken:
            print(f"  • {provider}")

    # Generate recommendations
    recommendations = tester.generate_recommendations()

    print("\n" + "=" * 60)
    print("🎯 RECOMMENDATIONS")
    print("=" * 60)

    if recommendations["use_portkey"]:
        print("\n1. Continue using Portkey for:")
        for provider in recommendations["use_portkey"]:
            print(f"   • {provider}")

    if recommendations["use_direct"]:
        print("\n2. Switch to direct API for:")
        for provider in recommendations["use_direct"]:
            print(f"   • {provider}")

    if recommendations["config_needed"]:
        print("\n3. Configuration needed:")
        for config in recommendations["config_needed"]:
            print(f"   • {config}")

    if recommendations["broken"]:
        print("\n4. Abandon these providers:")
        for provider in recommendations["broken"]:
            print(f"   • {provider}")

    # Save results
    output_file = f"connection_troubleshoot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Detailed results saved to: {output_file}")

    # Final recommendation
    print("\n" + "=" * 60)
    print("💡 FINAL RECOMMENDATION")
    print("=" * 60)

    if len(tester.working_providers) >= 4:
        print("✅ You have enough working providers for production.")
        print("   Consider bypassing Portkey for providers where direct API is faster.")
    else:
        print("⚠️  Less than 4 working providers detected.")
        print("   You need to add direct API keys for critical providers.")
        print("   Priority: OpenAI, Anthropic, Groq (for speed), DeepSeek (for cost)")


if __name__ == "__main__":
    # First, let's check if we can import the required libraries
    print("\n📦 Checking required libraries...")

    libraries = {
        "portkey_ai": False,
        "openai": False,
        "anthropic": False,
        "groq": False,
        "requests": False,
    }

    for lib in libraries:
        try:
            __import__(lib)
            libraries[lib] = True
            print(f"  ✅ {lib}")
        except ImportError:
            print(f"  ❌ {lib} - Run: pip install {lib}")

    # Check if we have at least portkey
    if not libraries["portkey_ai"]:
        print("\n⚠️  portkey_ai not installed. Installing...")
        os.system("pip install portkey-ai")

    # Run the tests
    asyncio.run(main())
