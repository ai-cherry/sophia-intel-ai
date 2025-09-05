"""
Comprehensive test suite for Foundational Knowledge System
"""

import asyncio
import json
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.knowledge.classification_engine import ClassificationEngine
from app.knowledge.foundational_manager import FoundationalKnowledgeManager
from app.knowledge.models import (
    ConflictType,
    KnowledgeClassification,
    KnowledgeEntity,
    KnowledgePriority,
    KnowledgeVersion,
    PayReadyContext,
    SyncConflict,
    SyncOperation,
)
from app.knowledge.storage_adapter import StorageAdapter
from app.knowledge.versioning_engine import VersioningEngine

# ========== Fixtures ==========


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        yield f.name


@pytest.fixture
def mock_config(temp_db, monkeypatch):
    """Mock configuration for testing"""
    monkeypatch.setenv("DB_TYPE", "sqlite")
    monkeypatch.setenv("DB_PATH", temp_db)
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setenv("AIRTABLE_API_KEY", "test_key")


@pytest.fixture
def sample_entity():
    """Create sample knowledge entity"""
    return KnowledgeEntity(
        name="Pay Ready Mission",
        category="company_overview",
        classification=KnowledgeClassification.FOUNDATIONAL,
        priority=KnowledgePriority.CRITICAL,
        content={
            "mission": "AI-first resident engagement platform",
            "scale": "$20B+ annual rent processed",
            "employees": 100,
        },
        metadata={"source": "test", "confidence": 0.95},
    )


@pytest.fixture
def pay_ready_context():
    """Create Pay-Ready context"""
    return PayReadyContext()


# ========== Model Tests ==========


class TestKnowledgeModels:
    """Test data models"""

    def test_knowledge_entity_creation(self, sample_entity):
        """Test creating knowledge entity"""
        assert sample_entity.name == "Pay Ready Mission"
        assert sample_entity.classification == KnowledgeClassification.FOUNDATIONAL
        assert sample_entity.is_foundational is True
        assert sample_entity.priority == KnowledgePriority.CRITICAL

    def test_foundational_flag_auto_set(self):
        """Test automatic foundational flag setting"""
        entity = KnowledgeEntity(
            name="Test",
            category="test",
            classification=KnowledgeClassification.STRATEGIC,
            content={"test": "data"},
        )
        assert entity.is_foundational is True

        entity2 = KnowledgeEntity(
            name="Test2",
            category="test",
            classification=KnowledgeClassification.OPERATIONAL,
            content={"test": "data"},
        )
        assert entity2.is_foundational is False

    def test_priority_validation(self):
        """Test priority validation for foundational knowledge"""
        entity = KnowledgeEntity(
            name="Test",
            category="test",
            classification=KnowledgeClassification.FOUNDATIONAL,
            priority=KnowledgePriority.LOW,
            content={"test": "data"},
        )
        # Should auto-upgrade to HIGH
        assert entity.priority >= KnowledgePriority.HIGH

    def test_version_creation(self, sample_entity):
        """Test knowledge version creation"""
        version = KnowledgeVersion(
            knowledge_id=sample_entity.id,
            version_number=1,
            content=sample_entity.content,
            change_summary="Initial version",
            changed_by="test_user",
        )

        assert version.knowledge_id == sample_entity.id
        assert version.version_number == 1
        assert version.change_summary == "Initial version"

    def test_version_diff_generation(self):
        """Test version diff generation"""
        v1 = KnowledgeVersion(
            knowledge_id="test",
            version_number=1,
            content={"field1": "value1", "field2": "value2"},
        )

        v2 = KnowledgeVersion(
            knowledge_id="test",
            version_number=2,
            content={"field1": "value1_modified", "field3": "value3"},
        )

        diff = v2.generate_diff(v1)

        assert diff["type"] == "update"
        assert diff["version_from"] == 1
        assert diff["version_to"] == 2
        assert len(diff["changes"]) > 0

    def test_sync_conflict_creation(self, sample_entity):
        """Test sync conflict creation"""
        local = sample_entity.to_dict()
        remote = sample_entity.to_dict()
        remote["content"]["new_field"] = "remote_value"

        conflict = SyncConflict(
            knowledge_id=sample_entity.id,
            sync_operation_id="test_sync",
            local_version=local,
            remote_version=remote,
            conflict_type=ConflictType.CONTENT,
        )

        assert conflict.resolution_status.value == "pending"
        assert conflict.conflict_type == ConflictType.CONTENT

    def test_conflict_auto_resolution(self, sample_entity):
        """Test automatic conflict resolution"""
        local = sample_entity.to_dict()
        remote = sample_entity.to_dict()
        remote["content"]["new_field"] = "remote_value"

        conflict = SyncConflict(
            knowledge_id=sample_entity.id,
            sync_operation_id="test_sync",
            local_version=local,
            remote_version=remote,
            conflict_type=ConflictType.CONTENT,
        )

        # Test remote wins strategy
        resolved = conflict.auto_resolve("remote_wins")
        assert "new_field" in resolved.content
        assert conflict.resolution_status.value == "auto_resolved"

    def test_pay_ready_context(self, pay_ready_context):
        """Test Pay-Ready context"""
        assert pay_ready_context.company == "Pay Ready"
        assert "$20B+" in pay_ready_context.metrics["annual_rent_processed"]
        assert pay_ready_context.metrics["employee_count"] == 100
        assert len(pay_ready_context.key_differentiators) > 0


