"""
Test Script for Sophia V7 Unified Hybrid Memory System
Tests the integration of Zep + Neon + Qdrant + Redis for comprehensive
cross-domain intelligence and memory capabilities.
"""
import asyncio
from core.memory.unified_hybrid_memory import MemoryQuery, UnifiedHybridMemory
async def test_unified_hybrid_memory():
    """Test the unified hybrid memory system"""
    print("🧠 Testing Sophia V7 Unified Hybrid Memory System")
    print("=" * 60)
    # Configuration for memory systems
    config = {
        "zep": {"url": "http://localhost:8000", "api_key": None},  # Set if required
        "neon": {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "password",
            "database": "sophia_v7",
        },
        "qdrant": {"url": "http://localhost:6333", "api_key": None},
        "redis": {"url": "${REDIS_URL}"},
    }
    # Initialize memory system
    memory_system = UnifiedHybridMemory(config)
    try:
        print("🔧 Initializing unified memory system...")
        await memory_system.initialize()
        print("✅ Memory system initialized successfully")
        # Test 1: Store episodic memory (Gong conversation)
        print("\n📞 Test 1: Storing Gong conversation in episodic memory")
        session_id = await memory_system.store_episodic_memory(
            session_id="gong_session_001",
            user_id="sales_rep_001",
            agent_role="conversation_analyst",
            message="Customer asked about pricing for enterprise plan",
            response="Provided enterprise pricing details and discussed ROI benefits",
            domain="gong",
            metadata={
                "conversation_type": "pricing_discussion",
                "customer_segment": "enterprise",
                "confidence_score": 0.9,
            },
        )
        print(f"✅ Stored episodic memory with session: {session_id}")
        # Test 2: Store foundational data (PayReady knowledge)
        print("\n📚 Test 2: Storing PayReady foundational knowledge")
        foundational_id = await memory_system.store_foundational_data(
            category="competitive_intelligence",
            title="PayReady vs Competitor Analysis",
            content="PayReady offers superior API integration capabilities compared to competitors, with 99.9% uptime and faster processing speeds.",
            importance_weight=0.9,
            access_level="standard",
            domain="payready",
            metadata={
                "source": "competitive_analysis_2025",
                "last_updated": "2025-01-01",
            },
        )
        print(f"✅ Stored foundational data with ID: {foundational_id}")
        # Test 3: Store  development intelligence
        print("\n💻 Test 3: Storing  development intelligence")
        _session = await memory_system.store_episodic_memory(
            session_id="_session_001",
            user_id="dev_team_001",
            agent_role="code_analyzer",
            message="Code review for payment processing module",
            response="Identified performance optimization opportunities and security enhancements",
            domain="",
            metadata={
                "code_module": "payment_processing",
                "review_type": "security_performance",
                "confidence_score": 0.85,
            },
        )
        print(f"✅ Stored  development memory: {_session}")
        # Test 4: Hybrid query across all memory systems
        print("\n🔍 Test 4: Hybrid query across all memory systems")
        query = MemoryQuery(
            query="payment processing performance optimization",
            domain="",
            user_id="test_user",
            session_id="_session_001",
            memory_types=["episodic", "foundational", "vector", "cache"],
            max_results=10,
            confidence_threshold=0.7,
        )
        result = await memory_system.hybrid_query(query)
        print("✅ Hybrid query completed:")
        print(f"   📊 Total results: {result.total_results}")
        print(f"   🎯 Confidence scores: {result.confidence_scores}")
        print(f"   ⚡ Response times: {result.response_times}")
        if result.synthesis:
            print(f"   🧠 Synthesis: {result.synthesis}")
        # Test 5: Cross-domain query (Gong +  correlation)
        print("\n🔗 Test 5: Cross-domain correlation query")
        cross_domain_query = MemoryQuery(
            query="customer satisfaction and development velocity correlation",
            domain="cross_domain",
            user_id="business_analyst",
            memory_types=["foundational", "vector"],
            max_results=15,
            confidence_threshold=0.6,
        )
        cross_result = await memory_system.hybrid_query(cross_domain_query)
        print("✅ Cross-domain query completed:")
        print(f"   📊 Total results: {cross_result.total_results}")
        print(
            f"   🎯 Average confidence: {sum(cross_result.confidence_scores.values()) / len(cross_result.confidence_scores) if cross_result.confidence_scores else 0}"
        )
        # Test 6: Store business insight from cross-domain analysis
        print("\n💡 Test 6: Storing unified business insight")
        insight_id = await memory_system.store_business_insight(
            insight_type="performance_correlation",
            title="Development Velocity Impact on Customer Satisfaction",
            description="Analysis shows strong positive correlation between development deployment frequency and customer satisfaction scores.",
            domains_involved=["", "gong", "hubspot"],
            confidence_score=0.87,
            business_impact="high",
            recommendations=[
                "Increase deployment frequency to improve customer satisfaction",
                "Implement automated testing to maintain quality at higher velocity",
                "Monitor customer feedback during development sprints",
            ],
            evidence={
                "correlation_coefficient": 0.73,
                "sample_size": 150,
                "time_period": "Q4_2024",
            },
        )
        print(f"✅ Stored business insight with ID: {insight_id}")
        # Test 7: Get cross-domain correlations
        print("\n📈 Test 7: Retrieving cross-domain correlations")
        correlations = await memory_system.get_cross_domain_correlations(
            "gong", ""
        )
        print(f"✅ Found {len(correlations)} cross-domain correlations")
        # Test 8: Performance metrics
        print("\n📊 Test 8: Performance metrics")
        metrics = memory_system.get_performance_metrics()
        print("✅ Performance metrics:")
        print(f"   🧠 Memory systems: {metrics['memory_systems']}")
        print(f"   ⚡ Performance: {metrics['performance']}")
        print(f"   🔗 Unified intelligence: {metrics['unified_intelligence']}")
        # Test 9: Domain-specific query routing
        print("\n🎯 Test 9: Domain-specific query routing")
        gong_query = MemoryQuery(
            query="sales conversation sentiment analysis",
            domain="gong",
            user_id="sales_manager",
            session_id="gong_session_001",
        )
        gong_result = await memory_system.hybrid_query(gong_query)
        print("✅ Gong-specific query completed:")
        print(f"   📞 Results: {gong_result.total_results}")
        print(
            f"   🎯 Confidence: {sum(gong_result.confidence_scores.values()) / len(gong_result.confidence_scores) if gong_result.confidence_scores else 0:.2f}"
        )
        # Test 10:  development query
        print("\n💻 Test 10:  development query")
        _query = MemoryQuery(
            query="code quality and deployment optimization",
            domain="",
            user_id="dev_lead",
            session_id="_session_001",
        )
        _result = await memory_system.hybrid_query(_query)
        print("✅  development query completed:")
        print(f"   💻 Results: {_result.total_results}")
        print(
            f"   🎯 Confidence: {sum(_result.confidence_scores.values()) / len(_result.confidence_scores) if _result.confidence_scores else 0:.2f}"
        )
        print("\n🎉 All tests completed successfully!")
        print("🧠 Unified Hybrid Memory System is operational")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
