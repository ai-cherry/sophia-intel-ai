#!/usr/bin/env python3
"""
Performance Benchmark Script for Agno AgentOS Embedding Infrastructure
Validates performance targets and generates benchmark report
"""

import asyncio
import json
import os
import statistics
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

import numpy as np

# Add project root to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.embeddings.agno_embedding_service import (
    AgnoEmbeddingService,
    AgnoEmbeddingRequest,
    EmbeddingModel,
    MODEL_REGISTRY,
)

# ============================================
# Benchmark Configuration
# ============================================

PERFORMANCE_TARGETS = {
    "single_embedding_latency_ms": 50,      # Target: <50ms for single embedding
    "batch_embedding_latency_ms": 500,      # Target: <500ms for batch of 100
    "cache_hit_rate": 0.5,                  # Target: >50% cache hit rate
    "cost_reduction": 0.3,                  # Target: 30-50% cost reduction
    "throughput_per_second": 20,            # Target: 20+ embeddings per second
    "p95_latency_ms": 100,                  # 95th percentile latency
    "p99_latency_ms": 200,                  # 99th percentile latency
}

# Test datasets
TEST_DATASETS = {
    "short_texts": [
        "Machine learning is transforming AI",
        "Python is great for data science",
        "Cloud computing enables scalability",
        "Neural networks learn patterns",
        "API design is crucial for systems",
    ] * 20,  # 100 short texts
    
    "medium_texts": [
        """Machine learning has revolutionized artificial intelligence by enabling 
        computers to learn from data without being explicitly programmed. This paradigm 
        shift has led to breakthroughs in computer vision, natural language processing, 
        and predictive analytics.""",
        """Python has become the lingua franca of data science due to its simplicity, 
        extensive libraries, and strong community support. Libraries like NumPy, Pandas, 
        and scikit-learn have made complex data operations accessible to developers and 
        researchers worldwide.""",
    ] * 10,  # 20 medium texts
    
    "long_texts": [
        """The field of artificial intelligence has undergone tremendous transformation 
        over the past decade, driven largely by advances in deep learning and neural 
        network architectures. What began as theoretical research in the 1950s has now 
        become a practical reality affecting every aspect of our daily lives. From 
        recommendation systems that power social media feeds to autonomous vehicles 
        navigating city streets, AI has moved from science fiction to science fact.
        
        The key breakthrough came with the realization that neural networks with multiple 
        hidden layers, when combined with vast amounts of data and computational power, 
        could learn increasingly abstract representations of complex patterns. This deep 
        learning revolution was catalyzed by several factors: the availability of big data, 
        advances in GPU computing, and algorithmic innovations like backpropagation and 
        dropout regularization.
        
        Today's AI systems can perform tasks that were once thought to be uniquely human: 
        understanding natural language, recognizing faces in photos, playing complex games 
        at superhuman levels, and even creating art and music. However, these achievements 
        come with challenges. Issues of bias, interpretability, and ethical AI deployment 
        remain active areas of research and debate."""
    ] * 5,  # 5 long texts
    
    "code_samples": [
        """def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)""",
        """class BinarySearchTree:
            def __init__(self):
                self.root = None
                
            def insert(self, value):
                if self.root is None:
                    self.root = TreeNode(value)
                else:
                    self._insert_recursive(self.root, value)""",
    ] * 10,  # 20 code samples
    
    "multilingual": [
        "Hello world",
        "Bonjour le monde",
        "Hola mundo",
        "你好世界",
        "こんにちは世界",
        "مرحبا بالعالم",
        "Здравствуй мир",
        "Olá mundo",
    ] * 5,  # 40 multilingual texts
}

# ============================================
# Benchmark Tests
# ============================================