# ========== Storage Adapter Tests ==========


@pytest.mark.asyncio
class TestStorageAdapter:
    """Test storage adapter"""

    async def test_storage_initialization(self, mock_config):
        """Test storage adapter initialization"""
        storage = StorageAdapter()
        assert storage.db_type == "sqlite"
        assert storage.connection is not None
        storage.close()

    async def test_create_knowledge(self, mock_config, sample_entity):
        """Test creating knowledge in storage"""
        storage = StorageAdapter()

        created = await storage.create_knowledge(sample_entity)
        assert created.id == sample_entity.id

        # Verify it was stored
        retrieved = await storage.get_knowledge(sample_entity.id)
        assert retrieved is not None
        assert retrieved.name == sample_entity.name

        storage.close()

    async def test_update_knowledge(self, mock_config, sample_entity):
        """Test updating knowledge"""
        storage = StorageAdapter()

        # Create
        await storage.create_knowledge(sample_entity)

        # Update
        sample_entity.name = "Updated Name"
        updated = await storage.update_knowledge(sample_entity)

        # Verify
        retrieved = await storage.get_knowledge(sample_entity.id)
        assert retrieved.name == "Updated Name"

        storage.close()

    async def test_delete_knowledge(self, mock_config, sample_entity):
        """Test deleting knowledge"""
        storage = StorageAdapter()

        # Create
        await storage.create_knowledge(sample_entity)

        # Delete
        result = await storage.delete_knowledge(sample_entity.id)
        assert result is True

        # Verify deleted
        retrieved = await storage.get_knowledge(sample_entity.id)
        assert retrieved is None

        storage.close()

    async def test_list_knowledge(self, mock_config):
        """Test listing knowledge with filters"""
        storage = StorageAdapter()

        # Create multiple entities
        for i in range(5):
            entity = KnowledgeEntity(
                name=f"Test {i}",
                category="test",
                classification=(
                    KnowledgeClassification.FOUNDATIONAL
                    if i < 3
                    else KnowledgeClassification.OPERATIONAL
                ),
                content={"index": i},
            )
            await storage.create_knowledge(entity)

        # List all
        all_items = await storage.list_knowledge()
        assert len(all_items) >= 5

        # List with classification filter
        foundational = await storage.list_knowledge(classification="foundational")
        assert len(foundational) >= 3

        storage.close()

    async def test_search_knowledge(self, mock_config, sample_entity):
        """Test searching knowledge"""
        storage = StorageAdapter()

        await storage.create_knowledge(sample_entity)

        # Search
        results = await storage.search_knowledge("Pay Ready")
        assert len(results) > 0
        assert results[0].name == sample_entity.name

        storage.close()

    async def test_thread_safety(self, mock_config):
        """Test thread safety with concurrent operations"""
        storage = StorageAdapter()

        # Ensure lock exists
        assert hasattr(storage, "_connection_lock")

        # Create multiple entities concurrently
        async def create_entity(i):
            entity = KnowledgeEntity(
                name=f"Concurrent {i}",
                category="test",
                content={"index": i},
            )
            return await storage.create_knowledge(entity)

        # Run concurrent creates
        tasks = [create_entity(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10

        storage.close()


# ========== Classification Engine Tests ==========


@pytest.mark.asyncio
class TestClassificationEngine:
    """Test classification engine"""

    async def test_classify_foundational(self):
        """Test classifying foundational knowledge"""
        engine = ClassificationEngine()

        entity = KnowledgeEntity(
            name="Pay Ready Company Mission",
            category="company_overview",
            content={
                "text": "Pay Ready is an AI-first platform processing $20B in rent",
                "mission": "Transform multifamily housing payments",
            },
        )

        classification = await engine.classify(entity)
        assert classification == KnowledgeClassification.FOUNDATIONAL

    async def test_classify_strategic(self):
        """Test classifying strategic knowledge"""
        engine = ClassificationEngine()

        entity = KnowledgeEntity(
            name="Q1 Strategic Initiative",
            category="planning",
            content={
                "text": "Executive decision to expand into new markets",
                "type": "board presentation",
            },
        )

        classification = await engine.classify(entity)
        assert classification == KnowledgeClassification.STRATEGIC

    async def test_classify_operational(self):
        """Test classifying operational knowledge"""
        engine = ClassificationEngine()

        entity = KnowledgeEntity(
            name="Daily Report",
            category="operations",
            content={
                "text": "Standard operational metrics and KPIs",
                "type": "daily report",
            },
        )

        classification = await engine.classify(entity)
        assert classification == KnowledgeClassification.OPERATIONAL

    async def test_priority_determination(self):
        """Test priority determination"""
        engine = ClassificationEngine()

        # Critical priority
        entity1 = KnowledgeEntity(
            name="CEO Decision",
            category="executive",
            content={"text": "Critical board decision on acquisition"},
        )
        priority1 = await engine.determine_priority(entity1)
        assert priority1 == KnowledgePriority.CRITICAL

        # High priority
        entity2 = KnowledgeEntity(
            name="Strategic Plan",
            category="strategy",
            content={"text": "Strategic initiative for Pay Ready growth"},
        )
        priority2 = await engine.determine_priority(entity2)
        assert priority2 == KnowledgePriority.HIGH

    async def test_tag_suggestions(self):
        """Test tag suggestions"""
        engine = ClassificationEngine()

        entity = KnowledgeEntity(
            name="Pay Ready AI Platform",
            category="product",
            classification=KnowledgeClassification.FOUNDATIONAL,
            priority=KnowledgePriority.HIGH,
            content={
                "text": "Pay Ready uses AI for automated rent collection, processing $20B annually",
            },
        )

        tags = await engine.suggest_tags(entity)

        assert "foundational" in tags
        assert "pay_ready" in tags
        assert "ai_powered" in tags
        assert "scale_20b" in tags

    async def test_sensitivity_detection(self):
        """Test sensitive information detection"""
        engine = ClassificationEngine()

        entity = KnowledgeEntity(
            name="Financial Report",
            category="finance",
            content={
                "text": "Revenue: $100M, Profit margin: 30%, Strategic acquisition plan",
                "email": "test@payready.com",
            },
        )

        sensitivity = await engine.detect_sensitivity(entity)

        assert sensitivity["contains_financial"] is True
        assert sensitivity["contains_strategic"] is True
        assert sensitivity["contains_pii"] is True  # Email detected


# ========== Versioning Engine Tests ==========


@pytest.mark.asyncio
class TestVersioningEngine:
    """Test versioning engine"""

    async def test_create_version(self, mock_config, sample_entity):
        """Test creating version"""
        storage = StorageAdapter()
        engine = VersioningEngine(storage)

        # Create entity first
        await storage.create_knowledge(sample_entity)

        # Create version
        version = await engine.create_version(sample_entity, "test_user", "Initial version")

        assert version.version_number == 1
        assert version.changed_by == "test_user"
        assert version.change_summary == "Initial version"

        storage.close()

    async def test_version_history(self, mock_config, sample_entity):
        """Test getting version history"""
        storage = StorageAdapter()
        engine = VersioningEngine(storage)

        await storage.create_knowledge(sample_entity)

        # Create multiple versions
        for i in range(3):
            sample_entity.content[f"field_{i}"] = f"value_{i}"
            await engine.create_version(sample_entity, "test_user", f"Version {i+1}")

        # Get history
        history = await engine.get_history(sample_entity.id)
        assert len(history) >= 3

        storage.close()

    async def test_rollback(self, mock_config, sample_entity):
        """Test rolling back to previous version"""
        storage = StorageAdapter()
        engine = VersioningEngine(storage)

        await storage.create_knowledge(sample_entity)

        # Create initial version
        v1 = await engine.create_version(sample_entity, "user1", "Version 1")

        # Modify and create new version
        original_content = sample_entity.content.copy()
        sample_entity.content["new_field"] = "new_value"
        await storage.update_knowledge(sample_entity)
        v2 = await engine.create_version(sample_entity, "user2", "Version 2")

        # Rollback to v1
        rolled_back = await engine.rollback(sample_entity.id, 1)

        assert "new_field" not in rolled_back.content
        assert rolled_back.content == original_content

        storage.close()

    async def test_version_comparison(self, mock_config, sample_entity):
        """Test comparing versions"""
        storage = StorageAdapter()
        engine = VersioningEngine(storage)

        await storage.create_knowledge(sample_entity)

        # Create v1
        v1 = await engine.create_version(sample_entity, "user1", "Version 1")

        # Modify for v2
        sample_entity.content["modified_field"] = "new_value"
        sample_entity.content.pop("mission", None)
        await storage.update_knowledge(sample_entity)
        v2 = await engine.create_version(sample_entity, "user2", "Version 2")

        # Compare
        comparison = await engine.compare(sample_entity.id, 1, 2)

        assert comparison["version_1"] == 1
        assert comparison["version_2"] == 2
        assert "diff" in comparison

        storage.close()


# ========== Foundational Manager Tests ==========


@pytest.mark.asyncio
class TestFoundationalManager:
    """Test foundational knowledge manager"""

    async def test_manager_initialization(self, mock_config):
        """Test manager initialization"""
        manager = FoundationalKnowledgeManager()

        assert manager.storage is not None
        assert manager.versioning is not None
        assert manager.classifier is not None
        assert manager.pay_ready_context is not None

    async def test_create_with_classification(self, mock_config):
        """Test creating knowledge with auto-classification"""
        manager = FoundationalKnowledgeManager()

        entity = KnowledgeEntity(
            name="Test Entity",
            category="test",
            content={"text": "Pay Ready mission and vision"},
        )

        created = await manager.create(entity)

        assert created.classification != KnowledgeClassification.OPERATIONAL
        assert created.is_foundational is True

    async def test_get_with_caching(self, mock_config, sample_entity):
        """Test getting knowledge with cache"""
        manager = FoundationalKnowledgeManager()

        # Create
        created = await manager.create(sample_entity)

        # Get (should cache)
        retrieved1 = await manager.get(created.id)

        # Get again (should hit cache)
        retrieved2 = await manager.get(created.id)

        assert retrieved1.id == retrieved2.id
        assert retrieved1.name == retrieved2.name

    async def test_update_with_versioning(self, mock_config, sample_entity):
        """Test updating with version tracking"""
        manager = FoundationalKnowledgeManager()

        # Create
        created = await manager.create(sample_entity)
        initial_version = created.version

        # Update
        created.content["new_field"] = "new_value"
        updated = await manager.update(created)

        assert updated.version > initial_version

        # Check version history
        history = await manager.get_version_history(updated.id)
        assert len(history) >= 2

    async def test_list_foundational(self, mock_config):
        """Test listing foundational knowledge"""
        manager = FoundationalKnowledgeManager()

        # Create mixed entities
        for i in range(3):
            entity = KnowledgeEntity(
                name=f"Foundational {i}",
                category="test",
                classification=KnowledgeClassification.FOUNDATIONAL,
                content={"index": i},
            )
            await manager.create(entity)

        for i in range(2):
            entity = KnowledgeEntity(
                name=f"Operational {i}",
                category="test",
                classification=KnowledgeClassification.OPERATIONAL,
                content={"index": i},
            )
            await manager.create(entity)

        # List foundational only
        foundational = await manager.list_foundational()

        assert all(e.is_foundational for e in foundational)
        assert len(foundational) >= 3

    async def test_get_pay_ready_context(self, mock_config, sample_entity):
        """Test getting Pay-Ready context"""
        manager = FoundationalKnowledgeManager()

        await manager.create(sample_entity)

        context = await manager.get_pay_ready_context()

        assert context["company"] == "Pay Ready"
        assert "mission" in context
        assert "foundational_knowledge" in context

    async def test_statistics(self, mock_config):
        """Test getting statistics"""
        manager = FoundationalKnowledgeManager()

        # Create some entities
        for i in range(5):
            entity = KnowledgeEntity(
                name=f"Test {i}",
                category=f"cat_{i % 2}",
                classification=(
                    KnowledgeClassification.FOUNDATIONAL
                    if i < 3
                    else KnowledgeClassification.OPERATIONAL
                ),
                priority=KnowledgePriority.HIGH if i < 2 else KnowledgePriority.MEDIUM,
                content={"index": i},
            )
            await manager.create(entity)

        stats = await manager.get_statistics()

        assert stats["total_entries"] >= 5
        assert stats["foundational_count"] >= 3
        assert stats["operational_count"] >= 2
        assert len(stats["by_classification"]) > 0
        assert len(stats["by_priority"]) > 0
        assert len(stats["by_category"]) > 0


# ========== Integration Tests ==========


@pytest.mark.asyncio
class TestIntegration:
    """Integration tests"""

    async def test_full_workflow(self, mock_config):
        """Test complete workflow"""
        manager = FoundationalKnowledgeManager()

        # 1. Create foundational knowledge
        entity = KnowledgeEntity(
            name="Pay Ready Core",
            category="company",
            content={
                "mission": "AI-first platform",
                "scale": "$20B",
            },
        )
        created = await manager.create(entity)

        # 2. Update and track version
        created.content["new_metric"] = "100 employees"
        updated = await manager.update(created)

        # 3. Search for it
        results = await manager.search("Pay Ready")
        assert len(results) > 0

        # 4. Get version history
        history = await manager.get_version_history(updated.id)
        assert len(history) >= 2

        # 5. Rollback to previous version
        rolled_back = await manager.rollback_to_version(updated.id, 1)
        assert "new_metric" not in rolled_back.content

        # 6. Get statistics
        stats = await manager.get_statistics()
        assert stats["total_entries"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
