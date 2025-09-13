"""
Multi-Modal Embedding System
=============================
Advanced embedding infrastructure supporting code, documentation,
semantic meaning, and usage patterns for intelligent retrieval.
AI Context:
- Multiple embedding strategies for different content types
- Hierarchical indexing for efficient retrieval
- Graph-based contextual embeddings
- Smart chunking for optimal context windows
"""
import hashlib
import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional
import numpy as np
logger = logging.getLogger(__name__)
class EmbeddingType(Enum):
    """Types of embeddings supported"""
    CODE = "code"  # Source code embeddings
    DOCUMENTATION = "documentation"  # Doc strings and comments
    SEMANTIC = "semantic"  # Semantic meaning and intent
    USAGE = "usage"  # Usage patterns and examples
    STRUCTURAL = "structural"  # AST and code structure
    BEHAVIORAL = "behavioral"  # Runtime behavior patterns
    RELATIONAL = "relational"  # Relationships between components
class ChunkingStrategy(Enum):
    """Strategies for chunking content"""
    FIXED_SIZE = "fixed_size"  # Fixed token/character count
    SEMANTIC_BOUNDARIES = "semantic_boundaries"  # Natural breaks
    AST_BASED = "ast_based"  # Based on AST structure
    SLIDING_WINDOW = "sliding_window"  # Overlapping windows
    HIERARCHICAL = "hierarchical"  # Multi-level chunks
    DYNAMIC = "dynamic"  # Adaptive based on content
