"""
Dual-Tier Embedding System with Intelligent Routing.
Optimizes for both quality (Tier-A) and speed (Tier-B).
"""

import os
import json
import hashlib
import sqlite3
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import tiktoken
from pathlib import Path

from app.portkey_config import gateway, Role

# ============================================
# Configuration
# ============================================

class EmbeddingTier(Enum):
    """Embedding tier selection."""
    TIER_A = "tier_a"  # High-quality, long-context
    TIER_B = "tier_b"  # Fast, standard

@dataclass
class EmbeddingConfig:
    """Configuration for dual-tier embeddings."""
    
    # Tier A: High-quality, long-context
    tier_a_model: str = "togethercomputer/m2-bert-80M-32k-retrieval"
    tier_a_dim: int = 768
    tier_a_max_tokens: int = 32768
    tier_a_batch_size: int = 10
    
    # Tier B: Fast, standard
    tier_b_model: str = "BAAI/bge-large-en-v1.5"
    tier_b_dim: int = 1024
    tier_b_max_tokens: int = 512
    tier_b_batch_size: int = 100
    
    # Routing thresholds
    token_threshold: int = 2048  # Use Tier-A above this
    priority_keywords: List[str] = None
    language_priorities: Dict[str, EmbeddingTier] = None
    
    # Cache settings
    cache_db_path: str = "tmp/embedding_cache.db"
    cache_ttl_days: int = 30
    
    def __post_init__(self):
        if self.priority_keywords is None:
            self.priority_keywords = [
                "critical", "security", "authentication", "payment",
                "privacy", "compliance", "legal", "architecture"
            ]
        
        if self.language_priorities is None:
            self.language_priorities = {
                "python": EmbeddingTier.TIER_A,
                "rust": EmbeddingTier.TIER_A,
                "go": EmbeddingTier.TIER_A,
                "javascript": EmbeddingTier.TIER_B,
                "typescript": EmbeddingTier.TIER_B,
                "markdown": EmbeddingTier.TIER_B
            }

# ============================================
# Embedding Cache
# ============================================

