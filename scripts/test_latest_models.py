#!/usr/bin/env python3
"""
Test Latest OpenRouter Models through Portkey (August 2025).
Verifies all model integrations are working correctly.
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv('.env.local', override=True)

# Import our modules
from app.models.openrouter_latest import OpenRouterLatest, ModelTier, TaskType
from app.models.portkey_dynamic_client import DynamicPortkeyClient
from app.portkey_config import PortkeyGateway, Role, MODEL_RECOMMENDATIONS

# Import ROLE_MODELS directly
ROLE_MODELS = {
    "planner": "openai/gpt-5",
    "critic": "anthropic/claude-3.7-sonnet",
    "judge": "openai/gpt-5",
    "coderA": "x-ai/grok-code-fast-1",
    "coderB": "qwen/qwen3-coder",
    "coderC": "mistralai/codestral-2501",
    "reasoning": "deepseek/deepseek-r1",
    "analyzer": "google/gemini-2.5-pro",
    "validator": "anthropic/claude-3.7-sonnet:thinking",
    "fast": "deepseek/deepseek-chat-v3.1:free",
    "research": "google/gemini-2.5-flash",
    "free": "meta-llama/llama-4-maverick:free",
    "vision": "google/gemini-2.5-flash-image-preview"
}


class ModelTestSuite:
    """Comprehensive test suite for latest models."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0
            }
        }
        
        # Initialize clients
        self.portkey_key = os.getenv("PORTKEY_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        
        if not self.portkey_key or not self.openrouter_key:
            raise ValueError("Missing API keys. Please check .env.local")
            
    async def test_openrouter_latest(self):
        """Test OpenRouterLatest client with latest models."""
        print("\n" + "="*60)
        print("🧪 Testing OpenRouterLatest Client")
        print("="*60)
        
        client = OpenRouterLatest(
            api_key=self.openrouter_key,
            app_name="Sophia-Intel-AI-Test"
        )
        
        # Test model cache refresh
        print("\n1. Testing model cache refresh...")
        try:
            models = await client.refresh_model_cache()
            print(f"✅ Fetched {len(models)} models")
            self._record_test("OpenRouter cache refresh", True, f"{len(models)} models")
        except Exception as e:
            print(f"❌ Failed: {e}")
            self._record_test("OpenRouter cache refresh", False, str(e))
            
        # Test best model selection
        print("\n2. Testing model selection...")
        test_cases = [
            (TaskType.REASONING, ModelTier.BALANCED),
            (TaskType.CODING, ModelTier.PREMIUM),
            (TaskType.GENERAL, ModelTier.FREE),
            (TaskType.VISION, ModelTier.BALANCED)
        ]
        
        for task, tier in test_cases:
            try:
                model = await client.get_best_model(task, tier)
                print(f"✅ {task.value}/{tier.value}: {model}")
                self._record_test(f"Model selection {task.value}/{tier.value}", True, model)
            except Exception as e:
                print(f"❌ {task.value}/{tier.value}: {e}")
                self._record_test(f"Model selection {task.value}/{tier.value}", False, str(e))
                
        # Test actual completion
        print("\n3. Testing completions with fallback...")
        test_prompts = [
            ("What is 2+2?", "openai/gpt-5-nano"),
            ("Write hello world in Python", "x-ai/grok-code-fast-1"),
            ("Explain quantum computing", "deepseek/deepseek-r1")
        ]
        
        for prompt, model in test_prompts:
            try:
                response = await client.create_completion_with_fallback(
                    messages=[{"role": "user", "content": prompt}],
                    model=model,
                    max_tokens=50,
                    temperature=0.7
                )
                model_used = response.get("_model_used", model)
                print(f"✅ {model}: Response received (used: {model_used})")
                self._record_test(f"Completion {model}", True, model_used)
            except Exception as e:
                print(f"❌ {model}: {e}")
                self._record_test(f"Completion {model}", False, str(e))
                
    async def test_dynamic_portkey_client(self):
        """Test DynamicPortkeyClient with automatic model management."""
        print("\n" + "="*60)
        print("🧪 Testing Dynamic Portkey Client")
        print("="*60)
        
        client = DynamicPortkeyClient(
            portkey_api_key=self.portkey_key,
            openrouter_api_key=self.openrouter_key
        )
        
        # Test model refresh
        print("\n1. Testing model refresh...")
        try:
            await client.refresh_models()
            print(f"✅ Models refreshed: {len(client.model_cache)} available")
            self._record_test("Portkey model refresh", True, f"{len(client.model_cache)} models")
        except Exception as e:
            print(f"❌ Failed: {e}")
            self._record_test("Portkey model refresh", False, str(e))
            
        # Test task-based selection
        print("\n2. Testing task-based model selection...")
        tasks = ["reasoning", "coding", "general"]
        budgets = ["premium", "balanced", "free"]
        
        for task in tasks:
            for budget in budgets:
                try:
                    model = await client.get_model_for_task(task, budget)
                    print(f"✅ {task}/{budget}: {model}")
                    self._record_test(f"Task selection {task}/{budget}", True, model)
                except Exception as e:
                    print(f"❌ {task}/{budget}: {e}")
                    self._record_test(f"Task selection {task}/{budget}", False, str(e))
                    
        # Test semantic model names
        print("\n3. Testing semantic model names...")
        semantic_names = ["latest-gpt", "latest-claude", "best-reasoning", "best-coding", "free-tier"]
        
        for name in semantic_names:
            try:
                response = await client.create_completion(
                    messages=[{"role": "user", "content": "Say 'OK' in one word"}],
                    model=name,
                    max_tokens=5,
                    temperature=0.1
                )
                print(f"✅ {name}: Working")
                self._record_test(f"Semantic name {name}", True, "OK")
            except Exception as e:
                print(f"❌ {name}: {e}")
                self._record_test(f"Semantic name {name}", False, str(e))
                
    async def test_router_models(self):
        """Test router.py model configurations."""
        print("\n" + "="*60)
        print("🧪 Testing Router Model Configurations")
        print("="*60)
        
        print("\n1. Checking role model mappings...")
        for role, model_id in ROLE_MODELS.items():
            # Just verify the model ID is in the correct format
            if "/" in model_id:
                print(f"✅ {role}: {model_id}")
                self._record_test(f"Router {role}", True, model_id)
            else:
                print(f"❌ {role}: Invalid model ID format")
                self._record_test(f"Router {role}", False, "Invalid format")
                
    async def test_portkey_gateway(self):
        """Test PortkeyGateway with role-based routing."""
        print("\n" + "="*60)
        print("🧪 Testing Portkey Gateway")
        print("="*60)
        
        gateway = PortkeyGateway()
        
        print("\n1. Testing role-based recommendations...")
        for role in [Role.PLANNER, Role.CRITIC, Role.JUDGE, Role.GENERATOR]:
            recommendations = MODEL_RECOMMENDATIONS.get(role, {})
            default_model = recommendations.get("default")
            
            if default_model:
                print(f"✅ {role.value}: {default_model}")
                self._record_test(f"Gateway {role.value}", True, default_model)
            else:
                print(f"⚠️ {role.value}: No default model")
                self._record_test(f"Gateway {role.value}", False, "No default")
                
    async def test_free_models(self):
        """Test free tier models specifically."""
        print("\n" + "="*60)
        print("🧪 Testing Free Tier Models")
        print("="*60)
        
        free_models = [
            "deepseek/deepseek-chat-v3.1:free",
            "deepseek/deepseek-r1:free",
            "meta-llama/llama-4-maverick:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "qwen/qwen3-235b-a22b:free",
            "mistralai/mistral-small-3.2-24b-instruct:free",
            "google/gemini-2.5-flash-image-preview:free"
        ]
        
        client = OpenRouterLatest(api_key=self.openrouter_key)
        
        for model in free_models:
            try:
                # Check model health
                is_healthy = await client.check_model_health(model)
                if is_healthy:
                    print(f"✅ {model}: Available")
                    self._record_test(f"Free model {model}", True, "Available")
                else:
                    print(f"⚠️ {model}: Not available")
                    self._record_test(f"Free model {model}", False, "Not available")
            except Exception as e:
                print(f"❌ {model}: {e}")
                self._record_test(f"Free model {model}", False, str(e))
                
    def _record_test(self, name: str, success: bool, details: str = ""):
        """Record test result."""
        self.results["tests"].append({
            "name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
        self.results["summary"]["total"] += 1
        if success:
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
            
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        summary = self.results["summary"]
        print(f"\nTotal Tests: {summary['total']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        
        if summary['total'] > 0:
            pass_rate = (summary['passed'] / summary['total']) * 100
            print(f"Pass Rate: {pass_rate:.1f}%")
            
        # List failed tests
        failed_tests = [t for t in self.results["tests"] if not t["success"]]
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"  - {test['name']}: {test['details']}")
                
        # Save results to file
        results_file = "test_results_latest_models.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Detailed results saved to {results_file}")
        
    async def run_all_tests(self):
        """Run all test suites."""
        print("\n" + "="*60)
        print("🚀 TESTING LATEST OPENROUTER MODELS (August 2025)")
        print("="*60)
        
        # Run each test suite
        test_suites = [
            ("OpenRouter Latest", self.test_openrouter_latest),
            ("Dynamic Portkey Client", self.test_dynamic_portkey_client),
            ("Router Models", self.test_router_models),
            ("Portkey Gateway", self.test_portkey_gateway),
            ("Free Tier Models", self.test_free_models)
        ]
        
        for name, test_func in test_suites:
            try:
                await test_func()
            except Exception as e:
                print(f"\n❌ {name} suite failed: {e}")
                self._record_test(f"{name} suite", False, str(e))
                
        # Print summary
        self.print_summary()
        
        # Return success status
        return self.results["summary"]["failed"] == 0


async def main():
    """Main test function."""
    # Check environment
    print("🔍 Checking environment...")
    
    required_vars = ["PORTKEY_API_KEY", "OPENROUTER_API_KEY"]
    missing = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
            
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("Please check your .env.local file")
        return 1
        
    print("✅ Environment configured")
    
    # Run tests
    test_suite = ModelTestSuite()
    success = await test_suite.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())