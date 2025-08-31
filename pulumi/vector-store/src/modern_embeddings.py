"""
Modern Three-Tier Embedding System for Sophia Intel AI - Vector Store Service
Consolidates dual_tier_embeddings.py + modernbert_embeddings.py + embedding_pipeline.py
Implements 2025 SOTA models with intelligent routing and standardized pipeline.
"""

import os
import json
import hashlib
import sqlite3
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
import tiktoken

# Pydantic imports for standardization
from pydantic import BaseModel, Field

# Gateway integration
from app.portkey_config import gateway

logger = logging.getLogger(__name__)


class EmbeddingTier(Enum):
    """Modern three-tier embedding selection."""
    TIER_S = "tier_s"  # Superior: 2025 SOTA models (Voyage-3, ModernBERT)
    TIER_A = "tier_a"  # Advanced: Multi-modal, multilingual
    TIER_B = "tier_b"  # Basic: Fast, efficient for development


class EmbeddingPurpose(Enum):
    """Purpose of embedding generation."""
    SEARCH = "search"
    CLUSTERING = "clustering"
    CLASSIFICATION = "classification"
    SIMILARITY = "similarity"
    INDEXING = "indexing"


@dataclass
class ModernEmbeddingConfig:
    """Configuration for modern three-tier embedding system."""
    
    # Tier S: Superior Quality (2025 SOTA)
    tier_s_model: str = "voyage-3-large"
    tier_s_dim: int = 1024
    tier_s_max_tokens: int = 8192
    tier_s_batch_size: int = 16
    
    # Tier A: Advanced Multi-modal
    tier_a_model: str = "cohere/embed-multilingual-v3.0"
    tier_a_dim: int = 768
    tier_a_max_tokens: int = 2048
    tier_a_batch_size: int = 32
    
    # Tier B: Fast Standard
    tier_b_model: str = "BAAI/bge-base-en-v1.5"
    tier_b_dim: int = 768
    tier_b_max_tokens: int = 512
    tier_b_batch_size: int = 128
    
    # Intelligent Routing Configuration
    token_threshold_s: int = 4096  # Use Tier-S above this
    token_threshold_a: int = 1024  # Use Tier-A above this
    
    # Quality-based routing keywords
    quality_keywords: List[str] = field(default_factory=lambda: [
        "production", "critical", "security", "financial", "compliance",
        "legal", "architecture", "performance", "safety"
    ])
    
    # Speed-based routing keywords  
    speed_keywords: List[str] = field(default_factory=lambda: [
        "test", "debug", "quick", "draft", "experimental", "prototype"
    ])
    
    # Language-based routing priorities
    language_priorities: Dict[str, EmbeddingTier] = field(default_factory=lambda: {
        "python": EmbeddingTier.TIER_S,
        "rust": EmbeddingTier.TIER_S,
        "go": EmbeddingTier.TIER_S,
        "typescript": EmbeddingTier.TIER_A,
        "javascript": EmbeddingTier.TIER_A,
        "markdown": EmbeddingTier.TIER_B,
        "json": EmbeddingTier.TIER_B
    })
    
    # Performance settings
    cache_db_path: str = "data/modern_embedding_cache.db"
    enable_quantization: bool = True
    max_cache_size: int = 100000
    cache_ttl_hours: int = 24


@dataclass
class EmbeddingMetadata:
    """Standardized metadata for embeddings."""
    model: str
    tier: str
    dimensions: int
    purpose: str
    source_hash: str
    token_count: int
    generation_time_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    quality_score: float = 1.0
    cache_hit: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass 
class EmbeddingResult:
    """Result of embedding generation with metadata."""
    embedding: List[float]
    metadata: EmbeddingMetadata
    text: str
    text_hash: str
    
    @property
    def vector(self) -> np.ndarray:
        """Get embedding as numpy array."""
        return np.array(self.embedding)
    
    @property
    def normalized_vector(self) -> np.ndarray:
        """Get normalized embedding vector."""
        vec = self.vector
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "embedding": self.embedding,
            "metadata": self.metadata.to_dict(),
            "text": self.text,
            "text_hash": self.text_hash
        }


