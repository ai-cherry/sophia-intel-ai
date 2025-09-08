from typing import Any

import weaviate
import weaviate.classes as wvc

from app import settings
from app.core.ai_logger import logger
from app.core.circuit_breaker import with_circuit_breaker
from app.memory.embed_router import (
    DIM_A,
    DIM_B,
    MODEL_A,
    MODEL_B,
    choose_model_for_chunk,
    embed_with_cache,
)


def _client():
    """Get Weaviate client instance (local/no-auth by default)."""
    try:
        # Try v4 client first
        return weaviate.connect_to_local(settings.WEAVIATE_URL)
    except:
        # Fallback to v3 client
        from weaviate import Client

        return Client(url=settings.WEAVIATE_URL)


def ensure_schema(collection: str, dim: int):
    """
    Ensure the collection exists with proper configuration.

    Args:
        collection: Collection name
        dim: Vector dimension
    """
    with _client() as client:
        try:
            # v4 client
            names = [c.name for c in client.collections.list_all()]
            if collection not in names:
                client.collections.create(
                    name=collection,
                    vectorizer_config=wvc.config.Configure.Vectorizer.none(),
                    vector_index_config=wvc.config.Configure.VectorIndex.hnsw(),
                    properties=[
                        wvc.config.Property(
                            name="path", data_type=wvc.config.DataType.TEXT
                        ),
                        wvc.config.Property(
                            name="content", data_type=wvc.config.DataType.TEXT
                        ),
                        wvc.config.Property(
                            name="lang", data_type=wvc.config.DataType.TEXT
                        ),
                        wvc.config.Property(
                            name="start_line", data_type=wvc.config.DataType.INT
                        ),
                        wvc.config.Property(
                            name="end_line", data_type=wvc.config.DataType.INT
                        ),
                        wvc.config.Property(
                            name="chunk_id", data_type=wvc.config.DataType.TEXT
                        ),
                        wvc.config.Property(
                            name="priority", data_type=wvc.config.DataType.TEXT
                        ),
                    ],
                )
        except:
            # v3 client fallback
            existing_classes = {c["class"] for c in client.schema.get()["classes"]}
            if collection not in existing_classes:
                schema = {
                    "class": collection,
                    "properties": [
                        {"name": "path", "dataType": ["text"]},
                        {"name": "content", "dataType": ["text"]},
                        {"name": "lang", "dataType": ["string"]},
                        {"name": "start_line", "dataType": ["int"]},
                        {"name": "end_line", "dataType": ["int"]},
                        {"name": "chunk_id", "dataType": ["string"]},
                        {"name": "priority", "dataType": ["string"]},
                    ],
                }
                client.schema.create_class(schema)


async def upsert_chunks_dual(ids, texts, payloads, lang=""):
    """
    Routes chunks to A or B collection based on length/priority.
    Embeds accordingly and writes to the appropriate collection.

    Args:
        ids: List of chunk IDs
        texts: List of chunk texts
        payloads: List of metadata dictionaries
        lang: Language hint for routing
    """
    # Split batches by chosen model
    A_idx, A_txt, B_idx, B_txt = [], [], [], []

    for i, t in enumerate(texts):
        pr = payloads[i].get("priority")
        m, _ = choose_model_for_chunk(t, lang=lang, priority=pr)
        if m == MODEL_A:
            A_idx.append(i)
            A_txt.append(t)
        else:
            B_idx.append(i)
            B_txt.append(t)

    with _client() as client:
        # Process Tier A chunks
        if A_txt:
            collection_a = get_config().get("WEAVIATE_COLLECTION_A", "CodeChunk_A")
            ensure_schema(collection_a, DIM_A)

            try:
                # v4 client
                colA = client.collections.get(collection_a)
                vecsA = embed_with_cache(A_txt, MODEL_A)
                with colA.batch.dynamic() as batch:
                    for k, i in enumerate(A_idx):
                        # Add content to payload for BM25
                        props = {**payloads[i], "content": texts[i]}
                        batch.add_object(
                            properties=props, vector=vecsA[k], uuid=str(ids[i])
                        )
            except:
                # v3 client fallback
                vecsA = embed_with_cache(A_txt, MODEL_A)
                with client.batch as batch:
                    for k, i in enumerate(A_idx):
                        props = {**payloads[i], "content": texts[i]}
                        batch.add_data_object(
                            props, collection_a, uuid=str(ids[i]), vector=vecsA[k]
                        )

        # Process Tier B chunks
        if B_txt:
            collection_b = get_config().get("WEAVIATE_COLLECTION_B", "CodeChunk_B")
            ensure_schema(collection_b, DIM_B)

            try:
                # v4 client
                colB = client.collections.get(collection_b)
                vecsB = embed_with_cache(B_txt, MODEL_B)
                with colB.batch.dynamic() as batch:
                    for k, i in enumerate(B_idx):
                        props = {**payloads[i], "content": texts[i]}
                        batch.add_object(
                            properties=props, vector=vecsB[k], uuid=str(ids[i])
                        )
            except:
                # v3 client fallback
                vecsB = embed_with_cache(B_txt, MODEL_B)
                with client.batch as batch:
                    for k, i in enumerate(B_idx):
                        props = {**payloads[i], "content": texts[i]}
                        batch.add_data_object(
                            props, collection_b, uuid=str(ids[i]), vector=vecsB[k]
                        )


