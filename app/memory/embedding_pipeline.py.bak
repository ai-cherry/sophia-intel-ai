"""
Standardized Embedding Pipeline for Sophia Intel AI
Provides consistent embedding generation with metadata tracking.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import hashlib
import asyncio
import logging

import numpy as np
from pydantic import BaseModel, Field

# Optional OpenAI import
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

from app.core.config import settings

# Optional observability imports
try:
    from app.core.observability import metrics, trace_async
except ImportError:
    # Fallback if observability not available
    class DummyMetrics:
        def __init__(self):
            self.embedding_cache_hits = type('obj', (object,), {'inc': lambda: None})()
            self.embedding_cache_misses = type('obj', (object,), {'inc': lambda: None})()
            self.embeddings_generated = type('obj', (object,), {'inc': lambda x: None})()
            self.embedding_errors = type('obj', (object,), {'inc': lambda: None})()
        
        def get_embedding_cache_hit_rate(self):
            return 0.0
    
    metrics = DummyMetrics()
    
    def trace_async(func):
        """Dummy decorator when tracing not available."""
        return func

logger = logging.getLogger(__name__)

# ============================================
# Data Models
# ============================================

class EmbeddingModel(str, Enum):
    """Available embedding models."""
    ADA_002 = "text-embedding-ada-002"
    EMBEDDING_3_SMALL = "text-embedding-3-small"
    EMBEDDING_3_LARGE = "text-embedding-3-large"
    EMBEDDING_3_SMALL_512 = "text-embedding-3-small-512"  # Reduced dimensions
    EMBEDDING_3_LARGE_1024 = "text-embedding-3-large-1024"  # Reduced dimensions

class EmbeddingPurpose(str, Enum):
    """Purpose of embedding generation."""
    SEARCH = "search"
    CLUSTERING = "clustering"
    CLASSIFICATION = "classification"
    SIMILARITY = "similarity"
    INDEXING = "indexing"

@dataclass
class EmbeddingMetadata:
    """Metadata for embeddings."""
    model: str
    dimensions: int
    purpose: str
    source_hash: str
    token_count: int
    generation_time_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: str = "2.0.0"
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    embedding: List[float]
    metadata: EmbeddingMetadata
    text: str
    text_hash: str
    
    @property
    def vector(self) -> np.ndarray:
        """Get embedding as numpy array."""
        return np.array(self.embedding)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "embedding": self.embedding,
            "metadata": self.metadata.to_dict(),
            "text": self.text,
            "text_hash": self.text_hash
        }

class EmbeddingRequest(BaseModel):
    """Request for embedding generation."""
    texts: List[str]
    model: EmbeddingModel = EmbeddingModel.EMBEDDING_3_SMALL
    purpose: EmbeddingPurpose = EmbeddingPurpose.SEARCH
    dimensions: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

# ============================================
# Embedding Pipeline
# ============================================

class StandardizedEmbeddingPipeline:
    """Standardized pipeline for generating embeddings."""
    
    def __init__(self):
        """Initialize the embedding pipeline."""
        if OPENAI_AVAILABLE and hasattr(settings, 'openai_api_key'):
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        else:
            self.client = None
        self._cache = {}  # Simple in-memory cache
        self._model_dimensions = {
            EmbeddingModel.ADA_002: 1536,
            EmbeddingModel.EMBEDDING_3_SMALL: 1536,
            EmbeddingModel.EMBEDDING_3_LARGE: 3072,
            EmbeddingModel.EMBEDDING_3_SMALL_512: 512,
            EmbeddingModel.EMBEDDING_3_LARGE_1024: 1024,
        }
    
    @trace_async
    async def generate_embeddings(
        self,
        request: EmbeddingRequest
    ) -> List[EmbeddingResult]:
        """Generate embeddings for texts.
        
        Args:
            request: Embedding request with texts and configuration
            
        Returns:
            List of embedding results with metadata
        """
        start_time = datetime.utcnow()
        
        # Pre-process texts
        processed_texts = self._preprocess_texts(request.texts)
        
        # Check cache for existing embeddings
        results = []
        texts_to_embed = []
        text_indices = []
        
        for i, text in enumerate(processed_texts):
            cache_key = self._get_cache_key(text, request.model, request.purpose)
            
            if cache_key in self._cache:
                # Use cached embedding
                cached = self._cache[cache_key]
                metrics.embedding_cache_hits.inc()
                results.append((i, cached))
            else:
                # Need to generate embedding
                texts_to_embed.append(text)
                text_indices.append(i)
                metrics.embedding_cache_misses.inc()
        
        # Generate new embeddings if needed
        if texts_to_embed:
            new_embeddings = await self._generate_batch(
                texts_to_embed,
                request.model,
                request.dimensions
            )
            
            # Create results and cache
            for idx, text, embedding in zip(text_indices, texts_to_embed, new_embeddings):
                result = self._create_result(
                    text=text,
                    embedding=embedding,
                    model=request.model,
                    purpose=request.purpose,
                    start_time=start_time,
                    custom_metadata=request.metadata
                )
                
                # Cache the result
                cache_key = self._get_cache_key(text, request.model, request.purpose)
                self._cache[cache_key] = result
                
                results.append((idx, result))
        
        # Sort results by original index
        results.sort(key=lambda x: x[0])
        
        # Update metrics
        metrics.embeddings_generated.inc(len(texts_to_embed))
        
        return [result for _, result in results]
    
    async def _generate_batch(
        self,
        texts: List[str],
        model: EmbeddingModel,
        dimensions: Optional[int] = None
    ) -> List[List[float]]:
        """Generate embeddings for a batch of texts.
        
        Args:
            texts: Texts to embed
            model: Embedding model to use
            dimensions: Optional dimension reduction
            
        Returns:
            List of embedding vectors
        """
        # Return mock embeddings if OpenAI not available
        if not self.client:
            logger.warning("OpenAI client not available, returning mock embeddings")
            dim = dimensions or self._model_dimensions.get(model, 1536)
            return [[0.1] * dim for _ in texts]
        
        try:
            # Prepare request parameters
            params = {
                "input": texts,
                "model": model.value
            }
            
            # Add dimensions if specified and supported
            if dimensions and model in [
                EmbeddingModel.EMBEDDING_3_SMALL,
                EmbeddingModel.EMBEDDING_3_LARGE
            ]:
                params["dimensions"] = dimensions
            
            # Call OpenAI API
            response = await self.client.embeddings.create(**params)
            
            # Extract embeddings
            embeddings = [item.embedding for item in response.data]
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            metrics.embedding_errors.inc()
            raise
    
    def _preprocess_texts(self, texts: List[str]) -> List[str]:
        """Preprocess texts for embedding.
        
        Args:
            texts: Raw texts
            
        Returns:
            Processed texts
        """
        processed = []
        
        for text in texts:
            # Normalize whitespace
            text = ' '.join(text.split())
            
            # Truncate if too long (8191 token limit)
            # Rough estimate: 1 token ≈ 4 characters
            max_chars = 30000
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
                logger.warning(f"Truncated text from {len(text)} to {max_chars} chars")
            
            processed.append(text)
        
        return processed
    
    def _create_result(
        self,
        text: str,
        embedding: List[float],
        model: EmbeddingModel,
        purpose: EmbeddingPurpose,
        start_time: datetime,
        custom_metadata: Dict[str, Any]
    ) -> EmbeddingResult:
        """Create an embedding result with metadata.
        
        Args:
            text: Original text
            embedding: Embedding vector
            model: Model used
            purpose: Purpose of embedding
            start_time: When generation started
            custom_metadata: Additional metadata
            
        Returns:
            Complete embedding result
        """
        # Calculate metadata
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        token_count = len(text) // 4  # Rough estimate
        generation_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        metadata = EmbeddingMetadata(
            model=model.value,
            dimensions=len(embedding),
            purpose=purpose.value,
            source_hash=text_hash[:16],
            token_count=token_count,
            generation_time_ms=generation_time_ms,
            custom_metadata=custom_metadata
        )
        
        return EmbeddingResult(
            embedding=embedding,
            metadata=metadata,
            text=text,
            text_hash=text_hash
        )
    
    def _get_cache_key(
        self,
        text: str,
        model: EmbeddingModel,
        purpose: EmbeddingPurpose
    ) -> str:
        """Generate cache key for embedding.
        
        Args:
            text: Text to embed
            model: Model to use
            purpose: Purpose of embedding
            
        Returns:
            Cache key
        """
        components = [
            hashlib.sha256(text.encode()).hexdigest(),
            model.value,
            purpose.value
        ]
        return ":".join(components)
    
    def clear_cache(self):
        """Clear the embedding cache."""
        self._cache.clear()
        logger.info("Embedding cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache statistics
        """
        return {
            "size": len(self._cache),
            "memory_mb": sum(
                len(str(v.embedding)) for v in self._cache.values()
            ) / (1024 * 1024),
            "hit_rate": metrics.get_embedding_cache_hit_rate()
        }

