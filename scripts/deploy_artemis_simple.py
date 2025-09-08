#!/usr/bin/env python3
"""
Simple Artemis Swarm Deployment
Tests Portkey connectivity with multiple LLM providers
"""
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment variable for Portkey API key
if not os.environ.get("PORTKEY_API_KEY"):
    raise RuntimeError("PORTKEY_API_KEY is required for this script.")

from portkey_ai import Portkey

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ArtemisSwarmLite:
    """Lightweight Artemis Swarm for testing Portkey connectivity"""

    # Virtual keys for each provider
    VIRTUAL_KEYS = {
        "deepseek": "deepseek-vk-24102f",
        "openai": "openai-vk-190a60",
        "anthropic": "anthropic-vk-b42804",
        "groq": "groq-vk-6b9b52",
        "gemini": "gemini-vk-3d6108",
        "together": "together-ai-670469",
    }

    # Model mappings
    MODELS = {
        "deepseek": "deepseek-chat",
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-haiku-20240307",
        "groq": "llama-3.3-70b-versatile",
        "gemini": "gemini-1.5-flash",
        "together": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    }

    def __init__(self):
        """Initialize the swarm"""
        self.api_key = os.environ.get("PORTKEY_API_KEY")
        if not self.api_key:
            raise ValueError("PORTKEY_API_KEY not found in environment")

        self.clients = {}
        self.results = []
        logger.info(
            f"Initialized Artemis Swarm with {len(self.VIRTUAL_KEYS)} providers"
        )

    def get_client(self, provider: str) -> Portkey:
        """Get or create Portkey client for a provider"""
        if provider not in self.clients:
            vk = self.VIRTUAL_KEYS.get(provider)
            if not vk:
                raise ValueError(f"Unknown provider: {provider}")

            self.clients[provider] = Portkey(api_key=self.api_key, virtual_key=vk)
            logger.info(f"Created client for {provider} with VK: {vk}")

        return self.clients[provider]

    async def test_provider(self, provider: str) -> Dict[str, Any]:
        """Test a single provider"""
        logger.info(f"🧪 Testing provider: {provider}")

        try:
            client = self.get_client(provider)
            model = self.MODELS.get(provider)

            if not model:
                raise ValueError(f"No model configured for {provider}")

            # Simple test message
            messages = [
                {
                    "role": "system",
                    "content": f"You are Artemis-{provider}, part of the Artemis Code Excellence swarm. Respond with a brief greeting and confirm your provider.",
                },
                {
                    "role": "user",
                    "content": "Hello! Please confirm you're working and state your provider name.",
                },
            ]

            # Make the API call (synchronous - Portkey SDK doesn't have async methods)
            start_time = datetime.now()

            # Run sync call in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model=model, messages=messages, max_tokens=100, temperature=0.7
                    ),
                ),
                timeout=30.0,
            )
            end_time = datetime.now()

            # Extract response
            content = (
                response.choices[0].message.content
                if response.choices
                else "No response"
            )

            result = {
                "provider": provider,
                "model": model,
                "status": "success",
                "response": content,
                "latency_ms": int((end_time - start_time).total_seconds() * 1000),
                "timestamp": datetime.now().isoformat(),
            }

            if hasattr(response, "usage") and response.usage:
                result["tokens"] = {
                    "prompt": response.usage.prompt_tokens,
                    "completion": response.usage.completion_tokens,
                    "total": response.usage.total_tokens,
                }

            logger.info(
                f"✅ {provider} responded successfully in {result['latency_ms']}ms"
            )
            return result

        except asyncio.TimeoutError:
            logger.error(f"⏱️ {provider} timed out")
            return {
                "provider": provider,
                "model": self.MODELS.get(provider),
                "status": "timeout",
                "error": "Request timed out after 30 seconds",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"❌ {provider} failed: {e}")
            return {
                "provider": provider,
                "model": self.MODELS.get(provider),
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def test_all_providers(self) -> Dict[str, Any]:
        """Test all providers in parallel"""
        logger.info("🚀 Testing all providers in parallel...")

        # Create tasks for all providers
        tasks = [self.test_provider(provider) for provider in self.VIRTUAL_KEYS.keys()]

        # Run all tests in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for provider, result in zip(self.VIRTUAL_KEYS.keys(), results):
            if isinstance(result, Exception):
                processed_results.append(
                    {
                        "provider": provider,
                        "status": "exception",
                        "error": str(result),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            else:
                processed_results.append(result)

        return {
            "test_name": "Artemis Swarm Connectivity Test",
            "timestamp": datetime.now().isoformat(),
            "providers_tested": len(processed_results),
            "results": processed_results,
            "summary": self._generate_summary(processed_results),
        }

    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate test summary"""
        successful = [r for r in results if r.get("status") == "success"]
        failed = [r for r in results if r.get("status") in ["error", "exception"]]
        timed_out = [r for r in results if r.get("status") == "timeout"]

        total_tokens = sum(r.get("tokens", {}).get("total", 0) for r in successful)

        avg_latency = (
            sum(r.get("latency_ms", 0) for r in successful) / len(successful)
            if successful
            else 0
        )

        return {
            "total_providers": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "timed_out": len(timed_out),
            "success_rate": f"{(len(successful) / len(results) * 100):.1f}%",
            "total_tokens_used": total_tokens,
            "average_latency_ms": int(avg_latency),
            "working_providers": [r["provider"] for r in successful],
            "failed_providers": [r["provider"] for r in failed],
            "timed_out_providers": [r["provider"] for r in timed_out],
        }

    async def collaborative_task(self, task: str) -> Dict[str, Any]:
        """Execute a task using multiple providers collaboratively"""
        logger.info(f"📋 Collaborative task: {task[:100]}...")

        # Select working providers (test first)
        test_results = await self.test_all_providers()
        working_providers = test_results["summary"]["working_providers"]

        if not working_providers:
            return {
                "error": "No working providers available",
                "timestamp": datetime.now().isoformat(),
            }

        logger.info(f"Using {len(working_providers)} working providers")

        # Assign roles to working providers
        roles = {
            "architect": working_providers[0] if len(working_providers) > 0 else None,
            "developer": (
                working_providers[1]
                if len(working_providers) > 1
                else working_providers[0]
            ),
            "reviewer": (
                working_providers[2]
                if len(working_providers) > 2
                else working_providers[0]
            ),
        }

        results = {}

        # Phase 1: Architecture
        if roles["architect"]:
            client = self.get_client(roles["architect"])
            messages = [
                {
                    "role": "system",
                    "content": "You are a system architect. Design a high-level solution.",
                },
                {"role": "user", "content": f"Design architecture for: {task}"},
            ]

            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model=self.MODELS[roles["architect"]],
                        messages=messages,
                        max_tokens=500,
                        temperature=0.7,
                    ),
                )
                results["architecture"] = {
                    "provider": roles["architect"],
                    "response": response.choices[0].message.content,
                }
            except Exception as e:
                results["architecture"] = {"error": str(e)}

        # Phase 2: Implementation
        if roles["developer"] and "architecture" in results:
            client = self.get_client(roles["developer"])
            arch_summary = results["architecture"].get("response", "")[:500]
            messages = [
                {
                    "role": "system",
                    "content": "You are a senior developer. Implement the solution.",
                },
                {
                    "role": "user",
                    "content": f"Implement this architecture:\n{arch_summary}\n\nFor task: {task}",
                },
            ]

            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model=self.MODELS[roles["developer"]],
                        messages=messages,
                        max_tokens=1000,
                        temperature=0.3,
                    ),
                )
                results["implementation"] = {
                    "provider": roles["developer"],
                    "response": response.choices[0].message.content,
                }
            except Exception as e:
                results["implementation"] = {"error": str(e)}

        # Phase 3: Review
        if roles["reviewer"] and "implementation" in results:
            client = self.get_client(roles["reviewer"])
            impl_summary = results["implementation"].get("response", "")[:500]
            messages = [
                {
                    "role": "system",
                    "content": "You are a code reviewer. Review the implementation.",
                },
                {
                    "role": "user",
                    "content": f"Review this implementation:\n{impl_summary}",
                },
            ]

            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model=self.MODELS[roles["reviewer"]],
                        messages=messages,
                        max_tokens=500,
                        temperature=0.5,
                    ),
                )
                results["review"] = {
                    "provider": roles["reviewer"],
                    "response": response.choices[0].message.content,
                }
            except Exception as e:
                results["review"] = {"error": str(e)}

        return {
            "task": task,
            "timestamp": datetime.now().isoformat(),
            "roles_assigned": roles,
            "phases": results,
        }


async def main():
    """Main execution"""
    print("=" * 80)
    print("🚀 ARTEMIS SWARM DEPLOYMENT - PORTKEY CONNECTIVITY TEST")
    print("=" * 80)

    swarm = ArtemisSwarmLite()

    # Phase 1: Test all providers
    print("\n📡 Phase 1: Testing Provider Connectivity")
    print("-" * 40)

    test_results = await swarm.test_all_providers()

    # Display results
    summary = test_results["summary"]
    print("\n📊 Connectivity Results:")
    print(f"  Total Providers: {summary['total_providers']}")
    print(f"  ✅ Successful: {summary['successful']}")
    print(f"  ❌ Failed: {summary['failed']}")
    print(f"  ⏱️ Timed Out: {summary['timed_out']}")
    print(f"  Success Rate: {summary['success_rate']}")
    print(f"  Average Latency: {summary['average_latency_ms']}ms")

    if summary["working_providers"]:
        print("\n✅ Working Providers:")
        for provider in summary["working_providers"]:
            print(f"  • {provider}")

    if summary["failed_providers"]:
        print("\n❌ Failed Providers:")
        for provider in summary["failed_providers"]:
            print(f"  • {provider}")

    # Save detailed results
    output_file = Path(
        f"artemis_connectivity_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w") as f:
        json.dump(test_results, f, indent=2, default=str)

    print(f"\n💾 Detailed results saved to: {output_file}")

    # Phase 2: Collaborative Task (if providers are working)
    if summary["successful"] >= 2:
        print("\n" + "=" * 80)
        print("📋 Phase 2: Collaborative Task Execution")
        print("-" * 40)

        test_task = "Create a Python function to validate email addresses with comprehensive error handling"

        print(f"\nTask: {test_task}")
        print("\n⏳ Executing collaborative task...")

        collab_result = await swarm.collaborative_task(test_task)

        if "error" not in collab_result:
            print("\n✅ Collaborative task completed!")
            print("\nRoles Assigned:")
            for role, provider in collab_result["roles_assigned"].items():
                print(f"  • {role}: {provider}")

            # Save collaborative results
            collab_file = Path(
                f"artemis_collaborative_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(collab_file, "w") as f:
                json.dump(collab_result, f, indent=2, default=str)

            print(f"\n💾 Collaborative results saved to: {collab_file}")
        else:
            print(f"\n❌ Collaborative task failed: {collab_result['error']}")
    else:
        print("\n⚠️ Insufficient working providers for collaborative task")

    print("\n" + "=" * 80)
    print("✅ ARTEMIS SWARM DEPLOYMENT TEST COMPLETE!")
    print("=" * 80)

    # Return success code based on results
    return 0 if summary["successful"] > 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