@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation"""
    model: str = "text-embedding-3-large"
    dimensions: int = 3072
    chunk_size: int = 512
    chunk_overlap: int = 50
    strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC_BOUNDARIES
    include_metadata: bool = True
    normalize: bool = True
@dataclass
class CodeChunk:
    """Represents a chunk of code for embedding"""
    content: str
    start_line: int
    end_line: int
    file_path: str
    chunk_type: str  # function, class, module, etc.
    metadata: dict[str, Any] = field(default_factory=dict)
    parent_chunk: Optional[str] = None
    child_chunks: list[str] = field(default_factory=list)
    @property
    def id(self) -> str:
        """Generate unique ID for chunk"""
        content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:8]
        return f"{self.file_path}:{self.start_line}:{self.end_line}:{content_hash}"
@dataclass
class EmbeddingResult:
    """Result of embedding generation"""
    chunk_id: str
    embedding: np.ndarray
    embedding_type: EmbeddingType
    metadata: dict[str, Any]
    timestamp: str
    model: str
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "chunk_id": self.chunk_id,
            "embedding": self.embedding.tolist(),
            "embedding_type": self.embedding_type.value,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "model": self.model,
        }
class CodeChunker:
    """Intelligent code chunking system"""
    def __init__(self, config: EmbeddingConfig):
        self.config = config
    def chunk_file(self, file_path: Path, content: str) -> list[CodeChunk]:
        """Chunk a file based on configured strategy"""
        if self.config.strategy == ChunkingStrategy.AST_BASED:
            return self._ast_based_chunking(file_path, content)
        elif self.config.strategy == ChunkingStrategy.SEMANTIC_BOUNDARIES:
            return self._semantic_chunking(file_path, content)
        elif self.config.strategy == ChunkingStrategy.SLIDING_WINDOW:
            return self._sliding_window_chunking(file_path, content)
        elif self.config.strategy == ChunkingStrategy.HIERARCHICAL:
            return self._hierarchical_chunking(file_path, content)
        else:
            return self._fixed_size_chunking(file_path, content)
    def _ast_based_chunking(self, file_path: Path, content: str) -> list[CodeChunk]:
        """Chunk based on AST structure"""
        import ast
        chunks = []
        try:
            tree = ast.parse(content)
            # Module-level chunk
            module_chunk = CodeChunk(
                content=content,
                start_line=1,
                end_line=len(content.split("\n")),
                file_path=str(file_path),
                chunk_type="module",
                metadata={"name": file_path.stem},
            )
            chunks.append(module_chunk)
            # Extract classes and functions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_source = ast.get_source_segment(content, node) or ""
                    chunk = CodeChunk(
                        content=class_source,
                        start_line=node.lineno,
                        end_line=node.end_lineno or node.lineno,
                        file_path=str(file_path),
                        chunk_type="class",
                        metadata={
                            "name": node.name,
                            "docstring": ast.get_docstring(node) or "",
                        },
                        parent_chunk=module_chunk.id,
                    )
                    chunks.append(chunk)
                    module_chunk.child_chunks.append(chunk.id)
                    # Extract methods from class
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            method_source = ast.get_source_segment(content, item) or ""
                            method_chunk = CodeChunk(
                                content=method_source,
                                start_line=item.lineno,
                                end_line=item.end_lineno or item.lineno,
                                file_path=str(file_path),
                                chunk_type="method",
                                metadata={
                                    "name": f"{node.name}.{item.name}",
                                    "docstring": ast.get_docstring(item) or "",
                                    "is_async": isinstance(item, ast.AsyncFunctionDef),
                                },
                                parent_chunk=chunk.id,
                            )
                            chunks.append(method_chunk)
                            chunk.child_chunks.append(method_chunk.id)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Only process top-level functions
                    if not any(
                        isinstance(parent, ast.ClassDef)
                        for parent in ast.walk(tree)
                        if hasattr(parent, "body") and node in parent.body
                    ):
                        func_source = ast.get_source_segment(content, node) or ""
                        chunk = CodeChunk(
                            content=func_source,
                            start_line=node.lineno,
                            end_line=node.end_lineno or node.lineno,
                            file_path=str(file_path),
                            chunk_type="function",
                            metadata={
                                "name": node.name,
                                "docstring": ast.get_docstring(node) or "",
                                "is_async": isinstance(node, ast.AsyncFunctionDef),
                            },
                            parent_chunk=module_chunk.id,
                        )
                        chunks.append(chunk)
                        module_chunk.child_chunks.append(chunk.id)
        except SyntaxError as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            # Fall back to fixed size chunking
            return self._fixed_size_chunking(file_path, content)
        return chunks
    def _semantic_chunking(self, file_path: Path, content: str) -> list[CodeChunk]:
        """Chunk based on semantic boundaries"""
        chunks = []
        lines = content.split("\n")
        current_chunk = []
        current_start = 1
        # Semantic markers
        markers = [
            "class ",
            "def ",
            "async def ",
            "# ---",
            "# ===",
            '"""',
            "'''",
        ]
        for i, line in enumerate(lines, 1):
            # Check for semantic boundary
            is_boundary = any(line.strip().startswith(marker) for marker in markers)
            if is_boundary and current_chunk:
                # Save current chunk
                chunk = CodeChunk(
                    content="\n".join(current_chunk),
                    start_line=current_start,
                    end_line=i - 1,
                    file_path=str(file_path),
                    chunk_type="semantic_block",
                    metadata={},
                )
                chunks.append(chunk)
                # Start new chunk
                current_chunk = [line]
                current_start = i
            else:
                current_chunk.append(line)
                # Check size limit
                if len("\n".join(current_chunk)) > self.config.chunk_size * 4:
                    chunk = CodeChunk(
                        content="\n".join(current_chunk),
                        start_line=current_start,
                        end_line=i,
                        file_path=str(file_path),
                        chunk_type="semantic_block",
                        metadata={},
                    )
                    chunks.append(chunk)
                    current_chunk = []
                    current_start = i + 1
        # Save final chunk
        if current_chunk:
            chunk = CodeChunk(
                content="\n".join(current_chunk),
                start_line=current_start,
                end_line=len(lines),
                file_path=str(file_path),
                chunk_type="semantic_block",
                metadata={},
            )
            chunks.append(chunk)
        return chunks
    def _sliding_window_chunking(
        self, file_path: Path, content: str
    ) -> list[CodeChunk]:
        """Create overlapping chunks"""
        chunks = []
        lines = content.split("\n")
        window_size = self.config.chunk_size // 80  # Approximate lines per chunk
        overlap = self.config.chunk_overlap // 80
        for i in range(0, len(lines), window_size - overlap):
            end = min(i + window_size, len(lines))
            chunk = CodeChunk(
                content="\n".join(lines[i:end]),
                start_line=i + 1,
                end_line=end,
                file_path=str(file_path),
                chunk_type="window",
                metadata={"window_index": len(chunks)},
            )
            chunks.append(chunk)
        return chunks
    def _hierarchical_chunking(self, file_path: Path, content: str) -> list[CodeChunk]:
        """Create multi-level chunks"""
        chunks = []
        # Level 1: Entire file
        file_chunk = CodeChunk(
            content=content[: self.config.chunk_size * 2],  # Summary
            start_line=1,
            end_line=len(content.split("\n")),
            file_path=str(file_path),
            chunk_type="file_summary",
            metadata={"level": 1},
        )
        chunks.append(file_chunk)
        # Level 2: AST-based chunks
        ast_chunks = self._ast_based_chunking(file_path, content)
        for chunk in ast_chunks:
            chunk.metadata["level"] = 2
            chunk.parent_chunk = file_chunk.id
            file_chunk.child_chunks.append(chunk.id)
        chunks.extend(ast_chunks)
        # Level 3: Fine-grained chunks for large functions
        for chunk in ast_chunks:
            if len(chunk.content) > self.config.chunk_size * 2:
                sub_chunks = self._fixed_size_chunking(
                    Path(chunk.file_path), chunk.content
                )
                for sub_chunk in sub_chunks:
                    sub_chunk.metadata["level"] = 3
                    sub_chunk.parent_chunk = chunk.id
                    chunk.child_chunks.append(sub_chunk.id)
                chunks.extend(sub_chunks)
        return chunks
    def _fixed_size_chunking(self, file_path: Path, content: str) -> list[CodeChunk]:
        """Simple fixed-size chunking"""
        chunks = []
        lines = content.split("\n")
        chunk_size = self.config.chunk_size // 80  # Approximate lines
        for i in range(0, len(lines), chunk_size):
            end = min(i + chunk_size, len(lines))
            chunk = CodeChunk(
                content="\n".join(lines[i:end]),
                start_line=i + 1,
                end_line=end,
                file_path=str(file_path),
                chunk_type="fixed_block",
                metadata={"block_index": len(chunks)},
            )
            chunks.append(chunk)
        return chunks