class EmbeddingBenchmark:
    """Benchmark suite for Agno embedding service"""
    
    def __init__(self):
        self.service = AgnoEmbeddingService()
        self.results = defaultdict(list)
        self.metrics = {}
        
    async def run_all_benchmarks(self):
        """Run complete benchmark suite"""
        print("=" * 80)
        print("AGNO AGENTOS EMBEDDING INFRASTRUCTURE PERFORMANCE BENCHMARK")
        print("=" * 80)
        print(f"Start Time: {datetime.now().isoformat()}")
        print()
        
        # Run individual benchmarks
        await self.benchmark_single_embedding()
        await self.benchmark_batch_embedding()
        await self.benchmark_cache_performance()
        await self.benchmark_model_selection()
        await self.benchmark_concurrent_requests()
        await self.benchmark_cost_efficiency()
        await self.benchmark_different_content_types()
        
        # Generate report
        self.generate_report()
        
    async def benchmark_single_embedding(self):
        """Benchmark single embedding generation"""
        print("1. SINGLE EMBEDDING BENCHMARK")
        print("-" * 40)
        
        latencies = []
        
        for text in TEST_DATASETS["short_texts"][:20]:
            request = AgnoEmbeddingRequest(texts=[text])
            
            start = time.perf_counter()
            response = await self.service.embed(request)
            latency_ms = (time.perf_counter() - start) * 1000
            
            latencies.append(latency_ms)
        
        # Calculate statistics
        avg_latency = statistics.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        p99_latency = np.percentile(latencies, 99)
        
        self.metrics["single_embedding"] = {
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency,
            "p99_latency_ms": p99_latency,
            "min_latency_ms": min(latencies),
            "max_latency_ms": max(latencies),
            "samples": len(latencies)
        }
        
        # Check against target
        passed = avg_latency < PERFORMANCE_TARGETS["single_embedding_latency_ms"]
        status = "✓ PASSED" if passed else "✗ FAILED"
        
        print(f"Average Latency: {avg_latency:.2f}ms (Target: <{PERFORMANCE_TARGETS['single_embedding_latency_ms']}ms) {status}")
        print(f"P95 Latency: {p95_latency:.2f}ms")
        print(f"P99 Latency: {p99_latency:.2f}ms")
        print()
        
    async def benchmark_batch_embedding(self):
        """Benchmark batch embedding generation"""
        print("2. BATCH EMBEDDING BENCHMARK")
        print("-" * 40)
        
        batch_sizes = [10, 50, 100]
        
        for batch_size in batch_sizes:
            texts = TEST_DATASETS["short_texts"][:batch_size]
            request = AgnoEmbeddingRequest(texts=texts)
            
            start = time.perf_counter()
            response = await self.service.embed(request)
            latency_ms = (time.perf_counter() - start) * 1000
            
            throughput = batch_size / (latency_ms / 1000)
            
            self.metrics[f"batch_{batch_size}"] = {
                "latency_ms": latency_ms,
                "throughput_per_second": throughput,
                "embeddings_generated": len(response.embeddings)
            }
            
            print(f"Batch Size {batch_size}:")
            print(f"  Latency: {latency_ms:.2f}ms")
            print(f"  Throughput: {throughput:.2f} embeddings/second")
        
        # Check 100-batch against target
        batch_100_latency = self.metrics["batch_100"]["latency_ms"]
        passed = batch_100_latency < PERFORMANCE_TARGETS["batch_embedding_latency_ms"]
        status = "✓ PASSED" if passed else "✗ FAILED"
        
        print(f"\nBatch-100 Performance: {batch_100_latency:.2f}ms (Target: <{PERFORMANCE_TARGETS['batch_embedding_latency_ms']}ms) {status}")
        print()
        
    async def benchmark_cache_performance(self):
        """Benchmark cache hit rate and performance"""
        print("3. CACHE PERFORMANCE BENCHMARK")
        print("-" * 40)
        
        # Generate embeddings for same texts multiple times
        test_texts = TEST_DATASETS["short_texts"][:10]
        
        # First pass - cache miss
        cache_miss_latencies = []
        for text in test_texts:
            request = AgnoEmbeddingRequest(texts=[text])
            start = time.perf_counter()
            await self.service.embed(request)
            cache_miss_latencies.append((time.perf_counter() - start) * 1000)
        
        # Second pass - cache hit
        cache_hit_latencies = []
        for text in test_texts:
            request = AgnoEmbeddingRequest(texts=[text])
            start = time.perf_counter()
            await self.service.embed(request)
            cache_hit_latencies.append((time.perf_counter() - start) * 1000)
        
        # Calculate cache performance
        avg_cache_miss = statistics.mean(cache_miss_latencies)
        avg_cache_hit = statistics.mean(cache_hit_latencies)
        cache_speedup = avg_cache_miss / avg_cache_hit if avg_cache_hit > 0 else 0
        
        # Get actual cache metrics from service
        service_metrics = self.service.get_metrics()
        cache_hit_rate = service_metrics.get("cache_hit_rate", 0)
        
        self.metrics["cache"] = {
            "avg_cache_miss_ms": avg_cache_miss,
            "avg_cache_hit_ms": avg_cache_hit,
            "cache_speedup": cache_speedup,
            "cache_hit_rate": cache_hit_rate
        }
        
        # Check against target
        passed = cache_hit_rate >= PERFORMANCE_TARGETS["cache_hit_rate"]
        status = "✓ PASSED" if passed else "✗ FAILED"
        
        print(f"Cache Miss Latency: {avg_cache_miss:.2f}ms")
        print(f"Cache Hit Latency: {avg_cache_hit:.2f}ms")
        print(f"Cache Speedup: {cache_speedup:.1f}x")
        print(f"Cache Hit Rate: {cache_hit_rate:.2%} (Target: >{PERFORMANCE_TARGETS['cache_hit_rate']:.0%}) {status}")
        print()
        
    async def benchmark_model_selection(self):
        """Benchmark model selection for different use cases"""
        print("4. MODEL SELECTION BENCHMARK")
        print("-" * 40)
        
        use_cases = ["rag", "search", "code", "general"]
        
        for use_case in use_cases:
            # Select appropriate test data
            if use_case == "code":
                texts = TEST_DATASETS["code_samples"][:5]
            else:
                texts = TEST_DATASETS["short_texts"][:5]
            
            request = AgnoEmbeddingRequest(
                texts=texts,
                use_case=use_case
            )
            
            response = await self.service.embed(request)
            
            self.metrics[f"model_selection_{use_case}"] = {
                "model_used": response.model_used,
                "provider": response.provider,
                "dimensions": response.dimensions,
                "latency_ms": response.latency_ms
            }
            
            print(f"{use_case.upper()}: {response.model_used} ({response.provider})")
        
        print()
        
    async def benchmark_concurrent_requests(self):
        """Benchmark concurrent request handling"""
        print("5. CONCURRENT REQUESTS BENCHMARK")
        print("-" * 40)
        
        concurrent_levels = [5, 10, 20]
        
        for level in concurrent_levels:
            texts = TEST_DATASETS["short_texts"][:level]
            requests = [
                AgnoEmbeddingRequest(texts=[text])
                for text in texts
            ]
            
            start = time.perf_counter()
            responses = await asyncio.gather(*[
                self.service.embed(req) for req in requests
            ])
            total_time = time.perf_counter() - start
            
            throughput = level / total_time
            avg_latency = (total_time / level) * 1000
            
            self.metrics[f"concurrent_{level}"] = {
                "total_time_s": total_time,
                "throughput_per_second": throughput,
                "avg_latency_ms": avg_latency
            }
            
            print(f"Concurrent Level {level}:")
            print(f"  Total Time: {total_time:.2f}s")
            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Avg Latency: {avg_latency:.2f}ms")
        
        print()
        
    async def benchmark_cost_efficiency(self):
        """Benchmark cost efficiency and optimization"""
        print("6. COST EFFICIENCY BENCHMARK")
        print("-" * 40)
        
        # Generate embeddings and track costs
        total_cost_without_cache = 0
        total_cost_with_cache = 0
        
        # Simulate without cache (each request unique)
        for i, text in enumerate(TEST_DATASETS["short_texts"][:20]):
            request = AgnoEmbeddingRequest(texts=[f"{text} {i}"])  # Make unique
            response = await self.service.embed(request)
            total_cost_without_cache += response.cost_estimate
        
        # Simulate with cache (repeated requests)
        for text in TEST_DATASETS["short_texts"][:10]:
            # First request (cache miss)
            request = AgnoEmbeddingRequest(texts=[text])
            response = await self.service.embed(request)
            total_cost_with_cache += response.cost_estimate
            
            # Second request (cache hit)
            response = await self.service.embed(request)
            # Cache hits have zero cost
            if not response.cached:
                total_cost_with_cache += response.cost_estimate
        
        cost_reduction = 1 - (total_cost_with_cache / total_cost_without_cache) if total_cost_without_cache > 0 else 0
        
        self.metrics["cost"] = {
            "total_cost_without_cache": total_cost_without_cache,
            "total_cost_with_cache": total_cost_with_cache,
            "cost_reduction": cost_reduction
        }
        
        # Check against target
        passed = cost_reduction >= PERFORMANCE_TARGETS["cost_reduction"]
        status = "✓ PASSED" if passed else "✗ FAILED"
        
        print(f"Cost without cache: ${total_cost_without_cache:.4f}")
        print(f"Cost with cache: ${total_cost_with_cache:.4f}")
        print(f"Cost Reduction: {cost_reduction:.1%} (Target: >{PERFORMANCE_TARGETS['cost_reduction']:.0%}) {status}")
        print()
        
    async def benchmark_different_content_types(self):
        """Benchmark performance across different content types"""
        print("7. CONTENT TYPE BENCHMARK")
        print("-" * 40)
        
        content_types = {
            "short": TEST_DATASETS["short_texts"][:10],
            "medium": TEST_DATASETS["medium_texts"][:5],
            "long": TEST_DATASETS["long_texts"][:2],
            "code": TEST_DATASETS["code_samples"][:5],
            "multilingual": TEST_DATASETS["multilingual"][:8]
        }
        
        for content_type, texts in content_types.items():
            request = AgnoEmbeddingRequest(texts=texts)
            
            start = time.perf_counter()
            response = await self.service.embed(request)
            latency_ms = (time.perf_counter() - start) * 1000
            
            self.metrics[f"content_{content_type}"] = {
                "count": len(texts),
                "total_latency_ms": latency_ms,
                "avg_per_text_ms": latency_ms / len(texts),
                "model_used": response.model_used,
                "tokens_processed": response.tokens_processed
            }
            
            print(f"{content_type.upper()}:")
            print(f"  Model: {response.model_used}")
            print(f"  Total: {latency_ms:.2f}ms for {len(texts)} texts")
            print(f"  Average: {latency_ms/len(texts):.2f}ms per text")
        
        print()
        
    def generate_report(self):
        """Generate comprehensive benchmark report"""
        print("=" * 80)
        print("BENCHMARK SUMMARY REPORT")
        print("=" * 80)
        
        # Overall performance assessment
        passed_tests = 0
        total_tests = 0
        
        # Check single embedding latency
        total_tests += 1
        if self.metrics["single_embedding"]["avg_latency_ms"] < PERFORMANCE_TARGETS["single_embedding_latency_ms"]:
            passed_tests += 1
        
        # Check batch embedding latency
        total_tests += 1
        if self.metrics["batch_100"]["latency_ms"] < PERFORMANCE_TARGETS["batch_embedding_latency_ms"]:
            passed_tests += 1
        
        # Check cache hit rate
        total_tests += 1
        if self.metrics["cache"]["cache_hit_rate"] >= PERFORMANCE_TARGETS["cache_hit_rate"]:
            passed_tests += 1
        
        # Check cost reduction
        total_tests += 1
        if self.metrics["cost"]["cost_reduction"] >= PERFORMANCE_TARGETS["cost_reduction"]:
            passed_tests += 1
        
        # Check throughput
        total_tests += 1
        if self.metrics["concurrent_20"]["throughput_per_second"] >= PERFORMANCE_TARGETS["throughput_per_second"]:
            passed_tests += 1
        
        print(f"Performance Score: {passed_tests}/{total_tests} targets met ({passed_tests/total_tests:.0%})")
        print()
        
        print("KEY METRICS:")
        print("-" * 40)
        print(f"• Single Embedding Latency: {self.metrics['single_embedding']['avg_latency_ms']:.2f}ms")
        print(f"• Batch-100 Latency: {self.metrics['batch_100']['latency_ms']:.2f}ms")
        print(f"• Cache Hit Rate: {self.metrics['cache']['cache_hit_rate']:.2%}")
        print(f"• Cost Reduction: {self.metrics['cost']['cost_reduction']:.1%}")
        print(f"• Peak Throughput: {self.metrics['concurrent_20']['throughput_per_second']:.2f} req/s")
        print()
        
        print("RECOMMENDATIONS:")
        print("-" * 40)
        
        if self.metrics["single_embedding"]["avg_latency_ms"] > PERFORMANCE_TARGETS["single_embedding_latency_ms"]:
            print("⚠️ Single embedding latency exceeds target. Consider:")
            print("   - Optimizing model selection logic")
            print("   - Using smaller models for simple queries")
            print("   - Implementing request batching")
        
        if self.metrics["cache"]["cache_hit_rate"] < PERFORMANCE_TARGETS["cache_hit_rate"]:
            print("⚠️ Cache hit rate below target. Consider:")
            print("   - Increasing cache size")
            print("   - Implementing better cache key generation")
            print("   - Using LRU cache with longer TTL")
        
        if self.metrics["cost"]["cost_reduction"] < PERFORMANCE_TARGETS["cost_reduction"]:
            print("⚠️ Cost reduction below target. Consider:")
            print("   - More aggressive caching")
            print("   - Using cheaper models when appropriate")
            print("   - Implementing request deduplication")
        
        # Save detailed report to file
        self.save_report()
        
        print()
        print(f"✅ Detailed report saved to: benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        print("=" * 80)
        
    def save_report(self):
        """Save detailed benchmark results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"benchmark_results_{timestamp}.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "performance_targets": PERFORMANCE_TARGETS,
            "metrics": self.metrics,
            "summary": {
                "single_embedding_latency_ms": self.metrics["single_embedding"]["avg_latency_ms"],
                "batch_100_latency_ms": self.metrics["batch_100"]["latency_ms"],
                "cache_hit_rate": self.metrics["cache"]["cache_hit_rate"],
                "cost_reduction": self.metrics["cost"]["cost_reduction"],
                "peak_throughput": self.metrics["concurrent_20"]["throughput_per_second"]
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

# ============================================
# Main Execution
# ============================================

async def main():
    """Run the benchmark suite"""
    benchmark = EmbeddingBenchmark()
    await benchmark.run_all_benchmarks()

if __name__ == "__main__":
    asyncio.run(main())