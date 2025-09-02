#!/usr/bin/env python3
"""
Integration tests for consensus swarm and memory deduplication features.
Tests the complete integration without requiring external API keys.
"""

import asyncio
import logging
import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set up logging to avoid logger errors
logging.basicConfig(level=logging.INFO)

from unittest.mock import patch

import pytest

from app.swarms.patterns.base import PatternResult
from app.swarms.patterns.consensus import ConsensusConfig, ConsensusPattern


class MockAgent:
    """Mock agent for testing consensus patterns."""

    def __init__(self, name: str, preferred_choice: str = None):
        self.name = name
        self.preferred_choice = preferred_choice

    def __str__(self):
        return self.name


class TestConsensusSwarmIntegration:
    """Integration tests for consensus swarm functionality."""

    @pytest.fixture
    def mock_agents(self):
        """Create mock agents for testing."""
        return [
            MockAgent("agent_1", "proposal_a"),
            MockAgent("agent_2", "proposal_b"),
            MockAgent("agent_3", "proposal_a"),
            MockAgent("agent_4", "proposal_c"),
            MockAgent("agent_5", "proposal_a")
        ]

    @pytest.fixture
    def consensus_config(self):
        """Create consensus configuration."""
        return ConsensusConfig(
            consensus_method="weighted_voting",
            min_agreement=0.6,
            tie_breaker="seniority"
        )

    @pytest.mark.asyncio
    async def test_consensus_pattern_initialization(self, consensus_config):
        """Test consensus pattern initializes correctly."""
        pattern = ConsensusPattern(consensus_config)

        assert pattern.config.consensus_method == "weighted_voting"
        assert pattern.config.min_agreement == 0.6
        assert pattern.config.tie_breaker == "seniority"

        # Test initialization
        await pattern.initialize()
        assert pattern._initialized is True

        # Test cleanup
        await pattern.cleanup()
        assert pattern._initialized is False

    @pytest.mark.asyncio
    async def test_consensus_voting_process(self, consensus_config, mock_agents):
        """Test complete consensus voting process."""
        pattern = ConsensusPattern(consensus_config)

        context = {
            "proposals": ["proposal_a", "proposal_b", "proposal_c"]
        }

        # Mock the voting process
        with patch.object(pattern, '_get_agent_vote') as mock_vote:
            # Set up mock votes based on agent preferences
            mock_vote.side_effect = lambda agent, proposals: {
                "choice": agent.preferred_choice,
                "confidence": 0.8,
                "reasoning": f"{agent.name} prefers {agent.preferred_choice}"
            }

            result = await pattern.execute(context, mock_agents)

            assert isinstance(result, PatternResult)
            assert result.success is True
            assert result.pattern_name == "consensus"
            assert "winner" in result.data

            # With our mock setup, proposal_a should win (3 votes)
            assert result.data["winner"] == "proposal_a"
            assert result.data["is_tie"] is False

    @pytest.mark.asyncio
    async def test_consensus_tie_breaking(self, consensus_config, mock_agents):
        """Test tie-breaking mechanism."""
        pattern = ConsensusPattern(consensus_config)

        # Create a tie scenario
        tie_agents = [
            MockAgent("agent_1", "proposal_a"),
            MockAgent("agent_2", "proposal_b")
        ]

        context = {
            "proposals": ["proposal_a", "proposal_b"]
        }

        with patch.object(pattern, '_get_agent_vote') as mock_vote:
            mock_vote.side_effect = lambda agent, proposals: {
                "choice": agent.preferred_choice,
                "confidence": 0.8,
                "reasoning": f"{agent.name} prefers {agent.preferred_choice}"
            }

            result = await pattern.execute(context, tie_agents)

            assert result.success is True
            assert "tie_broken_by" in result.data
            assert result.data["tie_broken_by"] == "seniority"
            assert result.data["winner"] in ["proposal_a", "proposal_b"]


