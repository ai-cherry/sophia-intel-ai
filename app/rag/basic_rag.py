"""
Basic RAG Pipeline Implementation
Phase 2, Week 1-2: Simple document ingestion and retrieval with Ollama
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import hashlib

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Weaviate
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Weaviate client
import weaviate
from weaviate.embedded import EmbeddedOptions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RAGConfig:
    """Configuration for RAG pipeline"""
    ollama_base_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    weaviate_url: str = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    llm_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    embedding_model: str = "nomic-embed-text"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    collection_name: str = "Documents"
    k_results: int = 4
    temperature: float = 0.3


class BasicRAGPipeline:
    """Simple RAG implementation using Ollama and Weaviate"""
    
    def __init__(self, config: Optional[RAGConfig] = None):
        """Initialize the RAG pipeline"""
        self.config = config or RAGConfig()
        self.client = None
        self.vectorstore = None
        self.llm = None
        self.embeddings = None
        self.text_splitter = None
        self.qa_chain = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all RAG components"""
        try:
            # Initialize Weaviate client
            logger.info(f"Connecting to Weaviate at {self.config.weaviate_url}")
            self.client = weaviate.Client(
                url=self.config.weaviate_url,
                timeout_config=(5, 15)
            )
            
            # Test connection
            if not self.client.is_ready():
                raise ConnectionError("Weaviate is not ready")
            
            # Initialize Ollama LLM
            logger.info(f"Initializing Ollama LLM with model {self.config.llm_model}")
            self.llm = Ollama(
                base_url=self.config.ollama_base_url,
                model=self.config.llm_model,
                temperature=self.config.temperature,
                num_predict=512
            )
            
            # Initialize embeddings
            logger.info(f"Initializing embeddings with {self.config.embedding_model}")
            self.embeddings = OllamaEmbeddings(
                base_url=self.config.ollama_base_url,
                model=self.config.embedding_model
            )
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.chunk_size,
                chunk_overlap=self.config.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            # Initialize or get vector store
            self._setup_vectorstore()
            
            # Setup QA chain
            self._setup_qa_chain()
            
            logger.info("✅ RAG pipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {e}")
            raise
    
    def _setup_vectorstore(self):
        """Setup Weaviate vector store"""
        try:
            # Create schema if it doesn't exist
            schema = {
                "class": self.config.collection_name,
                "vectorizer": "none",  # We'll provide our own embeddings
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                    },
                    {
                        "name": "source",
                        "dataType": ["text"],
                    },
                    {
                        "name": "chunk_id",
                        "dataType": ["text"],
                    }
                ]
            }
            
            # Check if schema exists
            existing_schema = self.client.schema.get()
            class_exists = any(
                c["class"] == self.config.collection_name 
                for c in existing_schema.get("classes", [])
            )
            
            if not class_exists:
                logger.info(f"Creating Weaviate schema for {self.config.collection_name}")
                self.client.schema.create_class(schema)
            
            # Initialize vector store
            self.vectorstore = Weaviate(
                client=self.client,
                index_name=self.config.collection_name,
                text_key="content",
                embedding=self.embeddings,
                by_text=False,
                attributes=["source", "chunk_id"]
            )
            
        except Exception as e:
            logger.error(f"Failed to setup vector store: {e}")
            raise
    
    def _setup_qa_chain(self):
        """Setup the QA chain with custom prompt"""
        prompt_template = """You are a helpful AI assistant. Use the following context to answer the question.
If you don't know the answer based on the context, say so honestly.

Context:
{context}

Question: {question}

Answer: """
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": self.config.k_results}
            ),
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )
    
    def ingest_text(self, text: str, source: str = "unknown") -> Dict[str, Any]:
        """
        Ingest text content into the vector store
        
        Args:
            text: Text content to ingest
            source: Source identifier for the content
            
        Returns:
            Dict with ingestion results
        """
        try:
            logger.info(f"Ingesting text from source: {source}")
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            logger.info(f"Split text into {len(chunks)} chunks")
            
            # Create documents with metadata
            documents = []
            for i, chunk in enumerate(chunks):
                chunk_id = hashlib.md5(f"{source}_{i}_{chunk[:50]}".encode()).hexdigest()
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": source,
                        "chunk_id": chunk_id,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                )
                documents.append(doc)
            
            # Add to vector store
            ids = self.vectorstore.add_documents(documents)
            
            result = {
                "status": "success",
                "source": source,
                "chunks_created": len(chunks),
                "document_ids": ids,
                "message": f"Successfully ingested {len(chunks)} chunks from {source}"
            }
            
            logger.info(result["message"])
            return result
            
        except Exception as e:
            logger.error(f"Failed to ingest text: {e}")
            return {
                "status": "error",
                "source": source,
                "error": str(e)
            }
    
    def ingest_file(self, file_path: str) -> Dict[str, Any]:
        """
        Ingest a file into the vector store
        
        Args:
            file_path: Path to the file to ingest
            
        Returns:
            Dict with ingestion results
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.ingest_text(content, source=file_path)
            
        except Exception as e:
            logger.error(f"Failed to ingest file {file_path}: {e}")
            return {
                "status": "error",
                "source": file_path,
                "error": str(e)
            }
    
    def query(self, question: str, return_sources: bool = True) -> Dict[str, Any]:
        """
        Query the RAG system
        
        Args:
            question: Question to ask
            return_sources: Whether to return source documents
            
        Returns:
            Dict with answer and optionally source documents
        """
        try:
            logger.info(f"Processing query: {question}")
            
            # Get response from QA chain
            response = self.qa_chain({"query": question})
            
            result = {
                "status": "success",
                "question": question,
                "answer": response.get("result", "No answer found"),
            }
            
            if return_sources and "source_documents" in response:
                sources = []
                for doc in response["source_documents"]:
                    sources.append({
                        "content": doc.page_content[:200] + "...",
                        "source": doc.metadata.get("source", "unknown"),
                        "chunk_id": doc.metadata.get("chunk_id", "unknown")
                    })
                result["sources"] = sources
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            return {
                "status": "error",
                "question": question,
                "error": str(e)
            }
    
    def clear_collection(self) -> bool:
        """Clear all documents from the collection"""
        try:
            logger.info(f"Clearing collection {self.config.collection_name}")
            self.client.schema.delete_class(self.config.collection_name)
            self._setup_vectorstore()
            logger.info("Collection cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        try:
            # Get object count
            result = self.client.query.aggregate(self.config.collection_name).with_meta_count().do()
            
            count = 0
            if "data" in result and "Aggregate" in result["data"]:
                aggregate = result["data"]["Aggregate"].get(self.config.collection_name, [])
                if aggregate and len(aggregate) > 0:
                    count = aggregate[0].get("meta", {}).get("count", 0)
            
            return {
                "status": "success",
                "collection": self.config.collection_name,
                "document_count": count,
                "weaviate_url": self.config.weaviate_url,
                "llm_model": self.config.llm_model,
                "embedding_model": self.config.embedding_model
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Example usage and testing
if __name__ == "__main__":
    # Initialize RAG pipeline
    rag = BasicRAGPipeline()
    
    # Get current stats
    print("\n📊 Initial Stats:")
    print(json.dumps(rag.get_stats(), indent=2))
    
    # Example: Ingest some sample text
    sample_text = """
    Sophia Intel AI is an advanced AI orchestration platform that combines multiple AI models,
    intelligent routing, and sophisticated caching to deliver optimal performance. The system
    uses Weaviate for vector storage, Redis for caching, and supports multiple LLM providers
    including OpenAI, Anthropic, and local models via Ollama.
    
    The platform features a multi-agent architecture where specialized agents collaborate
    to solve complex tasks. It includes comprehensive monitoring with Prometheus and Grafana,
    cost tracking, and advanced debugging capabilities.
    """
    
    print("\n📝 Ingesting sample text...")
    result = rag.ingest_text(sample_text, source="sample_documentation")
    print(json.dumps(result, indent=2))
    
    # Query the system
    print("\n❓ Testing query...")
    response = rag.query("What is Sophia Intel AI?")
    print(json.dumps(response, indent=2))
    
    # Final stats
    print("\n📊 Final Stats:")
    print(json.dumps(rag.get_stats(), indent=2))