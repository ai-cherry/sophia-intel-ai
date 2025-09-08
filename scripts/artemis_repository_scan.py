#!/usr/bin/env python3
"""
Artemis Microswarm Repository Scanner
Uses 3 specialized agents to comprehensively analyze the codebase
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.artemis.unified_factory import ArtemisUnifiedFactory
from app.core.enhanced_llm_router import LLMProviderType, enhanced_router


class ArtemisMicroswarm:
    """Artemis microswarm for repository analysis"""

    def __init__(self):
        self.factory = ArtemisUnifiedFactory()
        self.results = {}

    def agent1_redundancy_scanner(self) -> Dict[str, Any]:
        """Agent 1: Grok Code Fast 1 - Scan for redundancies"""
        print("\n🚀 Agent 1: Grok Code Fast 1 - Redundancy Scanner")
        print("=" * 70)

        messages = [
            {
                "role": "system",
                "content": """You are a specialized code analysis agent using Grok Code Fast 1.
Your mission: Perform deep redundancy analysis of the sophia-intel-ai repository.

Focus on:
1. Code Redundancies:
   - Duplicate functions/methods across files
   - Similar patterns that could be abstracted
   - Repeated configuration blocks
   - Redundant imports

2. Architectural Redundancies:
   - Multiple implementations of similar functionality
   - Overlapping services or modules
   - Duplicate API endpoints
   - Redundant data models

3. Configuration Redundancies:
   - Duplicate environment variables
   - Repeated configuration patterns
   - Multiple config files with overlapping settings

Scan these key directories:
- /app/core/ (configuration and routing)
- /app/artemis/ and /app/sophia/ (compare for duplication)
- /app/orchestrators/ (base class redundancies)
- /app/factories/ (factory pattern duplications)

Provide specific file paths and code snippets where possible.""",
            },
            {
                "role": "user",
                "content": "Scan the entire repository at /Users/lynnmusil/sophia-intel-ai and identify all redundancies. Focus on patterns that appear 3+ times.",
            },
        ]

        try:
            # Use factory's execute_with_agent method
            response = self.factory.execute_with_agent(
                agent_name="code_architect", messages=messages, model_override="grok-code-fast-1"
            )

            return {
                "agent": "Grok Code Fast 1",
                "focus": "Redundancies & Code Patterns",
                "findings": (
                    response.choices[0].message.content
                    if hasattr(response, "choices")
                    else str(response)
                ),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error in Agent 1: {e}")
            return {
                "agent": "Grok Code Fast 1",
                "focus": "Redundancies & Code Patterns",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def agent2_security_analyzer(self) -> Dict[str, Any]:
        """Agent 2: Gemini Flash - Security and secrets analysis"""
        print("\n🔒 Agent 2: Gemini 2.5 Flash - Security Analyzer")
        print("=" * 70)

        messages = [
            {
                "role": "system",
                "content": """You are a specialized security analysis agent using Gemini 2.5 Flash.
Your mission: Analyze security and secrets handling in the sophia-intel-ai repository.

Focus on:
1. Key and Secret Handling:
   - API key storage in /app/core/portkey_config.py
   - AIMLAPI keys in /app/core/aimlapi_config.py
   - Environment variable usage
   - Hardcoded secrets or credentials
   - Virtual key management

2. Security Patterns:
   - Authentication/authorization implementation
   - Token management
   - Session handling
   - Input validation
   - CORS configuration

3. Security Vulnerabilities:
   - Potential injection points
   - Insecure configurations
   - Missing security headers
   - Unprotected endpoints
   - Exposed sensitive data

Examine:
- All config files in /app/core/
- Environment files (.env, .env.template)
- API routes in /app/api/
- WebSocket handlers
- Authentication modules

