#!/usr/bin/env python3
"""
ARTEMIS PARALLEL SWARM - EXACT MODELS WITH PROPER PROVIDERS
Military-grade parallel execution with your specified models
"""

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

# Set API keys explicitly if not loaded
if not os.environ.get("AIMLAPI_API_KEY"):
    os.environ["AIMLAPI_API_KEY"] = "562d964ac0b54357874b01de33cb91e9"
if not os.environ.get("OPENROUTER_API_KEY"):
    os.environ["OPENROUTER_API_KEY"] = (
        "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"
    )
if not os.environ.get("PORTKEY_API_KEY"):
    os.environ["PORTKEY_API_KEY"] = "hPxFZGd8AN269n4bznDf2/Onbi8I"


@dataclass
class AgentResult:
    """Result from an agent execution"""

    agent_name: str
    model: str
    provider: str
    success: bool
    response: str
    execution_time: float
    tokens_used: int
    error: Optional[str] = None


class ArtemisParallelSwarm:
    """Artemis Military Swarm with exact specified models"""

    def __init__(self):
        self.start_time = time.time()
        self.results = []

        # Repository scan prompt for ALL agents
        self.repository_scan_prompt = """
        MISSION: Comprehensive Repository Analysis - sophia-intel-ai

        You are an elite military-grade AI agent conducting a FULL repository scan.

        OBJECTIVES:
        1. SECURITY ASSESSMENT
           - Identify exposed API keys, credentials, or sensitive data
           - Detect unsafe WebSocket implementations
           - Find SQL injection vulnerabilities
           - Check for XSS/CSRF vulnerabilities

        2. ARCHITECTURE ANALYSIS
           - Map the complete system architecture
           - Identify code duplication and redundancy
           - Analyze the dual orchestrator pattern (Sophia/Artemis)
           - Evaluate the swarm implementation

        3. PERFORMANCE BOTTLENECKS
           - Find inefficient algorithms (O(n²) or worse)
           - Identify memory leaks or excessive allocations
           - Detect blocking I/O in async contexts
           - Find unnecessary database queries

        4. CODE QUALITY ISSUES
           - Detect dead code and unused imports
           - Find missing error handling
           - Identify missing type hints
           - Check test coverage gaps

        5. CRITICAL IMPROVEMENTS
           - List TOP 5 most critical issues to fix
           - Provide specific file paths and line numbers
           - Estimate effort and impact for each fix

        CONSTRAINTS:
        - Be SPECIFIC with file paths and code locations
        - Prioritize by SEVERITY and IMPACT
        - Provide ACTIONABLE recommendations
        - Focus on REAL issues, not theoretical

        Repository structure includes:
        - /app/ - Main application code with orchestrators and swarms
        - /agent-ui/ - React frontend with dashboards
        - /scripts/ - Utility and deployment scripts
        - /k8s/ - Kubernetes configurations
        - /tests/ - Test suites

        Provide a comprehensive analysis with military precision.
        """

    async def call_gemini_direct(self) -> AgentResult:
        """Agent 1: Gemini 2.5 Flash via Portkey"""
        agent_name = "RECONNAISSANCE ALPHA"
        model = "google/gemini-2.5-flash"
        provider = "Portkey Gateway"

        print(f"\n🎯 {agent_name} deploying {model}...")
        start = time.time()

        # Use Portkey with virtual key
        portkey_key = os.environ.get("PORTKEY_API_KEY", "")

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://api.portkey.ai/v1/chat/completions",
                    headers={
                        "x-portkey-api-key": portkey_key,
                        "x-portkey-provider": "google",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": self.repository_scan_prompt}],
                        "max_tokens": 2048,
                        "temperature": 0.7,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    tokens = data.get("usage", {}).get("total_tokens", 0)

                    return AgentResult(
                        agent_name=agent_name,
                        model=model,
                        provider=provider,
                        success=True,
                        response=content,
                        execution_time=time.time() - start,
                        tokens_used=tokens,
                    )
                else:
                    return AgentResult(
                        agent_name=agent_name,
                        model=model,
                        provider=provider,
                        success=False,
                        response="",
                        execution_time=time.time() - start,
                        tokens_used=0,
                        error=f"API Error: {response.status_code} - {response.text}",
                    )
        except Exception as e:
            return AgentResult(
                agent_name=agent_name,
                model=model,
                provider=provider,
                success=False,
                response="",
                execution_time=time.time() - start,
                tokens_used=0,
                error=str(e),
            )

    async def call_grok_openrouter(self) -> AgentResult:
        """Agent 2: Grok Code Fast via OpenRouter"""
        agent_name = "TACTICAL BRAVO"
        model = "x-ai/grok-code-fast-1"
        provider = "OpenRouter"

        print(f"\n⚡ {agent_name} deploying {model}...")
        start = time.time()

        # Get OpenRouter key from env
        openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not openrouter_key or "YOUR_" in openrouter_key:
            # Try Portkey's OpenRouter key
            openrouter_key = os.environ.get("PORTKEY_API_KEY", "")

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://sophia-intel-ai.com",
                        "X-Title": "Artemis Military Swarm",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": self.repository_scan_prompt}],
                        "max_tokens": 2048,
                        "temperature": 0.7,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    tokens = data.get("usage", {}).get("total_tokens", 0)

                    return AgentResult(
                        agent_name=agent_name,
                        model=model,
                        provider=provider,
                        success=True,
                        response=content,
                        execution_time=time.time() - start,
                        tokens_used=tokens,
                    )
                else:
                    return AgentResult(
                        agent_name=agent_name,
                        model=model,
                        provider=provider,
                        success=False,
                        response="",
                        execution_time=time.time() - start,
                        tokens_used=0,
                        error=f"API Error: {response.status_code} - {response.text}",
                    )
        except Exception as e:
            return AgentResult(
                agent_name=agent_name,
                model=model,
                provider=provider,
                success=False,
                response="",
                execution_time=time.time() - start,
                tokens_used=0,
                error=str(e),
            )

    async def call_glm_aimlapi(self) -> AgentResult:
        """Agent 3: GLM-4.5-Air via AIMLAPI"""
        agent_name = "STRATEGIC CHARLIE"
        model = "zhipu/glm-4.5-air"
        provider = "AIMLAPI"

        print(f"\n🚀 {agent_name} deploying {model}...")
        start = time.time()

        # Get AIMLAPI key
        aimlapi_key = os.environ.get("AIMLAPI_API_KEY", "")

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://api.aimlapi.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {aimlapi_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": self.repository_scan_prompt}],
                        "max_completion_tokens": 2048,
                        "temperature": 0.7,
                    },
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    tokens = data.get("usage", {}).get("total_tokens", 0)

                    return AgentResult(
                        agent_name=agent_name,
                        model=model,
                        provider=provider,
                        success=True,
                        response=content,
                        execution_time=time.time() - start,
                        tokens_used=tokens,
                    )
                else:
                    return AgentResult(
                        agent_name=agent_name,
                        model=model,
                        provider=provider,
                        success=False,
                        response="",
                        execution_time=time.time() - start,
                        tokens_used=0,
                        error=f"API Error: {response.status_code} - {response.text}",
                    )
        except Exception as e:
            return AgentResult(
                agent_name=agent_name,
                model=model,
                provider=provider,
                success=False,
                response="",
                execution_time=time.time() - start,
                tokens_used=0,
                error=str(e),
            )

    async def call_llama_scout(self) -> AgentResult:
        """Agent 4: Llama-4-Scout via AIMLAPI (or HuggingFace)"""
        agent_name = "INTELLIGENCE DELTA"
        model = "meta-llama/llama-4-scout"
        provider = "AIMLAPI/Meta"

        print(f"\n🔍 {agent_name} deploying {model}...")
        start = time.time()

        # Try AIMLAPI first
        aimlapi_key = os.environ.get("AIMLAPI_API_KEY", "")

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://api.aimlapi.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {aimlapi_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": self.repository_scan_prompt}],
                        "max_tokens": 2048,
                        "temperature": 0.7,
                    },
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    tokens = data.get("usage", {}).get("total_tokens", 0)

                    return AgentResult(
                        agent_name=agent_name,
                        model=model,
                        provider=provider,
                        success=True,
                        response=content,
                        execution_time=time.time() - start,
                        tokens_used=tokens,
                    )
                else:
                    return AgentResult(
                        agent_name=agent_name,
                        model=model,
                        provider=provider,
                        success=False,
                        response="",
                        execution_time=time.time() - start,
                        tokens_used=0,
                        error=f"API Error: {response.status_code} - {response.text}",
                    )
        except Exception as e:
            return AgentResult(
                agent_name=agent_name,
                model=model,
                provider=provider,
                success=False,
                response="",
                execution_time=time.time() - start,
                tokens_used=0,
                error=str(e),
            )

    async def run_parallel_swarm(self) -> List[AgentResult]:
        """Execute all agents simultaneously"""
        print("\n" + "=" * 70)
        print("🚀 ARTEMIS PARALLEL SWARM ACTIVATION")
        print("=" * 70)
        print(f"📅 Timestamp: {datetime.now().isoformat()}")
        print("📁 Repository: sophia-intel-ai")
        print("🎯 Mission: Parallel Repository Scan")
        print("👥 Agents: 4 Military Units")
        print("=" * 70)

        # Launch all agents simultaneously
        tasks = [
            self.call_gemini_direct(),
            self.call_grok_openrouter(),
            self.call_glm_aimlapi(),
            self.call_llama_scout(),
        ]

        print("\n⚡ LAUNCHING PARALLEL EXECUTION...")
        results = await asyncio.gather(*tasks)

        return results

    def score_agent_output(self, result: AgentResult) -> Dict[str, Any]:
        """Score each agent's output"""
        scores = {
            "agent": result.agent_name,
            "model": result.model,
            "provider": result.provider,
            "success": result.success,
            "execution_time": round(result.execution_time, 2),
            "tokens_used": result.tokens_used,
            "response_length": len(result.response) if result.success else 0,
            "scores": {},
        }

        if result.success and result.response:
            response_lower = result.response.lower()

            # Quality Score (0-100)
            quality = 0
            if "security" in response_lower:
                quality += 15
            if "architecture" in response_lower:
                quality += 15
            if "performance" in response_lower:
                quality += 15
            if "code quality" in response_lower:
                quality += 15
            if any(path in response_lower for path in ["/app/", "/scripts/", ".py", ".tsx"]):
                quality += 20
            if any(word in response_lower for word in ["critical", "vulnerability", "issue"]):
                quality += 20
            scores["scores"]["quality"] = min(quality, 100)

            # Speed Score (0-100)
            if result.execution_time < 5:
                speed = 100
            elif result.execution_time < 10:
                speed = 80
            elif result.execution_time < 20:
                speed = 60
            elif result.execution_time < 30:
                speed = 40
            else:
                speed = 20
            scores["scores"]["speed"] = speed

            # Accuracy Score (0-100)
            accuracy = 0
            if "sophia" in response_lower and "artemis" in response_lower:
                accuracy += 30
            if "orchestrator" in response_lower:
                accuracy += 20
            if "websocket" in response_lower:
                accuracy += 20
            if "swarm" in response_lower:
                accuracy += 15
            if "api" in response_lower or "key" in response_lower:
                accuracy += 15
            scores["scores"]["accuracy"] = min(accuracy, 100)

            # Thoroughness Score (0-100)
            thoroughness = min(100, (len(result.response) / 100))  # 1 point per 100 chars, max 100
            if result.response.count("\n") > 20:
                thoroughness = min(100, thoroughness + 20)
            if result.response.count("-") > 10:
                thoroughness = min(100, thoroughness + 10)
            scores["scores"]["thoroughness"] = int(thoroughness)

            # Prioritization Score (0-100)
            prioritization = 0
            if any(word in response_lower for word in ["top", "critical", "priority", "urgent"]):
                prioritization += 40
            if any(word in response_lower for word in ["1.", "2.", "3.", "first", "second"]):
                prioritization += 30
            if "immediate" in response_lower or "asap" in response_lower:
                prioritization += 30
            scores["scores"]["prioritization"] = min(prioritization, 100)

            # Communication Score (0-100)
            communication = 50  # Base score
            if result.response.count("\n") > 5:
                communication += 20  # Good formatting
            if any(word in response_lower for word in ["recommend", "suggest", "should"]):
                communication += 15
            if len(result.response) > 500 and len(result.response) < 5000:
                communication += 15  # Good length
            scores["scores"]["communication"] = min(communication, 100)

            # Overall Score (weighted average)
            weights = {
                "quality": 0.25,
                "speed": 0.15,
                "accuracy": 0.20,
                "thoroughness": 0.15,
                "prioritization": 0.15,
                "communication": 0.10,
            }

            overall = sum(scores["scores"][metric] * weight for metric, weight in weights.items())
            scores["scores"]["overall"] = round(overall, 1)
        else:
            # Failed agent gets 0 scores
            scores["scores"] = {
                "quality": 0,
                "speed": 0,
                "accuracy": 0,
                "thoroughness": 0,
                "prioritization": 0,
                "communication": 0,
                "overall": 0,
            }
            scores["error"] = result.error

        return scores

    def generate_report(self, results: List[AgentResult]) -> str:
        """Generate comprehensive scored report"""
        report = []
        report.append("\n" + "=" * 70)
        report.append("📊 ARTEMIS PARALLEL SWARM - FINAL REPORT")
        report.append("=" * 70)

        # Score all agents
        scored_results = [self.score_agent_output(result) for result in results]

        # Summary stats
        successful = sum(1 for r in scored_results if r["success"])
        total_tokens = sum(r["tokens_used"] for r in scored_results)
        avg_time = sum(r["execution_time"] for r in scored_results) / len(scored_results)

        report.append("\n📈 EXECUTION SUMMARY:")
        report.append(f"  ✓ Success Rate: {successful}/{len(results)} agents")
        report.append(f"  ⏱️ Average Time: {avg_time:.2f} seconds")
        report.append(f"  🔤 Total Tokens: {total_tokens:,}")
        report.append(
            f"  ⚡ Parallel Speedup: {(avg_time * len(results) / max(r['execution_time'] for r in scored_results)):.1f}x"
        )

        # Individual agent scores
        report.append("\n" + "=" * 70)
        report.append("🎯 INDIVIDUAL AGENT PERFORMANCE:")
        report.append("=" * 70)

        for i, score in enumerate(scored_results, 1):
            report.append(f"\n{'🟢' if score['success'] else '🔴'} AGENT {i}: {score['agent']}")
            report.append(f"  Model: {score['model']}")
            report.append(f"  Provider: {score['provider']}")
            report.append(
                f"  Execution: {score['execution_time']}s | {score['tokens_used']} tokens"
            )

            if score["success"]:
                report.append(f"  Response: {score['response_length']} characters")
                report.append("\n  📊 SCORES:")
                for metric, value in score["scores"].items():
                    if metric != "overall":
                        report.append(f"    • {metric.capitalize()}: {value}/100")
                report.append(f"  🏆 OVERALL SCORE: {score['scores']['overall']}/100")
            else:
                report.append(f"  ❌ ERROR: {score.get('error', 'Unknown error')}")

        # Ranking
        report.append("\n" + "=" * 70)
        report.append("🏆 FINAL RANKINGS:")
        report.append("=" * 70)

        successful_agents = [s for s in scored_results if s["success"]]
        if successful_agents:
            ranked = sorted(successful_agents, key=lambda x: x["scores"]["overall"], reverse=True)
            for rank, agent in enumerate(ranked, 1):
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "🏅"
                report.append(
                    f"{medal} Rank {rank}: {agent['agent']} - Score: {agent['scores']['overall']}/100"
                )
                report.append(f"   Model: {agent['model']} | Time: {agent['execution_time']}s")

        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"artemis_parallel_{timestamp}.json"

        with open(result_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "summary": {
                        "success_rate": f"{successful}/{len(results)}",
                        "total_tokens": total_tokens,
                        "average_time": avg_time,
                    },
                    "agents": scored_results,
                    "raw_responses": [
                        {"agent": r.agent_name, "response": r.response if r.success else r.error}
                        for r in results
                    ],
                },
                f,
                indent=2,
            )

        report.append(f"\n💾 Detailed results saved to: {result_file}")

        return "\n".join(report)


async def main():
    """Execute the Artemis Parallel Swarm"""
    swarm = ArtemisParallelSwarm()

    # Run all agents in parallel
    results = await swarm.run_parallel_swarm()

    # Generate and print report
    report = swarm.generate_report(results)
    print(report)

    # Print sample of best response
    successful = [r for r in results if r.success and r.response]
    if successful:
        best = max(successful, key=lambda r: len(r.response))
        print("\n" + "=" * 70)
        print("📝 SAMPLE OUTPUT (First 500 chars from best agent):")
        print("=" * 70)
        print(f"Agent: {best.agent_name}")
        print(f"Response Preview:\n{best.response[:500]}...")


if __name__ == "__main__":
    asyncio.run(main())