class EmbeddingRequest(BaseModel):
    """Standardized request for embedding generation."""
    texts: List[str]
    purpose: EmbeddingPurpose = EmbeddingPurpose.SEARCH
    priority: str = "balanced"  # quality, balanced, speed
    force_tier: Optional[EmbeddingTier] = None
    language: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModernEmbeddingCache:
    """Advanced caching system with statistics and optimization."""
    
    def __init__(self, config: ModernEmbeddingConfig):
        self.config = config
        self.db_path = config.cache_db_path
        self._initialize_cache()
    
    def _initialize_cache(self):
        """Initialize optimized SQLite cache."""
        Path(os.path.dirname(self.db_path)).mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Main cache table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embedding_cache (
                    text_hash TEXT,
                    model TEXT,
                    tier TEXT,
                    purpose TEXT,
                    embedding TEXT,
                    dimension INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1,
                    quality_score REAL DEFAULT 1.0,
                    token_count INTEGER DEFAULT 0,
                    PRIMARY KEY (text_hash, model, purpose)
                )
            """)
            
            # Performance indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_model_tier ON embedding_cache(model, tier)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_accessed_at ON embedding_cache(accessed_at DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_access_count ON embedding_cache(access_count DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_quality_score ON embedding_cache(quality_score DESC)")
            
            # Statistics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_statistics (
                    model TEXT,
                    tier TEXT,
                    total_embeddings INTEGER DEFAULT 0,
                    cache_hits INTEGER DEFAULT 0,
                    cache_misses INTEGER DEFAULT 0,
                    avg_generation_time_ms REAL DEFAULT 0,
                    avg_quality_score REAL DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (model, tier)
                )
            """)
            
            conn.commit()
    
    def get_cached(
        self, 
        text_hash: str, 
        model: str, 
        purpose: str,
        tier: EmbeddingTier
    ) -> Optional[Tuple[List[float], EmbeddingMetadata]]:
        """Get cached embedding with metadata."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT embedding, dimension, quality_score, token_count, created_at
                FROM embedding_cache
                WHERE text_hash = ? AND model = ? AND purpose = ?
            """, (text_hash, model, purpose))
            
            row = cursor.fetchone()
            if row:
                # Update access statistics
                conn.execute("""
                    UPDATE embedding_cache
                    SET access_count = access_count + 1,
                        accessed_at = CURRENT_TIMESTAMP
                    WHERE text_hash = ? AND model = ? AND purpose = ?
                """, (text_hash, model, purpose))
                
                # Update cache hit statistics
                conn.execute("""
                    INSERT OR IGNORE INTO cache_statistics (model, tier, cache_hits)
                    VALUES (?, ?, 1)
                    ON CONFLICT(model, tier) DO UPDATE SET
                        cache_hits = cache_hits + 1,
                        last_updated = CURRENT_TIMESTAMP
                """, (model, tier.value))
                
                conn.commit()
                
                # Create metadata
                metadata = EmbeddingMetadata(
                    model=model,
                    tier=tier.value,
                    dimensions=row[1],
                    purpose=purpose,
                    source_hash=text_hash,
                    token_count=row[3],
                    generation_time_ms=0,  # Cached, no generation time
                    quality_score=row[2],
                    cache_hit=True,
                    timestamp=datetime.fromisoformat(row[4])
                )
                
                return json.loads(row[0]), metadata
        
        # Record cache miss
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO cache_statistics (model, tier, cache_misses)
                VALUES (?, ?, 1)
                ON CONFLICT(model, tier) DO UPDATE SET
                    cache_misses = cache_misses + 1,
                    last_updated = CURRENT_TIMESTAMP
            """, (model, tier.value))
            conn.commit()
        
        return None
    
    def cache_embedding(
        self,
        text_hash: str,
        model: str,
        purpose: str,
        tier: EmbeddingTier,
        embedding: List[float],
        metadata: EmbeddingMetadata
    ):
        """Cache embedding with comprehensive metadata."""
        with sqlite3.connect(self.db_path) as conn:
            # Check cache size and evict if necessary
            cursor = conn.execute("SELECT COUNT(*) FROM embedding_cache")
            cache_size = cursor.fetchone()[0]
            
            if cache_size >= self.config.max_cache_size:
                # Evict least recently accessed entries
                conn.execute("""
                    DELETE FROM embedding_cache
                    WHERE rowid IN (
                        SELECT rowid FROM embedding_cache
                        ORDER BY accessed_at ASC
                        LIMIT ?
                    )
                """, (self.config.max_cache_size // 10,))  # Evict 10%
            
            # Insert new cache entry
            conn.execute("""
                INSERT OR REPLACE INTO embedding_cache
                (text_hash, model, tier, purpose, embedding, dimension, quality_score, token_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                text_hash, model, tier.value, purpose,
                json.dumps(embedding), len(embedding),
                metadata.quality_score, metadata.token_count
            ))
            
            # Update statistics
            conn.execute("""
                INSERT OR IGNORE INTO cache_statistics (model, tier, total_embeddings)
                VALUES (?, ?, 1)
                ON CONFLICT(model, tier) DO UPDATE SET
                    total_embeddings = total_embeddings + 1,
                    avg_generation_time_ms = (avg_generation_time_ms + ?) / 2,
                    avg_quality_score = (avg_quality_score + ?) / 2,
                    last_updated = CURRENT_TIMESTAMP
            """, (model, tier.value, metadata.generation_time_ms, metadata.quality_score))
            
            conn.commit()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        with sqlite3.connect(self.db_path) as conn:
            # Overall statistics
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    AVG(quality_score) as avg_quality,
                    AVG(access_count) as avg_access_count,
                    SUM(CASE WHEN accessed_at > datetime('now', '-1 hour') THEN 1 ELSE 0 END) as recent_hits
                FROM embedding_cache
            """)
            overall_stats = dict(zip([col[0] for col in cursor.description], cursor.fetchone()))
            
            # Per-model statistics
            cursor = conn.execute("""
                SELECT model, tier, total_embeddings, cache_hits, cache_misses,
                       avg_generation_time_ms, avg_quality_score
                FROM cache_statistics
                ORDER BY total_embeddings DESC
            """)
            
            model_stats = []
            total_hits = total_requests = 0
            
            for row in cursor.fetchall():
                hits, misses = row[3], row[4]
                requests = hits + misses
                hit_rate = hits / requests if requests > 0 else 0
                
                model_stats.append({
                    "model": row[0],
                    "tier": row[1],
                    "total_embeddings": row[2],
                    "cache_hit_rate": hit_rate,
                    "avg_generation_time_ms": row[5],
                    "avg_quality_score": row[6]
                })
                
                total_hits += hits
                total_requests += requests
            
            return {
                "overall": overall_stats,
                "global_hit_rate": total_hits / total_requests if total_requests > 0 else 0,
                "model_statistics": model_stats,
                "cache_size_mb": os.path.getsize(self.db_path) / (1024 * 1024) if os.path.exists(self.db_path) else 0
            }


class IntelligentEmbeddingRouter:
    """Advanced routing logic for three-tier embedding selection."""
    
    def __init__(self, config: ModernEmbeddingConfig):
        self.config = config
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def select_tier(
        self,
        text: str,
        priority: str = "balanced",
        language: Optional[str] = None,
        purpose: EmbeddingPurpose = EmbeddingPurpose.SEARCH,
        force_tier: Optional[EmbeddingTier] = None
    ) -> EmbeddingTier:
        """Intelligently select embedding tier based on multiple factors."""
        
        # Force tier if specified
        if force_tier:
            return force_tier
        
        # Priority-based routing
        if priority == "quality":
            return EmbeddingTier.TIER_S
        elif priority == "speed":
            return EmbeddingTier.TIER_B
        
        # Keyword-based routing
        text_lower = text.lower()
        
        # Check for quality-demanding keywords
        for keyword in self.config.quality_keywords:
            if keyword in text_lower:
                return EmbeddingTier.TIER_S
        
        # Check for speed-optimized keywords
        for keyword in self.config.speed_keywords:
            if keyword in text_lower:
                return EmbeddingTier.TIER_B
        
        # Language-based routing
        if language and language.lower() in self.config.language_priorities:
            return self.config.language_priorities[language.lower()]
        
        # Token count-based routing
        token_count = len(self.tokenizer.encode(text))
        if token_count > self.config.token_threshold_s:
            return EmbeddingTier.TIER_S
        elif token_count > self.config.token_threshold_a:
            return EmbeddingTier.TIER_A
        
        # Purpose-based routing
        if purpose in [EmbeddingPurpose.CLASSIFICATION, EmbeddingPurpose.CLUSTERING]:
            return EmbeddingTier.TIER_A
        
        # Default to balanced tier
        return EmbeddingTier.TIER_A
    
    def batch_route(
        self,
        texts: List[str],
        priorities: Optional[List[str]] = None,
        languages: Optional[List[str]] = None,
        purposes: Optional[List[EmbeddingPurpose]] = None
    ) -> Dict[EmbeddingTier, List[int]]:
        """Route batch of texts to appropriate tiers."""
        tier_indices = {
            EmbeddingTier.TIER_S: [],
            EmbeddingTier.TIER_A: [],
            EmbeddingTier.TIER_B: []
        }
        
        for i, text in enumerate(texts):
            priority = priorities[i] if priorities else "balanced"
            language = languages[i] if languages else None
            purpose = purposes[i] if purposes else EmbeddingPurpose.SEARCH
            
            tier = self.select_tier(text, priority, language, purpose)
            tier_indices[tier].append(i)
        
        return tier_indices


class ModernThreeTierEmbedder:
    """
    State-of-the-art three-tier embedding system.
    Combines the best features from all previous implementations:
    - Intelligent routing (from dual_tier_embeddings.py)
    - 2025 SOTA models (from modernbert_embeddings.py)
    - Standardized pipeline (from embedding_pipeline.py)
    """
    
    def __init__(self, config: Optional[ModernEmbeddingConfig] = None):
        self.config = config or ModernEmbeddingConfig()
        self.router = IntelligentEmbeddingRouter(self.config)
        self.cache = ModernEmbeddingCache(self.config)
    
    async def embed_single(
        self,
        text: str,
        purpose: EmbeddingPurpose = EmbeddingPurpose.SEARCH,
        priority: str = "balanced",
        language: Optional[str] = None,
        force_tier: Optional[EmbeddingTier] = None
    ) -> EmbeddingResult:
        """Generate single embedding with intelligent tier selection."""
        
        start_time = datetime.utcnow()
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        # Select optimal tier
        tier = self.router.select_tier(text, priority, language, purpose, force_tier)
        
        # Get model configuration for selected tier
        model, expected_dim, batch_size = self._get_tier_config(tier)
        
        # Check cache first
        cached_result = self.cache.get_cached(text_hash, model, purpose.value, tier)
        if cached_result:
            embedding, metadata = cached_result
            return EmbeddingResult(
                embedding=embedding,
                metadata=metadata,
                text=text,
                text_hash=text_hash
            )
        
        # Generate embedding
        try:
            embedding = await self._generate_embedding(text, model, tier)
        except Exception as e:
            logger.error(f"Embedding generation failed for {model}: {e}")
            # Fallback to lower tier
            if tier != EmbeddingTier.TIER_B:
                return await self.embed_single(
                    text, purpose, priority, language, EmbeddingTier.TIER_B
                )
            raise
        
        # Create metadata
        generation_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        token_count = len(self.router.tokenizer.encode(text))
        
        metadata = EmbeddingMetadata(
            model=model,
            tier=tier.value,
            dimensions=len(embedding),
            purpose=purpose.value,
            source_hash=text_hash[:16],
            token_count=token_count,
            generation_time_ms=generation_time_ms,
            quality_score=self._calculate_quality_score(tier, token_count)
        )
        
        # Cache the result
        self.cache.cache_embedding(text_hash, model, purpose.value, tier, embedding, metadata)
        
        return EmbeddingResult(
            embedding=embedding,
            metadata=metadata,
            text=text,
            text_hash=text_hash
        )
    
    async def embed_batch(self, request: EmbeddingRequest) -> List[EmbeddingResult]:
        """Generate embeddings for batch of texts with intelligent routing."""
        
        # Route texts to appropriate tiers
        priorities = [request.priority] * len(request.texts)
        languages = [request.language] * len(request.texts)
        purposes = [request.purpose] * len(request.texts)
        
        tier_indices = self.router.batch_route(request.texts, priorities, languages, purposes)
        
        # Process each tier concurrently
        tasks = []
        for tier, indices in tier_indices.items():
            if indices:
                tier_texts = [request.texts[i] for i in indices]
                task = self._process_tier_batch(tier, tier_texts, request.purpose, request.priority, request.language)
                tasks.append((tier, indices, task))
        
        # Execute all tier processing concurrently
        results = [None] * len(request.texts)
        
        for tier, indices, task in tasks:
            tier_results = await task
            for i, result in zip(indices, tier_results):
                results[i] = result
        
        return results
    
    async def _process_tier_batch(
        self,
        tier: EmbeddingTier,
        texts: List[str],
        purpose: EmbeddingPurpose,
        priority: str,
        language: Optional[str]
    ) -> List[EmbeddingResult]:
        """Process a batch of texts for a specific tier."""
        model, expected_dim, batch_size = self._get_tier_config(tier)
        
        # Process in chunks according to tier batch size
        results = []
        for i in range(0, len(texts), batch_size):
            chunk = texts[i:i + batch_size]
            chunk_results = await asyncio.gather(*[
                self.embed_single(text, purpose, priority, language, tier)
                for text in chunk
            ])
            results.extend(chunk_results)
        
        return results
    
    def _get_tier_config(self, tier: EmbeddingTier) -> Tuple[str, int, int]:
        """Get model configuration for tier."""
        if tier == EmbeddingTier.TIER_S:
            return self.config.tier_s_model, self.config.tier_s_dim, self.config.tier_s_batch_size
        elif tier == EmbeddingTier.TIER_A:
            return self.config.tier_a_model, self.config.tier_a_dim, self.config.tier_a_batch_size
        else:
            return self.config.tier_b_model, self.config.tier_b_dim, self.config.tier_b_batch_size
    
    async def _generate_embedding(self, text: str, model: str, tier: EmbeddingTier) -> List[float]:
        """Generate embedding using Portkey gateway."""
        try:
            # Use gateway for model access with proper error handling
            response = await gateway.embeddings.create(
                model=model,
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            
            # Apply quantization for speed tier if enabled
            if self.config.enable_quantization and tier == EmbeddingTier.TIER_B:
                embedding = self._quantize_embedding(embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding with {model}: {e}")
            raise
    
    def _quantize_embedding(self, embedding: List[float]) -> List[float]:
        """Apply 8-bit quantization for faster operations."""
        vec = np.array(embedding)
        
        # Normalize to unit vector
        vec_norm = vec / np.linalg.norm(vec)
        
        # Quantize to 8-bit
        vec_quantized = np.round(vec_norm * 127).astype(np.int8)
        
        # Dequantize back to float
        vec_dequantized = vec_quantized.astype(np.float32) / 127
        
        return vec_dequantized.tolist()
    
    def _calculate_quality_score(self, tier: EmbeddingTier, token_count: int) -> float:
        """Calculate quality score based on tier and context."""
        base_scores = {
            EmbeddingTier.TIER_S: 0.95,
            EmbeddingTier.TIER_A: 0.85,
            EmbeddingTier.TIER_B: 0.75
        }
        
        base_score = base_scores[tier]
        
        # Adjust for token count (longer texts might be more complex)
        if token_count > 2000:
            base_score += 0.05
        elif token_count < 50:
            base_score -= 0.05
        
        return min(1.0, max(0.0, base_score))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive embedding statistics."""
        return {
            "cache_statistics": self.cache.get_statistics(),
            "tier_configuration": {
                "tier_s": {
                    "model": self.config.tier_s_model,
                    "dimensions": self.config.tier_s_dim,
                    "max_tokens": self.config.tier_s_max_tokens,
                    "batch_size": self.config.tier_s_batch_size
                },
                "tier_a": {
                    "model": self.config.tier_a_model,
                    "dimensions": self.config.tier_a_dim,
                    "max_tokens": self.config.tier_a_max_tokens,
                    "batch_size": self.config.tier_a_batch_size
                },
                "tier_b": {
                    "model": self.config.tier_b_model,
                    "dimensions": self.config.tier_b_dim,
                    "max_tokens": self.config.tier_b_max_tokens,
                    "batch_size": self.config.tier_b_batch_size
                }
            },
            "routing_configuration": {
                "token_threshold_s": self.config.token_threshold_s,
                "token_threshold_a": self.config.token_threshold_a,
                "quality_keywords": self.config.quality_keywords,
                "speed_keywords": self.config.speed_keywords,
                "language_priorities": {k: v.value for k, v in self.config.language_priorities.items()}
            }
        }


# Utility functions for similarity calculations
def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """Calculate cosine similarity between embeddings."""
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dot_product / (norm1 * norm2))


def euclidean_distance(embedding1: List[float], embedding2: List[float]) -> float:
    """Calculate Euclidean distance between embeddings."""
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    return float(np.linalg.norm(vec1 - vec2))


# Global instance for the service
modern_embedder = None

async def get_modern_embedder() -> ModernThreeTierEmbedder:
    """Get the global modern embedder instance."""
    global modern_embedder
    if modern_embedder is None:
        modern_embedder = ModernThreeTierEmbedder()
    return modern_embedder