#!/usr/bin/env python3
"""
Test Suite for True Parallel Execution with Portkey Virtual Keys

This test suite verifies that our swarm system achieves TRUE parallelism
by using different virtual keys that route to different providers.
"""

import asyncio
import time
import os
import sys
from typing import Dict, List, Any
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portkey_ai import Portkey
from app.swarms.core.portkey_virtual_keys import (
    PORTKEY_VIRTUAL_KEYS,
    PROVIDER_CONFIGS,
    calculate_swarm_capacity,
    VirtualKeyAllocator
)


class ParallelExecutionTester:
    """Test true parallel execution with Portkey virtual keys"""
    
    def __init__(self):
        self.portkey_api_key = os.getenv("PORTKEY_API_KEY")
        if not self.portkey_api_key:
            raise ValueError("PORTKEY_API_KEY not set in environment")
        
        self.results = []
        self.clients = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Portkey clients for each virtual key"""
        
        for name, virtual_key in PORTKEY_VIRTUAL_KEYS.items():
            if virtual_key and virtual_key in PROVIDER_CONFIGS:
                try:
                    client = Portkey(
                        api_key=self.portkey_api_key,
                        virtual_key=virtual_key
                    )
                    self.clients[name] = {
                        "client": client,
                        "virtual_key": virtual_key,
                        "config": PROVIDER_CONFIGS[virtual_key]
                    }
                    print(f"✅ Initialized client for {name}: {virtual_key}")
                except Exception as e:
                    print(f"❌ Failed to initialize {name}: {e}")
    
    async def test_single_provider(self, provider_name: str, prompt: str) -> Dict[str, Any]:
        """Test a single provider"""
        
        if provider_name not in self.clients:
            return {"error": f"Provider {provider_name} not configured"}
        
        client_info = self.clients[provider_name]
        client = client_info["client"]
        config = client_info["config"]
        
        # Select appropriate model for this provider
        model = config["models"][0] if config["models"] else "gpt-4"
        
        start_time = time.time()
        
        try:
            response = await asyncio.to_thread(
                client.chat.completions.create,
                model=model,
                messages=[
                    {"role": "system", "content": f"You are testing {provider_name}"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            elapsed = time.time() - start_time
            
            return {
                "provider": provider_name,
                "virtual_key": client_info["virtual_key"],
                "model": model,
                "response_length": len(response.choices[0].message.content),
                "elapsed_time": elapsed,
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "provider": provider_name,
                "virtual_key": client_info["virtual_key"],
                "model": model,
                "error": str(e),
                "elapsed_time": elapsed,
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_parallel_execution(
        self,
        providers: List[str],
        prompt: str = "Write a haiku about parallel computing"
    ) -> Dict[str, Any]:
        """
        Test TRUE parallel execution across multiple providers.
        
        If execution is truly parallel, max(times) should be close to individual times.
        If serial, sum(times) would be close to total time.
        """
        
        print(f"\n{'='*70}")
        print(f"TESTING PARALLEL EXECUTION")
        print(f"{'='*70}")
        print(f"Providers: {providers}")
        print(f"Prompt: {prompt}")
        print(f"{'='*70}\n")
        
        # Create tasks for parallel execution
        tasks = []
        for provider in providers:
            if provider in self.clients:
                tasks.append(self.test_single_provider(provider, prompt))
            else:
                print(f"⚠️  Skipping {provider} - not configured")
        
        if not tasks:
            return {"error": "No valid providers to test"}
        
        # Execute all tasks in parallel
        print(f"🚀 Launching {len(tasks)} parallel requests at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        
        overall_start = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        overall_elapsed = time.time() - overall_start
        
        # Analyze results
        successful_results = []
        failed_results = []
        individual_times = []
        
        for result in results:
            if isinstance(result, Exception):
                failed_results.append(str(result))
            elif result.get("success"):
                successful_results.append(result)
                individual_times.append(result["elapsed_time"])
            else:
                failed_results.append(result)
        
        # Calculate parallelism metrics
        if individual_times:
            max_time = max(individual_times)
            sum_time = sum(individual_times)
            avg_time = sum_time / len(individual_times)
            
            # Parallelism ratio: how close to perfect parallelism?
            # Perfect = max_time / overall_elapsed = 1.0
            # Serial = sum_time / overall_elapsed = 1.0
            parallelism_ratio = max_time / overall_elapsed if overall_elapsed > 0 else 0
            
            # Speedup factor
            theoretical_serial_time = sum_time
            actual_parallel_time = overall_elapsed
            speedup = theoretical_serial_time / actual_parallel_time if actual_parallel_time > 0 else 1
            
        else:
            max_time = sum_time = avg_time = 0
            parallelism_ratio = speedup = 0
        
        # Print results
        print(f"\n{'='*70}")
        print(f"RESULTS")
        print(f"{'='*70}")
        
        print(f"\n📊 Execution Statistics:")
        print(f"   Total Providers Tested: {len(tasks)}")
        print(f"   Successful: {len(successful_results)}")
        print(f"   Failed: {len(failed_results)}")
        
        print(f"\n⏱️  Timing Analysis:")
        print(f"   Overall Execution Time: {overall_elapsed:.2f}s")
        print(f"   Individual Times: {[f'{t:.2f}s' for t in individual_times]}")
        print(f"   Max Individual Time: {max_time:.2f}s")
        print(f"   Sum of Individual Times: {sum_time:.2f}s")
        
        print(f"\n🎯 Parallelism Metrics:")
        print(f"   Parallelism Ratio: {parallelism_ratio:.2%} (100% = perfect parallel)")
        print(f"   Speedup Factor: {speedup:.2f}x")
        
        if speedup > len(tasks) * 0.7:  # 70% of theoretical max
            print(f"   ✅ TRUE PARALLEL EXECUTION ACHIEVED!")
        elif speedup > len(tasks) * 0.4:
            print(f"   ⚠️  PARTIAL PARALLELISM (some blocking detected)")
        else:
            print(f"   ❌ SERIAL EXECUTION (providers may be sharing rate limits)")
        
        print(f"\n📋 Provider Details:")
        for result in successful_results:
            print(f"   {result['provider']:12} → {result['model']:20} → {result['elapsed_time']:.2f}s")
        
        for result in failed_results:
            if isinstance(result, dict):
                print(f"   {result['provider']:12} → FAILED: {result.get('error', 'Unknown')}")
        
        return {
            "test_type": "parallel_execution",
            "providers_tested": len(tasks),
            "successful": len(successful_results),
            "failed": len(failed_results),
            "overall_time": overall_elapsed,
            "individual_times": individual_times,
            "parallelism_ratio": parallelism_ratio,
            "speedup_factor": speedup,
            "is_truly_parallel": speedup > len(tasks) * 0.7,
            "results": successful_results
        }
    
    async def test_swarm_configuration(self, swarm_type: str = "coding_swarm"):
        """Test a specific swarm configuration"""
        
        from app.swarms.core.portkey_virtual_keys import OPTIMAL_AGENT_MAPPING
        
        if swarm_type not in OPTIMAL_AGENT_MAPPING:
            print(f"❌ Unknown swarm type: {swarm_type}")
            return
        
        mapping = OPTIMAL_AGENT_MAPPING[swarm_type]
        
        print(f"\n{'='*70}")
        print(f"TESTING {swarm_type.upper()} CONFIGURATION")
        print(f"{'='*70}")
        
        # Get unique providers from the mapping
        unique_providers = []
        provider_map = {}
        
        for agent, virtual_key in mapping.items():
            # Find which provider name corresponds to this virtual key
            for provider_name, vk in PORTKEY_VIRTUAL_KEYS.items():
                if vk == virtual_key and provider_name not in unique_providers:
                    unique_providers.append(provider_name)
                    provider_map[agent] = provider_name
                    break
        
        print(f"\nAgent Assignments:")
        for agent, provider in provider_map.items():
            vk = mapping[agent]
            config = PROVIDER_CONFIGS.get(vk, {})
            print(f"   {agent:15} → {provider:12} → {config.get('provider', 'unknown')}")
        
        # Test parallel execution with these providers
        result = await self.test_parallel_execution(
            unique_providers[:4],  # Test up to 4 providers
            f"Generate code for a {swarm_type.replace('_', ' ')}"
        )
        
        return result
    
    async def benchmark_all_providers(self):
        """Benchmark all configured providers"""
        
        print(f"\n{'='*70}")
        print(f"BENCHMARKING ALL PROVIDERS")
        print(f"{'='*70}")
        
        results = {}
        
        for provider_name in self.clients.keys():
            print(f"\n📍 Testing {provider_name}...")
            
            result = await self.test_single_provider(
                provider_name,
                "Return 'OK' if you receive this message"
            )
            
            results[provider_name] = result
            
            if result.get("success"):
                print(f"   ✅ {provider_name}: {result['elapsed_time']:.2f}s")
            else:
                print(f"   ❌ {provider_name}: {result.get('error', 'Failed')}")
        
        # Sort by response time
        successful = [r for r in results.values() if r.get("success")]
        successful.sort(key=lambda x: x["elapsed_time"])
        
        print(f"\n🏆 Performance Ranking:")
        for i, result in enumerate(successful[:10], 1):
            print(f"   {i}. {result['provider']:12} → {result['elapsed_time']:.2f}s → {result['model']}")
        
        return results


async def main():
    """Main test execution"""
    
    print("\n" + "="*70)
    print("PORTKEY VIRTUAL KEYS - PARALLEL EXECUTION TEST SUITE")
    print("="*70)
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv('.env.portkey')
    
    # Validate configuration
    from app.swarms.core.portkey_virtual_keys import validate_virtual_keys
    if not validate_virtual_keys():
        print("❌ Virtual keys validation failed")
        return
    
    # Create tester
    tester = ParallelExecutionTester()
    
    # Test 1: Parallel execution with different providers
    print("\n\n🧪 TEST 1: True Parallel Execution")
    await tester.test_parallel_execution([
        "OPENAI",
        "ANTHROPIC",
        "GROQ",
        "TOGETHER"
    ])
    
    # Test 2: Coding swarm configuration
    print("\n\n🧪 TEST 2: Coding Swarm Configuration")
    await tester.test_swarm_configuration("coding_swarm")
    
    # Test 3: Fast swarm configuration
    print("\n\n🧪 TEST 3: Fast Swarm Configuration")
    await tester.test_swarm_configuration("fast_swarm")
    
    # Test 4: Benchmark all providers
    print("\n\n🧪 TEST 4: Provider Benchmarks")
    await tester.benchmark_all_providers()
    
    # Final summary
    print("\n" + "="*70)
    print("TEST SUITE COMPLETE")
    print("="*70)
    print("\n✅ If speedup factors are close to the number of providers,")
    print("   you have achieved TRUE PARALLEL EXECUTION!")
    print("\n❌ If speedup factors are close to 1.0,")
    print("   your providers may be sharing rate limits.")


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())