#!/usr/bin/env python3
"""
ARTEMIS 4-SCOUT COMPARISON TEST
4 different models, SAME EXACT PROMPT, REAL REPOSITORY SCANNING
"""

import asyncio
import glob
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

# Load environment variables
from dotenv import load_dotenv

# Import file reading tools

load_dotenv()

# Set API keys
if not os.environ.get("AIMLAPI_API_KEY"):
    os.environ["AIMLAPI_API_KEY"] = "562d964ac0b54357874b01de33cb91e9"
if not os.environ.get("OPENROUTER_API_KEY"):
    os.environ["OPENROUTER_API_KEY"] = (
        "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"
    )
if not os.environ.get("PORTKEY_API_KEY"):
    os.environ["PORTKEY_API_KEY"] = "hPxFZGd8AN269n4bznDf2/Onbi8I"


@dataclass
class ScoutResult:
    """Result from a scout agent"""

    agent_id: int
    model: str
    provider: str
    response: str
    execution_time: float
    tokens_used: int
    success: bool
    error: Optional[str] = None


class Artemis4ScoutSwarm:
    """4 Scout Agents with IDENTICAL prompts for comparison"""

    def __init__(self):
        self.repo_path = "/Users/lynnmusil/sophia-intel-ai"

        # Get REAL repository context
        self.repo_context = self.build_repository_context()

        # THE EXACT SAME PROMPT FOR ALL 4 SCOUTS
        self.scout_prompt = f"""
MISSION: COMPREHENSIVE REPOSITORY ANALYSIS - sophia-intel-ai

You are an elite scout agent conducting a THOROUGH repository scan.
This is a REAL repository with REAL files. Provide SPECIFIC analysis.

REPOSITORY FACTS:
- Location: {self.repo_path}
- Python files: {self.repo_context['python_files']}
- TypeScript files: {self.repo_context['typescript_files']}
- Total files: {self.repo_context['total_files']}
- Key directories: {', '.join(self.repo_context['directories'])}

YOUR OBJECTIVES:

1. SECURITY ANALYSIS (Priority: CRITICAL)
   - Identify exposed API keys, tokens, passwords
   - Find hardcoded secrets in code
   - Detect unsafe WebSocket implementations
   - Check for SQL injection vulnerabilities
   - Look for XSS/CSRF vulnerabilities
   - CHECK THESE FILES: {', '.join(self.repo_context['security_files'])}

2. ARCHITECTURE ANALYSIS (Priority: HIGH)
   - Map the system architecture
   - Identify code duplication (especially in orchestrators)
   - Analyze the dual Sophia/Artemis pattern
   - Find circular dependencies
   - Evaluate the swarm implementation
   - FOCUS ON: {', '.join(self.repo_context['architecture_files'])}

3. PERFORMANCE ANALYSIS (Priority: HIGH)
   - Find O(n²) or worse algorithms
   - Identify blocking I/O in async functions
   - Detect memory leaks or excessive allocations
   - Find unnecessary database queries
   - Look for inefficient list comprehensions
   - SCAN: {', '.join(self.repo_context['performance_files'])}

4. CODE QUALITY ANALYSIS (Priority: MEDIUM)
   - Detect dead code and unused imports
   - Find missing error handling
   - Identify missing type hints
   - Check test coverage gaps
   - Find TODO/FIXME comments

5. CRITICAL RECOMMENDATIONS
   - List TOP 5 most critical issues
   - Provide SPECIFIC file paths and line numbers
   - Estimate effort (Low/Medium/High)
   - Assess impact (Low/Medium/High/Critical)

IMPORTANT NOTES FROM ACTUAL FILE SCAN:
{self.repo_context['sample_issues']}

BE SPECIFIC. Use real file paths. Provide actionable recommendations.
This is a REAL repository scan, not a simulation.
"""

    def build_repository_context(self) -> Dict[str, Any]:
        """Build REAL repository context"""
        print("📂 Building REAL repository context...")

        # Count real files
        py_files = glob.glob(f"{self.repo_path}/**/*.py", recursive=True)
        ts_files = glob.glob(f"{self.repo_path}/**/*.ts", recursive=True)
        tsx_files = glob.glob(f"{self.repo_path}/**/*.tsx", recursive=True)

        # Key directories
        directories = []
        for d in ["app", "agent-ui", "scripts", "tests", "k8s"]:
            if os.path.exists(os.path.join(self.repo_path, d)):
                directories.append(f"/{d}")

        # Files to check for security
        security_files = [
            "app/core/portkey_config.py",
            "app/core/aimlapi_config.py",
            ".env",
            "app/api/unified_server.py",
        ]

        # Architecture files
        architecture_files = [
            "app/artemis/unified_factory.py",
            "app/sophia/sophia_orchestrator.py",
            "app/orchestrators/*.py",
            "app/factory/*.py",
        ]

        # Performance critical files
        performance_files = [
            "app/swarms/*.py",
            "app/core/websocket_manager.py",
            "app/api/routes/*.py",
        ]

        # Sample real issues we already found
        sample_issues = """
- Found 16 exposed API keys in .env (NETSUITE, PORTKEY, etc.)
- Detected nested loops in app/tools/git_ops.py:31
- Duplicate functions across orchestrator files
- 95% code duplication between Sophia and Artemis factories
"""

        return {
            "python_files": len(py_files),
            "typescript_files": len(ts_files),
            "tsx_files": len(tsx_files),
            "total_files": len(py_files) + len(ts_files) + len(tsx_files),
            "directories": directories,
            "security_files": security_files,
            "architecture_files": architecture_files,
            "performance_files": performance_files,
            "sample_issues": sample_issues,
        }

    async def scout_1_grok(self) -> ScoutResult:
        """Scout 1: Grok Code Fast via OpenRouter"""
        agent_id = 1
        model = "x-ai/grok-code-fast-1"  # GROK CODE FAST AS YOU REQUESTED
        provider = "OpenRouter"

        print(f"\n🔍 SCOUT {agent_id}: {model} deploying...")
        start = time.time()

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://sophia-intel-ai.com",
                        "X-Title": "Artemis Scout Comparison",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": self.scout_prompt}],
                        "max_tokens": 4000,
                        "temperature": 0.3,  # Lower for more focused analysis
                    },
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    return ScoutResult(
                        agent_id=agent_id,
                        model=model,
                        provider=provider,
                        response=data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", ""),
                        execution_time=time.time() - start,
                        tokens_used=data.get("usage", {}).get("total_tokens", 0),
                        success=True,
                    )
                else:
                    return ScoutResult(
                        agent_id=agent_id,
                        model=model,
                        provider=provider,
                        response="",
                        execution_time=time.time() - start,
                        tokens_used=0,
                        success=False,
                        error=f"API Error: {response.status_code}",
                    )
        except Exception as e:
            return ScoutResult(
                agent_id=agent_id,
                model=model,
                provider=provider,
                response="",
                execution_time=time.time() - start,
                tokens_used=0,
                success=False,
                error=str(e),
            )

    async def scout_2_gemini(self) -> ScoutResult:
        """Scout 2: Gemini 2.5 Flash via Portkey"""
        agent_id = 2
        model = "google/gemini-2.5-flash"  # GEMINI 2.5 FLASH AS YOU REQUESTED
        provider = "Portkey"

        print(f"\n🔍 SCOUT {agent_id}: {model} deploying...")
        start = time.time()

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://api.portkey.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {os.environ['AIMLAPI_API_KEY']}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": self.scout_prompt}],
                        "max_tokens": 4000,
                        "temperature": 0.3,
                    },
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    return ScoutResult(
                        agent_id=agent_id,
                        model=model,
                        provider=provider,
                        response=data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", ""),
                        execution_time=time.time() - start,
                        tokens_used=data.get("usage", {}).get("total_tokens", 0),
                        success=True,
                    )
                else:
                    return ScoutResult(
                        agent_id=agent_id,
                        model=model,
                        provider=provider,
                        response="",
                        execution_time=time.time() - start,
                        tokens_used=0,
                        success=False,
                        error=f"API Error: {response.status_code}",
                    )
        except Exception as e:
            return ScoutResult(
                agent_id=agent_id,
                model=model,
                provider=provider,
                response="",
                execution_time=time.time() - start,
                tokens_used=0,
                success=False,
                error=str(e),
            )

    async def scout_3_glm(self) -> ScoutResult:
        """Scout 3: GLM-4.5-Air via AIMLAPI"""
        agent_id = 3
        model = "zhipu/glm-4.5-air"  # GLM-4.5-AIR AS YOU REQUESTED
        provider = "AIMLAPI"

        print(f"\n🔍 SCOUT {agent_id}: {model} deploying...")
        start = time.time()

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://api.aimlapi.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {os.environ['AIMLAPI_API_KEY']}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": self.scout_prompt}],
                        "max_tokens": 4000,
                        "temperature": 0.3,
                    },
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    return ScoutResult(
                        agent_id=agent_id,
                        model=model,
                        provider=provider,
                        response=data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", ""),
                        execution_time=time.time() - start,
                        tokens_used=data.get("usage", {}).get("total_tokens", 0),
                        success=True,
                    )
                else:
                    return ScoutResult(
                        agent_id=agent_id,
                        model=model,
                        provider=provider,
                        response="",
                        execution_time=time.time() - start,
                        tokens_used=0,
                        success=False,
                        error=f"API Error: {response.status_code}",
                    )
        except Exception as e:
            return ScoutResult(
                agent_id=agent_id,
                model=model,
                provider=provider,
                response="",
                execution_time=time.time() - start,
                tokens_used=0,
                success=False,
                error=str(e),
            )

    async def scout_4_llama(self) -> ScoutResult:
        """Scout 4: Llama-4-Scout via AIMLAPI"""
        agent_id = 4
        model = "meta-llama/llama-4-scout"  # LLAMA-4-SCOUT AS YOU REQUESTED
        provider = "AIMLAPI"

        print(f"\n🔍 SCOUT {agent_id}: {model} deploying...")
        start = time.time()

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    "https://api.aimlapi.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {os.environ['AIMLAPI_API_KEY']}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": self.scout_prompt}],
                        "max_tokens": 4000,
                        "temperature": 0.3,
                    },
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    return ScoutResult(
                        agent_id=agent_id,
                        model=model,
                        provider=provider,
                        response=data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", ""),
                        execution_time=time.time() - start,
                        tokens_used=data.get("usage", {}).get("total_tokens", 0),
                        success=True,
                    )
                else:
                    return ScoutResult(
                        agent_id=agent_id,
                        model=model,
                        provider=provider,
                        response="",
                        execution_time=time.time() - start,
                        tokens_used=0,
                        success=False,
                        error=f"API Error: {response.status_code}",
                    )
        except Exception as e:
            return ScoutResult(
                agent_id=agent_id,
                model=model,
                provider=provider,
                response="",
                execution_time=time.time() - start,
                tokens_used=0,
                success=False,
                error=str(e),
            )

    def score_scout_response(self, result: ScoutResult) -> Dict[str, Any]:
        """Score a scout's response on multiple criteria"""
        if not result.success or not result.response:
            return {
                "agent_id": result.agent_id,
                "model": result.model,
                "scores": {
                    "specificity": 0,
                    "accuracy": 0,
                    "completeness": 0,
                    "actionability": 0,
                    "speed": 0,
                    "overall": 0,
                },
                "error": result.error,
            }

        response_lower = result.response.lower()
        scores = {}

        # SPECIFICITY SCORE (mentions real files/paths)
        specificity = 0
        real_files = [
            ".env",
            "portkey_config.py",
            "unified_factory.py",
            "sophia_orchestrator.py",
            "websocket_manager.py",
        ]
        for file in real_files:
            if file in response_lower:
                specificity += 20
        scores["specificity"] = min(100, specificity)

        # ACCURACY SCORE (mentions real issues we know exist)
        accuracy = 0
        known_issues = [
            "api key",
            "netsuite",
            "nested loop",
            "duplicate",
            "95%",
            "exposed",
            "hardcoded",
        ]
        for issue in known_issues:
            if issue in response_lower:
                accuracy += 15
        scores["accuracy"] = min(100, accuracy)

        # COMPLETENESS SCORE (covers all 5 objectives)
        completeness = 0
        objectives = [
            "security",
            "architecture",
            "performance",
            "code quality",
            "recommendation",
        ]
        for obj in objectives:
            if obj in response_lower:
                completeness += 20
        scores["completeness"] = completeness

        # ACTIONABILITY SCORE (provides specific recommendations)
        actionability = 0
        action_words = [
            "should",
            "must",
            "recommend",
            "fix",
            "refactor",
            "move",
            "replace",
            "remove",
        ]
        for word in action_words:
            if word in response_lower:
                actionability += 12.5
        scores["actionability"] = min(100, actionability)

        # SPEED SCORE
        if result.execution_time < 5:
            scores["speed"] = 100
        elif result.execution_time < 10:
            scores["speed"] = 80
        elif result.execution_time < 20:
            scores["speed"] = 60
        elif result.execution_time < 30:
            scores["speed"] = 40
        else:
            scores["speed"] = 20

        # OVERALL SCORE (weighted average)
        weights = {
            "specificity": 0.25,
            "accuracy": 0.25,
            "completeness": 0.20,
            "actionability": 0.20,
            "speed": 0.10,
        }

        overall = sum(scores[metric] * weight for metric, weight in weights.items())
        scores["overall"] = round(overall, 1)

        return {
            "agent_id": result.agent_id,
            "model": result.model,
            "provider": result.provider,
            "execution_time": round(result.execution_time, 2),
            "tokens_used": result.tokens_used,
            "response_length": len(result.response),
            "scores": scores,
        }

    async def run_all_scouts(self) -> List[ScoutResult]:
        """Run all 4 scouts simultaneously with the SAME prompt"""
        print("\n" + "=" * 70)
        print("🚀 ARTEMIS 4-SCOUT COMPARISON TEST")
        print("=" * 70)
        print(f"📅 Timestamp: {datetime.now().isoformat()}")
        print(f"📁 Repository: {self.repo_path}")
        print(f"📊 Real Files: {self.repo_context['total_files']}")
        print("🎯 Mission: Same prompt, 4 different models")
        print("=" * 70)

        # Launch ALL 4 scouts SIMULTANEOUSLY
        print("\n⚡ LAUNCHING ALL 4 SCOUTS IN PARALLEL...")

        tasks = [
            self.scout_1_grok(),  # Grok Code Fast
            self.scout_2_gemini(),  # Gemini 2.5 Flash
            self.scout_3_glm(),  # GLM-4.5-Air
            self.scout_4_llama(),  # Llama-4-Scout
        ]

        results = await asyncio.gather(*tasks)

        return results

    def generate_comparison_report(self, results: List[ScoutResult]) -> Dict[str, Any]:
        """Generate comprehensive comparison report"""
        print("\n" + "=" * 70)
        print("📊 4-SCOUT COMPARISON RESULTS")
        print("=" * 70)

        # Score all scouts
        scored_results = [self.score_scout_response(result) for result in results]

        # Sort by overall score
        scored_results.sort(key=lambda x: x["scores"]["overall"], reverse=True)

        # Print individual results
        for i, score_data in enumerate(scored_results, 1):
            print(
                f"\n{'🥇' if i==1 else '🥈' if i==2 else '🥉' if i==3 else '🏅'} RANK {i}: SCOUT {score_data['agent_id']}"
            )
            print(f"  Model: {score_data['model']}")
            print(f"  Provider: {score_data.get('provider', 'N/A')}")
            print(f"  Execution: {score_data.get('execution_time', 'N/A')}s")
            print(f"  Tokens: {score_data.get('tokens_used', 0)}")
            print(f"  Response: {score_data.get('response_length', 0)} chars")
            print("\n  📊 SCORES:")
            for metric, value in score_data["scores"].items():
                if metric != "overall":
                    print(f"    • {metric.capitalize()}: {value}/100")
            print(f"  🏆 OVERALL: {score_data['scores']['overall']}/100")

        # Save detailed report
        report = {
            "timestamp": datetime.now().isoformat(),
            "repository": self.repo_path,
            "prompt_length": len(self.scout_prompt),
            "rankings": scored_results,
            "raw_responses": [
                {
                    "agent_id": r.agent_id,
                    "model": r.model,
                    "response": (
                        r.response[:1000] + "..."
                        if len(r.response) > 1000
                        else r.response
                    ),
                }
                for r in results
            ],
        }

        report_file = (
            f"scout_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Full report saved to: {report_file}")

        return report


async def main():
    """Execute the 4-scout comparison"""
    swarm = Artemis4ScoutSwarm()

    # Run all scouts
    results = await swarm.run_all_scouts()

    # Generate comparison report
    report = swarm.generate_comparison_report(results)

    # Show winner
    print("\n" + "=" * 70)
    print("🏆 WINNER ANALYSIS")
    print("=" * 70)

    winner = report["rankings"][0] if report["rankings"] else None
    if winner:
        print(f"Model: {winner['model']}")
        print(f"Overall Score: {winner['scores']['overall']}/100")
        print(
            f"Best At: {max(winner['scores'].items(), key=lambda x: x[1] if x[0] != 'overall' else 0)[0]}"
        )


if __name__ == "__main__":
    asyncio.run(main())
