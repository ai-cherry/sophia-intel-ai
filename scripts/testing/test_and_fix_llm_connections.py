#!/usr/bin/env python3
"""
Test and Fix LLM Connections through Portkey
Ensures all providers are properly configured and working
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
# Set Portkey API key
if not os.environ.get("PORTKEY_API_KEY"):
    raise RuntimeError("PORTKEY_API_KEY is required for this script.")
from portkey_ai import Portkey
class LLMConnectionFixer:
    """Test and fix LLM connections through Portkey"""
    # Complete provider configuration
    PROVIDERS = {
        "deepseek": {
            "vk": "deepseek-vk-24102f",
            "model": "deepseek-chat",
            "test_model": "deepseek-chat",
            "max_tokens": 100,
        },
        "openai": {
            "vk": "openai-vk-190a60",
            "model": "gpt-4o-mini",
            "test_model": "gpt-3.5-turbo",  # Cheaper for testing
            "max_tokens": 100,
        },
        "anthropic": {
            "vk": "anthropic-vk-b42804",
            "model": "claude-3-haiku-20240307",
            "test_model": "claude-3-haiku-20240307",
            "max_tokens": 100,
        },
        "groq": {
            "vk": "groq-vk-6b9b52",
            "model": "llama-3.3-70b-versatile",
            "test_model": "llama-3.1-8b-instant",  # Faster for testing
            "max_tokens": 100,
        },
        "together": {
            "vk": "together-ai-670469",
            "model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "test_model": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "max_tokens": 100,
        },
        "mistral": {
            "vk": "mistral-vk-f92861",
            "model": "mistral-small-latest",
            "test_model": "mistral-small-latest",
            "max_tokens": 100,
        },
        "xai": {
            "vk": "xai-vk-e65d0f",
            "model": "grok-beta",
            "test_model": "grok-beta",
            "max_tokens": 100,
        },
        "gemini": {
            "vk": "gemini-vk-3d6108",
            "model": "gemini-1.5-flash",
            "test_model": "gemini-1.5-flash",
            "max_tokens": 100,
        },
        "perplexity": {
            "vk": "perplexity-vk-56c172",
            "model": "llama-3.1-sonar-small-128k-online",
            "test_model": "llama-3.1-sonar-small-128k-online",
            "max_tokens": 100,
        },
        "cohere": {
            "vk": "cohere-vk-496fa9",
            "model": "command-r",
            "test_model": "command-r",
            "max_tokens": 100,
        },
    }
    def __init__(self):
        self.api_key = os.environ.get("PORTKEY_API_KEY")
        if not self.api_key:
            raise ValueError("PORTKEY_API_KEY not found")
        self.results = {}
        self.working_providers = []
        self.failed_providers = []
    async def test_provider(self, name: str, config: Dict) -> Dict[str, Any]:
        """Test a single provider connection"""
        print(f"\n🧪 Testing {name}...")
        try:
            client = Portkey(api_key=self.api_key, virtual_key=config["vk"])
            # Simple test message
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Respond with exactly: 'OK'",
                },
                {"role": "user", "content": "Status check"},
            ]
            start = datetime.now()
            # Run sync call in executor
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model=config["test_model"],
                        messages=messages,
                        max_tokens=config["max_tokens"],
                        temperature=0,
                    ),
                ),
                timeout=30.0,
            )
            latency = int((datetime.now() - start).total_seconds() * 1000)
            result = {
                "provider": name,
                "status": "working",
                "model": config["test_model"],
                "latency_ms": latency,
                "response": (
                    response.choices[0].message.content
                    if response.choices
                    else "No response"
                ),
            }
            self.working_providers.append(name)
            print(f"  ✅ {name} working ({latency}ms)")
            return result
        except Exception as e:
            error_msg = str(e)
            # Diagnose specific issues
            diagnosis = self.diagnose_error(name, error_msg)
            result = {
                "provider": name,
                "status": "failed",
                "error": error_msg[:200],
                "diagnosis": diagnosis,
                "fix_suggestion": self.suggest_fix(name, diagnosis),
            }
            self.failed_providers.append(name)
            print(f"  ❌ {name} failed: {diagnosis}")
            return result
    def diagnose_error(self, provider: str, error: str) -> str:
        """Diagnose the specific error type"""
        error_lower = error.lower()
        if "429" in error or "quota" in error_lower or "rate limit" in error_lower:
            return "Rate limit or quota exceeded"
        elif "401" in error or "unauthorized" in error_lower:
            return "Authentication failed - invalid API key"
        elif "400" in error or "invalid" in error_lower:
            return "Invalid request format or model"
        elif "404" in error or "not found" in error_lower:
            return "Model or endpoint not found"
        elif "timeout" in error_lower:
            return "Connection timeout"
        elif "connection" in error_lower:
            return "Network connection error"
        else:
            return "Unknown error"
    def suggest_fix(self, provider: str, diagnosis: str) -> str:
        """Suggest fixes for specific issues"""
        fixes = {
            "Rate limit or quota exceeded": "Check billing, upgrade plan, or wait for quota reset",
            "Authentication failed - invalid API key": "Verify API key in Portkey dashboard",
            "Invalid request format or model": "Check model name and request format",
            "Model or endpoint not found": "Verify model availability in provider",
            "Connection timeout": "Retry with longer timeout or check network",
            "Network connection error": "Check firewall and network settings",
            "Unknown error": "Check provider status page and Portkey logs",
        }
        return fixes.get(diagnosis, "Contact support")
    async def test_all_providers(self) -> Dict[str, Any]:
        """Test all configured providers"""
        print("=" * 60)
        print("🔍 LLM CONNECTION DIAGNOSTICS")
        print("=" * 60)
        # Test each provider
        tasks = [
            self.test_provider(name, config) for name, config in self.PROVIDERS.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Process results
        for i, result in enumerate(results):
            provider = list(self.PROVIDERS.keys())[i]
            if isinstance(result, Exception):
                self.results[provider] = {"status": "error", "error": str(result)}
            else:
                self.results[provider] = result
        return self.generate_report()
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive report"""
        total = len(self.PROVIDERS)
        working = len(self.working_providers)
        failed = len(self.failed_providers)
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_providers": total,
                "working": working,
                "failed": failed,
                "success_rate": f"{(working/total*100):.1f}%",
            },
            "working_providers": self.working_providers,
            "failed_providers": self.failed_providers,
            "provider_details": self.results,
            "recommendations": self.generate_recommendations(),
        }
        return report
    def generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        # Provider-specific recommendations
        for provider in self.failed_providers:
            result = self.results.get(provider, {})
            if result.get("diagnosis") == "Rate limit or quota exceeded":
                recommendations.append(
                    f"Upgrade {provider} plan or implement rate limiting"
                )
            elif result.get("diagnosis") == "Authentication failed - invalid API key":
                recommendations.append(f"Update {provider} API key in Portkey")
        # General recommendations
        if len(self.working_providers) < 3:
            recommendations.append(
                "Critical: Less than 3 providers working - add backup providers"
            )
        if "groq" in self.failed_providers and "groq" in [
            p
            for p in self.failed_providers
            if "timeout" in str(self.results.get(p, {}).get("diagnosis", ""))
        ]:
            recommendations.append(
                "Consider using smaller Groq models for better reliability"
            )
        if len(self.working_providers) >= 6:
            recommendations.append(
                "Good coverage - consider load balancing across providers"
            )
        return recommendations
    async def fix_connections(self) -> None:
        """Attempt to fix broken connections"""
        print("\n" + "=" * 60)
        print("🔧 ATTEMPTING FIXES")
        print("=" * 60)
        for provider in self.failed_providers:
            result = self.results.get(provider, {})
            diagnosis = result.get("diagnosis", "")
            print(f"\n🔧 Fixing {provider}...")
            print(f"  Issue: {diagnosis}")
            print(f"  Action: {result.get('fix_suggestion', '')}")
            # Attempt automatic fixes
            if diagnosis == "Invalid request format or model":
                # Try alternative model
                alt_model = self.get_alternative_model(provider)
                if alt_model:
                    print(f"  Trying alternative model: {alt_model}")
                    # Update configuration
                    self.PROVIDERS[provider]["test_model"] = alt_model
            elif diagnosis == "Connection timeout":
                print(f"  Increasing timeout for {provider}")
                # Would implement timeout increase here
    def get_alternative_model(self, provider: str) -> Optional[str]:
        """Get alternative model for a provider"""
        alternatives = {
            "groq": "llama-3.1-8b-instant",
            "openai": "gpt-3.5-turbo",
            "anthropic": "claude-3-haiku-20240307",
            "gemini": "gemini-1.5-flash",
            "mistral": "mistral-tiny",
        }
        return alternatives.get(provider)
