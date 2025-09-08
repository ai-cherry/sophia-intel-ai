#!/usr/bin/env python3
"""
Artemis Comparative Microswarm
3 agents receive IDENTICAL comprehensive prompts for fair comparison
All run SIMULTANEOUSLY to analyze the entire repository
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

from app.artemis.unified_factory import ArtemisUnifiedFactory
from app.core.aimlapi_config import aimlapi_manager
from app.core.enhanced_llm_router import LLMProviderType, enhanced_router


class ArtemisComparativeSwarm:
    """Artemis swarm with identical prompts for agent comparison"""

    def __init__(self):
        self.factory = ArtemisUnifiedFactory()
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.results = {}

        # IDENTICAL COMPREHENSIVE PROMPT FOR ALL AGENTS
        self.universal_prompt = {
            "system": """You are a specialized agent in the Artemis microswarm analyzing the sophia-intel-ai repository.

COMPREHENSIVE ANALYSIS MISSION - Cover ALL areas:

1. CODE REDUNDANCIES & PATTERNS:
   - Identify duplicate functions/methods across files
   - Find similar code patterns that could be abstracted
   - Locate repeated configuration blocks
   - Analyze redundant imports (2600+ import statements across 500+ files)
   - Compare /app/artemis/ vs /app/sophia/ for duplication
   - Examine base orchestrator classes (base_orchestrator.py vs unified_base.py)
   - Review factory pattern duplications (6+ similar implementations)
   - Check for repeated logger declarations (322 instances)

2. SECURITY & SECRETS HANDLING:
   - Analyze API key management in /app/core/portkey_config.py (14 virtual keys)
   - Review AIMLAPI configuration in /app/core/aimlapi_config.py
   - Check for hardcoded secrets or credentials
   - Evaluate environment variable security
   - Assess authentication/authorization implementations
   - Review WebSocket security (WSS handlers)
   - Check for unprotected API endpoints
   - Identify input validation gaps
   - Review CORS configurations
   - Look for potential injection vulnerabilities

3. EMBEDDINGS & MEMORY ARCHITECTURE:
   - Analyze memory systems in /app/memory/
   - Review vector database integrations (Pinecone, Weaviate, Qdrant)
   - Evaluate embedding strategies and models
   - Assess chunking strategies for documents
   - Review RAG implementation patterns
   - Analyze context window management
   - Check Redis integration for caching
   - Evaluate conversation history handling

4. DATABASE & PERFORMANCE:
   - Review database connection patterns
   - Analyze query optimization opportunities
   - Check for connection pooling efficiency
   - Identify performance bottlenecks
   - Review caching strategies
   - Look for memory leaks
   - Assess schema design patterns

REQUIREMENTS:
- Provide SPECIFIC file paths and line numbers where possible
- Include code snippets for critical findings
- Prioritize findings as HIGH/MEDIUM/LOW
- Suggest concrete remediation steps
- Estimate effort required for fixes

Focus on the most critical issues that impact:
- Code maintainability
- Security posture
- Performance
- Scalability""",
            "user": """Perform a comprehensive analysis of the sophia-intel-ai repository at /Users/lynnmusil/sophia-intel-ai.

Cover ALL areas:
1. Code redundancies and architectural patterns
2. Security vulnerabilities and secrets handling
3. Embedding strategies and memory systems
4. Database architecture and performance

