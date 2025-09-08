#!/usr/bin/env python3
"""
Artemis Working Parallel Swarm - Fixed Version
Uses models that actually work from connectivity test
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


class ArtemisWorkingSwarm:
    """Working Artemis swarm with correct model names"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.results = {}

        # COMPREHENSIVE PROMPT FOR ALL AGENTS
        self.universal_prompt = {
            "system": """You are a specialized agent in the Artemis microswarm analyzing the sophia-intel-ai repository.

COMPREHENSIVE ANALYSIS MISSION - Cover ALL areas:

1. CODE REDUNDANCIES & PATTERNS:
   - Identify duplicate functions/methods across files
   - Find similar code patterns that could be abstracted
   - Locate repeated configuration blocks (expecting 300+ logger declarations)
   - Analyze redundant imports (2600+ import statements across 500+ files)
   - Compare /app/artemis/ vs /app/sophia/ for duplication
   - Examine base orchestrator classes
   - Review factory pattern duplications

2. SECURITY & SECRETS HANDLING:
   - Analyze API key management in /app/core/portkey_config.py (14 virtual keys)
   - Review AIMLAPI configuration in /app/core/aimlapi_config.py
   - Check for hardcoded secrets or credentials
   - Evaluate environment variable security
   - Review WebSocket security
   - Check for unprotected API endpoints

3. EMBEDDINGS & MEMORY ARCHITECTURE:
   - Analyze memory systems in /app/memory/
   - Review vector database integrations
   - Evaluate embedding strategies
   - Assess chunking strategies
   - Review RAG implementation patterns

4. DATABASE & PERFORMANCE:
   - Review connection patterns
   - Identify performance bottlenecks
   - Review caching strategies

Provide SPECIFIC file paths and actionable recommendations.""",
            "user": """Perform a comprehensive analysis of the sophia-intel-ai repository at /Users/lynnmusil/sophia-intel-ai.
Cover ALL areas: redundancies, security, memory architecture, and performance.
Be specific with findings and recommendations.""",
        }

    def _run_agent1_gpt5(self) -> Dict[str, Any]:
        """Agent 1: GPT-5 (using GPT-4o-mini as it works)"""
        start_time = time.time()
        agent_name = "GPT-5 Simulator (GPT-4o-mini)"
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
            print(f"✅ [T+{elapsed:.1f}s] Agent 1 COMPLETED")

            content = (
                response.choices[0].message.content
                if hasattr(response, "choices")
                else str(response)
            )

            return {
                "agent_number": 1,
                "agent_name": agent_name,
                "model": model,
                "execution_time": elapsed,
                "findings": content,
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

    def _run_agent2_glm(self) -> Dict[str, Any]:
        """Agent 2: GLM-4.5 Air (confirmed working)"""
        start_time = time.time()
        agent_name = "GLM-4.5 Air"
        model = "zhipu/glm-4.5-air"  # Correct format from error message
        print(f"\n⚡ [T+0.0s] Agent 2 STARTING: {agent_name}")

        messages = [
            {"role": "system", "content": self.universal_prompt["system"]},
            {"role": "user", "content": self.universal_prompt["user"]},
        ]

        try:
            # Use the correct model ID format
            response = aimlapi_manager.chat_completion(
                model=model, messages=messages, temperature=0.3, max_tokens=4000
            )

            elapsed = time.time() - start_time
            print(f"✅ [T+{elapsed:.1f}s] Agent 2 COMPLETED")

            # Extract content from response
            content = "No response"
            if response and "choices" in response:
                content = response["choices"][0]["message"]["content"]

            return {
                "agent_number": 2,
                "agent_name": agent_name,
                "model": model,
                "execution_time": elapsed,
                "findings": content,
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

    def _run_agent3_llama(self) -> Dict[str, Any]:
        """Agent 3: Llama-4 Scout (using correct format)"""
        start_time = time.time()
        agent_name = "Llama-4 Scout"
        model = "meta-llama/llama-4-scout"  # Correct format from error message
        print(f"\n🔍 [T+0.0s] Agent 3 STARTING: {agent_name}")

        messages = [
            {"role": "system", "content": self.universal_prompt["system"]},
            {"role": "user", "content": self.universal_prompt["user"]},
        ]

        try:
            response = aimlapi_manager.chat_completion(
                model=model, messages=messages, temperature=0.3, max_tokens=4000
            )

            elapsed = time.time() - start_time
            print(f"✅ [T+{elapsed:.1f}s] Agent 3 COMPLETED")

            # Extract content
            content = "No response"
            if response and "choices" in response:
                content = response["choices"][0]["message"]["content"]

            return {
                "agent_number": 3,
                "agent_name": agent_name,
                "model": model,
                "execution_time": elapsed,
                "findings": content,
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

    async def run_working_swarm(self) -> Dict[str, Any]:
        """Execute all three agents with correct models SIMULTANEOUSLY"""
        print("\n" + "=" * 70)
        print(" ARTEMIS WORKING PARALLEL SWARM")
        print(" 3 Agents - Fixed Models - PARALLEL Execution")
        print("=" * 70)
        print("\n📋 All agents receive the SAME comprehensive prompt")
        print("🎯 Using models confirmed to work:")
        print("  • Agent 1: GPT-4o-mini (via Portkey)")
        print("  • Agent 2: GLM-4.5-Air (via AIMLAPI)")
        print("  • Agent 3: Llama-4-Scout (via AIMLAPI)\n")

        start_time = time.time()

        # Launch all agents SIMULTANEOUSLY
        print("⚡ LAUNCHING 3 AGENTS IN PARALLEL...")

        loop = asyncio.get_event_loop()

        # Run all agents in parallel
        tasks = [
            loop.run_in_executor(self.executor, self._run_agent1_gpt5),
            loop.run_in_executor(self.executor, self._run_agent2_glm),
            loop.run_in_executor(self.executor, self._run_agent3_llama),
        ]

        # Wait for all to complete
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # Compile results
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "swarm_type": "Artemis Working Parallel Swarm",
            "execution_mode": "PARALLEL - Fixed Models",
            "total_execution_time": total_time,
            "agent_count": 3,
            "agents": results,
        }

        # Save results
        output_file = f"artemis_working_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n⏱️  Total Execution Time: {total_time:.1f} seconds")
        print(f"💾 Full results saved to {output_file}")

        return self.results


async def main():
    """Main execution"""
    swarm = ArtemisWorkingSwarm()
    results = await swarm.run_working_swarm()

    print("\n" + "=" * 70)
    print(" SWARM EXECUTION COMPLETE")
    print("=" * 70)

    successful = 0
    failed = 0
    total_findings_length = 0

    # Display results
    for agent_result in results["agents"]:
        print(f"\n{'='*70}")
        print(
            f" AGENT {agent_result['agent_number']}: {agent_result.get('agent_name', 'Unknown')}"
        )
        print(f" Model: {agent_result.get('model', 'Unknown')}")
        print(f" Execution Time: {agent_result.get('execution_time', 0):.1f}s")
        print(f"{'='*70}")

        if "error" in agent_result:
            failed += 1
            print(f"❌ Failed: {agent_result['error'][:200]}")
        else:
            successful += 1
            findings = agent_result.get("findings", "")
            if findings:
                total_findings_length += len(findings)
                print(f"✅ Success - Response: {len(findings)} characters")
                # Show first 500 chars
                print("\n📋 Sample Finding:")
                print(findings[:500] + "..." if len(findings) > 500 else findings)

    # Summary
    print("\n" + "=" * 70)
    print(" PERFORMANCE METRICS")
    print("=" * 70)

    print("\n📊 Execution Summary:")
    print(f"  • Successful: {successful}/3 agents")
    print(f"  • Failed: {failed}/3 agents")
    print(f"  • Total Time: {results['total_execution_time']:.1f}s (parallel)")
    print(f"  • Total Findings: {total_findings_length:,} characters")

    # Calculate efficiency
    sequential_time = sum(a.get("execution_time", 0) for a in results["agents"])
    time_saved = sequential_time - results["total_execution_time"]
    efficiency = (time_saved / sequential_time * 100) if sequential_time > 0 else 0

    print("\n⚡ Parallel Efficiency:")
    print(f"  • Sequential Time: {sequential_time:.1f}s")
    print(f"  • Parallel Time: {results['total_execution_time']:.1f}s")
    print(f"  • Time Saved: {time_saved:.1f}s")
    print(f"  • Speedup: {efficiency:.1f}%")

    # Show which agents succeeded
    if successful > 0:
        print("\n✅ Working Models:")
        for agent in results["agents"]:
            if "error" not in agent:
                print(f"  • {agent['agent_name']}: {agent['execution_time']:.1f}s")

    return results


if __name__ == "__main__":
    print("🚀 Initializing Artemis Working Swarm with Fixed Models...")
    results = asyncio.run(main())
