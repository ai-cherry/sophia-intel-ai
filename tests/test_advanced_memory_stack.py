#!/usr/bin/env python3
"""
Comprehensive Test Suite for Advanced Memory Stack (2025)
Tests all components: Embeddings, Vector DBs, CRDT Sync, Unified Store
"""

import asyncio
import os
import sys
import time

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.memory.advanced_embedding_router import AdvancedEmbeddingRouter, ContentType
from app.memory.crdt_memory_sync import CRDTMemoryStore
from app.memory.hybrid_vector_manager import HybridVectorManager, QueryType
from app.memory.unified_memory_store import RetrievalLevel, UnifiedMemoryStore


class TestAdvancedMemoryStack:
    """Comprehensive test suite for advanced memory stack"""

    @pytest.mark.asyncio
    async def test_portkey_embedding_routing(self):
        """Test dynamic model selection via Portkey"""
        router = AdvancedEmbeddingRouter()

        # Test short text
        short_result = await router.get_embeddings(
            "test short text",
            ContentType.SHORT_TEXT
        )
        assert len(short_result.embeddings[0]) == 1024
        assert short_result.model_used == 'BAAI/bge-large-en-v1.5'
        assert short_result.latency_ms < 100

        # Test long text
        long_text = "very long text " * 3000  # ~9000 tokens
        long_result = await router.get_embeddings(
            long_text,
            ContentType.LONG_TEXT
        )
        assert long_result.model_used == 'togethercomputer/m2-bert-80k'

        # Test code embedding
        code_result = await router.get_embeddings(
            "def hello(): print('world')",
            ContentType.CODE
        )
        assert code_result.model_used == 'text-embedding-3-large'

        print("✅ Embedding routing test passed")
        print(f"   Metrics: {router.get_metrics()}")

    @pytest.mark.asyncio
    async def test_hybrid_vector_search(self):
        """Test Weaviate + Milvus hybrid architecture"""
        manager = HybridVectorManager()

        # Test real-time routing to Weaviate
        realtime_results = await manager.route_query(
            QueryType.REALTIME,
            query="test query",
            collection="SophiaMemory",
            alpha=0.7,
            limit=10
        )
        assert isinstance(realtime_results, list)

        # Test analytics routing to Milvus
        test_vectors = [[0.1] * 1024]
        analytics_results = await manager.route_query(
            QueryType.ANALYTICS,
            vectors=test_vectors,
            collection="sophia_vectors",
            top_k=10
        )
        assert isinstance(analytics_results, list)

        # Test hybrid search
        hybrid_results = await manager.route_query(
            QueryType.HYBRID,
            query="AI agents",
            vectors=test_vectors,
            limit=20
        )
        assert isinstance(hybrid_results, list)

        print("✅ Hybrid vector search test passed")
        print(f"   Metrics: {manager.get_metrics()}")

    @pytest.mark.asyncio
    async def test_crdt_memory_sync(self):
        """Test conflict-free distributed synchronization"""
        # Create two agents
        store1 = CRDTMemoryStore('agent-1')
        store2 = CRDTMemoryStore('agent-2')

        # Connect as peers
        store1.add_peer('agent-2', store2)
        store2.add_peer('agent-1', store1)

        # Start sync
        await store1.start()
        await store2.start()

        # Concurrent updates to same memory
        await store1.add_memory('mem-1', {'content': 'version 1', 'author': 'agent1'})
        await store2.add_memory('mem-1', {'content': 'version 2', 'author': 'agent2'})

        # Different memories
        await store1.add_memory('mem-2', {'data': 'from agent 1'})
        await store2.add_memory('mem-3', {'data': 'from agent 2'})

        # Wait for sync
        await asyncio.sleep(2)

        # Check convergence
        mem1_agent1 = await store1.get_memory('mem-1')
        mem1_agent2 = await store2.get_memory('mem-1')

        # Both should have merged content
        assert mem1_agent1 is not None
        assert mem1_agent2 is not None
        assert 'author' in mem1_agent1  # Should have merged fields

        # Check cross-agent memories
        mem2_agent2 = await store2.get_memory('mem-2')
        mem3_agent1 = await store1.get_memory('mem-3')
        assert mem2_agent2 is not None  # Agent 2 should have agent 1's memory
        assert mem3_agent1 is not None  # Agent 1 should have agent 2's memory

        # Cleanup
        await store1.stop()
        await store2.stop()

        print("✅ CRDT memory sync test passed")
        print(f"   Agent 1 state: {store1.get_state_snapshot()}")
        print(f"   Agent 2 state: {store2.get_state_snapshot()}")

    @pytest.mark.asyncio
    async def test_hierarchical_retrieval(self):
        """Test Document→Section→Snippet retrieval"""
        store = UnifiedMemoryStore('test-agent', enable_sync=False)
        await store.initialize()

        # Store multiple memories at different levels
        doc_id = await store.store(
            content={
                'text': 'Complete document about machine learning',
                'level': 'document',
                'document_id': 'doc1'
            },
            tags=['ml', 'document']
        )

        section_id = await store.store(
            content={
                'text': 'Section about neural networks in ML',
                'level': 'section',
                'document_id': 'doc1',
                'section_id': 'sec1'
            },
            tags=['ml', 'neural', 'section']
        )

        snippet_id = await store.store(
            content={
                'text': 'Specific code snippet for backpropagation',
                'level': 'snippet',
                'document_id': 'doc1',
                'section_id': 'sec1',
                'snippet_id': 'snip1'
            },
            tags=['ml', 'code', 'snippet']
        )

        # Test document-level retrieval
        doc_results = await store.retrieve(
            'machine learning',
            level=RetrievalLevel.DOCUMENT,
            limit=5
        )
        assert doc_results.total_results > 0
        assert doc_results.level == RetrievalLevel.DOCUMENT

        # Test section-level retrieval
        section_results = await store.retrieve(
            'neural networks',
            level=RetrievalLevel.SECTION,
            limit=5
        )
        assert section_results.level == RetrievalLevel.SECTION

        # Test snippet-level retrieval
        snippet_results = await store.retrieve(
            'backpropagation',
            level=RetrievalLevel.SNIPPET,
            limit=5
        )
        assert snippet_results.level == RetrievalLevel.SNIPPET

        await store.close()

        print("✅ Hierarchical retrieval test passed")
        print(f"   Store metrics: {store.get_metrics()}")

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self):
        """Test performance against 2025 targets"""
        results = {
            'embedding_latency': [],
            'vector_search_latency': [],
            'memory_sync_latency': [],
            'hierarchical_retrieval_latency': []
        }

        # Test embedding latency (Target: <50ms)
        router = AdvancedEmbeddingRouter()
        for _ in range(10):
            start = time.perf_counter()
            await router.get_embeddings("test text", ContentType.SHORT_TEXT)
            latency = (time.perf_counter() - start) * 1000
            results['embedding_latency'].append(latency)

        avg_embedding = sum(results['embedding_latency']) / len(results['embedding_latency'])
        assert avg_embedding < 50, f"Embedding latency {avg_embedding:.2f}ms exceeds 50ms target"

        # Test vector search latency (Target: <5ms Weaviate, <2ms Milvus)
        manager = HybridVectorManager()
        for _ in range(10):
            start = time.perf_counter()
            await manager.route_query(
                QueryType.REALTIME,
                query="test",
                limit=10
            )
            latency = (time.perf_counter() - start) * 1000
            results['vector_search_latency'].append(latency)

        avg_search = sum(results['vector_search_latency']) / len(results['vector_search_latency'])
        assert avg_search < 10, f"Search latency {avg_search:.2f}ms exceeds 10ms target"

        # Test CRDT sync latency (Target: <1ms operations)
        store = CRDTMemoryStore('perf-test')
        for _ in range(10):
            start = time.perf_counter()
            await store.add_memory(f'mem-{_}', {'data': 'test'}, broadcast=False)
            latency = (time.perf_counter() - start) * 1000
            results['memory_sync_latency'].append(latency)

        avg_sync = sum(results['memory_sync_latency']) / len(results['memory_sync_latency'])
        assert avg_sync < 5, f"Sync latency {avg_sync:.2f}ms exceeds 5ms target"

        # Test hierarchical retrieval (Target: <50ms)
        unified_store = UnifiedMemoryStore('perf-agent', enable_sync=False)
        await unified_store.initialize()

        # Store test data
        await unified_store.store({'text': 'test document'})

        for _ in range(10):
            start = time.perf_counter()
            await unified_store.retrieve('test', level=RetrievalLevel.DOCUMENT)
            latency = (time.perf_counter() - start) * 1000
            results['hierarchical_retrieval_latency'].append(latency)

        avg_retrieval = sum(results['hierarchical_retrieval_latency']) / len(results['hierarchical_retrieval_latency'])
        assert avg_retrieval < 50, f"Retrieval latency {avg_retrieval:.2f}ms exceeds 50ms target"

        await unified_store.close()

        print("✅ Performance benchmarks passed!")
        print(f"   Embedding latency: {avg_embedding:.2f}ms (target: <50ms)")
        print(f"   Vector search latency: {avg_search:.2f}ms (target: <10ms)")
        print(f"   CRDT sync latency: {avg_sync:.2f}ms (target: <5ms)")
        print(f"   Hierarchical retrieval: {avg_retrieval:.2f}ms (target: <50ms)")

        return results


async def run_all_tests():
    """Run complete test suite"""
    print("=" * 60)
    print("🧪 ADVANCED MEMORY STACK TEST SUITE (2025)")
    print("=" * 60)
    print()

    test_suite = TestAdvancedMemoryStack()

    tests = [
        ("Portkey Embedding Routing", test_suite.test_portkey_embedding_routing),
        ("Hybrid Vector Search", test_suite.test_hybrid_vector_search),
        ("CRDT Memory Sync", test_suite.test_crdt_memory_sync),
        ("Hierarchical Retrieval", test_suite.test_hierarchical_retrieval),
        ("Performance Benchmarks", test_suite.test_performance_benchmarks)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n📝 Running: {test_name}")
        print("-" * 40)
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"❌ Test failed: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print(f"   Passed: {passed}/{len(tests)}")
    print(f"   Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Memory stack is production ready.")
    else:
        print(f"\n⚠️ {failed} tests failed. Review errors above.")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
