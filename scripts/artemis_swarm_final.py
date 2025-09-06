#!/usr/bin/env python3
"""
Artemis Parallel Microswarm - Final Version
3 specialized agents running SIMULTANEOUSLY with proper Artemis factory integration
"""

import asyncio
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.artemis.unified_factory import ArtemisUnifiedFactory
from app.core.aimlapi_config import aimlapi_manager
from app.core.enhanced_llm_router import LLMProviderType, enhanced_router


class ArtemisParallelSwarm:
    """Artemis parallel microswarm with proper factory integration"""

    def __init__(self):
        self.factory = ArtemisUnifiedFactory()
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.results = {}

    def _run_agent1_sync(self) -> Dict[str, Any]:
        """Agent 1: Grok Code Fast 1 - Synchronous execution"""
        start_time = time.time()
        print("\n🚀 [T+0.0s] Agent 1 STARTING: Grok Code Fast 1 - Redundancy Scanner")

        messages = [
            {
                "role": "system",
                "content": """You are Agent 1 of Artemis microswarm using Grok Code Fast 1.
MISSION: Deep redundancy analysis of sophia-intel-ai repository.

CRITICAL SCAN TARGETS:
1. Orchestrator Redundancies:
   - /app/orchestrators/base_orchestrator.py vs unified_base.py (200+ lines duplication)
   - ExecutionPriority, TaskStatus classes duplicated
   - OrchestratorConfig patterns repeated 20+ times

2. Factory Redundancies:
   - /app/sophia/unified_factory.py vs /app/artemis/unified_factory.py
   - 6+ factory implementations with 70% overlap
   - Agent configuration patterns duplicated

3. Import Redundancies:
   - 2,600+ redundant import statements
   - 322 logger declarations identical
   - FastAPI/Pydantic imports repeated 20+ times

4. Configuration Redundancies:
   - 20+ similar *Config classes
   - Duplicate environment variables
   - Repeated max_concurrent_tasks = 8

Provide SPECIFIC file:line references and consolidation recommendations.""",
            },
            {
                "role": "user",
                "content": "Scan /Users/lynnmusil/sophia-intel-ai for redundancies. Focus on patterns appearing 3+ times. Be specific with file paths and line numbers.",
            },
        ]

        try:
            # Use AIMLAPI manager directly (synchronous)
            response = aimlapi_manager.chat_completion(
                model="grok-code-fast-1", messages=messages, temperature=0.3, max_tokens=32768
            )

            elapsed = time.time() - start_time
            print(f"✅ [T+{elapsed:.1f}s] Agent 1 COMPLETED")

            content = (
                response.get("choices", [{}])[0].get("message", {}).get("content", "No response")
            )

            return {
                "agent": "Grok Code Fast 1 (92 tokens/sec)",
                "focus": "Redundancies & Code Patterns",
                "execution_time": elapsed,
                "findings": content,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ [T+{elapsed:.1f}s] Agent 1 FAILED: {str(e)[:100]}")
            return {
                "agent": "Grok Code Fast 1",
                "focus": "Redundancies & Code Patterns",
                "execution_time": elapsed,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _run_agent2_sync(self) -> Dict[str, Any]:
        """Agent 2: Gemini Flash via factory - Synchronous execution"""
        start_time = time.time()
        print("\n🔒 [T+0.0s] Agent 2 STARTING: Gemini Flash - Security Analyzer")

        messages = [
            {
                "role": "system",
                "content": """You are Agent 2 of Artemis microswarm.
MISSION: Security and secrets analysis of sophia-intel-ai.

CRITICAL SECURITY SCAN:
1. API Key Exposure:
   - 14 Portkey virtual keys in portkey_config.py
   - AIMLAPI key in aimlapi_config.py
   - Check for hardcoded keys
   - Environment variable security

2. Authentication Gaps:
   - Unprotected WebSocket endpoints
   - Missing auth on API routes
   - Session management issues
   - Token validation problems

3. Security Vulnerabilities:
   - SQL injection risks
   - XSS vulnerabilities
   - CORS misconfigurations
   - Insecure direct object references

4. Critical Files:
   - /app/core/portkey_config.py (VK keys)
   - /app/core/aimlapi_config.py (API key)
   - /app/api/routes/*.py (endpoints)
   - WebSocket handlers

Identify SPECIFIC vulnerabilities with remediation steps.""",
            },
            {
                "role": "user",
                "content": "Analyze all security aspects in /Users/lynnmusil/sophia-intel-ai. Focus on API keys, authentication, and vulnerabilities.",
            },
        ]

        try:
            # Use factory's execute_with_agent
            response = self.factory.execute_with_agent(
                agent_name="security_analyst",
                messages=messages,
                model_override="gpt-4o-mini",  # Fallback since Gemini might not work
            )

            elapsed = time.time() - start_time
            print(f"✅ [T+{elapsed:.1f}s] Agent 2 COMPLETED")

            content = (
                response.choices[0].message.content
                if hasattr(response, "choices")
                else str(response)
            )

            return {
                "agent": "Security Analyst (Factory)",
                "focus": "Security & Secrets Handling",
                "execution_time": elapsed,
                "findings": content,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ [T+{elapsed:.1f}s] Agent 2 FAILED: {str(e)[:100]}")
            return {
                "agent": "Security Analyst",
                "focus": "Security & Secrets Handling",
                "execution_time": elapsed,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _run_agent3_sync(self) -> Dict[str, Any]:
        """Agent 3: Llama Scout - Synchronous execution"""
        start_time = time.time()
        print("\n🧠 [T+0.0s] Agent 3 STARTING: Llama-4 Scout - Data Architecture")

        messages = [
            {
                "role": "system",
                "content": """You are Agent 3 of Artemis microswarm using Llama-4 Scout.
MISSION: Data architecture analysis of sophia-intel-ai.

CRITICAL DATA SCAN:
1. Memory Systems Analysis:
   - /app/memory/unified_memory.py architecture
   - Memory manager patterns
   - Redis integration (if exists)
   - Context window optimization
   - Conversation history storage

2. Embedding Infrastructure:
   - Vector databases (Pinecone, Weaviate, Qdrant)
   - Embedding model configurations
   - Chunking strategies
   - Similarity search algorithms
   - RAG implementation quality

3. Database Architecture:
   - Connection pooling efficiency
   - Query optimization opportunities
   - Schema design patterns
   - Caching strategies
   - Data consistency issues

4. Performance Bottlenecks:
   - Memory leaks
   - Inefficient queries
   - Missing indexes
   - Cache misses

Provide SPECIFIC architectural improvements with implementation details.""",
            },
            {
                "role": "user",
                "content": "Analyze embeddings, memory, and database architecture in /Users/lynnmusil/sophia-intel-ai. Focus on performance and scalability.",
            },
        ]

        try:
            # Use AIMLAPI for Llama-4 Scout
            response = aimlapi_manager.chat_completion(
                model="llama-4-scout", messages=messages, temperature=0.4, max_tokens=16384
            )

            elapsed = time.time() - start_time
            print(f"✅ [T+{elapsed:.1f}s] Agent 3 COMPLETED")

            content = (
                response.get("choices", [{}])[0].get("message", {}).get("content", "No response")
            )

            return {
                "agent": "Llama-4 Scout",
                "focus": "Embeddings, Memory & Database",
                "execution_time": elapsed,
                "findings": content,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ [T+{elapsed:.1f}s] Agent 3 FAILED: {str(e)[:100]}")
            return {
                "agent": "Llama-4 Scout",
                "focus": "Embeddings, Memory & Database",
                "execution_time": elapsed,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def run_parallel_swarm(self) -> Dict[str, Any]:
        """Execute all three agents in PARALLEL using thread pool"""
        print("\n" + "=" * 70)
        print(" ARTEMIS PARALLEL MICROSWARM EXECUTION")
        print(" 3 Specialized Agents Running SIMULTANEOUSLY")
        print("=" * 70)

        start_time = time.time()

        # Launch all agents SIMULTANEOUSLY using thread pool
        print("\n⚡ LAUNCHING 3 AGENTS IN PARALLEL...")
        print("  • Agent 1: Grok Code Fast 1 - Redundancy Analysis")
        print("  • Agent 2: Security Analyst - Vulnerability Scan")
        print("  • Agent 3: Llama-4 Scout - Data Architecture")

        loop = asyncio.get_event_loop()

        # Run all agents in parallel threads
        tasks = [
            loop.run_in_executor(self.executor, self._run_agent1_sync),
            loop.run_in_executor(self.executor, self._run_agent2_sync),
            loop.run_in_executor(self.executor, self._run_agent3_sync),
        ]

        # Wait for all to complete
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # Compile results
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "swarm_type": "Artemis Parallel Microswarm",
            "execution_mode": "PARALLEL (3 agents simultaneously)",
            "total_execution_time": total_time,
            "agent_count": 3,
            "agents": results,
        }

        # Save results
        output_file = f"artemis_swarm_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n⏱️  Total Parallel Execution: {total_time:.1f} seconds")
        print(f"💾 Results saved to {output_file}")

        return self.results


async def main():
    """Main execution"""
    swarm = ArtemisParallelSwarm()
    results = await swarm.run_parallel_swarm()

    print("\n" + "=" * 70)
    print(" SWARM ANALYSIS COMPLETE - SUMMARY")
    print("=" * 70)

    successful = 0
    failed = 0

    for i, agent_result in enumerate(results["agents"], 1):
        print(f"\n{'='*70}")
        print(f" AGENT {i}: {agent_result.get('agent', 'Unknown')}")
        print(f" Focus: {agent_result.get('focus', 'Unknown')}")
        print(f" Time: {agent_result.get('execution_time', 0):.1f}s")
        print(f"{'='*70}")

        if "error" in agent_result:
            failed += 1
            print(f"❌ Failed: {agent_result['error'][:200]}")
        else:
            successful += 1
            findings = agent_result.get("findings", "")
            if findings:
                # Show key findings (first 600 chars)
                print("📋 Key Findings:")
                print(findings[:600] + "..." if len(findings) > 600 else findings)

    print("\n" + "=" * 70)
    print(" EXECUTION METRICS")
    print("=" * 70)
    print(f"  ✅ Successful: {successful}/3 agents")
    print(f"  ❌ Failed: {failed}/3 agents")
    print(f"  ⏱️  Total Time: {results['total_execution_time']:.1f}s (parallel)")

    # Calculate efficiency
    sequential_time = sum(a.get("execution_time", 0) for a in results["agents"])
    time_saved = sequential_time - results["total_execution_time"]
    efficiency = (time_saved / sequential_time * 100) if sequential_time > 0 else 0

    print(f"  📊 Sequential Time: {sequential_time:.1f}s")
    print(f"  ⚡ Time Saved: {time_saved:.1f}s")
    print(f"  🎯 Efficiency: {efficiency:.1f}% faster than sequential")

    return results


if __name__ == "__main__":
    print("🚀 Initializing Artemis Microswarm...")
    results = asyncio.run(main())
