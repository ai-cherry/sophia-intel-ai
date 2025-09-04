"""
DEPRECATED: LangGraph RAG Pipeline - REPLACED BY AGNO
This module has been deprecated in favor of AGNO-based implementations.
Use app.infrastructure.agno.rag_pipeline instead.
"""

# DEPRECATED - DO NOT USE
# This file has been replaced by AGNO-based implementations
# All LangChain imports commented out to prevent conflicts with AGNO framework

# import asyncio
# import json
# import logging
# from dataclasses import dataclass, field
# from datetime import datetime
# from enum import Enum
# from typing import Any, Union

# # LangChain imports - DEPRECATED
# from langchain.embeddings.base import Embeddings
# from langchain.schema import Document  
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.vectorstores import FAISS, Chroma

# For embedding models
from sentence_transformers import SentenceTransformer

from app.core.ai_logger import logger

logger = logging.getLogger(__name__)

# ==================== Configuration ====================

@dataclass
class RAGConfig:
    """Configuration for RAG pipeline"""
    vector_store_type: str = "faiss"  # faiss or chroma
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5
    similarity_threshold: float = 0.7
    vector_store_path: Optional[str] = None
    persist_directory: Optional[str] = "./rag_store"
    collection_name: str = "default"

# ==================== Embedding Provider ====================

