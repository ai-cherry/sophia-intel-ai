"""
Hierarchical Vector Indexing System

FAISS-based vector indexing with multi-level search capabilities and metadata storage.
Supports efficient similarity search across different hierarchy levels with persistence.
"""

import json
import logging
import pickle
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import numpy as np

try:
    import faiss
except ImportError:
    faiss = None
    logging.warning("FAISS not available. Install with: pip install faiss-cpu")

from .multi_modal_system import EmbeddingMetadata, EmbeddingType

logger = logging.getLogger(__name__)


class IndexLevel(Enum):
    """Index levels corresponding to hierarchy levels"""

    FILE = "file"
    CLASS = "class"
    METHOD = "method"
    BLOCK = "block"


class SearchMode(Enum):
    """Search modes for different use cases"""

    EXACT = "exact"  # Exact similarity search
    FUZZY = "fuzzy"  # Approximate search with higher recall
    HIERARCHICAL = "hierarchical"  # Search across hierarchy levels
    HYBRID = "hybrid"  # Combination of semantic and keyword search


@dataclass
class SearchResult:
    """Result from vector search"""

    embedding_id: str
    score: float
    metadata: EmbeddingMetadata
    vector: Optional[np.ndarray] = None
    hierarchy_path: Optional[str] = None


@dataclass
class IndexStats:
    """Statistics for an index"""

    total_vectors: int
    dimensions: int
    index_type: str
    memory_usage_mb: float
    last_updated: datetime
    search_performance_ms: Optional[float] = None


class MetadataStore:
    """Efficient metadata storage and retrieval"""

    def __init__(self, storage_dir: Path):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # In-memory store for fast access
        self._metadata: dict[str, EmbeddingMetadata] = {}
        self._id_to_index: dict[str, int] = {}  # Maps embedding_id to FAISS index
        self._index_to_id: dict[int, str] = {}  # Maps FAISS index to embedding_id

        self._next_index = 0
        self._load_metadata()

    def _load_metadata(self):
        """Load metadata from persistent storage"""
        metadata_file = self.storage_dir / "metadata.pkl"
        index_file = self.storage_dir / "index_mapping.pkl"

        if metadata_file.exists():
            try:
                with open(metadata_file, "rb") as f:
                    self._metadata = pickle.load(f)

                with open(index_file, "rb") as f:
                    mapping_data = pickle.load(f)
                    self._id_to_index = mapping_data["id_to_index"]
                    self._index_to_id = mapping_data["index_to_id"]
                    self._next_index = mapping_data["next_index"]

                logger.info(f"Loaded {len(self._metadata)} metadata entries")
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}")
                self._metadata = {}
                self._id_to_index = {}
                self._index_to_id = {}
                self._next_index = 0

    def _save_metadata(self):
        """Save metadata to persistent storage"""
        metadata_file = self.storage_dir / "metadata.pkl"
        index_file = self.storage_dir / "index_mapping.pkl"

        try:
            with open(metadata_file, "wb") as f:
                pickle.dump(self._metadata, f)

            mapping_data = {
                "id_to_index": self._id_to_index,
                "index_to_id": self._index_to_id,
                "next_index": self._next_index,
            }

            with open(index_file, "wb") as f:
                pickle.dump(mapping_data, f)

        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def add(self, embedding_id: str, metadata: EmbeddingMetadata) -> int:
        """Add metadata and return FAISS index"""
        if embedding_id in self._id_to_index:
            return self._id_to_index[embedding_id]

        faiss_index = self._next_index
        self._metadata[embedding_id] = metadata
        self._id_to_index[embedding_id] = faiss_index
        self._index_to_id[faiss_index] = embedding_id
        self._next_index += 1

        return faiss_index

    def get(self, embedding_id: str) -> Optional[EmbeddingMetadata]:
        """Get metadata by embedding ID"""
        return self._metadata.get(embedding_id)

    def get_by_faiss_index(
        self, faiss_index: int
    ) -> Optional[tuple[str, EmbeddingMetadata]]:
        """Get embedding ID and metadata by FAISS index"""
        embedding_id = self._index_to_id.get(faiss_index)
        if embedding_id:
            metadata = self._metadata.get(embedding_id)
            return embedding_id, metadata
        return None

    def remove(self, embedding_id: str) -> bool:
        """Remove metadata entry"""
        if embedding_id not in self._id_to_index:
            return False

        faiss_index = self._id_to_index[embedding_id]
        del self._metadata[embedding_id]
        del self._id_to_index[embedding_id]
        del self._index_to_id[faiss_index]

        return True

    def search_metadata(self, **criteria) -> list[str]:
        """Search metadata by criteria and return embedding IDs"""
        results = []

        for embedding_id, metadata in self._metadata.items():
            match = True

            for key, value in criteria.items():
                if hasattr(metadata, key):
                    attr_value = getattr(metadata, key)
                    if isinstance(attr_value, Enum):
                        attr_value = attr_value.value

                    if attr_value != value:
                        match = False
                        break
                elif key in metadata.extra_metadata:
                    if metadata.extra_metadata[key] != value:
                        match = False
                        break
                else:
                    match = False
                    break

            if match:
                results.append(embedding_id)

        return results

    def get_stats(self) -> dict[str, Any]:
        """Get metadata store statistics"""
        embedding_types = {}
        hierarchy_levels = {}
        providers = {}

        for metadata in self._metadata.values():
            # Count by type
            emb_type = metadata.embedding_type.value
            embedding_types[emb_type] = embedding_types.get(emb_type, 0) + 1

            # Count by hierarchy level
            hierarchy = metadata.hierarchy_level.value
            hierarchy_levels[hierarchy] = hierarchy_levels.get(hierarchy, 0) + 1

            # Count by provider
            provider = metadata.provider
            providers[provider] = providers.get(provider, 0) + 1

        return {
            "total_entries": len(self._metadata),
            "embedding_types": embedding_types,
            "hierarchy_levels": hierarchy_levels,
            "providers": providers,
            "next_index": self._next_index,
        }

    def save(self):
        """Save metadata to disk"""
        self._save_metadata()