# ============================================
# Batch Processing
# ============================================

class BatchEmbeddingProcessor:
    """Process embeddings in batches for efficiency."""
    
    def __init__(
        self,
        pipeline: StandardizedEmbeddingPipeline,
        batch_size: int = 100,
        max_concurrent: int = 5
    ):
        """Initialize batch processor.
        
        Args:
            pipeline: Embedding pipeline to use
            batch_size: Size of each batch
            max_concurrent: Maximum concurrent batches
        """
        self.pipeline = pipeline
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_documents(
        self,
        documents: List[Dict[str, Any]],
        text_field: str = "content",
        model: EmbeddingModel = EmbeddingModel.EMBEDDING_3_SMALL,
        purpose: EmbeddingPurpose = EmbeddingPurpose.INDEXING
    ) -> List[Dict[str, Any]]:
        """Process documents and add embeddings.
        
        Args:
            documents: Documents to process
            text_field: Field containing text to embed
            model: Embedding model to use
            purpose: Purpose of embeddings
            
        Returns:
            Documents with embeddings added
        """
        # Create batches
        batches = [
            documents[i:i + self.batch_size]
            for i in range(0, len(documents), self.batch_size)
        ]
        
        # Process batches concurrently
        tasks = [
            self._process_batch(batch, text_field, model, purpose)
            for batch in batches
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Flatten results
        processed_documents = []
        for batch_result in results:
            processed_documents.extend(batch_result)
        
        return processed_documents
    
    async def _process_batch(
        self,
        batch: List[Dict[str, Any]],
        text_field: str,
        model: EmbeddingModel,
        purpose: EmbeddingPurpose
    ) -> List[Dict[str, Any]]:
        """Process a single batch of documents.
        
        Args:
            batch: Batch of documents
            text_field: Field containing text
            model: Embedding model
            purpose: Purpose of embeddings
            
        Returns:
            Processed documents
        """
        async with self.semaphore:
            # Extract texts
            texts = [doc.get(text_field, "") for doc in batch]
            
            # Generate embeddings
            request = EmbeddingRequest(
                texts=texts,
                model=model,
                purpose=purpose
            )
            
            results = await self.pipeline.generate_embeddings(request)
            
            # Add embeddings to documents
            for doc, result in zip(batch, results):
                doc["embedding"] = result.embedding
                doc["embedding_metadata"] = result.metadata.to_dict()
            
            return batch

# ============================================
# Similarity Functions
# ============================================

def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """Calculate cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding
        embedding2: Second embedding
        
    Returns:
        Cosine similarity score (0-1)
    """
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))

