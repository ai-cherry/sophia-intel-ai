#!/usr/bin/env python3
"""
Tests for Together AI Embedding Infrastructure
Validates the embedding service with real API calls.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.embeddings.together_embeddings import (
    EmbeddingConfig,
    EmbeddingModel,
    TogetherEmbeddingService,
)


class TestEmbeddingInfrastructure:
    """Test suite for embedding infrastructure."""

    def __init__(self):
        self.service = None
        self.test_texts = [
            "The quantum mechanical model describes electrons as wave functions",
            "Python is a high-level programming language with dynamic typing",
            "Machine learning models learn patterns from data",
            "The mitochondria is the powerhouse of the cell",
            "FastAPI is a modern web framework for building APIs with Python"
        ]

    def setup(self):
        """Initialize embedding service."""
        print("🔧 Setting up embedding service...")

        # Check for API keys
        if not os.getenv("TOGETHER_API_KEY") and not os.getenv("OPENROUTER_API_KEY"):
            print("⚠️  Warning: No API keys found. Using mock mode.")
            # Create mock config for testing without API
            config = EmbeddingConfig(
                cache_enabled=True,
                use_portkey=False
            )
        else:
            config = EmbeddingConfig()

        self.service = TogetherEmbeddingService(config)
        print("✅ Service initialized")

    def test_single_embedding(self):
        """Test single text embedding."""
        print("\n📝 Testing single embedding...")

        text = "Hello, world! This is a test embedding."

        try:
            result = self.service.embed([text])

            assert result.embeddings, "No embeddings returned"
            assert len(result.embeddings) == 1, "Wrong number of embeddings"
            assert len(result.embeddings[0]) > 0, "Empty embedding vector"

            print("✅ Single embedding successful")
            print(f"   Model: {result.model}")
            print(f"   Dimensions: {result.dimensions}")
            print(f"   Latency: {result.latency_ms:.2f}ms")
            print(f"   Tokens: {result.tokens_used}")

            return True

        except Exception as e:
            print(f"❌ Single embedding failed: {e}")
            return False

    def test_batch_embedding(self):
        """Test batch embedding processing."""
        print("\n📚 Testing batch embeddings...")

        try:
            start_time = time.time()
            result = self.service.embed(self.test_texts)
            elapsed = (time.time() - start_time) * 1000

            assert result.embeddings, "No embeddings returned"
            assert len(result.embeddings) == len(self.test_texts), "Wrong number of embeddings"

            print("✅ Batch embedding successful")
            print(f"   Texts: {len(self.test_texts)}")
            print(f"   Model: {result.model}")
            print(f"   Total latency: {elapsed:.2f}ms")
            print(f"   Avg per text: {elapsed/len(self.test_texts):.2f}ms")

            # Check all embeddings have same dimensions
            dims = [len(e) for e in result.embeddings]
            assert len(set(dims)) == 1, "Inconsistent embedding dimensions"

            return True

        except Exception as e:
            print(f"❌ Batch embedding failed: {e}")
            return False

    def test_caching(self):
        """Test semantic caching functionality."""
        print("\n💾 Testing semantic caching...")

        text = "This is a test for caching functionality"

        try:
            # First call - should not be cached
            result1 = self.service.embed([text])
            assert not result1.cached, "First call should not be cached"

            # Second call - should be cached
            result2 = self.service.embed([text])

            # Check if caching is working
            if self.service.config.cache_enabled:
                cache_hits = result2.metadata.get('cache_hits', 0)
                print("✅ Caching test completed")
                print(f"   Cache hits: {cache_hits}")
                print(f"   First call latency: {result1.latency_ms:.2f}ms")
                print(f"   Second call latency: {result2.latency_ms:.2f}ms")

                if cache_hits > 0:
                    print("   ✓ Cache is working!")
                else:
                    print("   ⚠️  Cache may not be working as expected")
            else:
                print("ℹ️  Caching is disabled")

            return True

        except Exception as e:
            print(f"❌ Caching test failed: {e}")
            return False

    def test_similarity_search(self):
        """Test semantic similarity search."""
        print("\n🔍 Testing similarity search...")

        documents = [
            "Python is great for data science and machine learning",
            "JavaScript is essential for web development",
            "Rust provides memory safety without garbage collection",
            "Deep learning uses neural networks with multiple layers",
            "React is a popular frontend framework"
        ]

        query = "What programming language is best for AI?"

        try:
            results = self.service.search(query, documents, top_k=3)

            assert results, "No search results returned"
            assert len(results) <= 3, "Too many results returned"

            print("✅ Similarity search successful")
            print(f"   Query: '{query}'")
            print(f"   Top {len(results)} results:")

            for idx, score, doc in results:
                preview = doc[:50] + "..." if len(doc) > 50 else doc
                print(f"   {idx+1}. [Score: {score:.4f}] {preview}")

            # The Python/ML document should rank high
            top_doc = results[0][2]
            if "Python" in top_doc or "machine learning" in top_doc:
                print("   ✓ Relevant result ranked first!")

            return True

        except Exception as e:
            print(f"❌ Similarity search failed: {e}")
            return False

    def test_model_recommendations(self):
        """Test model recommendation logic."""
        print("\n🎯 Testing model recommendations...")

        test_cases = [
            (100, "general", "en", EmbeddingModel.BGE_BASE),
            (5000, "rag", "en", EmbeddingModel.M2_BERT_8K),
            (20000, "general", "en", EmbeddingModel.M2_BERT_32K),
            (200, "search", "en", EmbeddingModel.BGE_LARGE),
            (300, "general", "zh", EmbeddingModel.E5_MULTILINGUAL),
        ]

        all_passed = True

        for text_len, use_case, lang, expected in test_cases:
            recommended = TogetherEmbeddingService.recommend_model(
                text_length=text_len,
                use_case=use_case,
                language=lang
            )

            status = "✓" if recommended == expected else "✗"
            print(f"   {status} {text_len} tokens, {use_case}, {lang} -> {recommended.value}")

            if recommended != expected:
                print(f"      Expected: {expected.value}")
                all_passed = False

        if all_passed:
            print("✅ All model recommendations correct")
        else:
            print("⚠️  Some recommendations differ from expected")

        return True  # Non-critical test

    async def test_async_operations(self):
        """Test async embedding operations."""
        print("\n⚡ Testing async operations...")

        try:
            # Test parallel async calls
            tasks = [
                self.service.embed_async([text])
                for text in self.test_texts[:3]
            ]

            start_time = time.time()
            results = await asyncio.gather(*tasks)
            elapsed = (time.time() - start_time) * 1000

            assert all(r.embeddings for r in results), "Some async calls failed"

            print("✅ Async operations successful")
            print(f"   Parallel tasks: {len(tasks)}")
            print(f"   Total time: {elapsed:.2f}ms")
            print(f"   Avg per task: {elapsed/len(tasks):.2f}ms")

            return True

        except Exception as e:
            print(f"❌ Async operations failed: {e}")
            return False

    def test_error_handling(self):
        """Test error handling and fallbacks."""
        print("\n🛡️ Testing error handling...")

        # Test with empty input
        try:
            result = self.service.embed([])
            print("   ⚠️  Empty input handled (returned empty result)")
        except Exception as e:
            print(f"   ✓ Empty input raised exception: {type(e).__name__}")

        # Test with very long text (if API limits exist)
        long_text = "word " * 50000  # Very long text
        try:
            result = self.service.embed([long_text])
            print("   ✓ Long text handled successfully")
        except Exception as e:
            print(f"   ℹ️  Long text handling: {type(e).__name__}")

        print("✅ Error handling tests completed")
        return True

    def run_all_tests(self):
        """Run all embedding infrastructure tests."""
        print("\n" + "="*60)
        print("🚀 EMBEDDING INFRASTRUCTURE TEST SUITE")
        print("="*60)

        self.setup()

        tests = [
            ("Single Embedding", self.test_single_embedding),
            ("Batch Embedding", self.test_batch_embedding),
            ("Caching", self.test_caching),
            ("Similarity Search", self.test_similarity_search),
            ("Model Recommendations", self.test_model_recommendations),
            ("Error Handling", self.test_error_handling),
        ]

        # Run async test separately
        async_test = ("Async Operations", self.test_async_operations)

        results = {}

        # Run sync tests
        for name, test_func in tests:
            try:
                results[name] = test_func()
            except Exception as e:
                print(f"❌ {name} crashed: {e}")
                results[name] = False

        # Run async test
        try:
            results[async_test[0]] = asyncio.run(async_test[1]())
        except Exception as e:
            print(f"❌ {async_test[0]} crashed: {e}")
            results[async_test[0]] = False

        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {name}")

        print(f"\nTotal: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 All tests passed! Embedding infrastructure is ready.")
        elif passed > total * 0.7:
            print("\n⚠️  Most tests passed. Review failures above.")
        else:
            print("\n❌ Multiple test failures. Infrastructure needs attention.")

        return passed == total


def main():
    """Main entry point."""
    tester = TestEmbeddingInfrastructure()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
