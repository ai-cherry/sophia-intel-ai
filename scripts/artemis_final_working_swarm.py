#!/usr/bin/env python3
"""
Artemis Final Working Parallel Swarm
Fixed response extraction for all model types
"""

import asyncio
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.aimlapi_config import aimlapi_manager
from app.core.enhanced_llm_router import LLMProviderType, enhanced_router


class ArtemisFinalSwarm:
    """Final working Artemis swarm with proper response extraction"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.results = {}

        # COMPREHENSIVE PROMPT FOR ALL AGENTS
        self.universal_prompt = {
            "system": """You are a specialized agent in the Artemis microswarm analyzing the sophia-intel-ai repository.

COMPREHENSIVE ANALYSIS MISSION:

1. CODE REDUNDANCIES:
   - Duplicate functions/methods
   - Similar code patterns needing abstraction
   - Repeated configuration blocks (300+ logger declarations expected)
   - Redundant imports (2600+ across 500+ files)
   - /app/artemis/ vs /app/sophia/ duplication
   - Base orchestrator class redundancies
   - Factory pattern duplications

2. SECURITY & SECRETS:
   - API key management in /app/core/portkey_config.py (14 virtual keys)
   - AIMLAPI configuration in /app/core/aimlapi_config.py
   - Hardcoded secrets or credentials
   - Environment variable security
   - WebSocket security issues
   - Unprotected API endpoints

3. MEMORY & EMBEDDINGS:
   - Memory systems in /app/memory/
   - Vector database integrations
   - Embedding strategies
   - RAG implementation patterns

4. PERFORMANCE:
   - Connection patterns
   - Performance bottlenecks
   - Caching strategies