class EmbeddingGenerator:
    """Generates embeddings for code chunks"""
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self._embedding_cache: dict[str, np.ndarray] = {}
    async def generate_embedding(
        self, chunk: CodeChunk, embedding_type: EmbeddingType
    ) -> EmbeddingResult:
        """Generate embedding for a code chunk"""
        # Check cache
        cache_key = f"{chunk.id}:{embedding_type.value}"
        if cache_key in self._embedding_cache:
            embedding = self._embedding_cache[cache_key]
        else:
            # Prepare content based on type
            content = self._prepare_content(chunk, embedding_type)
            # Generate embedding (mock for now - replace with actual model)
            embedding = await self._call_embedding_model(content)
            # Cache result
            self._embedding_cache[cache_key] = embedding
        # Create result
        from datetime import datetime
        result = EmbeddingResult(
            chunk_id=chunk.id,
            embedding=embedding,
            embedding_type=embedding_type,
            metadata={
                **chunk.metadata,
                "file_path": chunk.file_path,
                "lines": f"{chunk.start_line}-{chunk.end_line}",
            },
            timestamp=datetime.now().isoformat(),
            model=self.config.model,
        )
        return result
    def _prepare_content(self, chunk: CodeChunk, embedding_type: EmbeddingType) -> str:
        """Prepare content for embedding based on type"""
        if embedding_type == EmbeddingType.CODE:
            # Raw code
            return chunk.content
        elif embedding_type == EmbeddingType.DOCUMENTATION:
            # Extract docstrings and comments
            import re
            # Extract docstrings
            docstrings = re.findall(r'""".*?"""', chunk.content, re.DOTALL)
            docstrings.extend(re.findall(r"'''.*?'''", chunk.content, re.DOTALL))
            # Extract comments
            comments = re.findall(r"#.*$", chunk.content, re.MULTILINE)
            return "\n".join(docstrings + comments)
        elif embedding_type == EmbeddingType.SEMANTIC:
            # Include metadata and context
            context = f"""
File: {chunk.file_path}
Type: {chunk.chunk_type}
Metadata: {json.dumps(chunk.metadata)}
Content:
{chunk.content}
"""
            return context
        elif embedding_type == EmbeddingType.USAGE:
            # Focus on function calls and usage patterns
            import re
            # Extract function calls
            calls = re.findall(r"\w+\(.*?\)", chunk.content)
            # Extract imports
            imports = re.findall(r"^import .*$", chunk.content, re.MULTILINE)
            imports.extend(
                re.findall(r"^from .* import .*$", chunk.content, re.MULTILINE)
            )
            return "\n".join(imports + calls)
        elif embedding_type == EmbeddingType.STRUCTURAL:
            # Create structural representation
            import ast
            try:
                tree = ast.parse(chunk.content)
                # Create simplified AST representation
                structure = self._ast_to_string(tree)
                return structure
            except:
                return f"STRUCTURE: {chunk.chunk_type}"
        else:
            return chunk.content
    def _ast_to_string(self, node: Any, indent: int = 0) -> str:
        """Convert AST to string representation"""
        import ast
        lines = []
        prefix = "  " * indent
        if isinstance(node, ast.Module):
            for item in node.body:
                lines.append(self._ast_to_string(item, indent))
        elif isinstance(node, ast.ClassDef):
            lines.append(f"{prefix}CLASS {node.name}")
            for item in node.body:
                lines.append(self._ast_to_string(item, indent + 1))
        elif isinstance(node, ast.FunctionDef):
            args = ", ".join(arg.arg for arg in node.args.args)
            lines.append(f"{prefix}FUNCTION {node.name}({args})")
        elif isinstance(node, ast.AsyncFunctionDef):
            args = ", ".join(arg.arg for arg in node.args.args)
            lines.append(f"{prefix}ASYNC_FUNCTION {node.name}({args})")
        return "\n".join(lines)
    async def _call_embedding_model(self, content: str) -> np.ndarray:
        """Call the actual embedding model"""
        # This is a mock implementation - replace with actual model call
        # For example, using OpenAI, Cohere, or local model
        # Mock: generate random embedding
        np.random.seed(hash(content) % 2**32)
        embedding = np.random.randn(self.config.dimensions)
        if self.config.normalize:
            # L2 normalization
            embedding = embedding / np.linalg.norm(embedding)
        return embedding
    async def generate_multi_modal_embeddings(
        self, chunk: CodeChunk
    ) -> dict[EmbeddingType, EmbeddingResult]:
        """Generate multiple types of embeddings for a chunk"""
        results = {}
        embedding_types = [
            EmbeddingType.CODE,
            EmbeddingType.DOCUMENTATION,
            EmbeddingType.SEMANTIC,
            EmbeddingType.USAGE,
        ]
        for emb_type in embedding_types:
            result = await self.generate_embedding(chunk, emb_type)
            results[emb_type] = result
        return results