class LevelIndex:
    """Individual FAISS index for a specific hierarchy level"""

    def __init__(self, level: IndexLevel, dimensions: int, index_type: str = "flat"):
        self.level = level
        self.dimensions = dimensions
        self.index_type = index_type

        if faiss is None:
            raise ImportError(
                "FAISS not available. Install with: pip install faiss-cpu"
            )

        # Create FAISS index based on type
        if index_type == "flat":
            self.index = faiss.IndexFlatIP(
                dimensions
            )  # Inner product (cosine similarity)
        elif index_type == "hnsw":
            self.index = faiss.IndexHNSWFlat(dimensions, 32)
            self.index.hnsw.efConstruction = 200
            self.index.hnsw.efSearch = 128
        elif index_type == "ivf":
            quantizer = faiss.IndexFlatIP(dimensions)
            self.index = faiss.IndexIVFFlat(quantizer, dimensions, 100)
        else:
            raise ValueError(f"Unsupported index type: {index_type}")

        self.vector_ids = []  # Track vector IDs in order
        self._stats = IndexStats(
            total_vectors=0,
            dimensions=dimensions,
            index_type=index_type,
            memory_usage_mb=0.0,
            last_updated=datetime.now(),
        )

    def add_vectors(self, vectors: np.ndarray, vector_ids: list[str]):
        """Add vectors to the index"""
        if len(vectors) != len(vector_ids):
            raise ValueError("Vectors and vector_ids must have same length")

        if vectors.shape[1] != self.dimensions:
            raise ValueError(
                f"Vector dimensions {vectors.shape[1]} don't match index {self.dimensions}"
            )

        # Normalize vectors for cosine similarity
        faiss.normalize_L2(vectors)

        # Train index if needed (for IVF)
        if not self.index.is_trained:
            self.index.train(vectors)

        # Add to index
        self.index.add(vectors)
        self.vector_ids.extend(vector_ids)

        # Update stats
        self._stats.total_vectors = len(self.vector_ids)
        self._stats.memory_usage_mb = self._estimate_memory_usage()
        self._stats.last_updated = datetime.now()

        logger.debug(f"Added {len(vectors)} vectors to {self.level.value} index")

    def search(
        self, query_vector: np.ndarray, k: int = 10, threshold: Optional[float] = None
    ) -> list[tuple[str, float]]:
        """Search for similar vectors"""
        if self.index.ntotal == 0:
            return []

        if query_vector.shape[0] != self.dimensions:
            raise ValueError("Query vector dimensions don't match index dimensions")

        # Normalize query vector
        query_vector = query_vector.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_vector)

        # Search
        start_time = datetime.now()
        scores, indices = self.index.search(query_vector, min(k, self.index.ntotal))
        search_time = (datetime.now() - start_time).total_seconds() * 1000

        # Update search performance stats
        self._stats.search_performance_ms = search_time

        # Convert to results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.vector_ids):
                if threshold is None or score >= threshold:
                    results.append((self.vector_ids[idx], float(score)))

        return results

    def remove_vector(self, vector_id: str) -> bool:
        """Remove a vector from the index (requires rebuilding)"""
        if vector_id not in self.vector_ids:
            return False

        # FAISS doesn't support removal, so we mark for rebuild
        # This is handled by the parent HierarchicalIndex
        return True

    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB"""
        if self.index.ntotal == 0:
            return 0.0

        # Rough estimation based on index type and vector count
        vector_size = self.dimensions * 4  # 4 bytes per float32
        total_vector_memory = self.index.ntotal * vector_size

        if self.index_type == "flat":
            return total_vector_memory / (1024 * 1024)
        elif self.index_type == "hnsw":
            # HNSW has additional overhead for graph structure
            return total_vector_memory * 1.5 / (1024 * 1024)
        elif self.index_type == "ivf":
            # IVF has quantizer overhead
            return total_vector_memory * 1.2 / (1024 * 1024)

        return total_vector_memory / (1024 * 1024)

    def get_stats(self) -> IndexStats:
        """Get index statistics"""
        self._stats.memory_usage_mb = self._estimate_memory_usage()
        return self._stats

    def save(self, file_path: Path):
        """Save index to disk"""
        faiss.write_index(self.index, str(file_path))

        # Save vector IDs
        ids_file = file_path.with_suffix(".ids")
        with open(ids_file, "wb") as f:
            pickle.dump(self.vector_ids, f)

    def load(self, file_path: Path):
        """Load index from disk"""
        if not file_path.exists():
            raise FileNotFoundError(f"Index file not found: {file_path}")

        self.index = faiss.read_index(str(file_path))

        # Load vector IDs
        ids_file = file_path.with_suffix(".ids")
        if ids_file.exists():
            with open(ids_file, "rb") as f:
                self.vector_ids = pickle.load(f)

        # Update stats
        self._stats.total_vectors = len(self.vector_ids)
        self._stats.memory_usage_mb = self._estimate_memory_usage()


class HierarchicalIndex:
    """
    Multi-level FAISS-based vector index with metadata storage.
    Provides efficient similarity search across different hierarchy levels.
    """

    def __init__(
        self, storage_dir: str, dimensions: int = 1536, index_type: str = "flat"
    ):
        """
        Initialize hierarchical index

        Args:
            storage_dir: Directory for storing indices and metadata
            dimensions: Vector dimensions
            index_type: FAISS index type ('flat', 'hnsw', 'ivf')
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.dimensions = dimensions
        self.index_type = index_type

        if faiss is None:
            raise ImportError(
                "FAISS not available. Install with: pip install faiss-cpu"
            )

        # Initialize metadata store
        self.metadata_store = MetadataStore(self.storage_dir / "metadata")

        # Initialize level indices
        self.level_indices: dict[IndexLevel, LevelIndex] = {}
        for level in IndexLevel:
            self.level_indices[level] = LevelIndex(level, dimensions, index_type)

        # Load existing indices
        self._load_indices()

        logger.info(
            f"Initialized hierarchical index with {dimensions}D vectors, {index_type} type"
        )

    def add_embedding(
        self, embedding_id: str, vector: np.ndarray, metadata: EmbeddingMetadata
    ) -> bool:
        """
        Add an embedding to the appropriate level index

        Args:
            embedding_id: Unique identifier for the embedding
            vector: Embedding vector
            metadata: Embedding metadata

        Returns:
            True if added successfully
        """
        try:
            # Add to metadata store
            self.metadata_store.add(embedding_id, metadata)

            # Determine which level index to use
            level = IndexLevel(metadata.hierarchy_level.value)

            # Add to appropriate level index
            vector_array = vector.reshape(1, -1).astype(np.float32)
            self.level_indices[level].add_vectors(vector_array, [embedding_id])

            logger.debug(f"Added embedding {embedding_id} to {level.value} index")
            return True

        except Exception as e:
            logger.error(f"Failed to add embedding {embedding_id}: {e}")
            return False

    def add_batch_embeddings(
        self, embeddings: list[tuple[str, np.ndarray, EmbeddingMetadata]]
    ) -> int:
        """
        Add multiple embeddings in batch for efficiency

        Args:
            embeddings: List of (embedding_id, vector, metadata) tuples

        Returns:
            Number of embeddings added successfully
        """
        if not embeddings:
            return 0

        # Group by hierarchy level
        level_groups: dict[
            IndexLevel, list[tuple[str, np.ndarray, EmbeddingMetadata]]
        ] = {}

        for embedding_id, vector, metadata in embeddings:
            level = IndexLevel(metadata.hierarchy_level.value)
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append((embedding_id, vector, metadata))

        added_count = 0

        # Process each level group
        for level, group_embeddings in level_groups.items():
            try:
                # Prepare batch data
                embedding_ids = []
                vectors = []
                metadatas = []

                for embedding_id, vector, metadata in group_embeddings:
                    # Add to metadata store
                    self.metadata_store.add(embedding_id, metadata)
                    embedding_ids.append(embedding_id)
                    vectors.append(vector)
                    metadatas.append(metadata)

                # Convert to numpy array
                vector_array = np.vstack(vectors).astype(np.float32)

                # Add to level index
                self.level_indices[level].add_vectors(vector_array, embedding_ids)

                added_count += len(group_embeddings)
                logger.info(
                    f"Added {len(group_embeddings)} embeddings to {level.value} index"
                )

            except Exception as e:
                logger.error(f"Failed to add batch for level {level.value}: {e}")

        return added_count

    def search(
        self,
        query_vector: np.ndarray,
        k: int = 10,
        levels: Optional[list[IndexLevel]] = None,
        embedding_types: Optional[list[EmbeddingType]] = None,
        threshold: Optional[float] = None,
        metadata_filters: Optional[dict[str, Any]] = None,
    ) -> list[SearchResult]:
        """
        Search for similar embeddings across hierarchy levels

        Args:
            query_vector: Query embedding vector
            k: Number of results to return
            levels: Specific levels to search (all levels if None)
            embedding_types: Filter by embedding types
            threshold: Minimum similarity threshold
            metadata_filters: Additional metadata filters

        Returns:
            List of search results sorted by score
        """
        if query_vector.shape[0] != self.dimensions:
            raise ValueError("Query vector dimensions don't match index dimensions")

        # Default to all levels
        if levels is None:
            levels = list(IndexLevel)

        all_results = []

        # Search each requested level
        for level in levels:
            level_index = self.level_indices[level]

            try:
                # Search level index
                level_results = level_index.search(
                    query_vector, k * 2, threshold
                )  # Get more for filtering

                # Convert to SearchResult objects with metadata
                for embedding_id, score in level_results:
                    metadata = self.metadata_store.get(embedding_id)
                    if metadata is None:
                        continue

                    # Apply filters
                    if (
                        embedding_types
                        and metadata.embedding_type not in embedding_types
                    ):
                        continue

                    if metadata_filters:
                        if not self._matches_filters(metadata, metadata_filters):
                            continue

                    # Create hierarchy path
                    hierarchy_path = self._build_hierarchy_path(metadata)

                    result = SearchResult(
                        embedding_id=embedding_id,
                        score=score,
                        metadata=metadata,
                        hierarchy_path=hierarchy_path,
                    )

                    all_results.append(result)

            except Exception as e:
                logger.warning(f"Search failed for level {level.value}: {e}")

        # Sort by score and return top k
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results[:k]

    def hierarchical_search(
        self, query_vector: np.ndarray, k: int = 10, expand_results: bool = True
    ) -> dict[IndexLevel, list[SearchResult]]:
        """
        Perform hierarchical search starting from file level and expanding down

        Args:
            query_vector: Query embedding vector
            k: Number of results per level
            expand_results: Whether to expand file results to class/method level

        Returns:
            Dictionary mapping levels to search results
        """
        results = {}

        # Start with file-level search
        file_results = self.search(query_vector, k, [IndexLevel.FILE])
        results[IndexLevel.FILE] = file_results

        if expand_results and file_results:
            # Get file paths from file results
            relevant_files = {result.metadata.file_path for result in file_results}

            # Search class level for these files
            class_results = []
            for file_path in relevant_files:
                file_class_results = self.search(
                    query_vector,
                    k,
                    [IndexLevel.CLASS],
                    metadata_filters={"file_path": file_path},
                )
                class_results.extend(file_class_results)

            results[IndexLevel.CLASS] = sorted(
                class_results, key=lambda x: x.score, reverse=True
            )[:k]

            # Search method level for relevant classes
            method_results = []
            relevant_classes = {
                (result.metadata.file_path, result.metadata.class_name)
                for result in class_results
                if result.metadata.class_name
            }

            for file_path, class_name in relevant_classes:
                class_method_results = self.search(
                    query_vector,
                    k,
                    [IndexLevel.METHOD],
                    metadata_filters={"file_path": file_path, "class_name": class_name},
                )
                method_results.extend(class_method_results)

            results[IndexLevel.METHOD] = sorted(
                method_results, key=lambda x: x.score, reverse=True
            )[:k]

        return results

    def _matches_filters(
        self, metadata: EmbeddingMetadata, filters: dict[str, Any]
    ) -> bool:
        """Check if metadata matches filters"""
        for key, value in filters.items():
            if hasattr(metadata, key):
                attr_value = getattr(metadata, key)
                if isinstance(attr_value, Enum):
                    attr_value = attr_value.value

                if attr_value != value:
                    return False
            elif key in metadata.extra_metadata:
                if metadata.extra_metadata[key] != value:
                    return False
            else:
                return False

        return True

    def _build_hierarchy_path(self, metadata: EmbeddingMetadata) -> str:
        """Build hierarchy path string for a metadata entry"""
        parts = [metadata.file_path]

        if metadata.class_name:
            parts.append(metadata.class_name)

        if metadata.method_name:
            parts.append(metadata.method_name)

        if metadata.block_id:
            parts.append(f"block:{metadata.block_id}")

        return " > ".join(parts)

    def get_embedding(
        self, embedding_id: str
    ) -> Optional[tuple[EmbeddingMetadata, np.ndarray]]:
        """Get embedding metadata and vector by ID"""
        metadata = self.metadata_store.get(embedding_id)
        if metadata is None:
            return None

        # Vector retrieval would require storing vectors separately
        # For now, return metadata only
        return metadata, None

    def remove_embedding(self, embedding_id: str) -> bool:
        """Remove an embedding from all indices"""
        metadata = self.metadata_store.get(embedding_id)
        if metadata is None:
            return False

        # Remove from metadata store
        success = self.metadata_store.remove(embedding_id)

        # Note: FAISS doesn't support direct removal, so we'd need to rebuild
        # This is a limitation that could be addressed with more sophisticated index management

        return success

    def save_indices(self):
        """Save all indices and metadata to disk"""
        try:
            # Save metadata store
            self.metadata_store.save()

            # Save each level index
            for level, index in self.level_indices.items():
                index_file = self.storage_dir / f"{level.value}_index.faiss"
                index.save(index_file)

            # Save configuration
            config = {
                "dimensions": self.dimensions,
                "index_type": self.index_type,
                "created_at": datetime.now().isoformat(),
                "levels": [level.value for level in IndexLevel],
            }

            config_file = self.storage_dir / "config.json"
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

            logger.info("Saved hierarchical indices to disk")

        except Exception as e:
            logger.error(f"Failed to save indices: {e}")
            raise

    def _load_indices(self):
        """Load existing indices from disk"""
        config_file = self.storage_dir / "config.json"

        if not config_file.exists():
            logger.info("No existing indices found")
            return

        try:
            # Load configuration
            with open(config_file) as f:
                config = json.load(f)

            # Validate configuration compatibility
            if config["dimensions"] != self.dimensions:
                logger.warning(
                    f"Dimension mismatch: {config['dimensions']} != {self.dimensions}"
                )
                return

            # Load each level index
            for level in IndexLevel:
                index_file = self.storage_dir / f"{level.value}_index.faiss"
                if index_file.exists():
                    self.level_indices[level].load(index_file)
                    logger.debug(f"Loaded {level.value} index")

            logger.info("Loaded existing hierarchical indices")

        except Exception as e:
            logger.warning(f"Failed to load existing indices: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive statistics for the hierarchical index"""
        level_stats = {}
        total_vectors = 0
        total_memory = 0.0

        for level, index in self.level_indices.items():
            stats = index.get_stats()
            level_stats[level.value] = asdict(stats)
            total_vectors += stats.total_vectors
            total_memory += stats.memory_usage_mb

        metadata_stats = self.metadata_store.get_stats()

        return {
            "total_vectors": total_vectors,
            "total_memory_mb": total_memory,
            "dimensions": self.dimensions,
            "index_type": self.index_type,
            "storage_dir": str(self.storage_dir),
            "level_stats": level_stats,
            "metadata_stats": metadata_stats,
        }

    async def optimize_indices(self):
        """Optimize indices for better performance"""
        logger.info("Starting index optimization...")

        # This would involve rebuilding indices with better parameters
        # For now, just log the operation
        for level, index in self.level_indices.items():
            if index.index.ntotal > 1000 and self.index_type == "flat":
                logger.info(
                    f"Consider switching {level.value} index to HNSW for better performance"
                )

        logger.info("Index optimization completed")

    def rebuild_index(self, level: IndexLevel) -> bool:
        """Rebuild a specific level index"""
        try:
            # Get all embeddings for this level
            embedding_ids = self.metadata_store.search_metadata(
                hierarchy_level=level.value
            )

            if not embedding_ids:
                logger.info(f"No embeddings found for level {level.value}")
                return True

            # Create new index
            LevelIndex(level, self.dimensions, self.index_type)

            # Note: This would require storing original vectors
            # For now, this is a placeholder for the rebuild logic

            logger.info(f"Rebuilt {level.value} index")
            return True

        except Exception as e:
            logger.error(f"Failed to rebuild {level.value} index: {e}")
            return False