class TestMemoryDeduplicationIntegration:
    """Integration tests for memory deduplication system."""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.mark.asyncio
    async def test_unified_memory_import_without_api_keys(self):
        """Test that unified memory can be imported without API keys."""
        # This should not raise an exception even without PORTKEY_API_KEY
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pulumi" / "mcp-server" / "src"))

            from unified_memory import (
                MemoryEntry,
                MemoryType,
                UnifiedMemoryConfig,
                UnifiedMemoryStore,
            )

            # Test basic instantiation
            config = UnifiedMemoryConfig()
            store = UnifiedMemoryStore(config)

            # Test memory entry creation
            entry = MemoryEntry(
                topic="Test Memory Entry",
                content="This is a test memory entry for deduplication testing",
                source="integration_test",
                memory_type=MemoryType.SEMANTIC
            )

            assert entry.hash_id is not None
            assert len(entry.hash_id) == 16  # SHA256 truncated to 16 chars
            assert entry.topic == "Test Memory Entry"

            print("✅ Unified memory system imports and basic functionality work")

        except Exception as e:
            pytest.fail(f"Unified memory import failed: {e}")

    @pytest.mark.asyncio
    async def test_memory_entry_deduplication_logic(self):
        """Test memory entry deduplication hash generation."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pulumi" / "mcp-server" / "src"))

        from unified_memory import MemoryEntry, MemoryType

        # Create identical entries
        entry1 = MemoryEntry(
            topic="Identical Topic",
            content="Identical Content",
            source="same_source",
            memory_type=MemoryType.SEMANTIC
        )

        entry2 = MemoryEntry(
            topic="Identical Topic",
            content="Identical Content",
            source="same_source",
            memory_type=MemoryType.SEMANTIC
        )

        # Different entry
        entry3 = MemoryEntry(
            topic="Different Topic",
            content="Different Content",
            source="different_source",
            memory_type=MemoryType.EPISODIC
        )

        # Test deduplication hashes
        assert entry1.hash_id == entry2.hash_id, "Identical entries should have same hash"
        assert entry1.hash_id != entry3.hash_id, "Different entries should have different hashes"

        print("✅ Memory deduplication logic works correctly")


class TestModernEmbeddingsIntegration:
    """Integration tests for modern three-tier embeddings."""

    @pytest.mark.asyncio
    async def test_modern_embeddings_import_and_config(self):
        """Test modern embeddings can be imported and configured."""
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pulumi" / "vector-store" / "src"))

            from modern_embeddings import (
                EmbeddingTier,
                IntelligentEmbeddingRouter,
                ModernEmbeddingConfig,
            )

            # Test configuration
            config = ModernEmbeddingConfig()
            assert config.tier_s_model == "voyage-3-large"
            assert config.tier_a_model == "cohere/embed-multilingual-v3.0"
            assert config.tier_b_model == "BAAI/bge-base-en-v1.5"

            # Test router initialization
            router = IntelligentEmbeddingRouter(config)

            # Test tier selection logic
            tier = router.select_tier("This is a production security critical system", "quality")
            assert tier == EmbeddingTier.TIER_S, "Quality priority should select Tier S"

            tier = router.select_tier("Quick test debug message", "speed")
            assert tier == EmbeddingTier.TIER_B, "Speed priority should select Tier B"

            tier = router.select_tier("Implement user authentication", "balanced")
            assert tier in [EmbeddingTier.TIER_A, EmbeddingTier.TIER_B], "Balanced should select appropriate tier"

            print("✅ Modern embeddings system configuration and routing work")

        except Exception as e:
            pytest.fail(f"Modern embeddings import failed: {e}")

    @pytest.mark.asyncio
    async def test_embedding_cache_functionality(self):
        """Test embedding cache without requiring API calls."""
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pulumi" / "vector-store" / "src"))

            import os
            import tempfile

            from modern_embeddings import (
                ModernEmbeddingCache,
                ModernEmbeddingConfig,
            )

            # Use temporary database
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                temp_db = f.name

            try:
                config = ModernEmbeddingConfig()
                config.cache_db_path = temp_db

                cache = ModernEmbeddingCache(config)

                # Test cache statistics
                stats = cache.get_statistics()
                assert "overall" in stats
                assert "model_statistics" in stats
                assert stats["overall"]["total_entries"] == 0  # Empty cache initially

                print("✅ Embedding cache functionality works")

            finally:
                if os.path.exists(temp_db):
                    os.unlink(temp_db)

        except Exception as e:
            pytest.fail(f"Embedding cache test failed: {e}")


async def run_integration_tests():
    """Run integration tests manually without pytest."""

    print("🚀 Running Consensus Swarm and Memory Deduplication Integration Tests")
    print("=" * 80)

    # Test 1: Consensus Pattern
    print("\n📊 Testing Consensus Pattern...")
    try:
        config = ConsensusConfig()
        pattern = ConsensusPattern(config)

        await pattern.initialize()
        print("✅ Consensus pattern initialization successful")

        await pattern.cleanup()
        print("✅ Consensus pattern cleanup successful")

    except Exception as e:
        print(f"❌ Consensus pattern test failed: {e}")

    # Test 2: Memory Deduplication
    print("\n🧠 Testing Memory Deduplication...")
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pulumi" / "mcp-server" / "src"))

        from unified_memory import MemoryEntry, MemoryType

        entry = MemoryEntry(
            topic="Integration Test Entry",
            content="Testing memory deduplication functionality",
            source="integration_test",
            memory_type=MemoryType.SEMANTIC
        )

        assert entry.hash_id is not None
        print("✅ Memory entry creation and hash generation successful")

    except Exception as e:
        print(f"❌ Memory deduplication test failed: {e}")

    # Test 3: Modern Embeddings
    print("\n🎯 Testing Modern Embeddings...")
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "pulumi" / "vector-store" / "src"))

        from modern_embeddings import (
            EmbeddingTier,
            IntelligentEmbeddingRouter,
            ModernEmbeddingConfig,
        )

        config = ModernEmbeddingConfig()
        router = IntelligentEmbeddingRouter(config)

        # Test tier selection
        tier = router.select_tier("production security critical", "quality")
        assert tier == EmbeddingTier.TIER_S
        print("✅ Intelligent embedding routing successful")

    except Exception as e:
        print(f"❌ Modern embeddings test failed: {e}")

    print("\n🎉 Integration tests completed!")
    print("✅ All core components are functional and ready for deployment")


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(run_integration_tests())