Be thorough, specific, and provide actionable recommendations.""",
        }

    def _run_agent1_grok(self) -> Dict[str, Any]:
        """Agent 1: Grok Code Fast 1"""
        start_time = time.time()
        agent_name = "Grok Code Fast 1"
        print(f"\n🚀 [T+0.0s] Agent 1 STARTING: {agent_name}")

        messages = [
            {"role": "system", "content": self.universal_prompt["system"]},
            {"role": "user", "content": self.universal_prompt["user"]},
        ]

        try:
            response = aimlapi_manager.chat_completion(
                model="grok-code-fast-1",
                messages=messages,
                temperature=0.3,
                max_tokens=32768,
            )

            elapsed = time.time() - start_time
            print(f"✅ [T+{elapsed:.1f}s] Agent 1 COMPLETED: {agent_name}")

            content = (
                response.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "No response")
            )

            return {
                "agent_number": 1,
                "agent_name": agent_name,
                "model": "grok-code-fast-1",
                "specs": "92 tokens/sec, $0.20/$1.50 per M tokens",
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
                "model": "grok-code-fast-1",
                "execution_time": elapsed,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _run_agent2_gemini(self) -> Dict[str, Any]:
        """Agent 2: Gemini 2.5 Flash (or fallback)"""
        start_time = time.time()
        agent_name = "Gemini 2.5 Flash"
        print(f"\n⚡ [T+0.0s] Agent 2 STARTING: {agent_name}")

        messages = [
            {"role": "system", "content": self.universal_prompt["system"]},
            {"role": "user", "content": self.universal_prompt["user"]},
        ]

        try:
            # Try Gemini first, fallback to another model if needed
            try:
                response = enhanced_router.create_completion(
                    messages=messages,
                    model="gemini-2-5-flash",
                    provider_type=LLMProviderType.AIMLAPI,
                    temperature=0.3,
                    max_tokens=16384,
                )
                actual_model = "gemini-2-5-flash"
            except:
                # Fallback to GLM-4.5-Air
                response = aimlapi_manager.chat_completion(
                    model="glm-4.5-air",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=16384,
                )
                actual_model = "glm-4.5-air (fallback)"
                agent_name = "GLM-4.5 Air (Gemini fallback)"

            elapsed = time.time() - start_time
            print(f"✅ [T+{elapsed:.1f}s] Agent 2 COMPLETED: {agent_name}")

            if hasattr(response, "choices"):
                content = response.choices[0].message.content
            else:
                content = (
                    response.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "No response")
                )

            return {
                "agent_number": 2,
                "agent_name": agent_name,
                "model": actual_model,
                "specs": "Fast processing, economy tier",
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
        """Agent 3: Llama-4 Scout"""
        start_time = time.time()
        agent_name = "Llama-4 Scout"
        print(f"\n🔍 [T+0.0s] Agent 3 STARTING: {agent_name}")

        messages = [
            {"role": "system", "content": self.universal_prompt["system"]},
            {"role": "user", "content": self.universal_prompt["user"]},
        ]

        try:
            response = aimlapi_manager.chat_completion(
                model="llama-4-scout",
                messages=messages,
                temperature=0.3,
                max_tokens=16384,
            )

            elapsed = time.time() - start_time
            print(f"✅ [T+{elapsed:.1f}s] Agent 3 COMPLETED: {agent_name}")

            content = (
                response.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "No response")
            )

            return {
                "agent_number": 3,
                "agent_name": agent_name,
                "model": "llama-4-scout",
                "specs": "Pattern recognition specialist",
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
                "model": "llama-4-scout",
                "execution_time": elapsed,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def run_comparative_swarm(self) -> Dict[str, Any]:
        """Execute all three agents with IDENTICAL prompts SIMULTANEOUSLY"""
        print("\n" + "=" * 70)
        print(" ARTEMIS COMPARATIVE MICROSWARM")
        print(" 3 Agents - IDENTICAL Prompts - PARALLEL Execution")
        print("=" * 70)
        print("\n📋 All agents receive the SAME comprehensive analysis prompt")
        print("🎯 Objective: Compare analysis quality and performance\n")

        start_time = time.time()

        # Launch all agents SIMULTANEOUSLY
        print("⚡ LAUNCHING 3 AGENTS IN PARALLEL...")
        print("  • Agent 1: Grok Code Fast 1")
        print("  • Agent 2: Gemini 2.5 Flash / GLM-4.5 Air")
        print("  • Agent 3: Llama-4 Scout")

        loop = asyncio.get_event_loop()

        # Run all agents in parallel
        tasks = [
            loop.run_in_executor(self.executor, self._run_agent1_grok),
            loop.run_in_executor(self.executor, self._run_agent2_gemini),
            loop.run_in_executor(self.executor, self._run_agent3_llama),
        ]

        # Wait for all to complete
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # Compile results
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "swarm_type": "Artemis Comparative Microswarm",
            "execution_mode": "PARALLEL - Identical Prompts",
            "prompt_type": "Comprehensive Repository Analysis",
            "total_execution_time": total_time,
            "agent_count": 3,
            "agents": results,
        }

        # Save results
        output_file = (
            f"artemis_comparative_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n⏱️  Total Execution Time: {total_time:.1f} seconds")
        print(f"💾 Full results saved to {output_file}")

        return self.results

    def analyze_comparative_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and compare agent performance"""
        analysis = {
            "performance_metrics": {},
            "content_analysis": {},
            "recommendations": [],
        }

        for agent in results["agents"]:
            if "error" not in agent:
                agent_num = agent["agent_number"]
                findings_length = len(agent.get("findings", ""))

                analysis["performance_metrics"][f"agent_{agent_num}"] = {
                    "name": agent["agent_name"],
                    "model": agent.get("model", "unknown"),
                    "execution_time": agent["execution_time"],
                    "response_length": findings_length,
                    "tokens_per_second": (
                        findings_length / agent["execution_time"]
                        if agent["execution_time"] > 0
                        else 0
                    ),
                }

        # Determine fastest and most comprehensive
        valid_agents = [a for a in results["agents"] if "error" not in a]
        if valid_agents:
            fastest = min(valid_agents, key=lambda x: x["execution_time"])
            most_comprehensive = max(
                valid_agents, key=lambda x: len(x.get("findings", ""))
            )

            analysis["recommendations"].append(
                f"Fastest: {fastest['agent_name']} ({fastest['execution_time']:.1f}s)"
            )
            analysis["recommendations"].append(
                f"Most Comprehensive: {most_comprehensive['agent_name']} ({len(most_comprehensive.get('findings', ''))} chars)"
            )

        return analysis


