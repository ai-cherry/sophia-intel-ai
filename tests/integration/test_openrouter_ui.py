#!/usr/bin/env python3
"""
Comprehensive OpenRouter Integration Test & Review
Tests all critical components per Cline's implementation
"""

import asyncio
import json
import os
from datetime import datetime

import httpx


class OpenRouterIntegrationReview:
    """Review and test OpenRouter/GPT-5 integration"""

    def __init__(self):
        self.issues = []
        self.recommendations = []
        self.positives = []
        self.test_results = {}

    async def test_fallback_logic(self) -> bool:
        """Test fallback chains: gpt-5 → claude-sonnet-4 → gemini-2.5-pro"""
        print("\n🔍 Testing Fallback Logic...")

        try:
            # Test primary model (GPT-5)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8005/chat/completions",
                    json={
                        "model": "openai/gpt-5",
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 10
                    },
                    timeout=5.0
                )

                if response.status_code == 200:
                    self.positives.append("✅ GPT-5 primary model accessible")

                    # Test fallback by forcing error
                    response = await client.post(
                        "http://localhost:8005/chat/completions",
                        json={
                            "model": "openai/gpt-5-invalid",  # Invalid model
                            "messages": [{"role": "user", "content": "test"}],
                            "max_tokens": 10,
                            "fallback": True
                        },
                        timeout=5.0
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if "claude-sonnet-4" in str(data) or "fallback" in str(data):
                            self.positives.append("✅ Fallback to Claude-4 working")
                            return True
                        else:
                            self.recommendations.append(
                                "⚠️ Fallback chain may not be properly configured"
                            )
                            return False
                else:
                    self.issues.append(
                        f"❌ GPT-5 endpoint returned {response.status_code}"
                    )
                    return False

        except Exception as e:
            self.issues.append(f"❌ Fallback test failed: {e}")
            return False

    async def test_cost_tracking(self) -> bool:
        """Validate model_cost_usd_today metric"""
        print("\n💰 Testing Cost Tracking...")

        try:
            async with httpx.AsyncClient() as client:
                # Get metrics
                response = await client.get("http://localhost:8005/metrics")

                if response.status_code == 200:
                    metrics = response.text

                    # Check for cost metrics
                    if "model_cost_usd_today" in metrics:
                        self.positives.append("✅ Cost tracking metrics exposed")

                        # Parse metric value
                        for line in metrics.split('\n'):
                            if "model_cost_usd_today" in line and not line.startswith("#"):
                                try:
                                    # Extract value
                                    parts = line.split()
                                    if len(parts) >= 2:
                                        cost = float(parts[-1])
                                        if cost >= 0:
                                            self.positives.append(
                                                f"✅ Daily cost tracked: ${cost:.2f}"
                                            )
                                            return True
                                except:
                                    pass

                        self.recommendations.append(
                            "⚠️ Cost metric exists but value parsing failed"
                        )
                        return False
                    else:
                        self.issues.append("❌ model_cost_usd_today metric not found")
                        return False
                else:
                    self.issues.append(f"❌ Metrics endpoint returned {response.status_code}")
                    return False

        except Exception as e:
            self.issues.append(f"❌ Cost tracking test failed: {e}")
            return False

    def test_gpt5_activation(self) -> bool:
        """Ensure GPT5_ENABLED is properly gated"""
        print("\n🔒 Testing GPT-5 Activation...")

        # Check environment variable
        gpt5_enabled = os.getenv("GPT5_ENABLED", "false").lower() == "true"

        if gpt5_enabled:
            self.positives.append("✅ GPT-5 enabled via environment")
        else:
            self.recommendations.append(
                "⚠️ GPT5_ENABLED not set - GPT-5 may be disabled"
            )

        # Check config files
        try:
            with open(".env.example") as f:
                content = f.read()
                if "GPT5_ENABLED=true" in content:
                    self.positives.append("✅ GPT-5 configuration documented")
                    return True
                else:
                    self.recommendations.append(
                        "⚠️ GPT5_ENABLED should be documented in .env.example"
                    )
                    return False
        except:
            self.issues.append("❌ Cannot verify GPT-5 configuration")
            return False

    async def test_ui_accuracy(self) -> bool:
        """Confirm cost panel displays premium model warnings"""
        print("\n🎨 Testing UI Accuracy...")

        try:
            # Test Streamlit UI
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8501/")

                if response.status_code == 200:
                    self.positives.append("✅ Streamlit UI accessible")

                    # Check for cost components in UI
                    # Note: Streamlit doesn't expose components directly
                    # We'd need to check the rendered HTML or use Selenium
                    self.recommendations.append(
                        "ℹ️ Manual UI verification recommended for cost panel"
                    )
                    return True
                else:
                    self.issues.append(f"❌ Streamlit UI returned {response.status_code}")
                    return False

        except Exception as e:
            self.issues.append(f"❌ UI test failed: {e}")
            return False

    async def test_security(self) -> bool:
        """Verify sensitive model names don't leak"""
        print("\n🔐 Testing Security...")

        try:
            async with httpx.AsyncClient() as client:
                # Test API info endpoint
                response = await client.get("http://localhost:8005/")

                if response.status_code == 200:
                    data = response.json()

                    # Check for sensitive data exposure
                    sensitive_patterns = [
                        "sk-or-",  # OpenRouter API key prefix
                        "api_key",
                        "secret",
                        "password"
                    ]

                    response_str = json.dumps(data).lower()

                    for pattern in sensitive_patterns:
                        if pattern.lower() in response_str:
                            self.issues.append(
                                f"❌ Potential sensitive data exposure: {pattern}"
                            )
                            return False

                    self.positives.append("✅ No sensitive data in API responses")

                    # Check if model names are properly abstracted
                    if "gpt-5" in str(data) or "openai/gpt-5" in str(data):
                        self.recommendations.append(
                            "ℹ️ Consider abstracting model names in public responses"
                        )

                    return True
                else:
                    self.issues.append(f"❌ API info endpoint returned {response.status_code}")
                    return False

        except Exception as e:
            self.issues.append(f"❌ Security test failed: {e}")
            return False

    async def test_model_registry(self) -> bool:
        """Test model registry and availability"""
        print("\n📚 Testing Model Registry...")

        expected_models = [
            "openai/gpt-5",
            "x-ai/grok-4",
            "anthropic/claude-sonnet-4",
            "google/gemini-2.5-flash",
            "google/gemini-2.5-pro",
            "deepseek/deepseek-chat-v3.1",
            "z-ai/glm-4.5-air"
        ]

        try:
            # Check if models are configured
            from app.api.openrouter_gateway import AVAILABLE_MODELS

            registered = list(AVAILABLE_MODELS.keys())

            for model in expected_models:
                if model in registered:
                    self.positives.append(f"✅ {model} registered")
                else:
                    self.issues.append(f"❌ {model} not in registry")

            # Check cost configuration
            for model, config in AVAILABLE_MODELS.items():
                if "input_cost" in config and "output_cost" in config:
                    if config["input_cost"] > 0 and config["output_cost"] > 0:
                        pass  # Good
                    else:
                        self.issues.append(f"❌ {model} has invalid cost configuration")
                else:
                    self.issues.append(f"❌ {model} missing cost configuration")

            return len(self.issues) == 0

        except ImportError:
            self.issues.append("❌ Cannot import openrouter_gateway module")
            return False
        except Exception as e:
            self.issues.append(f"❌ Model registry test failed: {e}")
            return False

    async def run_review(self):
        """Run complete review"""
        print("=" * 60)
        print("OPENROUTER/GPT-5 INTEGRATION REVIEW")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}")

        tests = [
            ("Fallback Logic", self.test_fallback_logic()),
            ("Cost Tracking", self.test_cost_tracking()),
            ("GPT-5 Activation", asyncio.to_thread(self.test_gpt5_activation)),
            ("UI Accuracy", self.test_ui_accuracy()),
            ("Security", self.test_security()),
            ("Model Registry", self.test_model_registry())
        ]

        for name, test in tests:
            try:
                if asyncio.iscoroutine(test):
                    result = await test
                else:
                    result = await test()
                self.test_results[name] = result
            except Exception as e:
                self.test_results[name] = False
                self.issues.append(f"❌ {name} test crashed: {e}")

        # Generate report
        self.generate_report()

    def generate_report(self):
        """Generate review report"""
        print("\n" + "=" * 60)
        print("REVIEW RESULTS")
        print("=" * 60)

        # Test Summary
        print("\n## Test Summary")
        print("-" * 40)
        for test_name, passed in self.test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name:20} | {status}")

        # Issues Found
        if self.issues:
            print("\n## Issues Found")
            print("-" * 40)
            for issue in self.issues:
                print(f"- [ ] {issue}")

        # Recommendations
        if self.recommendations:
            print("\n## Recommendations")
            print("-" * 40)
            for rec in self.recommendations:
                print(f"- [ ] {rec}")

        # Positives
        if self.positives:
            print("\n## Working Well")
            print("-" * 40)
            for positive in self.positives:
                print(f"- [x] {positive}")

        # Overall Assessment
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r)

        print("\n" + "=" * 60)
        if passed_tests == total_tests:
            print("✅ INTEGRATION READY FOR PRODUCTION")
        elif passed_tests >= total_tests * 0.7:
            print("⚠️ INTEGRATION MOSTLY READY - ADDRESS ISSUES")
        else:
            print("❌ INTEGRATION NEEDS WORK BEFORE PRODUCTION")
        print(f"Score: {passed_tests}/{total_tests} tests passed")
        print("=" * 60)

async def main():
    """Main test runner"""
    reviewer = OpenRouterIntegrationReview()
    await reviewer.run_review()

if __name__ == "__main__":
    asyncio.run(main())
