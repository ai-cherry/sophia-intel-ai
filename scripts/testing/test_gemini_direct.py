#!/usr/bin/env python3
"""
TEST GEMINI WITH UPGRADED API KEY
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class GeminiDirectTest:
    def __init__(self):
        self.repo_path = "/Users/lynnmusil/sophia-intel-ai"
        self.api_key = "AIzaSyA0rewcfUHo87WMEz4a8Og1eAWTslxlgEE"  # Your upgraded key

        # Same prompt as other tests
        import glob

        py_files = glob.glob(f"{self.repo_path}/**/*.py", recursive=True)
        ts_files = glob.glob(f"{self.repo_path}/**/*.ts", recursive=True)

        self.scout_prompt = f"""
MISSION: COMPREHENSIVE REPOSITORY ANALYSIS - sophia-intel-ai

You are an elite scout agent conducting a THOROUGH repository scan.
This is a REAL repository with REAL files. Provide SPECIFIC analysis.

REPOSITORY FACTS:
- Location: {self.repo_path}
- Python files: {len(py_files)}
- TypeScript files: {len(ts_files)}
- Total files: {len(py_files) + len(ts_files)}
- Key directories: /app, /agent-ui, /scripts, /tests, /k8s

YOUR OBJECTIVES:

1. SECURITY ANALYSIS (Priority: CRITICAL)
   - Identify exposed API keys, tokens, passwords
   - Find hardcoded secrets in code
   - Detect unsafe WebSocket implementations
   - Check for SQL injection vulnerabilities
   - Look for XSS/CSRF vulnerabilities
   - CHECK THESE FILES: app/core/portkey_config.py, app/core/aimlapi_config.py, .env, app/api/unified_server.py

2. ARCHITECTURE ANALYSIS (Priority: HIGH)
   - Map the system architecture
   - Identify code duplication (especially in orchestrators)
   - Analyze the dual Sophia/Artemis pattern
   - Find circular dependencies
   - Evaluate the swarm implementation
   - FOCUS ON: app/artemis/unified_factory.py, app/sophia/sophia_orchestrator.py

3. PERFORMANCE ANALYSIS (Priority: HIGH)
   - Find O(n²) or worse algorithms
   - Identify blocking I/O in async functions
   - Detect memory leaks or excessive allocations
   - Find unnecessary database queries
   - Look for inefficient list comprehensions

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
- Found 16 exposed API keys in .env (NETSUITE, PORTKEY, etc.)
- Detected nested loops in app/tools/git_ops.py:31
- Duplicate functions across orchestrator files
- 95% code duplication between Sophia and Artemis factories

BE SPECIFIC. Use real file paths. Provide actionable recommendations.
This is a REAL repository scan, not a simulation.
"""

    async def test_gemini_direct(self):
        """Test Gemini via direct API"""
        print("\n" + "=" * 70)
        print("🚀 TESTING GEMINI 2.0 FLASH VIA DIRECT API")
        print("=" * 70)

        model = "gemini-2.0-flash-exp"  # Latest Gemini model
        start = time.time()

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                # Direct Gemini API endpoint
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [{"parts": [{"text": self.scout_prompt}]}],
                        "generationConfig": {
                            "temperature": 0.3,
                            "maxOutputTokens": 4000,
                        },
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    content = (
                        data.get("candidates", [{}])[0]
                        .get("content", {})
                        .get("parts", [{}])[0]
                        .get("text", "")
                    )
                    exec_time = time.time() - start

                    print("✅ SUCCESS: Gemini 2.0 Flash via Direct API")
                    print(f"  Model: {model}")
                    print(f"  Execution Time: {exec_time:.2f}s")
                    print(f"  Response Length: {len(content)} chars")

                    # Score it
                    score = self.score_response(content, exec_time)
                    print("\n  📊 SCORES:")
                    for metric, value in score.items():
                        print(f"    • {metric}: {value}/100")

                    return {
                        "model": model,
                        "provider": "Google Direct API",
                        "success": True,
                        "execution_time": exec_time,
                        "response_length": len(content),
                        "scores": score,
                        "response_preview": content[:500],
                    }
                else:
                    print(f"❌ FAILED: {response.status_code}")
                    print(f"  Error: {response.text[:500]}")
                    return {"success": False, "error": response.text}

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return {"success": False, "error": str(e)}

    def score_response(self, response, exec_time):
        """Score the response (same scoring as 4-scout test)"""
        response_lower = response.lower()
        scores = {}

        # Specificity (mentions real files)
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
        scores["Specificity"] = min(100, specificity)

        # Accuracy (mentions known issues)
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
        scores["Accuracy"] = min(100, accuracy)

        # Completeness (covers objectives)
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
        scores["Completeness"] = completeness

        # Actionability
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
        scores["Actionability"] = min(100, actionability)

        # Speed
        if exec_time < 5:
            scores["Speed"] = 100
        elif exec_time < 10:
            scores["Speed"] = 80
        elif exec_time < 20:
            scores["Speed"] = 60
        elif exec_time < 30:
            scores["Speed"] = 40
        else:
            scores["Speed"] = 20

        # Overall (weighted)
        weights = {
            "Specificity": 0.25,
            "Accuracy": 0.25,
            "Completeness": 0.20,
            "Actionability": 0.20,
            "Speed": 0.10,
        }

        overall = sum(
            scores.get(metric, 0) * weight for metric, weight in weights.items()
        )
        scores["Overall"] = round(overall, 1)

        return scores


async def main():
    tester = GeminiDirectTest()
    result = await tester.test_gemini_direct()

    if result.get("success"):
        # Update the complete comparison
        print("\n" + "=" * 70)
        print("📊 COMPLETE 5-MODEL COMPARISON WITH GEMINI")
        print("=" * 70)

        all_results = {
            "Grok Code Fast": {"score": 88.5, "time": 17.65, "tokens": 3625},
            "Llama-4-Scout": {"score": 86.0, "time": 11.45, "tokens": 1434},
            "GLM-4.5-Air": {"score": 84.5, "time": 61.98, "tokens": 9485},
            "GPT-4o-mini": {"score": 83.5, "time": 15.10, "tokens": 1665},
            "Gemini 2.0 Flash": {
                "score": result["scores"]["Overall"],
                "time": result["execution_time"],
                "tokens": "N/A (Direct API)",
            },
        }

        # Sort by score
        sorted_models = sorted(
            all_results.items(), key=lambda x: x[1]["score"], reverse=True
        )

        for i, (model, stats) in enumerate(sorted_models, 1):
            medal = (
                "🥇"
                if i == 1
                else "🥈" if i == 2 else "🥉" if i == 3 else "🏅" if i == 4 else "🎖️"
            )
            print(f"\n{medal} RANK {i}: {model}")
            print(f"   Score: {stats['score']}/100")
            print(f"   Time: {stats['time']:.2f}s")
            print(f"   Tokens: {stats['tokens']}")

        # Save complete comparison
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(
            f"complete_5_model_comparison_with_gemini_{timestamp}.json", "w"
        ) as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "all_models": sorted_models,
                    "gemini_details": result,
                },
                f,
                indent=2,
            )

        print(
            f"\n💾 Complete comparison saved to: complete_5_model_comparison_with_gemini_{timestamp}.json"
        )


if __name__ == "__main__":
    asyncio.run(main())