Provide SPECIFIC findings with file paths and recommendations.""",
            "user": "Analyze the sophia-intel-ai repository at /Users/lynnmusil/sophia-intel-ai. Cover code redundancies, security issues, memory architecture, and performance. Be specific and actionable.",
        }

    def extract_content(self, response):
        """Extract content from various response types"""
        # Handle OpenAI ChatCompletion objects
        if hasattr(response, "choices"):
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content

        # Handle dict responses
        if isinstance(response, dict):
            if "choices" in response:
                if response["choices"] and len(response["choices"]) > 0:
                    return response["choices"][0]["message"]["content"]

        # Fallback to string representation
        return str(response) if response else "No response received"

    def _run_agent1_gpt(self) -> Dict[str, Any]:
        """Agent 1: GPT-4o-mini (confirmed working)"""
        start_time = time.time()
        agent_name = "GPT-4o-mini"
        model = "gpt-4o-mini"
        print(f"\n🚀 [T+0.0s] Agent 1 STARTING: {agent_name}")

        messages = [
            {"role": "system", "content": self.universal_prompt["system"]},
            {"role": "user", "content": self.universal_prompt["user"]},
        ]

        try:
            response = enhanced_router.create_completion(
                messages=messages,
                model=model,
                provider_type=LLMProviderType.PORTKEY,
                temperature=0.3,
                max_tokens=4000,
            )

            elapsed = time.time() - start_time
            content = self.extract_content(response)
            print(f"✅ [T+{elapsed:.1f}s] Agent 1 COMPLETED - {len(content)} chars")

            return {
                "agent_number": 1,
                "agent_name": agent_name,
                "model": model,
                "provider": "Portkey",
                "execution_time": elapsed,
                "findings": content,
                "response_length": len(content),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ [T+{elapsed:.1f}s] Agent 1 FAILED: {str(e)[:100]}")
            return {
                "agent_number": 1,
                "agent_name": agent_name,
                "execution_time": elapsed,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _run_agent2_deepseek(self) -> Dict[str, Any]:
        """Agent 2: DeepSeek Chat (alternative working model)"""
        start_time = time.time()
        agent_name = "DeepSeek Chat"
        model = "deepseek-chat"
        print(f"\n⚡ [T+0.0s] Agent 2 STARTING: {agent_name}")

        messages = [
            {"role": "system", "content": self.universal_prompt["system"]},
            {"role": "user", "content": self.universal_prompt["user"]},
        ]

        try:
            response = aimlapi_manager.chat_completion(
                model=model, messages=messages, temperature=0.3, max_tokens=4000
            )

            elapsed = time.time() - start_time
            content = self.extract_content(response)
            print(f"✅ [T+{elapsed:.1f}s] Agent 2 COMPLETED - {len(content)} chars")

            return {
                "agent_number": 2,
                "agent_name": agent_name,
                "model": model,
                "provider": "AIMLAPI",
                "execution_time": elapsed,
                "findings": content,
                "response_length": len(content),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ [T+{elapsed:.1f}s] Agent 2 FAILED: {str(e)[:100]}")
            return {
                "agent_number": 2,
                "agent_name": agent_name,
                "execution_time": elapsed,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _run_agent3_gpt_alternative(self) -> Dict[str, Any]:
        """Agent 3: GPT-4o-mini Alternative Instance"""
        start_time = time.time()
        agent_name = "GPT-4o-mini (Agent 3)"
        model = "gpt-4o-mini"
        print(f"\n🔍 [T+0.0s] Agent 3 STARTING: {agent_name}")

        # Slightly different prompt to get varied perspective
        messages = [
            {
                "role": "system",
                "content": self.universal_prompt["system"]
                + "\n\nFocus especially on architectural patterns and scalability issues.",
            },
            {"role": "user", "content": self.universal_prompt["user"]},
        ]

        try:
            response = enhanced_router.create_completion(
                messages=messages,
                model=model,
                provider_type=LLMProviderType.PORTKEY,
                temperature=0.4,  # Slightly higher for variety
                max_tokens=4000,
            )

            elapsed = time.time() - start_time
            content = self.extract_content(response)
            print(f"✅ [T+{elapsed:.1f}s] Agent 3 COMPLETED - {len(content)} chars")

            return {
                "agent_number": 3,
                "agent_name": agent_name,
                "model": model,
                "provider": "Portkey",
                "execution_time": elapsed,
                "findings": content,
                "response_length": len(content),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ [T+{elapsed:.1f}s] Agent 3 FAILED: {str(e)[:100]}")
            return {
                "agent_number": 3,
                "agent_name": agent_name,
                "execution_time": elapsed,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def run_final_swarm(self) -> Dict[str, Any]:
        """Execute all three agents SIMULTANEOUSLY"""
        print("\n" + "=" * 70)
        print(" ARTEMIS FINAL WORKING PARALLEL SWARM")
        print(" 3 Agents Running SIMULTANEOUSLY")
        print("=" * 70)
        print("\n🎯 Mission: Comprehensive Repository Analysis")
        print("📋 All agents receive the same comprehensive prompt")
        print("⚡ Models configured for parallel execution:")
        print("  • Agent 1: GPT-4o-mini (Primary)")
        print("  • Agent 2: DeepSeek Chat (Alternative)")
        print("  • Agent 3: GPT-4o-mini (Secondary)\n")

        start_time = time.time()

        # Launch all agents SIMULTANEOUSLY
        print("🚀 LAUNCHING ALL 3 AGENTS IN PARALLEL...")

        loop = asyncio.get_event_loop()

        # Run all agents in parallel
        tasks = [
            loop.run_in_executor(self.executor, self._run_agent1_gpt),
            loop.run_in_executor(self.executor, self._run_agent2_deepseek),
            loop.run_in_executor(self.executor, self._run_agent3_gpt_alternative),
        ]

        # Wait for all to complete
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # Compile results
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "swarm_type": "Artemis Final Working Parallel Swarm",
            "execution_mode": "PARALLEL - 3 Agents Simultaneously",
            "total_execution_time": total_time,
            "agent_count": 3,
            "agents": results,
        }

        # Save full results
        output_file = f"artemis_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n⏱️  Total Parallel Execution: {total_time:.1f} seconds")
        print(f"💾 Full results saved to {output_file}")

        return self.results


async def main():
    """Main execution with analysis"""
    swarm = ArtemisFinalSwarm()
    results = await swarm.run_final_swarm()

    print("\n" + "=" * 70)
    print(" PARALLEL SWARM ANALYSIS COMPLETE")
    print("=" * 70)

    successful = 0
    failed = 0
    total_findings = 0

    # Display detailed results
    for agent_result in results["agents"]:
        print(f"\n{'='*70}")
        print(f" AGENT {agent_result['agent_number']}: {agent_result.get('agent_name', 'Unknown')}")
        if "model" in agent_result:
            print(f" Model: {agent_result['model']}")
            print(f" Provider: {agent_result.get('provider', 'Unknown')}")
            print(f" Execution Time: {agent_result.get('execution_time', 0):.1f}s")
        print(f"{'='*70}")

        if "error" in agent_result:
            failed += 1
            print(f"❌ Failed: {agent_result['error'][:200]}")
        else:
            successful += 1
            findings = agent_result.get("findings", "")
            response_len = agent_result.get("response_length", len(findings))
            total_findings += response_len

            print("✅ Success")
            print(f"📊 Response: {response_len:,} characters")

            # Show key findings
            if findings and len(findings) > 50:
                print("\n📋 Key Findings Preview:")
                # Extract first substantive paragraph
                lines = findings.split("\n")
                preview = []
                char_count = 0
                for line in lines:
                    if line.strip() and char_count < 400:
                        preview.append(line)
                        char_count += len(line)
                print("\n".join(preview[:5]))

    # Performance Summary
    print("\n" + "=" * 70)
    print(" PERFORMANCE SUMMARY")
    print("=" * 70)

    print("\n📊 Execution Metrics:")
    print(f"  • Success Rate: {successful}/3 agents ({successful/3*100:.0f}%)")
    print(f"  • Total Execution: {results['total_execution_time']:.1f}s")
    print(f"  • Total Analysis: {total_findings:,} characters")

    # Calculate parallel efficiency
    if successful > 0:
        execution_times = [
            a.get("execution_time", 0) for a in results["agents"] if "error" not in a
        ]
        if execution_times:
            sequential_time = sum(execution_times)
            parallel_time = results["total_execution_time"]
            speedup = (
                (sequential_time - parallel_time) / sequential_time * 100
                if sequential_time > 0
                else 0
            )

            print("\n⚡ Parallel Performance:")
            print(f"  • Sequential Time: {sequential_time:.1f}s")
            print(f"  • Parallel Time: {parallel_time:.1f}s")
            print(f"  • Time Saved: {sequential_time - parallel_time:.1f}s")
            print(f"  • Speedup: {speedup:.1f}%")

            print("\n📈 Agent Performance:")
            for agent in results["agents"]:
                if "error" not in agent:
                    efficiency = (
                        agent["response_length"] / agent["execution_time"]
                        if agent["execution_time"] > 0
                        else 0
                    )
                    print(f"  • {agent['agent_name']}: {efficiency:.0f} chars/sec")

    # Final verdict
    print("\n" + "=" * 70)
    if successful == 3:
        print(" ✅ SWARM FULLY OPERATIONAL - ALL AGENTS SUCCEEDED")
    elif successful > 0:
        print(f" ⚠️ PARTIAL SUCCESS - {successful}/3 AGENTS OPERATIONAL")
    else:
        print(" ❌ SWARM FAILURE - NO AGENTS SUCCEEDED")
    print("=" * 70)

    return results


if __name__ == "__main__":
    print("🚀 Initializing Artemis Final Working Swarm...")
    print("📝 Repository: /Users/lynnmusil/sophia-intel-ai")
    print("🎯 Mission: Comprehensive parallel analysis\n")
    results = asyncio.run(main())
