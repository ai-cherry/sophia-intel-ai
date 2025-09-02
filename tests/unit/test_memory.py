"""
Unit Tests for Memory System
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.memory.dual_tier_embeddings import (
    DualTierEmbedder,
    EmbeddingConfig,
    EmbeddingRouter,
    EmbeddingTier,
)
from app.memory.embedding_pipeline import (
    EmbeddingModel,
    EmbeddingPurpose,
    EmbeddingRequest,
    cosine_similarity,
)
from app.memory.supermemory_mcp import MemoryType

# ============================================
# Supermemory Tests
# ============================================

class TestSupermemoryStore:
    """Test Supermemory storage system."""

    def test_add_memory(self, memory_store, sample_memory_entry):
        """Test adding memory to store."""
        memory = memory_store.add_memory(**sample_memory_entry)

        assert memory.hash_id is not None
        assert memory.topic == sample_memory_entry["topic"]
        assert memory.content == sample_memory_entry["content"]
        assert memory.memory_type == MemoryType(sample_memory_entry["memory_type"])

    def test_deduplication(self, memory_store, sample_memory_entry):
        """Test memory deduplication."""
        # Add same memory twice
        memory1 = memory_store.add_memory(**sample_memory_entry)
        memory2 = memory_store.add_memory(**sample_memory_entry)

        # Should return same hash_id
        assert memory1.hash_id == memory2.hash_id

    def test_search_memory(self, memory_store, sample_memory_entry):
        """Test searching memories."""
        # Add memory
        memory_store.add_memory(**sample_memory_entry)

        # Search for it
        results = memory_store.search(
            query="test content",
            limit=10
        )

        assert len(results) > 0
        assert results[0].content == sample_memory_entry["content"]

    def test_update_memory(self, memory_store, sample_memory_entry):
        """Test updating memory."""
        # Add memory
        memory = memory_store.add_memory(**sample_memory_entry)

        # Update it
        updated = memory_store.update_memory(
            hash_id=memory.hash_id,
            content="Updated content"
        )

        assert updated.content == "Updated content"
        assert updated.hash_id == memory.hash_id

    def test_delete_memory(self, memory_store, sample_memory_entry):
        """Test deleting memory."""
        # Add memory
        memory = memory_store.add_memory(**sample_memory_entry)

        # Delete it
        success = memory_store.delete_memory(memory.hash_id)
        assert success

        # Verify it's gone
        retrieved = memory_store.get_memory(memory.hash_id)
        assert retrieved is None

    def test_memory_types(self, memory_store):
        """Test different memory types."""
        memory_types = [
            MemoryType.EPISODIC,
            MemoryType.SEMANTIC,
            MemoryType.PROCEDURAL,
            MemoryType.WORKING
        ]

        for mem_type in memory_types:
            memory = memory_store.add_memory(
                topic=f"Test {mem_type.value}",
                content=f"Content for {mem_type.value}",
                memory_type=mem_type.value
            )
            assert memory.memory_type == mem_type

    def test_memory_metadata(self, memory_store):
        """Test memory metadata storage."""
        metadata = {
            "source": "test_file.py",
            "line_number": 42,
            "author": "test_user",
            "custom_field": "custom_value"
        }

        memory = memory_store.add_memory(
            topic="Metadata test",
            content="Test content",
            metadata=metadata
        )

        assert memory.metadata == metadata

    def test_memory_tags(self, memory_store):
        """Test memory tagging."""
        tags = ["python", "testing", "important"]

        memory = memory_store.add_memory(
            topic="Tagged memory",
            content="Content with tags",
            tags=tags
        )

        assert set(memory.tags) == set(tags)

        # Search by tag
        results = memory_store.search_by_tag("python")
        assert len(results) > 0
        assert "python" in results[0].tags

# ============================================
# Embedding Pipeline Tests
# ============================================

class TestEmbeddingPipeline:
    """Test standardized embedding pipeline."""

    @pytest.mark.asyncio
    async def test_generate_embeddings(self, embedding_pipeline):
        """Test embedding generation."""
        request = EmbeddingRequest(
            texts=["Test text 1", "Test text 2"],
            model=EmbeddingModel.EMBEDDING_3_SMALL,
            purpose=EmbeddingPurpose.SEARCH
        )

        results = await embedding_pipeline.generate_embeddings(request)

        assert len(results) == 2
        assert all(len(r.embedding) == 1536 for r in results)
        assert all(r.metadata.model == EmbeddingModel.EMBEDDING_3_SMALL.value for r in results)

    @pytest.mark.asyncio
    async def test_embedding_cache(self, embedding_pipeline):
        """Test embedding cache functionality."""
        request = EmbeddingRequest(
            texts=["Cached text"],
            model=EmbeddingModel.EMBEDDING_3_SMALL
        )

        # First call - should generate
        result1 = await embedding_pipeline.generate_embeddings(request)

        # Second call - should use cache
        result2 = await embedding_pipeline.generate_embeddings(request)

        assert result1[0].embedding == result2[0].embedding
        assert result1[0].text_hash == result2[0].text_hash

    def test_text_preprocessing(self, embedding_pipeline):
        """Test text preprocessing."""
        texts = [
            "  Text with   extra  spaces  ",
            "Text" * 10000,  # Very long text
            "Normal text"
        ]

        processed = embedding_pipeline._preprocess_texts(texts)

        # Check whitespace normalization
        assert processed[0] == "Text with extra spaces"

        # Check truncation
        assert len(processed[1]) <= 30003  # 30000 + "..."
        assert processed[1].endswith("...")

        # Check normal text unchanged
        assert processed[2] == "Normal text"

    @pytest.mark.asyncio
    async def test_batch_processing(self, embedding_pipeline):
        """Test batch embedding processing."""
        texts = [f"Text {i}" for i in range(100)]

        request = EmbeddingRequest(
            texts=texts,
            model=EmbeddingModel.EMBEDDING_3_SMALL
        )

        results = await embedding_pipeline.generate_embeddings(request)

        assert len(results) == 100
        assert all(r.text == texts[i] for i, r in enumerate(results))

    def test_embedding_metadata(self, embedding_pipeline):
        """Test embedding metadata generation."""
        request = EmbeddingRequest(
            texts=["Test text"],
            model=EmbeddingModel.EMBEDDING_3_LARGE,
            purpose=EmbeddingPurpose.CLUSTERING,
            metadata={"custom": "value"}
        )

        # Mock the result creation
        result = embedding_pipeline._create_result(
            text="Test text",
            embedding=[0.1] * 3072,
            model=EmbeddingModel.EMBEDDING_3_LARGE,
            purpose=EmbeddingPurpose.CLUSTERING,
            start_time=datetime.utcnow(),
            custom_metadata={"custom": "value"}
        )

        assert result.metadata.model == EmbeddingModel.EMBEDDING_3_LARGE.value
        assert result.metadata.purpose == EmbeddingPurpose.CLUSTERING.value
        assert result.metadata.dimensions == 3072
        assert result.metadata.custom_metadata == {"custom": "value"}

# ============================================
# Dual-Tier Embedding Tests
# ============================================

class TestDualTierEmbeddings:
    """Test dual-tier embedding system."""

    def test_tier_routing(self):
        """Test tier selection logic."""
        config = EmbeddingConfig()
        router = EmbeddingRouter(config)

        # Short text -> Tier B
        tier = router.select_tier("Short text")
        assert tier == EmbeddingTier.TIER_B

        # Long text -> Tier A
        long_text = "Long text " * 500
        tier = router.select_tier(long_text)
        assert tier == EmbeddingTier.TIER_A

        # Priority keyword -> Tier A
        tier = router.select_tier("This is about security")
        assert tier == EmbeddingTier.TIER_A

        # Language priority -> Tier A
        tier = router.select_tier("Code", language="python")
        assert tier == EmbeddingTier.TIER_A

    def test_batch_routing(self):
        """Test batch text routing."""
        config = EmbeddingConfig()
        router = EmbeddingRouter(config)

        texts = [
            "Short text",
            "Long text " * 500,
            "Security critical",
            "JavaScript code"
        ]

        metadata = [
            {},
            {},
            {},
            {"language": "javascript"}
        ]

        tier_indices = router.batch_route(texts, metadata)

        assert 0 in tier_indices[EmbeddingTier.TIER_B]
        assert 1 in tier_indices[EmbeddingTier.TIER_A]
        assert 2 in tier_indices[EmbeddingTier.TIER_A]
        assert 3 in tier_indices[EmbeddingTier.TIER_B]

    @pytest.mark.asyncio
    async def test_embed_single(self):
        """Test single text embedding."""
        embedder = DualTierEmbedder()

        with patch.object(embedder, 'standard_pipeline') as mock_pipeline:
            mock_pipeline.generate_embeddings = AsyncMock(
                return_value=[Mock(embedding=[0.1] * 1536)]
            )

            embedding, tier = await embedder.embed_single(
                "Test text",
                priority="low"
            )

            assert len(embedding) > 0
            assert tier == EmbeddingTier.TIER_B

    @pytest.mark.asyncio
    async def test_embed_batch(self):
        """Test batch text embedding."""
        embedder = DualTierEmbedder()

        with patch('app.memory.dual_tier_embeddings.gateway') as mock_gateway:
            mock_gateway.aembed = AsyncMock(
                return_value=[[0.1] * 768, [0.2] * 768]
            )

            texts = ["Text 1", "Text 2"]
            results = await embedder.embed_batch(texts, use_cache=False)

            assert len(results) == 2
            assert all(isinstance(r[0], list) for r in results)
            assert all(isinstance(r[1], EmbeddingTier) for r in results)

# ============================================
# Similarity Tests
# ============================================

class TestSimilarityFunctions:
    """Test similarity calculation functions."""

    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        # Identical vectors
        vec1 = [1.0, 0.0, 0.0]
        similarity = cosine_similarity(vec1, vec1)
        assert similarity == pytest.approx(1.0)

        # Orthogonal vectors
        vec2 = [0.0, 1.0, 0.0]
        similarity = cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(0.0)

        # Opposite vectors
        vec3 = [-1.0, 0.0, 0.0]
        similarity = cosine_similarity(vec1, vec3)
        assert similarity == pytest.approx(-1.0)

    def test_cosine_similarity_normalized(self):
        """Test cosine similarity with different magnitudes."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [2.0, 4.0, 6.0]  # Same direction, different magnitude

        similarity = cosine_similarity(vec1, vec2)
        assert similarity == pytest.approx(1.0)

    def test_zero_vector_similarity(self):
        """Test similarity with zero vector."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [0.0, 0.0, 0.0]

        similarity = cosine_similarity(vec1, vec2)
        assert similarity == 0.0
