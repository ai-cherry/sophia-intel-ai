#!/usr/bin/env python3
"""
ARTEMIS MILITARY SWARM - REAL AGENTS WITH EXACT SPECIFIED MODELS
Uses military-named agents from Artemis factory with proper providers
"""

import asyncio
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict

import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Artemis military factory
from app.artemis.agent_factory import (
    ArtemisAgentFactory,
)
from app.core.aimlapi_config import aimlapi_manager
from app.core.enhanced_llm_router import LLMProviderType, enhanced_router


class ArtemisMilitarySwarm:
    """Real Artemis military swarm with exact specified models"""

    def __init__(self):
        self.factory = ArtemisAgentFactory()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.results = {}

        # Load API keys from environment
        self.setup_api_keys()

        # COMPREHENSIVE REPOSITORY SCAN PROMPT - SAME FOR ALL AGENTS
        self.universal_prompt = {
            "system": """You are a tactical military intelligence agent in the Artemis swarm conducting a comprehensive repository analysis.

MISSION BRIEFING: Complete repository reconnaissance and threat assessment

TACTICAL OBJECTIVES:
1. CODE REDUNDANCIES & VULNERABILITIES
   - Identify duplicate functions/methods (expecting 300+ duplications)
   - Find security vulnerabilities and exposed secrets
   - Locate architectural weaknesses
   - Analyze import redundancies (2600+ statements)
   - Compare /app/artemis/ vs /app/sophia/ tactical differences

2. SECURITY THREAT ASSESSMENT
   - API key exposure in /app/core/portkey_config.py (14 virtual keys)
   - AIMLAPI configuration vulnerabilities
   - WebSocket security gaps
   - Authentication/authorization weaknesses
   - CORS misconfigurations

3. MEMORY & DATA ARCHITECTURE
   - Memory systems in /app/memory/
   - Vector database integration points
   - Embedding strategy effectiveness
   - RAG implementation quality

4. PERFORMANCE & SCALABILITY
   - Connection pooling efficiency
   - Query optimization opportunities
   - Caching strategy gaps
   - Bottleneck identification

PRIORITIZATION MATRIX:
- CRITICAL: Security vulnerabilities, exposed secrets
- HIGH: Architectural redundancies, performance bottlenecks
- MEDIUM: Code duplication, optimization opportunities
- LOW: Style issues, minor improvements

Provide SPECIFIC file paths, line numbers, and actionable tactical recommendations.
Report format: Military-style briefing with clear priorities.""",
            "user": """Execute comprehensive reconnaissance of sophia-intel-ai repository at /Users/lynnmusil/sophia-intel-ai.
Priority: Identify critical vulnerabilities and architectural weaknesses.
Report all findings with military precision and tactical recommendations.""",
        }

    def setup_api_keys(self):
        """Setup API keys for each provider"""
        # These would normally come from environment variables
        self.api_keys = {
            "google": os.getenv("GOOGLE_API_KEY", ""),
            "openrouter": os.getenv("OPENROUTER_API_KEY", ""),
            "aimlapi": os.getenv("AIMLAPI_API_KEY", ""),
            "huggingface": os.getenv("HUGGINGFACE_API_KEY", ""),
            "llama": os.getenv("LLAMA_API_KEY", ""),
        }

    def _run_agent1_gemini(self) -> Dict[str, Any]:
        """Agent 1: RECONNAISSANCE - Gemini 2.5 Flash via direct Google API"""
        start_time = time.time()
        agent_name = "RECON-ALPHA (Gemini 2.5 Flash)"
        model = "gemini-2.5-flash"

        print(f"\n🎯 [T+0.0s] TACTICAL AGENT 1 DEPLOYING: {agent_name}")

        messages = [
            {"role": "system", "content": self.universal_prompt["system"]},
            {"role": "user", "content": self.universal_prompt["user"]},
        ]

        try:
            # Use Google Gemini directly if available
            import google.generativeai as genai

            if self.api_keys["google"]:
                genai.configure(api_key=self.api_keys["google"])
                model_gemini = genai.GenerativeModel("gemini-2.5-flash")

                # Convert messages to Gemini format
                prompt = f"{self.universal_prompt['system']}\n\n{self.universal_prompt['user']}"
                response = model_gemini.generate_content(prompt)

                elapsed = time.time() - start_time
                print(f"✅ [T+{elapsed:.1f}s] RECON-ALPHA: Mission complete")

                return {
                    "agent_number": 1,
                    "agent_name": agent_name,
                    "military_role": "RECONNAISSANCE",
                    "model": model,
                    "provider": "Google Direct API",
                    "execution_time": elapsed,
                    "findings": response.text if response else "No response",
                    "response_length": len(response.text) if response else 0,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                # Fallback to Portkey if no direct key
                response = enhanced_router.create_completion(
                    messages=messages,
                    model="gemini-2.5-flash",
                    provider_type=LLMProviderType.PORTKEY,
                    temperature=0.3,
                    max_tokens=8000,
                )

                elapsed = time.time() - start_time
                content = (
                    response.choices[0].message.content
                    if hasattr(response, "choices")
                    else str(response)
                )
                print(
                    f"✅ [T+{elapsed:.1f}s] RECON-ALPHA: Mission complete (via Portkey)"
                )

                return {
                    "agent_number": 1,
                    "agent_name": agent_name,
                    "military_role": "RECONNAISSANCE",
                    "model": model,
                    "provider": "Portkey Fallback",
                    "execution_time": elapsed,
                    "findings": content,
                    "response_length": len(content),
                    "timestamp": datetime.now().isoformat(),
                }

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ [T+{elapsed:.1f}s] RECON-ALPHA: Mission failed - {str(e)[:100]}")
            return {
                "agent_number": 1,
                "agent_name": agent_name,
                "military_role": "RECONNAISSANCE",
                "execution_time": elapsed,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _run_agent2_grok(self) -> Dict[str, Any]:
        """Agent 2: STRIKE TEAM - Grok Code Fast via OpenRouter"""
        start_time = time.time()
        agent_name = "STRIKE-BRAVO (Grok Code Fast 1)"
        model = "x-ai/grok-code-fast-1"

        print(f"\n⚡ [T+0.0s] TACTICAL AGENT 2 DEPLOYING: {agent_name}")

        try:
            # Use OpenRouter directly
            if self.api_keys["openrouter"]:
                client = httpx.Client()
                response = client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_keys['openrouter']}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "sophia-intel-ai",
                        "X-Title": "Artemis Military Swarm",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": self.universal_prompt["system"],
                            },
                            {"role": "user", "content": self.universal_prompt["user"]},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 8000,
                    },
                    timeout=60.0,
                )

                elapsed = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    content = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "No response")
                    )
                    print(f"✅ [T+{elapsed:.1f}s] STRIKE-BRAVO: Target neutralized")

                    return {
                        "agent_number": 2,
                        "agent_name": agent_name,
                        "military_role": "STRIKE TEAM",
                        "model": model,
                        "provider": "OpenRouter Direct",
                        "execution_time": elapsed,
                        "findings": content,
                        "response_length": len(content),
                        "timestamp": datetime.now().isoformat(),
                    }
                else:
                    raise Exception(f"OpenRouter error: {response.status_code}")
            else:
                raise Exception("No OpenRouter API key")

        except Exception as e:
            elapsed = time.time() - start_time
            print(
                f"❌ [T+{elapsed:.1f}s] STRIKE-BRAVO: Mission failed - {str(e)[:100]}"
            )
            return {
                "agent_number": 2,
                "agent_name": agent_name,
                "military_role": "STRIKE TEAM",
                "execution_time": elapsed,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _run_agent3_glm(self) -> Dict[str, Any]:
        """Agent 3: INTELLIGENCE - GLM-4.5-Air via AIMLAPI"""
        start_time = time.time()
        agent_name = "INTEL-CHARLIE (GLM-4.5-Air)"
        model = "zhipu/glm-4.5-air"

        print(f"\n🔍 [T+0.0s] TACTICAL AGENT 3 DEPLOYING: {agent_name}")

        messages = [
            {"role": "system", "content": self.universal_prompt["system"]},
            {"role": "user", "content": self.universal_prompt["user"]},
        ]

        try:
            # Use AIMLAPI directly
            response = aimlapi_manager.chat_completion(
                model=model, messages=messages, temperature=0.3, max_tokens=8000
            )

            elapsed = time.time() - start_time

            # Extract content properly
            if hasattr(response, "choices"):
                content = response.choices[0].message.content
            elif isinstance(response, dict) and "choices" in response:
                content = response["choices"][0]["message"]["content"]
            else:
                content = str(response)

            print(f"✅ [T+{elapsed:.1f}s] INTEL-CHARLIE: Intelligence gathered")

            return {
                "agent_number": 3,
                "agent_name": agent_name,
                "military_role": "INTELLIGENCE",
                "model": model,
                "provider": "AIMLAPI",
                "execution_time": elapsed,
                "findings": content,
                "response_length": len(content) if content else 0,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            elapsed = time.time() - start_time
            print(
                f"❌ [T+{elapsed:.1f}s] INTEL-CHARLIE: Mission failed - {str(e)[:100]}"
            )
            return {
                "agent_number": 3,
                "agent_name": agent_name,
                "military_role": "INTELLIGENCE",
                "execution_time": elapsed,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _run_agent4_llama(self) -> Dict[str, Any]:
        """Agent 4: SCOUT - Llama-4-Scout via HuggingFace or Llama API"""
        start_time = time.time()
        agent_name = "SCOUT-DELTA (Llama-4-Scout)"
        model = "meta-llama/llama-4-scout"

        print(f"\n🎯 [T+0.0s] TACTICAL AGENT 4 DEPLOYING: {agent_name}")

        messages = [
            {"role": "system", "content": self.universal_prompt["system"]},
            {"role": "user", "content": self.universal_prompt["user"]},
        ]

        try:
            # Try HuggingFace first if available
            if self.api_keys["huggingface"]:
                # Use HuggingFace Inference API
                client = httpx.Client()
                response = client.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    headers={
                        "Authorization": f"Bearer {self.api_keys['huggingface']}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "inputs": f"{self.universal_prompt['system']}\n\n{self.universal_prompt['user']}",
                        "parameters": {"temperature": 0.3, "max_new_tokens": 8000},
                    },
                    timeout=60.0,
                )

                elapsed = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    content = (
                        data[0].get("generated_text", "")
                        if isinstance(data, list)
                        else str(data)
                    )
                    print(f"✅ [T+{elapsed:.1f}s] SCOUT-DELTA: Reconnaissance complete")

                    return {
                        "agent_number": 4,
                        "agent_name": agent_name,
                        "military_role": "SCOUT",
                        "model": model,
                        "provider": "HuggingFace",
                        "execution_time": elapsed,
                        "findings": content,
                        "response_length": len(content),
                        "timestamp": datetime.now().isoformat(),
                    }

            # Fallback to AIMLAPI
            response = aimlapi_manager.chat_completion(
                model=model, messages=messages, temperature=0.3, max_tokens=8000
            )

            elapsed = time.time() - start_time

            if hasattr(response, "choices"):
                content = response.choices[0].message.content
            else:
                content = str(response)

            print(
                f"✅ [T+{elapsed:.1f}s] SCOUT-DELTA: Reconnaissance complete (via AIMLAPI)"
            )

            return {
                "agent_number": 4,
                "agent_name": agent_name,
                "military_role": "SCOUT",
                "model": model,
                "provider": "AIMLAPI Fallback",
                "execution_time": elapsed,
                "findings": content,
                "response_length": len(content) if content else 0,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ [T+{elapsed:.1f}s] SCOUT-DELTA: Mission failed - {str(e)[:100]}")
            return {
                "agent_number": 4,
                "agent_name": agent_name,
                "military_role": "SCOUT",
                "execution_time": elapsed,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def deploy_military_swarm(self) -> Dict[str, Any]:
        """Deploy all 4 tactical agents SIMULTANEOUSLY"""
        print("\n" + "=" * 70)
        print(" ARTEMIS MILITARY SWARM DEPLOYMENT")
        print(" 4 Tactical Agents - Simultaneous Strike")
        print("=" * 70)
        print("\n📋 MISSION: Comprehensive Repository Analysis")
        print("🎯 OBJECTIVE: Identify vulnerabilities and weaknesses")
        print("\n⚔️ TACTICAL UNITS:")
        print("  • RECON-ALPHA: Gemini 2.5 Flash (Google Direct)")
        print("  • STRIKE-BRAVO: Grok Code Fast 1 (OpenRouter)")
        print("  • INTEL-CHARLIE: GLM-4.5-Air (AIMLAPI)")
        print("  • SCOUT-DELTA: Llama-4-Scout (HuggingFace/AIMLAPI)\n")

        start_time = time.time()

        # DEPLOY ALL AGENTS SIMULTANEOUSLY
        print("🚁 DEPLOYING ALL TACTICAL UNITS SIMULTANEOUSLY...")

        loop = asyncio.get_event_loop()

        # Launch all agents in parallel
        tasks = [
            loop.run_in_executor(self.executor, self._run_agent1_gemini),
            loop.run_in_executor(self.executor, self._run_agent2_grok),
            loop.run_in_executor(self.executor, self._run_agent3_glm),
            loop.run_in_executor(self.executor, self._run_agent4_llama),
        ]

        # Wait for all to complete
        results = await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # Compile results
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "swarm_type": "Artemis Military Swarm",
            "execution_mode": "SIMULTANEOUS TACTICAL DEPLOYMENT",
            "total_execution_time": total_time,
            "agent_count": 4,
            "agents": results,
        }

        # Save results
        output_file = (
            f"artemis_military_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n⏱️  Total Mission Time: {total_time:.1f} seconds")
        print(f"💾 Mission report saved to {output_file}")

        return self.results

    def score_agent_outputs(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Score each agent's output on multiple criteria"""
        scoring_report = {
            "mission": "Repository Analysis Scoring",
            "timestamp": datetime.now().isoformat(),
            "agents_scored": [],
        }

        for agent in results["agents"]:
            if "error" not in agent:
                findings = agent.get("findings", "")

                # Scoring criteria (0-10 scale)
                scores = {
                    "quality": 0,
                    "speed": 0,
                    "accuracy": 0,
                    "thoroughness": 0,
                    "prioritization": 0,
                    "communication": 0,
                }

                # Quality - based on response length and structure
                if len(findings) > 5000:
                    scores["quality"] = 9
                elif len(findings) > 3000:
                    scores["quality"] = 7
                elif len(findings) > 1000:
                    scores["quality"] = 5
                else:
                    scores["quality"] = 3

                # Speed - based on execution time
                exec_time = agent.get("execution_time", 999)
                if exec_time < 10:
                    scores["speed"] = 10
                elif exec_time < 20:
                    scores["speed"] = 8
                elif exec_time < 30:
                    scores["speed"] = 6
                else:
                    scores["speed"] = 4

                # Accuracy - check for specific keywords
                accuracy_keywords = [
                    "redundancy",
                    "security",
                    "vulnerability",
                    "memory",
                    "performance",
                ]
                found_keywords = sum(
                    1 for kw in accuracy_keywords if kw.lower() in findings.lower()
                )
                scores["accuracy"] = min(10, found_keywords * 2)

                # Thoroughness - check coverage of areas
                areas = ["CODE", "SECURITY", "MEMORY", "PERFORMANCE"]
                covered_areas = sum(1 for area in areas if area in findings.upper())
                scores["thoroughness"] = min(10, covered_areas * 2.5)

                # Prioritization - check for priority markers
                priority_markers = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
                has_priorities = sum(
                    1 for marker in priority_markers if marker in findings.upper()
                )
                scores["prioritization"] = min(10, has_priorities * 2.5)

                # Communication - clarity and structure
                if "###" in findings or "##" in findings:  # Has headers
                    scores["communication"] += 3
                if "•" in findings or "-" in findings:  # Has bullet points
                    scores["communication"] += 3
                if (
                    "file" in findings.lower() or "path" in findings.lower()
                ):  # Specific references
                    scores["communication"] += 4

                # Calculate total score
                total_score = sum(scores.values()) / 6  # Average of all criteria

                agent_score = {
                    "agent_name": agent["agent_name"],
                    "military_role": agent.get("military_role", "Unknown"),
                    "model": agent.get("model", "Unknown"),
                    "provider": agent.get("provider", "Unknown"),
                    "scores": scores,
                    "total_score": round(total_score, 2),
                    "execution_time": agent.get("execution_time", 0),
                    "response_length": agent.get("response_length", 0),
                }

                scoring_report["agents_scored"].append(agent_score)
            else:
                # Failed agent
                scoring_report["agents_scored"].append(
                    {
                        "agent_name": agent.get("agent_name", "Unknown"),
                        "military_role": agent.get("military_role", "Unknown"),
                        "status": "FAILED",
                        "error": agent.get("error", "Unknown error"),
                    }
                )

        # Rank agents by total score
        successful_agents = [
            a for a in scoring_report["agents_scored"] if "total_score" in a
        ]
        if successful_agents:
            successful_agents.sort(key=lambda x: x["total_score"], reverse=True)
            for i, agent in enumerate(successful_agents):
                agent["rank"] = i + 1

        return scoring_report


async def main():
    """Main execution with military precision"""
    swarm = ArtemisMilitarySwarm()

    print("🎖️ INITIALIZING ARTEMIS MILITARY COMMAND")
    print("📍 Target: /Users/lynnmusil/sophia-intel-ai")
    print("🎯 Mission: Full repository tactical analysis\n")

    # Deploy the swarm
    results = await swarm.deploy_military_swarm()

    print("\n" + "=" * 70)
    print(" TACTICAL ANALYSIS COMPLETE")
    print("=" * 70)

    # Display mission results
    successful = 0
    failed = 0

    for agent in results["agents"]:
        print(f"\n{'='*70}")
        print(
            f" {agent.get('military_role', 'UNKNOWN')}: {agent.get('agent_name', 'Unknown')}"
        )
        if "model" in agent:
            print(f" Model: {agent['model']}")
            print(f" Provider: {agent.get('provider', 'Unknown')}")
            print(f" Mission Time: {agent.get('execution_time', 0):.1f}s")
        print(f"{'='*70}")

        if "error" not in agent:
            successful += 1
            findings = agent.get("findings", "")
            print("✅ Mission Success")
            print(f"📊 Intel Gathered: {agent.get('response_length', 0):,} characters")

            # Show preview
            if findings and len(findings) > 100:
                print("\n📋 Intel Preview:")
                print(findings[:500] + "..." if len(findings) > 500 else findings)
        else:
            failed += 1
            print(f"❌ Mission Failed: {agent['error'][:200]}")

    # Score the outputs
    print("\n" + "=" * 70)
    print(" SCORING AGENT PERFORMANCE")
    print("=" * 70)

    scoring_report = swarm.score_agent_outputs(results)

    # Display scores
    for agent_score in scoring_report["agents_scored"]:
        if "total_score" in agent_score:
            print(f"\n🎖️ {agent_score['agent_name']}")
            print(f"   Role: {agent_score['military_role']}")
            print(f"   Model: {agent_score['model']}")
            print(f"   Provider: {agent_score['provider']}")
            print("   📊 Scores:")
            for criterion, score in agent_score["scores"].items():
                print(f"      • {criterion.capitalize()}: {score}/10")
            print(f"   🏆 Total Score: {agent_score['total_score']}/10")
            if "rank" in agent_score:
                print(f"   🥇 Rank: #{agent_score['rank']}")
        else:
            print(
                f"\n❌ {agent_score['agent_name']}: {agent_score.get('status', 'FAILED')}"
            )

    # Summary
    print("\n" + "=" * 70)
    print(" MISSION SUMMARY")
    print("=" * 70)
    print("  • Agents Deployed: 4")
    print(f"  • Successful: {successful}")
    print(f"  • Failed: {failed}")
    print(f"  • Total Time: {results['total_execution_time']:.1f}s")

    # Save scoring report
    scoring_file = f"artemis_scoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(scoring_file, "w") as f:
        json.dump(scoring_report, f, indent=2)
    print(f"  • Scoring Report: {scoring_file}")

    return results, scoring_report


if __name__ == "__main__":
    print("⚔️ ARTEMIS MILITARY SWARM ACTIVATION")
    print("=" * 70)
    results, scores = asyncio.run(main())