@with_circuit_breaker("database")
async def hybrid_search_merge(query: str, k: int = 8, semantic_weight: float = 0.65):
    """
    Query both collections with vector + BM25 and merge results.
    Simple weighted score: s = w*semantic + (1-w)*bm25_norm

    Args:
        query: Search query
        k: Number of results
        semantic_weight: Weight for semantic search (0-1)

    Returns:
        Merged and ranked results
    """

    # Generate query embeddings for both tiers
    qA = embed_with_cache([query], MODEL_A)[0]
    qB = embed_with_cache([query], MODEL_B)[0]

    out = []

    with _client() as client:
        # Search Collection A
        try:
            collection_a = get_config().get("WEAVIATE_COLLECTION_A", "CodeChunk_A")

            try:
                # v4 client
                colA = client.collections.get(collection_a)

                # Vector search
                resA = colA.query.near_vector(qA, limit=k)
                for r in resA.objects:
                    out.append(
                        {
                            "collection": "A",
                            "sem": (
                                r.metadata.distance
                                if hasattr(r.metadata, "distance")
                                else 0.5
                            ),
                            "bm25": 0.0,
                            "prop": r.properties,
                        }
                    )

                # BM25 search
                try:
                    bm = colA.query.bm25(query, limit=k)
                    for r in bm.objects:
                        out.append(
                            {
                                "collection": "A",
                                "sem": 1.0,  # No semantic score for BM25
                                "bm25": 0.8,  # Fixed BM25 score
                                "prop": r.properties,
                            }
                        )
                except:
                    pass  # BM25 might not be available

            except:
                # v3 client fallback
                result = (
                    client.query.get(
                        collection_a,
                        [
                            "path",
                            "lang",
                            "start_line",
                            "end_line",
                            "chunk_id",
                            "content",
                        ],
                    )
                    .with_near_vector({"vector": qA})
                    .with_limit(k)
                    .with_additional(["certainty", "id"])
                    .do()
                )
                if "data" in result and "Get" in result["data"]:
                    for r in result["data"]["Get"].get(collection_a, []):
                        out.append(
                            {
                                "collection": "A",
                                "sem": 1.0
                                - r.get("_additional", {}).get("certainty", 0.5),
                                "bm25": 0.0,
                                "prop": r,
                            }
                        )
        except Exception as e:
            logger.info(f"Error searching collection A: {e}")

        # Search Collection B
        try:
            collection_b = get_config().get("WEAVIATE_COLLECTION_B", "CodeChunk_B")

            try:
                # v4 client
                colB = client.collections.get(collection_b)

                # Vector search
                resB = colB.query.near_vector(qB, limit=k)
                for r in resB.objects:
                    out.append(
                        {
                            "collection": "B",
                            "sem": (
                                r.metadata.distance
                                if hasattr(r.metadata, "distance")
                                else 0.5
                            ),
                            "bm25": 0.0,
                            "prop": r.properties,
                        }
                    )

                # BM25 search
                try:
                    bm = colB.query.bm25(query, limit=k)
                    for r in bm.objects:
                        out.append(
                            {
                                "collection": "B",
                                "sem": 1.0,
                                "bm25": 0.8,
                                "prop": r.properties,
                            }
                        )
                except:
                    pass

            except:
                # v3 client fallback
                result = (
                    client.query.get(
                        collection_b,
                        [
                            "path",
                            "lang",
                            "start_line",
                            "end_line",
                            "chunk_id",
                            "content",
                        ],
                    )
                    .with_near_vector({"vector": qB})
                    .with_limit(k)
                    .with_additional(["certainty", "id"])
                    .do()
                )
                if "data" in result and "Get" in result["data"]:
                    for r in result["data"]["Get"].get(collection_b, []):
                        out.append(
                            {
                                "collection": "B",
                                "sem": 1.0
                                - r.get("_additional", {}).get("certainty", 0.5),
                                "bm25": 0.0,
                                "prop": r,
                            }
                        )
        except Exception as e:
            logger.info(f"Error searching collection B: {e}")

    # Normalize and combine scores
    def norm_sem(d):
        """Convert distance to similarity (0-1)."""
        return 1.0 / (1.0 + max(0.0, d))

    # Deduplicate by chunk_id and merge scores
    seen = {}
    for o in out:
        chunk_id = o["prop"].get("chunk_id", "")
        if chunk_id:
            if chunk_id in seen:
                # Merge scores for duplicate
                existing = seen[chunk_id]
                existing["sem"] = min(existing["sem"], o["sem"])
                existing["bm25"] = max(existing["bm25"], o["bm25"])
            else:
                seen[chunk_id] = o

    # Calculate final scores
    results = list(seen.values())
    for o in results:
        o["score"] = (
            semantic_weight * norm_sem(o["sem"]) + (1.0 - semantic_weight) * o["bm25"]
        )

    # Sort by score and return top k
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:k]


# Legacy functions for backward compatibility
def get_client():
    """Legacy: Get Weaviate client instance."""
    return _client()


def ensure_schema_legacy(client):
    """Legacy: Ensure the required classes exist in Weaviate schema."""
    ensure_schema(settings.WEAVIATE_CLASS_CODE, DIM_B)
    ensure_schema(settings.WEAVIATE_CLASS_DOC, DIM_B)


@with_circuit_breaker("database")
async def search_by_vector(
    vector: list[float], class_name: str = None, limit: int = 5
) -> list[dict[str, Any]]:
    """Legacy: Search Weaviate using a vector."""
    # Use hybrid search instead
    results = await hybrid_search_merge("", k=limit)
    return [r["prop"] for r in results]
