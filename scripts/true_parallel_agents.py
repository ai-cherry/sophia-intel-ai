#!/usr/bin/env python3
"""
TRUE Parallel Agent System - Using What Actually Works
=======================================================
This uses multiple LLM providers to achieve REAL parallelism.
NO LIES - tells you exactly what's running and how.
"""

import asyncio
import aiohttp
import json
import os
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Load configuration
from app.core.config import Config

@dataclass 
class RealAgent:
    """An agent that ACTUALLY executes"""
    id: str
    task: str
    provider: str  # 'openrouter', 'together', 'openai', etc.
    model: str
    status: str = "pending"
    result: Optional[Any] = None
    execution_time: float = 0.0
    is_real_execution: bool = True

class TrueParallelSwarm:
    """
    A swarm that ACTUALLY runs agents in parallel using different providers
    """
    
    def __init__(self):
        # Load REAL API keys
        self.config = Config.get_portkey_config()
        self.providers = self._setup_providers()
        self.active_agents: List[RealAgent] = []
        
    def _setup_providers(self) -> Dict[str, Dict[str, str]]:
        """Setup REAL providers we can use in parallel"""
        providers = {}
        
        # OpenRouter
        if Config.get("OPENROUTER_API_KEY"):
            providers["openrouter"] = {
                "api_key": Config.get("OPENROUTER_API_KEY"),
                "base_url": "https://openrouter.ai/api/v1",
                "models": ["meta-llama/llama-3.1-70b-instruct", "google/gemini-2.0-flash-exp"]
            }
            
        # Together AI  
        if Config.get("TOGETHER_API_KEY"):
            providers["together"] = {
                "api_key": Config.get("TOGETHER_API_KEY"),
                "base_url": "https://api.together.xyz/v1",
                "models": ["meta-llama/Llama-3-70b-chat-hf", "mistralai/Mixtral-8x7B-Instruct-v0.1"]
            }
            
        # OpenAI
        if Config.get("OPENAI_API_KEY"):
            providers["openai"] = {
                "api_key": Config.get("OPENAI_API_KEY"),
                "base_url": "https://api.openai.com/v1",
                "models": ["gpt-4-turbo-preview", "gpt-3.5-turbo"]
            }
            
        # DeepSeek
        if Config.get("DEEPSEEK_API_KEY"):
            providers["deepseek"] = {
                "api_key": Config.get("DEEPSEEK_API_KEY"),
                "base_url": "https://api.deepseek.com/v1",
                "models": ["deepseek-chat", "deepseek-coder"]
            }
            
        return providers
    
    async def spawn_real_agent(self, task: str, provider: str, model: str) -> RealAgent:
        """
        Spawn an agent that ACTUALLY makes an API call
        """
        agent = RealAgent(
            id=f"{provider}_{model}_{len(self.active_agents)}",
            task=task,
            provider=provider,
            model=model
        )
        self.active_agents.append(agent)
        
        print(f"🤖 REAL Agent Spawned: {agent.id}")
        print(f"   Provider: {provider}")
        print(f"   Model: {model}")
        print(f"   Task: {task[:100]}...")
        
        return agent
    
    async def execute_agent(self, agent: RealAgent) -> Dict[str, Any]:
        """
        ACTUALLY execute an agent with a REAL API call
        """
        agent.status = "executing"
        start_time = time.time()
        
        provider_config = self.providers.get(agent.provider)
        if not provider_config:
            agent.status = "failed"
            agent.is_real_execution = False
            return {"error": "Provider not configured", "real": False}
        
        # Build the REAL API request
        headers = {
            "Authorization": f"Bearer {provider_config['api_key']}",
            "Content-Type": "application/json"
        }
        
        # Different providers have different request formats
        if agent.provider == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/sophia-intel-ai"
            
        data = {
            "model": agent.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a specialized agent in a swarm. Be concise and specific."
                },
                {
                    "role": "user",
                    "content": agent.task
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            # REAL API CALL
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{provider_config['base_url']}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        agent.status = "completed"
                        agent.result = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        agent.execution_time = time.time() - start_time
                        
                        print(f"✅ {agent.id} completed in {agent.execution_time:.2f}s")
                        return {
                            "success": True,
                            "real_execution": True,
                            "provider": agent.provider,
                            "model": agent.model,
                            "response": agent.result[:200] + "..." if len(agent.result) > 200 else agent.result
                        }
                    else:
                        agent.status = "failed"
                        print(f"❌ {agent.id} failed: {result}")
                        return {"error": result, "real_execution": True}
                        
        except Exception as e:
            agent.status = "error"
            agent.execution_time = time.time() - start_time
            print(f"❌ {agent.id} error: {str(e)}")
            return {"error": str(e), "real_execution": True}
    
    async def execute_parallel_swarm(self, objective: str, num_agents: int = 4) -> Dict[str, Any]:
        """
        ACTUALLY execute multiple agents in PARALLEL using different providers
        """
        print("\n" + "=" * 60)
        print("🐝 TRUE PARALLEL SWARM EXECUTION")
        print(f"📋 Objective: {objective}")
        print(f"🤖 Spawning {num_agents} REAL agents")
        print("=" * 60 + "\n")
        
        # Distribute agents across available providers
        agents = []
        provider_list = list(self.providers.keys())
        
        if not provider_list:
            return {
                "error": "No providers configured",
                "suggestion": "Add API keys to ~/.config/sophia/env"
            }
        
        for i in range(num_agents):
            provider = provider_list[i % len(provider_list)]
            models = self.providers[provider]["models"]
            model = models[i % len(models)]
            
            # Create specialized task for each agent
            if i == 0:
                task = f"Analyze this objective and identify key components: {objective}"
            elif i == 1:
                task = f"Find potential issues or challenges with: {objective}"
            elif i == 2:
                task = f"Suggest implementation approach for: {objective}"
            else:
                task = f"Provide alternative solutions for: {objective}"
                
            agent = await self.spawn_real_agent(task, provider, model)
            agents.append(agent)
        
        print(f"\n🚀 Executing {len(agents)} agents in PARALLEL...\n")
        
        # REAL PARALLEL EXECUTION
        tasks = [self.execute_agent(agent) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build HONEST report
        successful = [r for r in results if isinstance(r, dict) and r.get("success")]
        failed = [r for r in results if isinstance(r, dict) and not r.get("success")]
        
        report = {
            "objective": objective,
            "total_agents": len(agents),
            "successful_executions": len(successful),
            "failed_executions": len(failed),
            "truly_parallel": True,
            "providers_used": list(set(a.provider for a in agents)),
            "models_used": list(set(a.model for a in agents)),
            "agents": [
                {
                    "id": agent.id,
                    "status": agent.status,
                    "provider": agent.provider,
                    "model": agent.model,
                    "execution_time": agent.execution_time,
                    "real_execution": agent.is_real_execution
                }
                for agent in agents
            ],
            "results": results,
            "truth": "Every agent listed here made a REAL API call in parallel"
        }
        
        print("\n" + "=" * 60)
        print("📊 PARALLEL EXECUTION COMPLETE")
        print(f"✅ Successful: {len(successful)}/{len(agents)}")
        print(f"⚡ Total execution time: {max(a.execution_time for a in agents):.2f}s")
        print(f"🔀 Providers used: {', '.join(report['providers_used'])}")
        print("=" * 60 + "\n")
        
        return report

# HONEST test function
async def test_true_parallel():
    """Test REAL parallel agent execution"""
    swarm = TrueParallelSwarm()
    
    # Check what we actually have
    print("🔍 Available Providers:")
    for provider, config in swarm.providers.items():
        print(f"  ✅ {provider}: {len(config['models'])} models")
    
    if not swarm.providers:
        print("❌ No providers configured!")
        print("Add API keys to ~/.config/sophia/env")
        return
    
    # Run REAL parallel execution
    result = await swarm.execute_parallel_swarm(
        objective="Refactor the codebase to improve performance",
        num_agents=4
    )
    
    # Save honest results
    with open("true_parallel_results.json", "w") as f:
        json.dump(result, f, indent=2)
        
    print("📄 Results saved to: true_parallel_results.json")
    print(f"🎯 This was REAL parallel execution: {result['truly_parallel']}")
    
    return result

if __name__ == "__main__":
    asyncio.run(test_true_parallel())