async def main():
    """Main execution with comparative analysis"""
    swarm = ArtemisComparativeSwarm()
    results = await swarm.run_comparative_swarm()

    print("\n" + "=" * 70)
    print(" COMPARATIVE ANALYSIS RESULTS")
    print("=" * 70)

    successful = 0
    failed = 0

    # Display individual results
    for agent_result in results["agents"]:
        print(f"\n{'='*70}")
        print(
            f" AGENT {agent_result['agent_number']}: {agent_result.get('agent_name', 'Unknown')}"
        )
        print(f" Model: {agent_result.get('model', 'Unknown')}")
        print(f" Specs: {agent_result.get('specs', 'N/A')}")
        print(f" Execution Time: {agent_result.get('execution_time', 0):.1f}s")
        print(f"{'='*70}")

        if "error" in agent_result:
            failed += 1
            print(f"❌ Failed: {agent_result['error'][:200]}")
        else:
            successful += 1
            findings = agent_result.get("findings", "")
            if findings:
                print(f"📊 Response Length: {len(findings)} characters")
                print("📋 Sample Finding (first 500 chars):")
                print(findings[:500] + "..." if len(findings) > 500 else findings)

    # Comparative analysis
    analysis = swarm.analyze_comparative_results(results)

    print("\n" + "=" * 70)
    print(" COMPARATIVE METRICS")
    print("=" * 70)

    print("\n📊 Performance Comparison:")
    for agent_id, metrics in analysis["performance_metrics"].items():
        print(f"\n  {metrics['name']}:")
        print(f"    • Model: {metrics['model']}")
        print(f"    • Time: {metrics['execution_time']:.1f}s")
        print(f"    • Response: {metrics['response_length']:,} chars")
        print(f"    • Speed: {metrics['tokens_per_second']:.0f} chars/sec")

    print("\n🏆 Winners:")
    for rec in analysis["recommendations"]:
        print(f"  • {rec}")

    print("\n📈 Summary:")
    print(f"  • Successful: {successful}/3 agents")
    print(f"  • Failed: {failed}/3 agents")
    print(f"  • Total Time: {results['total_execution_time']:.1f}s (parallel)")

    # Calculate efficiency
    sequential_time = sum(a.get("execution_time", 0) for a in results["agents"])
    time_saved = sequential_time - results["total_execution_time"]
    efficiency = (time_saved / sequential_time * 100) if sequential_time > 0 else 0

    print(f"  • Sequential Time: {sequential_time:.1f}s")
    print(f"  • Parallel Speedup: {efficiency:.1f}%")

    return results


if __name__ == "__main__":
    print("🚀 Initializing Artemis Comparative Microswarm...")
    print("📋 All agents will receive IDENTICAL comprehensive prompts")
    print("⚡ Agents will run SIMULTANEOUSLY for fair comparison\n")
    results = asyncio.run(main())