class EmbeddingIndex:
    """Manages the embedding index for efficient retrieval"""
    def __init__(self, dimensions: int = 3072):
        self.dimensions = dimensions
        self.embeddings: dict[str, EmbeddingResult] = {}
        self.type_indices: dict[EmbeddingType, list[str]] = {}
    def add_embedding(self, result: EmbeddingResult) -> None:
        """Add embedding to index"""
        self.embeddings[result.chunk_id] = result
        # Update type index
        if result.embedding_type not in self.type_indices:
            self.type_indices[result.embedding_type] = []
        self.type_indices[result.embedding_type].append(result.chunk_id)
    def search(
        self,
        query_embedding: np.ndarray,
        embedding_type: Optional[EmbeddingType] = None,
        top_k: int = 10,
        threshold: float = 0.7,
    ) -> list[tuple[str, float, EmbeddingResult]]:
        """Search for similar embeddings"""
        results = []
        # Filter by type if specified
        if embedding_type and embedding_type in self.type_indices:
            candidate_ids = self.type_indices[embedding_type]
        else:
            candidate_ids = list(self.embeddings.keys())
        # Calculate similarities
        for chunk_id in candidate_ids:
            result = self.embeddings[chunk_id]
            # Cosine similarity
            similarity = np.dot(query_embedding, result.embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(result.embedding)
            )
            if similarity >= threshold:
                results.append((chunk_id, float(similarity), result))
        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    def get_embedding(self, chunk_id: str) -> Optional[EmbeddingResult]:
        """Get embedding by chunk ID"""
        return self.embeddings.get(chunk_id)
    def remove_embedding(self, chunk_id: str) -> None:
        """Remove embedding from index"""
        if chunk_id in self.embeddings:
            result = self.embeddings[chunk_id]
            del self.embeddings[chunk_id]
            # Update type index
            if result.embedding_type in self.type_indices:
                self.type_indices[result.embedding_type].remove(chunk_id)
    def save_index(self, path: Path) -> None:
        """Save index to disk"""
        data = {
            "dimensions": self.dimensions,
            "embeddings": {
                chunk_id: result.to_dict()
                for chunk_id, result in self.embeddings.items()
            },
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    def load_index(self, path: Path) -> None:
        """Load index from disk"""
        with open(path) as f:
            data = json.load(f)
        self.dimensions = data["dimensions"]
        self.embeddings = {}
        self.type_indices = {}
        for _chunk_id, result_dict in data["embeddings"].items():
            result = EmbeddingResult(
                chunk_id=result_dict["chunk_id"],
                embedding=np.array(result_dict["embedding"]),
                embedding_type=EmbeddingType(result_dict["embedding_type"]),
                metadata=result_dict["metadata"],
                timestamp=result_dict["timestamp"],
                model=result_dict["model"],
            )
            self.add_embedding(result)
class MultiModalEmbeddingSystem:
    """Complete multi-modal embedding system"""
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.chunker = CodeChunker(config)
        self.generator = EmbeddingGenerator(config)
        self.index = EmbeddingIndex(config.dimensions)
    async def process_file(self, file_path: Path) -> int:
        """Process a file and generate embeddings"""
        # Read file
        content = file_path.read_text()
        # Chunk file
        chunks = self.chunker.chunk_file(file_path, content)
        # Generate embeddings
        count = 0
        for chunk in chunks:
            # Generate multi-modal embeddings
            embeddings = await self.generator.generate_multi_modal_embeddings(chunk)
            # Add to index
            for _emb_type, result in embeddings.items():
                self.index.add_embedding(result)
                count += 1
        logger.info(f"Generated {count} embeddings for {file_path}")
        return count
    async def process_directory(self, directory: Path) -> int:
        """Process all Python files in directory"""
        total = 0
        for py_file in directory.rglob("*.py"):
            # Skip virtual environments
            if any(skip in py_file.parts for skip in [".venv", "venv", "__pycache__"]):
                continue
            count = await self.process_file(py_file)
            total += count
        logger.info(f"Generated {total} total embeddings for {directory}")
        return total
    async def search(
        self,
        query: str,
        embedding_type: Optional[EmbeddingType] = None,
        top_k: int = 10,
    ) -> list[tuple[str, float, dict[str, Any]]]:
        """Search for relevant code chunks"""
        # Generate query embedding
        query_chunk = CodeChunk(
            content=query,
            start_line=0,
            end_line=0,
            file_path="query",
            chunk_type="query",
        )
        query_result = await self.generator.generate_embedding(
            query_chunk, embedding_type or EmbeddingType.SEMANTIC
        )
        # Search index
        results = self.index.search(
            query_result.embedding,
            embedding_type,
            top_k,
        )
        # Format results
        formatted = []
        for chunk_id, similarity, result in results:
            formatted.append(
                (
                    chunk_id,
                    similarity,
                    {
                        "file_path": result.metadata.get("file_path"),
                        "lines": result.metadata.get("lines"),
                        "type": result.embedding_type.value,
                        "metadata": result.metadata,
                    },
                )
            )
        return formatted