class EmbeddingCache:
    """
    SQLite-based embedding cache with SHA hashing.
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """Ensure cache database exists."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embedding_cache (
                    text_hash TEXT,
                    model TEXT,
                    embedding TEXT,
                    dimension INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP,
                    PRIMARY KEY (text_hash, model)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_text_hash 
                ON embedding_cache(text_hash)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_model 
                ON embedding_cache(model)
            """)
            
            conn.commit()
    
    def get_cached(
        self,
        text: str,
        model: str
    ) -> Optional[List[float]]:
        """
        Get cached embedding if exists.
        
        Args:
            text: Text that was embedded
            model: Model used for embedding
        
        Returns:
            Cached embedding vector or None
        """
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT embedding FROM embedding_cache
                WHERE text_hash = ? AND model = ?
            """, (text_hash, model))
            
            row = cursor.fetchone()
            if row:
                # Update access stats
                conn.execute("""
                    UPDATE embedding_cache
                    SET access_count = access_count + 1,
                        last_accessed = CURRENT_TIMESTAMP
                    WHERE text_hash = ? AND model = ?
                """, (text_hash, model))
                conn.commit()
                
                return json.loads(row[0])
        
        return None
    
    def cache_embedding(
        self,
        text: str,
        model: str,
        embedding: List[float]
    ):
        """
        Cache an embedding.
        
        Args:
            text: Original text
            model: Model used
            embedding: Embedding vector
        """
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO embedding_cache
                (text_hash, model, embedding, dimension)
                VALUES (?, ?, ?, ?)
            """, (
                text_hash,
                model,
                json.dumps(embedding),
                len(embedding)
            ))
            conn.commit()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM embedding_cache"
            ).fetchone()[0]
            
            by_model = conn.execute("""
                SELECT model, COUNT(*), AVG(access_count)
                FROM embedding_cache
                GROUP BY model
            """).fetchall()
            
            return {
                "total_cached": total,
                "by_model": [
                    {
                        "model": row[0],
                        "count": row[1],
                        "avg_access": row[2]
                    }
                    for row in by_model
                ]
            }

# ============================================
# Routing Logic
# ============================================

class EmbeddingRouter:
    """
    Intelligent routing between embedding tiers.
    """
    
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def select_tier(
        self,
        text: str,
        language: Optional[str] = None,
        priority: Optional[str] = None,
        force_tier: Optional[EmbeddingTier] = None
    ) -> EmbeddingTier:
        """
        Select appropriate embedding tier.
        
        Args:
            text: Text to embed
            language: Programming language (if applicable)
            priority: Priority level
            force_tier: Force specific tier
        
        Returns:
            Selected embedding tier
        """
        # Force tier if specified
        if force_tier:
            return force_tier
        
        # Check priority keywords
        text_lower = text.lower()
        for keyword in self.config.priority_keywords:
            if keyword in text_lower:
                return EmbeddingTier.TIER_A
        
        # Check language priority
        if language and language.lower() in self.config.language_priorities:
            return self.config.language_priorities[language.lower()]
        
        # Check token count
        token_count = len(self.tokenizer.encode(text))
        if token_count > self.config.token_threshold:
            return EmbeddingTier.TIER_A
        
        # High priority always gets Tier-A
        if priority == "high":
            return EmbeddingTier.TIER_A
        
        # Default to Tier-B for speed
        return EmbeddingTier.TIER_B
    
    def batch_route(
        self,
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[EmbeddingTier, List[int]]:
        """
        Route batch of texts to appropriate tiers.
        
        Args:
            texts: List of texts to embed
            metadata: Optional metadata for each text
        
        Returns:
            Mapping of tier to text indices
        """
        tier_indices = {
            EmbeddingTier.TIER_A: [],
            EmbeddingTier.TIER_B: []
        }
        
        for i, text in enumerate(texts):
            meta = metadata[i] if metadata else {}
            tier = self.select_tier(
                text,
                language=meta.get("language"),
                priority=meta.get("priority")
            )
            tier_indices[tier].append(i)
        
        return tier_indices

# ============================================
# Dual-Tier Embedding Engine
# ============================================

class DualTierEmbedder:
    """
    Dual-tier embedding engine with caching and routing.
    """
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
        self.router = EmbeddingRouter(self.config)
        self.cache = EmbeddingCache(self.config.cache_db_path)
    
    async def embed_single(
        self,
        text: str,
        language: Optional[str] = None,
        priority: Optional[str] = None,
        force_tier: Optional[EmbeddingTier] = None,
        use_cache: bool = True
    ) -> Tuple[List[float], EmbeddingTier]:
        """
        Embed single text with tier selection.
        
        Args:
            text: Text to embed
            language: Programming language
            priority: Priority level
            force_tier: Force specific tier
            use_cache: Use cache if available
        
        Returns:
            Tuple of (embedding vector, tier used)
        """
        # Select tier
        tier = self.router.select_tier(text, language, priority, force_tier)
        
        # Get model based on tier
        if tier == EmbeddingTier.TIER_A:
            model = self.config.tier_a_model
        else:
            model = self.config.tier_b_model
        
        # Check cache
        if use_cache:
            cached = self.cache.get_cached(text, model)
            if cached:
                return cached, tier
        
        # Generate embedding
        embeddings = await gateway.aembed([text], model=model)
        embedding = embeddings[0]
        
        # Cache result
        if use_cache:
            self.cache.cache_embedding(text, model, embedding)
        
        return embedding, tier
    
    async def embed_batch(
        self,
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        use_cache: bool = True
    ) -> List[Tuple[List[float], EmbeddingTier]]:
        """
        Embed batch of texts with intelligent routing.
        
        Args:
            texts: List of texts to embed
            metadata: Optional metadata for each text
            use_cache: Use cache if available
        
        Returns:
            List of (embedding vector, tier used) tuples
        """
        # Route texts to tiers
        tier_indices = self.router.batch_route(texts, metadata)
        
        # Prepare results
        results = [None] * len(texts)
        
        # Process Tier-A texts
        if tier_indices[EmbeddingTier.TIER_A]:
            tier_a_texts = []
            tier_a_positions = []
            
            for idx in tier_indices[EmbeddingTier.TIER_A]:
                # Check cache
                if use_cache:
                    cached = self.cache.get_cached(
                        texts[idx],
                        self.config.tier_a_model
                    )
                    if cached:
                        results[idx] = (cached, EmbeddingTier.TIER_A)
                        continue
                
                tier_a_texts.append(texts[idx])
                tier_a_positions.append(idx)
            
            # Batch embed uncached texts
            if tier_a_texts:
                embeddings = await gateway.aembed(
                    tier_a_texts,
                    model=self.config.tier_a_model,
                    batch_size=self.config.tier_a_batch_size
                )
                
                for i, (text, embedding) in enumerate(zip(tier_a_texts, embeddings)):
                    idx = tier_a_positions[i]
                    results[idx] = (embedding, EmbeddingTier.TIER_A)
                    
                    # Cache result
                    if use_cache:
                        self.cache.cache_embedding(
                            text,
                            self.config.tier_a_model,
                            embedding
                        )
        
        # Process Tier-B texts
        if tier_indices[EmbeddingTier.TIER_B]:
            tier_b_texts = []
            tier_b_positions = []
            
            for idx in tier_indices[EmbeddingTier.TIER_B]:
                # Check cache
                if use_cache:
                    cached = self.cache.get_cached(
                        texts[idx],
                        self.config.tier_b_model
                    )
                    if cached:
                        results[idx] = (cached, EmbeddingTier.TIER_B)
                        continue
                
                tier_b_texts.append(texts[idx])
                tier_b_positions.append(idx)
            
            # Batch embed uncached texts
            if tier_b_texts:
                embeddings = await gateway.aembed(
                    tier_b_texts,
                    model=self.config.tier_b_model,
                    batch_size=self.config.tier_b_batch_size
                )
                
                for i, (text, embedding) in enumerate(zip(tier_b_texts, embeddings)):
                    idx = tier_b_positions[i]
                    results[idx] = (embedding, EmbeddingTier.TIER_B)
                    
                    # Cache result
                    if use_cache:
                        self.cache.cache_embedding(
                            text,
                            self.config.tier_b_model,
                            embedding
                        )
        
        return results
    
    def get_dimension(self, tier: EmbeddingTier) -> int:
        """Get embedding dimension for tier."""
        if tier == EmbeddingTier.TIER_A:
            return self.config.tier_a_dim
        else:
            return self.config.tier_b_dim
    
    def get_stats(self) -> Dict[str, Any]:
        """Get embedding statistics."""
        cache_stats = self.cache.get_stats()
        
        return {
            "config": {
                "tier_a_model": self.config.tier_a_model,
                "tier_a_dim": self.config.tier_a_dim,
                "tier_b_model": self.config.tier_b_model,
                "tier_b_dim": self.config.tier_b_dim,
                "token_threshold": self.config.token_threshold
            },
            "cache": cache_stats
        }

# ============================================
# Embedding Utilities
# ============================================

def normalize_embedding(embedding: List[float]) -> List[float]:
    """Normalize embedding vector to unit length."""
    import math
    norm = math.sqrt(sum(x * x for x in embedding))
    if norm > 0:
        return [x / norm for x in embedding]
    return embedding

def cosine_similarity(
    embedding1: List[float],
    embedding2: List[float]
) -> float:
    """Calculate cosine similarity between embeddings."""
    import math
    
    # Normalize vectors
    norm1 = normalize_embedding(embedding1)
    norm2 = normalize_embedding(embedding2)
    
    # Dot product
    dot_product = sum(a * b for a, b in zip(norm1, norm2))
    
    return dot_product

def pad_or_truncate_embedding(
    embedding: List[float],
    target_dim: int
) -> List[float]:
    """Pad or truncate embedding to target dimension."""
    if len(embedding) == target_dim:
        return embedding
    elif len(embedding) < target_dim:
        # Pad with zeros
        return embedding + [0.0] * (target_dim - len(embedding))
    else:
        # Truncate
        return embedding[:target_dim]

# ============================================
# CLI Interface
# ============================================

async def main():
    """CLI for testing dual-tier embeddings."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dual-tier embedding system")
    parser.add_argument("--text", help="Text to embed")
    parser.add_argument("--file", help="File to embed")
    parser.add_argument("--language", help="Programming language")
    parser.add_argument("--priority", choices=["low", "medium", "high"])
    parser.add_argument("--tier", choices=["tier_a", "tier_b"])
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    
    args = parser.parse_args()
    
    embedder = DualTierEmbedder()
    
    if args.stats:
        stats = embedder.get_stats()
        print("\n📊 Embedding Statistics:")
        print(f"  Tier-A: {stats['config']['tier_a_model']} ({stats['config']['tier_a_dim']}D)")
        print(f"  Tier-B: {stats['config']['tier_b_model']} ({stats['config']['tier_b_dim']}D)")
        print(f"  Cache: {stats['cache']['total_cached']} entries")
        for model_stat in stats['cache']['by_model']:
            print(f"    {model_stat['model']}: {model_stat['count']} entries")
    
    elif args.text or args.file:
        # Get text
        if args.file:
            with open(args.file, 'r') as f:
                text = f.read()
        else:
            text = args.text
        
        # Select tier
        force_tier = None
        if args.tier:
            force_tier = EmbeddingTier(args.tier)
        
        # Embed
        embedding, tier = await embedder.embed_single(
            text,
            language=args.language,
            priority=args.priority,
            force_tier=force_tier
        )
        
        print(f"\n✅ Embedded using {tier.value}:")
        print(f"  Dimension: {len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")
        print(f"  Norm: {sum(x*x for x in embedding)**0.5:.4f}")

if __name__ == "__main__":
    asyncio.run(main())