class LocalEmbeddings(Embeddings):
    """Local embedding provider using sentence-transformers"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize with a sentence-transformer model"""
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        logger.info(f"Initialized local embeddings with model: {model_name}")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of documents"""
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        """Embed a query text"""
        embedding = self.model.encode([text], show_progress_bar=False)[0]
        return embedding.tolist()

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """Async embed documents"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_documents, texts)

    async def aembed_query(self, text: str) -> list[float]:
        """Async embed query"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_query, text)

# ==================== Knowledge Nodes ====================

class KnowledgeNodeType(Enum):
    """Types of knowledge nodes"""
    CODEBASE = "codebase"
    SYSTEM_LOGS = "system_logs"
    USER_DOCS = "user_docs"
    POLICIES = "policies"
    CONVERSATIONS = "conversations"
    METRICS = "metrics"

@dataclass
class KnowledgeNode:
    """A node in the knowledge graph"""
    node_id: str
    node_type: KnowledgeNodeType
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embeddings: Optional[list[float]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_document(self) -> Document:
        """Convert to LangChain Document"""
        return Document(
            page_content=self.content,
            metadata={
                **self.metadata,
                "node_id": self.node_id,
                "node_type": self.node_type.value,
                "timestamp": self.timestamp.isoformat()
            }
        )

# ==================== RAG Pipeline ====================

class LangGraphRAGPipeline:
    """
    Main RAG pipeline for contextual knowledge retrieval
    Provides vector store integration and retrieval mechanisms
    """

    def __init__(self, config: Optional[RAGConfig] = None):
        """
        Initialize RAG pipeline
        
        Args:
            config: RAG configuration
        """
        self.config = config or RAGConfig()
        self.embeddings = LocalEmbeddings(self.config.embedding_model)
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap
        )
        self.knowledge_nodes: dict[str, KnowledgeNode] = {}
        self.query_cache: dict[str, list[Document]] = {}
        self.cache_ttl = 300  # 5 minutes

        logger.info(f"Initialized RAG pipeline with {self.config.vector_store_type} vector store")

    async def initialize(self):
        """Initialize vector store"""
        if self.config.vector_store_type == "faiss":
            await self._init_faiss()
        elif self.config.vector_store_type == "chroma":
            await self._init_chroma()
        else:
            raise ValueError(f"Unknown vector store type: {self.config.vector_store_type}")

        logger.info("RAG pipeline initialized successfully")

    async def _init_faiss(self):
        """Initialize FAISS vector store"""
        try:
            # Try to load existing store
            if self.config.vector_store_path:
                self.vector_store = FAISS.load_local(
                    self.config.vector_store_path,
                    self.embeddings
                )
                logger.info(f"Loaded FAISS store from {self.config.vector_store_path}")
            else:
                # Create new store with dummy document
                dummy_doc = Document(
                    page_content="System initialized",
                    metadata={"type": "system"}
                )
                self.vector_store = FAISS.from_documents(
                    [dummy_doc],
                    self.embeddings
                )
                logger.info("Created new FAISS store")
        except Exception as e:
            logger.warning(f"Could not load FAISS store: {e}. Creating new one.")
            dummy_doc = Document(
                page_content="System initialized",
                metadata={"type": "system"}
            )
            self.vector_store = FAISS.from_documents(
                [dummy_doc],
                self.embeddings
            )

    async def _init_chroma(self):
        """Initialize Chroma vector store"""
        try:
            self.vector_store = Chroma(
                collection_name=self.config.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.config.persist_directory
            )
            logger.info(f"Initialized Chroma store at {self.config.persist_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize Chroma: {e}")
            raise

    # ==================== Document Management ====================

    async def add_documents(
        self,
        documents: list[Document],
        node_type: KnowledgeNodeType = KnowledgeNodeType.USER_DOCS
    ) -> list[str]:
        """
        Add documents to the vector store
        
        Args:
            documents: List of documents to add
            node_type: Type of knowledge node
            
        Returns:
            List of document IDs
        """
        # Split documents into chunks
        all_chunks = []
        doc_ids = []

        for doc in documents:
            chunks = self.text_splitter.split_documents([doc])

            # Create knowledge nodes
            for i, chunk in enumerate(chunks):
                node_id = f"{node_type.value}_{datetime.utcnow().timestamp()}_{i}"

                # Add node metadata
                chunk.metadata.update({
                    "node_id": node_id,
                    "node_type": node_type.value,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                })

                # Create knowledge node
                node = KnowledgeNode(
                    node_id=node_id,
                    node_type=node_type,
                    content=chunk.page_content,
                    metadata=chunk.metadata
                )

                self.knowledge_nodes[node_id] = node
                all_chunks.append(chunk)
                doc_ids.append(node_id)

        # Add to vector store
        if all_chunks:
            self.vector_store.add_documents(all_chunks)
            logger.info(f"Added {len(all_chunks)} chunks to vector store")

        # Clear cache
        self.query_cache.clear()

        return doc_ids

    async def add_text(
        self,
        text: str,
        metadata: Optional[dict[str, Any]] = None,
        node_type: KnowledgeNodeType = KnowledgeNodeType.USER_DOCS
    ) -> list[str]:
        """
        Add text to the vector store
        
        Args:
            text: Text content to add
            metadata: Optional metadata
            node_type: Type of knowledge node
            
        Returns:
            List of document IDs
        """
        doc = Document(
            page_content=text,
            metadata=metadata or {}
        )
        return await self.add_documents([doc], node_type)

    # ==================== Retrieval ====================

    async def retrieve(
        self,
        query: str,
        k: Optional[int] = None,
        filter_dict: Optional[dict[str, Any]] = None
    ) -> list[Document]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Query text
            k: Number of documents to retrieve
            filter_dict: Optional metadata filter
            
        Returns:
            List of relevant documents
        """
        k = k or self.config.top_k

        # Check cache
        cache_key = f"{query}_{k}_{json.dumps(filter_dict or {})}"
        if cache_key in self.query_cache:
            logger.debug(f"Cache hit for query: {query[:50]}...")
            return self.query_cache[cache_key]

        # Perform similarity search
        if filter_dict:
            docs = self.vector_store.similarity_search_with_score(
                query,
                k=k,
                filter=filter_dict
            )
        else:
            docs = self.vector_store.similarity_search_with_score(
                query,
                k=k
            )

        # Filter by similarity threshold
        filtered_docs = []
        for doc, score in docs:
            # Note: FAISS returns distance, not similarity
            # Lower distance = higher similarity
            if self.config.vector_store_type == "faiss":
                # Convert distance to similarity (rough approximation)
                similarity = 1 / (1 + score)
            else:
                similarity = score

            if similarity >= self.config.similarity_threshold:
                doc.metadata["similarity_score"] = similarity
                filtered_docs.append(doc)

        # Cache results
        self.query_cache[cache_key] = filtered_docs

        logger.info(f"Retrieved {len(filtered_docs)} documents for query: {query[:50]}...")

        return filtered_docs

    async def retrieve_by_type(
        self,
        query: str,
        node_type: KnowledgeNodeType,
        k: Optional[int] = None
    ) -> list[Document]:
        """
        Retrieve documents of a specific type
        
        Args:
            query: Query text
            node_type: Type of knowledge node
            k: Number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        return await self.retrieve(
            query,
            k=k,
            filter_dict={"node_type": node_type.value}
        )

    # ==================== Context Building ====================

    async def build_context(
        self,
        query: str,
        conversation_history: Optional[list[dict[str, str]]] = None,
        include_types: Optional[list[KnowledgeNodeType]] = None
    ) -> dict[str, Any]:
        """
        Build comprehensive context for a query
        
        Args:
            query: Query text
            conversation_history: Optional conversation history
            include_types: Types of knowledge to include
            
        Returns:
            Context dictionary with retrieved information
        """
        context = {
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "retrieved_knowledge": {},
            "conversation_summary": None
        }

        # Determine which types to include
        if include_types is None:
            include_types = [
                KnowledgeNodeType.CODEBASE,
                KnowledgeNodeType.USER_DOCS,
                KnowledgeNodeType.POLICIES
            ]

        # Retrieve from each knowledge type
        for node_type in include_types:
            docs = await self.retrieve_by_type(query, node_type, k=3)
            if docs:
                context["retrieved_knowledge"][node_type.value] = [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity": doc.metadata.get("similarity_score", 0)
                    }
                    for doc in docs
                ]

        # Add conversation context if available
        if conversation_history:
            # Summarize recent conversation
            recent_history = conversation_history[-5:]  # Last 5 exchanges
            summary = self._summarize_conversation(recent_history)
            context["conversation_summary"] = summary

        return context

    def _summarize_conversation(self, history: list[dict[str, str]]) -> str:
        """Summarize conversation history"""
        if not history:
            return ""

        summary_parts = []
        for exchange in history:
            if "user" in exchange:
                summary_parts.append(f"User: {exchange['user'][:100]}...")
            if "assistant" in exchange:
                summary_parts.append(f"Assistant: {exchange['assistant'][:100]}...")

        return " | ".join(summary_parts[-10:])  # Last 10 parts

    # ==================== Analytics ====================

    def get_statistics(self) -> dict[str, Any]:
        """Get RAG pipeline statistics"""
        stats = {
            "total_documents": len(self.knowledge_nodes),
            "documents_by_type": {},
            "cache_size": len(self.query_cache),
            "vector_store_type": self.config.vector_store_type,
            "embedding_model": self.config.embedding_model
        }

        # Count documents by type
        for node in self.knowledge_nodes.values():
            node_type = node.node_type.value
            stats["documents_by_type"][node_type] = stats["documents_by_type"].get(node_type, 0) + 1

        return stats

    # ==================== Persistence ====================

    async def save(self, path: Optional[str] = None):
        """Save vector store to disk"""
        save_path = path or self.config.vector_store_path

        if not save_path:
            logger.warning("No save path specified")
            return

        if self.config.vector_store_type == "faiss":
            self.vector_store.save_local(save_path)
            logger.info(f"Saved FAISS store to {save_path}")
        elif self.config.vector_store_type == "chroma":
            # Chroma auto-persists if persist_directory is set
            self.vector_store.persist()
            logger.info("Persisted Chroma store")

    async def clear(self):
        """Clear all data from the pipeline"""
        self.knowledge_nodes.clear()
        self.query_cache.clear()

        # Reinitialize vector store
        await self.initialize()

        logger.info("Cleared RAG pipeline")

# ==================== REST/gRPC Endpoint ====================

class RAGService:
    """
    Service layer for RAG pipeline
    Provides REST/gRPC endpoints for agents to query
    """

    def __init__(self, pipeline: LangGraphRAGPipeline):
        """
        Initialize RAG service
        
        Args:
            pipeline: RAG pipeline instance
        """
        self.pipeline = pipeline
        self.request_count = 0
        self.last_request_time = None

    async def query(
        self,
        text: str,
        context_type: Optional[str] = None,
        k: int = 5,
        include_metadata: bool = True
    ) -> dict[str, Any]:
        """
        Query endpoint for agents
        
        Args:
            text: Query text
            context_type: Optional context type filter
            k: Number of results
            include_metadata: Whether to include metadata
            
        Returns:
            Query results with context
        """
        self.request_count += 1
        self.last_request_time = datetime.utcnow()

        # Determine node type filter
        filter_dict = None
        if context_type:
            filter_dict = {"node_type": context_type}

        # Retrieve documents
        docs = await self.pipeline.retrieve(text, k=k, filter_dict=filter_dict)

        # Format response
        response = {
            "query": text,
            "results": [],
            "request_id": f"req_{self.request_count}",
            "timestamp": datetime.utcnow().isoformat()
        }

        for doc in docs:
            result = {
                "content": doc.page_content,
                "score": doc.metadata.get("similarity_score", 0)
            }

            if include_metadata:
                result["metadata"] = doc.metadata

            response["results"].append(result)

        return response

    async def index(
        self,
        content: str,
        content_type: str = "user_docs",
        metadata: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """
        Index new content
        
        Args:
            content: Content to index
            content_type: Type of content
            metadata: Optional metadata
            
        Returns:
            Indexing result
        """
        # Map content type to node type
        node_type_map = {
            "code": KnowledgeNodeType.CODEBASE,
            "logs": KnowledgeNodeType.SYSTEM_LOGS,
            "user_docs": KnowledgeNodeType.USER_DOCS,
            "policies": KnowledgeNodeType.POLICIES,
            "conversations": KnowledgeNodeType.CONVERSATIONS,
            "metrics": KnowledgeNodeType.METRICS
        }

        node_type = node_type_map.get(content_type, KnowledgeNodeType.USER_DOCS)

        # Add to pipeline
        doc_ids = await self.pipeline.add_text(content, metadata, node_type)

        return {
            "status": "indexed",
            "document_ids": doc_ids,
            "content_type": content_type,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def get_status(self) -> dict[str, Any]:
        """Get service status"""
        stats = self.pipeline.get_statistics()

        return {
            "status": "healthy",
            "request_count": self.request_count,
            "last_request": self.last_request_time.isoformat() if self.last_request_time else None,
            "pipeline_stats": stats
        }

# ==================== Example Usage ====================

async def example_usage():
    """Example of using the RAG pipeline"""

    # Initialize pipeline
    config = RAGConfig(
        vector_store_type="faiss",
        embedding_model="all-MiniLM-L6-v2",
        chunk_size=500,
        top_k=3
    )

    pipeline = LangGraphRAGPipeline(config)
    await pipeline.initialize()

    # Add some documents
    docs = [
        Document(
            page_content="The ChatOrchestrator handles WebSocket connections for real-time chat.",
            metadata={"source": "architecture.md", "section": "websocket"}
        ),
        Document(
            page_content="AGNO provides standardized runtime for micro-agents with lifecycle management.",
            metadata={"source": "agno.md", "section": "runtime"}
        ),
        Document(
            page_content="The Orchestra Manager interprets natural language commands and routes them to appropriate swarms.",
            metadata={"source": "manager.md", "section": "routing"}
        )
    ]

    await pipeline.add_documents(docs, KnowledgeNodeType.CODEBASE)

    # Query the pipeline
    results = await pipeline.retrieve("How does WebSocket chat work?")

    for doc in results:
        logger.info(f"Content: {doc.page_content[:100]}...")
        logger.info(f"Similarity: {doc.metadata.get('similarity_score', 0):.2f}")
        logger.info("---")

    # Build context for a query
    context = await pipeline.build_context(
        "Explain the agent runtime system",
        include_types=[KnowledgeNodeType.CODEBASE, KnowledgeNodeType.USER_DOCS]
    )

    logger.info(f"Context built with {len(context['retrieved_knowledge'])} knowledge types")

    # Create service
    service = RAGService(pipeline)

    # Query through service
    response = await service.query("What is AGNO?", k=2)
    logger.info(f"Service returned {len(response['results'])} results")

    # Save pipeline
    await pipeline.save("./rag_store")

if __name__ == "__main__":
    asyncio.run(example_usage())
