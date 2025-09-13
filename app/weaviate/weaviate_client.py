"""
Weaviate Client Adapter (real implementation)

Provides a minimal wrapper around the official weaviate-client (v3) for common operations
used by legacy adapters: storing vectors and searching by vector. No mock behavior.
"""
import asyncio
import json
import logging
from typing import Any, Optional, List, Dict

logger = logging.getLogger(__name__)


class WeaviateClient:
    """Thin wrapper around weaviate-client (v3.x) for add/search operations."""

    def __init__(self, url: str = "http://localhost:8080", api_key: Optional[str] = None):
        try:
            import weaviate  # type: ignore
        except Exception as e:
            raise ImportError(
                "weaviate-client is not installed. Install with: pip install weaviate-client"
            ) from e
        self._weaviate_mod = weaviate
        self.url = url.rstrip("/")
        self.api_key = api_key
        # Create client
        if api_key:
            from weaviate.auth import AuthApiKey  # type: ignore
            self._client = weaviate.Client(url=self.url, auth_client_secret=AuthApiKey(api_key))
        else:
            self._client = weaviate.Client(url=self.url)
        # Connection check
        try:
            self._client.schema.get()
            logger.info(f"✅ Weaviate connected at {self.url}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Weaviate at {self.url}: {e}") from e
        # Ensure default class exists
        self._ensure_docchunk_class()

    async def connect(self) -> bool:
        # Already connected in __init__ for simplicity
        return True

    def _ensure_docchunk_class(self) -> None:
        try:
            schema = self._client.schema.get()
            classes = {c.get("class") for c in schema.get("classes", [])}
            if "DocChunk" in classes:
                # Ensure required properties exist; add missing ones
                try:
                    props = next(
                        (c.get("properties", []) for c in schema.get("classes", []) if c.get("class") == "DocChunk"),
                        [],
                    )
                    prop_names = {p.get("name") for p in props}
                    needed = [
                        ("content", ["text"]),
                        ("source_uri", ["text"]),
                        ("domain", ["text"]),
                        ("timestamp", ["date"]),
                        ("confidence", ["number"]),
                        ("metadata", ["text"]),
                        ("repo_path", ["text"]),
                        ("title", ["text"]),
                    ]
                    for name, dtype in needed:
                        if name not in prop_names:
                            body = {"name": name, "dataType": dtype}
                            self._client.schema.property.create("DocChunk", body)
                            logger.info(f"Weaviate: added missing property DocChunk.{name}")
                except Exception as e:
                    logger.debug(f"DocChunk property ensure skipped: {e}")
                return
            body = {
                "class": "DocChunk",
                "vectorizer": "none",
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "source_uri", "dataType": ["text"]},
                    {"name": "domain", "dataType": ["text"]},
                    {"name": "timestamp", "dataType": ["date"]},
                    {"name": "confidence", "dataType": ["number"]},
                    {"name": "metadata", "dataType": ["text"]},
                    {"name": "repo_path", "dataType": ["text"]},
                    {"name": "title", "dataType": ["text"]},
                ],
            }
            self._client.schema.create_class(body)
            logger.info("Weaviate: created DocChunk class")
        except Exception as e:
            # Don’t block usage if schema exists or creation races
            logger.debug(f"DocChunk class ensure skipped: {e}")

    async def store_embedding(self, embedding: List[float], text: str, metadata: Dict[str, Any]) -> None:
        # Promote common fields to first-class properties for filtering
        repo_path = metadata.get("repo_path") or metadata.get("repo") or metadata.get("file_path")
        title = metadata.get("title") or metadata.get("name")
        data_object = {
            "content": text or "",
            "source_uri": metadata.get("source_uri") or repo_path or "unknown",
            "domain": metadata.get("domain") or "shared",
            "timestamp": metadata.get("timestamp"),
            "confidence": float(metadata.get("confidence", 1.0)),
            "metadata": json.dumps(metadata),
            "repo_path": repo_path or "",
            "title": title or "",
        }
        # Use non-batch create for single object, offloaded to thread to avoid blocking
        def _create():
            self._client.data_object.create(
                data_object=data_object,
                class_name="DocChunk",
                vector=embedding,
            )
        try:
            await asyncio.to_thread(_create)
        except Exception as e:
            raise RuntimeError(f"Failed to store embedding in Weaviate: {e}") from e

    async def search_embeddings(
        self, query_embedding: List[float], top_k: int = 5, repo_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            def _do_query():
                q = (
                    self._client.query.get(
                        "DocChunk",
                        ["content", "source_uri", "domain", "metadata", "repo_path", "title"],
                    )
                    .with_near_vector({"vector": query_embedding})
                    .with_additional(["certainty", "id"])
                    .with_limit(top_k)
                )
                # NOTE: We’re not applying a repo_path where filter here because metadata can be text.
                return q.do() or {}
            res = await asyncio.to_thread(_do_query)
            items = (res.get("data", {}).get("Get", {}).get("DocChunk") or [])
            out = []
            for it in items:
                md: Dict[str, Any] = {}
                try:
                    md = json.loads(it.get("metadata") or "{}")
                except Exception:
                    md = {"raw": it.get("metadata")}
                add = it.get("_additional") or {}
                certainty = add.get("certainty")
                score = float(certainty) if certainty is not None else 0.0
                out.append(
                    {
                        "id": it.get("source_uri"),
                        "text": it.get("content"),
                        "score": score,
                        "metadata": md,
                    }
                )
            return out
        except Exception as e:
            raise RuntimeError(f"Weaviate vector search failed: {e}") from e

    async def close(self) -> None:
        try:
            # v3 client has no explicit close; rely on GC.
            return None
        except Exception:
            return None


async def get_weaviate_client(url: str = "http://localhost:8080", api_key: Optional[str] = None) -> WeaviateClient:
        client = WeaviateClient(url=url, api_key=api_key)
        await client.connect()
        return client