Identify risks and provide specific remediation recommendations.""",
            },
            {
                "role": "user",
                "content": "Analyze all security aspects, key handling, and potential vulnerabilities in the repository at /Users/lynnmusil/sophia-intel-ai.",
            },
        ]

        try:
            # Use direct router call with Gemini
            response = enhanced_router.create_completion(
                messages=messages,
                model="gemini-2.5-flash",
                provider_type=LLMProviderType.PORTKEY,
                temperature=0.2,
                max_tokens=16384,
            )

            return {
                "agent": "Gemini 2.5 Flash",
                "focus": "Security & Secrets Handling",
                "findings": (
                    response.choices[0].message.content
                    if hasattr(response, "choices")
                    else str(response)
                ),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error in Agent 2: {e}")
            return {
                "agent": "Gemini 2.5 Flash",
                "focus": "Security & Secrets Handling",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def agent3_data_architect(self) -> Dict[str, Any]:
        """Agent 3: Llama-4 Scout - Embeddings, memory, and database analysis"""
        print("\n🧠 Agent 3: Llama-4 Scout - Data Architecture Analyst")
        print("=" * 70)

        messages = [
            {
                "role": "system",
                "content": """You are a specialized data architecture agent using Llama-4 Scout.
Your mission: Analyze embeddings, memory systems, and database structure in sophia-intel-ai.

Focus on:
1. Embedding Strategies:
   - Vector database usage (Pinecone, Weaviate, Qdrant)
   - Embedding models (OpenAI, Cohere, etc.)
   - Chunking strategies
   - Similarity search implementation
   - RAG patterns

2. Memory Systems:
   - Memory modules in /app/memory/
   - Short-term vs long-term memory patterns
   - Memory persistence (Redis, databases)
   - Context window management
   - Conversation history handling

3. Database Structure:
   - Database configurations
   - Connection pooling
   - Schema design
   - Query patterns
   - Caching strategies

Examine:
- /app/memory/ directory
- /app/embeddings/ if exists
- Vector database integrations
- Redis/cache configurations
- Database connection files

Evaluate efficiency and suggest architectural improvements.""",
            },
            {
                "role": "user",
                "content": "Analyze the embedding strategies, memory systems, and database architecture in the repository at /Users/lynnmusil/sophia-intel-ai.",
            },
        ]

        try:
            # Use factory with a different agent
            response = self.factory.execute_with_agent(
                agent_name="system_analyst", messages=messages, model_override="llama-4-scout"
            )

            return {
                "agent": "Llama-4 Scout",
                "focus": "Embeddings, Memory & Database",
                "findings": (
                    response.choices[0].message.content
                    if hasattr(response, "choices")
                    else str(response)
                ),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"Error in Agent 3: {e}")
            return {
                "agent": "Llama-4 Scout",
                "focus": "Embeddings, Memory & Database",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def run_microswarm(self) -> Dict[str, Any]:
        """Execute all three agents sequentially (sync version)"""
        print("\n" + "=" * 70)
        print(" ARTEMIS MICROSWARM REPOSITORY ANALYSIS")
        print(" Launching 3 specialized agents")
        print("=" * 70)

        # Run agents sequentially
        agent1_result = self.agent1_redundancy_scanner()
        agent2_result = self.agent2_security_analyzer()
        agent3_result = self.agent3_data_architect()

        # Compile results
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "swarm_type": "Artemis Microswarm",
            "agent_count": 3,
            "agents": [agent1_result, agent2_result, agent3_result],
        }

        # Save results
        output_file = f"artemis_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n💾 Full results saved to {output_file}")

        return self.results


def main():
    """Main execution"""
    swarm = ArtemisMicroswarm()
    results = swarm.run_microswarm()

    print("\n" + "=" * 70)
    print(" MICROSWARM ANALYSIS COMPLETE")
    print("=" * 70)

    # Display summary
    for agent_result in results["agents"]:
        print(f"\n{'='*70}")
        print(f" Agent: {agent_result.get('agent', 'Unknown')}")
        print(f" Focus: {agent_result.get('focus', 'Unknown')}")
        print(f"{'='*70}")

        if "error" in agent_result:
            print(f"❌ Error: {agent_result['error']}")
        else:
            findings = agent_result.get("findings", "")
            # Show first 1000 chars of findings
            if findings:
                print(findings[:1000] + "..." if len(findings) > 1000 else findings)

    return results


if __name__ == "__main__":
    results = main()
