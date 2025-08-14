import os, json
from functools import lru_cache
from integrations.mcp_tools import mcp_semantic_search

from haystack import Pipeline
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.retrievers import DenseRetriever

@lru_cache(maxsize=1)
def _store():
    return QdrantDocumentStore(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        collection_name=os.getenv("QDRANT_COLLECTION", "repo_docs"),
        recreate_index=False
    )

@lru_cache(maxsize=1)
def _pipe():
    pipe = Pipeline()
    embed = SentenceTransformersTextEmbedder(
        model=os.getenv("EMBEDDER", "sentence-transformers/all-MiniLM-L6-v2")
    )
    retr = DenseRetriever(document_store=_store(), top_k=int(os.getenv("RAG_TOPK", "8")))
    pipe.add_component("embed", embed)
    pipe.add_component("retr", retr)
    pipe.connect("embed.embedding", "retr.query_embedding")
    return pipe

def _haystack_search(query: str, k: int = 8):
    res = _pipe().run({"embed": {"text": query}})
    docs = res["retr"]["documents"]
    return [{"path": d.meta.get("path",""), "content": (d.content or "")[:800]} for d in docs[:k]]

def repo_search(query: str, k: int = 8):
    hits = mcp_semantic_search(query, k=k)
    return hits if hits else _haystack_search(query, k=k)

def rag_tool(query: str) -> str:
    return json.dumps(repo_search(query, k=int(os.getenv("RAG_TOPK","8"))))[:8000]