def euclidean_distance(embedding1: List[float], embedding2: List[float]) -> float:
    """Calculate Euclidean distance between two embeddings.
    
    Args:
        embedding1: First embedding
        embedding2: Second embedding
        
    Returns:
        Euclidean distance
    """
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    return float(np.linalg.norm(vec1 - vec2))

def find_most_similar(
    query_embedding: List[float],
    embeddings: List[List[float]],
    top_k: int = 10,
    metric: str = "cosine"
) -> List[Tuple[int, float]]:
    """Find most similar embeddings to query.
    
    Args:
        query_embedding: Query embedding
        embeddings: List of embeddings to search
        top_k: Number of results to return
        metric: Similarity metric (cosine or euclidean)
        
    Returns:
        List of (index, score) tuples
    """
    scores = []
    
    for i, embedding in enumerate(embeddings):
        if metric == "cosine":
            score = cosine_similarity(query_embedding, embedding)
        else:
            score = -euclidean_distance(query_embedding, embedding)
        
        scores.append((i, score))
    
    # Sort by score (highest first)
    scores.sort(key=lambda x: x[1], reverse=True)
    
    return scores[:top_k]

# ============================================
# Export
# ============================================

__all__ = [
    "StandardizedEmbeddingPipeline",
    "BatchEmbeddingProcessor",
    "EmbeddingModel",
    "EmbeddingPurpose",
    "EmbeddingMetadata",
    "EmbeddingResult",
    "EmbeddingRequest",
    "cosine_similarity",
    "euclidean_distance",
    "find_most_similar"
]