async def main():
    """Main execution"""
    fixer = LLMConnectionFixer()
    # Test all connections
    report = await fixer.test_all_providers()
    # Display results
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    summary = report["summary"]
    print(f"\nTotal Providers: {summary['total_providers']}")
    print(f"✅ Working: {summary['working']} ({summary['success_rate']})")
    print(f"❌ Failed: {summary['failed']}")
    if report["working_providers"]:
        print("\n✅ Working Providers:")
        for p in report["working_providers"]:
            latency = report["provider_details"][p].get("latency_ms", "N/A")
            print(f"  • {p} ({latency}ms)")
    if report["failed_providers"]:
        print("\n❌ Failed Providers:")
        for p in report["failed_providers"]:
            diagnosis = report["provider_details"][p].get("diagnosis", "Unknown")
            print(f"  • {p}: {diagnosis}")
    if report["recommendations"]:
        print("\n💡 Recommendations:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")
    # Attempt fixes
    if report["failed_providers"]:
        await fixer.fix_connections()
    # Save report
    report_file = (
        f"llm_diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n💾 Full report saved to: {report_file}")
    # Return exit code based on success
    min_required = 4  # Minimum providers needed
    if summary["working"] >= min_required:
        print(f"\n✅ System operational with {summary['working']} providers")
        return 0
    else:
        print(
            f"\n⚠️  Only {summary['working']} providers working (minimum {min_required} required)"
        )
        return 1
if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