async def test_memory_integration():
    """Test memory system integration with mock data"""
    print("\n🔧 Testing Memory Integration with Mock Data")
    print("=" * 50)
    # Mock configuration (will gracefully handle missing services)
    config = {
        "zep": {"url": "http://localhost:8000"},
        "neon": {
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "password",
            "database": "sophia_test",
        },
        "qdrant": {"url": "http://localhost:6333"},
        "redis": {"url": "${REDIS_URL}"},
    }
    memory_system = UnifiedHybridMemory(config)
    try:
        # Test initialization (will show which services are available)
        await memory_system.initialize()
        # Test query with mock data
        query = MemoryQuery(
            query="test unified intelligence query", domain="test", user_id="test_user"
        )
        result = await memory_system.hybrid_query(query)
        print(f"✅ Mock query completed with {result.total_results} results")
        # Test performance metrics
        metrics = memory_system.get_performance_metrics()
        print("📊 System status:")
        for system, status in metrics["memory_systems"].items():
            print(f"   {system}: {status}")
        return True
    except Exception as e:
        print(f"⚠️  Integration test with limited services: {e}")
        return False
if __name__ == "__main__":
    print("🚀 Starting Sophia V7 Unified Hybrid Memory Tests")
    print("=" * 60)
    # Run integration test first (handles missing services gracefully)
    asyncio.run(test_memory_integration())
    print("\n" + "=" * 60)
    print("Note: Full test requires Zep, PostgreSQL, Qdrant, and Redis services")
    print("Integration test shows which services are available")
    print("=" * 60)
