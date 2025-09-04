"""
DEPRECATED: LangGraph Knowledge Nodes - REPLACED BY AGNO
This module has been deprecated in favor of AGNO-based implementations.
Use app.infrastructure.agno.knowledge_nodes instead.
"""

# DEPRECATED - DO NOT USE
# This file has been replaced by AGNO-based implementations
# All imports commented out to prevent conflicts with AGNO framework

# import json
# import logging
# import re
# from pathlib import Path
# from typing import Any, Optional, Union

# from langchain.schema import Document

# from app.infrastructure.langgraph.rag_pipeline import (
#     KnowledgeNodeType,
#     LangGraphRAGPipeline,
# )

logger = logging.getLogger(__name__)

# ==================== Base Knowledge Source ====================

class KnowledgeSource:
    """Base class for knowledge sources"""

    def __init__(self, node_type: KnowledgeNodeType, pipeline: LangGraphRAGPipeline):
        """
        Initialize knowledge source
        
        Args:
            node_type: Type of knowledge node
            pipeline: RAG pipeline instance
        """
        self.node_type = node_type
        self.pipeline = pipeline
        self.indexed_count = 0

    async def index(self) -> int:
        """
        Index knowledge from this source
        
        Returns:
            Number of documents indexed
        """
        raise NotImplementedError

    async def update(self) -> int:
        """
        Update indexed knowledge
        
        Returns:
            Number of documents updated
        """
        raise NotImplementedError

# ==================== Codebase Node ====================

class CodebaseNode(KnowledgeSource):
    """
    Knowledge node for source code and documentation
    Indexes Python files, markdown docs, and configuration files
    """

    def __init__(
        self,
        pipeline: LangGraphRAGPipeline,
        root_path: str = ".",
        file_patterns: Optional[list[str]] = None
    ):
        """
        Initialize codebase node
        
        Args:
            pipeline: RAG pipeline instance
            root_path: Root directory to index
            file_patterns: File patterns to include
        """
        super().__init__(KnowledgeNodeType.CODEBASE, pipeline)
        self.root_path = Path(root_path)
        self.file_patterns = file_patterns or ["*.py", "*.md", "*.yaml", "*.json"]
        self.file_cache: dict[str, str] = {}

    async def index(self) -> int:
        """Index codebase files"""
        documents = []

        for pattern in self.file_patterns:
            for file_path in self.root_path.rglob(pattern):
                # Skip common directories
                if any(skip in str(file_path) for skip in [
                    "__pycache__", ".git", "node_modules", ".venv", "venv"
                ]):
                    continue

                try:
                    content = file_path.read_text(encoding='utf-8')

                    # Extract metadata from file
                    metadata = self._extract_metadata(file_path, content)

                    # Create document
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": str(file_path.relative_to(self.root_path)),
                            "file_type": file_path.suffix,
                            **metadata
                        }
                    )

                    documents.append(doc)
                    self.file_cache[str(file_path)] = content

                except Exception as e:
                    logger.warning(f"Failed to index {file_path}: {e}")

        # Add to pipeline
        if documents:
            doc_ids = await self.pipeline.add_documents(documents, self.node_type)
            self.indexed_count = len(doc_ids)
            logger.info(f"Indexed {self.indexed_count} code files")

        return self.indexed_count

    def _extract_metadata(self, file_path: Path, content: str) -> dict[str, Any]:
        """Extract metadata from file content"""
        metadata = {}

        if file_path.suffix == ".py":
            # Extract Python metadata
            # Find classes
            classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
            if classes:
                metadata["classes"] = classes

            # Find functions
            functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
            if functions:
                metadata["functions"] = functions

            # Find imports
            imports = re.findall(r'^(?:Union[from, import])\s+([.\w]+)', content, re.MULTILINE)
            if imports:
                metadata["imports"] = imports[:10]  # Limit to first 10

        elif file_path.suffix == ".md":
            # Extract markdown headers
            headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
            if headers:
                metadata["headers"] = headers

        return metadata

    async def update(self) -> int:
        """Update indexed codebase"""
        updated = 0

        for file_path, old_content in self.file_cache.items():
            path = Path(file_path)
            if path.exists():
                try:
                    new_content = path.read_text(encoding='utf-8')
                    if new_content != old_content:
                        # Re-index changed file
                        doc = Document(
                            page_content=new_content,
                            metadata={
                                "source": str(path.relative_to(self.root_path)),
                                "file_type": path.suffix,
                                "updated": True
                            }
                        )
                        await self.pipeline.add_documents([doc], self.node_type)
                        self.file_cache[file_path] = new_content
                        updated += 1
                except Exception as e:
                    logger.warning(f"Failed to update {file_path}: {e}")

        if updated > 0:
            logger.info(f"Updated {updated} code files")

        return updated

# ==================== System Logs Node ====================

class SystemLogsNode(KnowledgeSource):
    """
    Knowledge node for system logs and error patterns
    Indexes application logs for pattern recognition
    """

    def __init__(
        self,
        pipeline: LangGraphRAGPipeline,
        log_paths: Optional[list[str]] = None,
        max_lines: int = 1000
    ):
        """
        Initialize system logs node
        
        Args:
            pipeline: RAG pipeline instance
            log_paths: Paths to log files
            max_lines: Maximum lines to index per file
        """
        super().__init__(KnowledgeNodeType.SYSTEM_LOGS, pipeline)
        self.log_paths = log_paths or ["./logs/*.log"]
        self.max_lines = max_lines
        self.indexed_patterns: Set[str] = set()

    async def index(self) -> int:
        """Index system logs"""
        documents = []

        for log_pattern in self.log_paths:
            for log_path in Path(".").glob(log_pattern):
                try:
                    # Read last N lines
                    with open(log_path) as f:
                        lines = f.readlines()[-self.max_lines:]

                    # Group by log level and extract patterns
                    log_groups = self._group_logs(lines)

                    for level, entries in log_groups.items():
                        if entries:
                            doc = Document(
                                page_content="\n".join(entries[:100]),  # Limit entries
                                metadata={
                                    "source": str(log_path.name),
                                    "log_level": level,
                                    "entry_count": len(entries),
                                    "patterns": self._extract_patterns(entries)
                                }
                            )
                            documents.append(doc)

                except Exception as e:
                    logger.warning(f"Failed to index log {log_path}: {e}")

        # Add to pipeline
        if documents:
            doc_ids = await self.pipeline.add_documents(documents, self.node_type)
            self.indexed_count = len(doc_ids)
            logger.info(f"Indexed {self.indexed_count} log groups")

        return self.indexed_count

    def _group_logs(self, lines: list[str]) -> dict[str, list[str]]:
        """Group log lines by level"""
        groups = {
            "ERROR": [],
            "WARNING": [],
            "INFO": [],
            "DEBUG": []
        }

        for line in lines:
            for level in groups:
                if level in line:
                    groups[level].append(line.strip())
                    break

        return groups

    def _extract_patterns(self, entries: list[str]) -> list[str]:
        """Extract common patterns from log entries"""
        patterns = []

        # Extract error patterns
        error_patterns = set()
        for entry in entries[:50]:  # Sample first 50
            # Remove timestamps and specific values
            pattern = re.sub(r'\d{4}-\d{2}-\d{2}', 'DATE', entry)
            pattern = re.sub(r'\d{2}:\d{2}:\d{2}', 'TIME', pattern)
            pattern = re.sub(r'\b\d+\b', 'NUM', pattern)
            pattern = re.sub(r'0x[0-9a-fA-F]+', 'HEX', pattern)

            error_patterns.add(pattern[:100])  # Limit pattern length

        patterns.extend(list(error_patterns)[:10])  # Top 10 patterns

        return patterns

# ==================== User Documentation Node ====================

class UserDocsNode(KnowledgeSource):
    """
    Knowledge node for user documentation and guides
    """

    def __init__(
        self,
        pipeline: LangGraphRAGPipeline,
        docs_path: str = "./docs"
    ):
        """
        Initialize user docs node
        
        Args:
            pipeline: RAG pipeline instance
            docs_path: Path to documentation
        """
        super().__init__(KnowledgeNodeType.USER_DOCS, pipeline)
        self.docs_path = Path(docs_path)

    async def index(self) -> int:
        """Index user documentation"""
        documents = []

        # Index markdown files
        for md_file in self.docs_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')

                # Extract sections
                sections = self._extract_sections(content)

                for section_title, section_content in sections.items():
                    doc = Document(
                        page_content=section_content,
                        metadata={
                            "source": str(md_file.relative_to(self.docs_path)),
                            "section": section_title,
                            "doc_type": "user_guide"
                        }
                    )
                    documents.append(doc)

            except Exception as e:
                logger.warning(f"Failed to index doc {md_file}: {e}")

        # Add to pipeline
        if documents:
            doc_ids = await self.pipeline.add_documents(documents, self.node_type)
            self.indexed_count = len(doc_ids)
            logger.info(f"Indexed {self.indexed_count} documentation sections")

        return self.indexed_count

    def _extract_sections(self, content: str) -> dict[str, str]:
        """Extract sections from markdown content"""
        sections = {}

        # Split by headers
        parts = re.split(r'^(#+\s+.+)$', content, flags=re.MULTILINE)

        current_header = "Introduction"
        current_content = []

        for part in parts:
            if re.match(r'^#+\s+', part):
                # Save previous section
                if current_content:
                    sections[current_header] = "\n".join(current_content)

                # Start new section
                current_header = part.strip("# \n")
                current_content = []
            else:
                current_content.append(part)

        # Save last section
        if current_content:
            sections[current_header] = "\n".join(current_content)

        return sections

# ==================== Policy Node ====================

class PolicyNode(KnowledgeSource):
    """
    Knowledge node for security policies and compliance rules
    """

    def __init__(
        self,
        pipeline: LangGraphRAGPipeline,
        policy_files: Optional[list[str]] = None
    ):
        """
        Initialize policy node
        
        Args:
            pipeline: RAG pipeline instance
            policy_files: List of policy file paths
        """
        super().__init__(KnowledgeNodeType.POLICIES, pipeline)
        self.policy_files = policy_files or [
            "./policies/*.yaml",
            "./policies/*.json",
            "./security/*.md"
        ]

    async def index(self) -> int:
        """Index policy documents"""
        documents = []

        for pattern in self.policy_files:
            for policy_path in Path(".").glob(pattern):
                try:
                    content = policy_path.read_text(encoding='utf-8')

                    # Parse based on file type
                    if policy_path.suffix in ['.yaml', '.yml']:
                        import yaml
                        policy_data = yaml.safe_load(content)
                        content = json.dumps(policy_data, indent=2)
                    elif policy_path.suffix == '.json':
                        policy_data = json.loads(content)
                        content = json.dumps(policy_data, indent=2)

                    # Create document
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": str(policy_path.name),
                            "policy_type": self._determine_policy_type(policy_path.name),
                            "file_type": policy_path.suffix
                        }
                    )
                    documents.append(doc)

                except Exception as e:
                    logger.warning(f"Failed to index policy {policy_path}: {e}")

        # Add to pipeline
        if documents:
            doc_ids = await self.pipeline.add_documents(documents, self.node_type)
            self.indexed_count = len(doc_ids)
            logger.info(f"Indexed {self.indexed_count} policy documents")

        return self.indexed_count

    def _determine_policy_type(self, filename: str) -> str:
        """Determine policy type from filename"""
        filename_lower = filename.lower()

        if "security" in filename_lower:
            return "security"
        elif "compliance" in filename_lower:
            return "compliance"
        elif "access" in filename_lower:
            return "access_control"
        elif "data" in filename_lower:
            return "data_governance"
        else:
            return "general"

# ==================== Knowledge Graph Manager ====================

class KnowledgeGraphManager:
    """
    Manages all knowledge nodes and provides unified access
    """

    def __init__(self, pipeline: LangGraphRAGPipeline):
        """
        Initialize knowledge graph manager
        
        Args:
            pipeline: RAG pipeline instance
        """
        self.pipeline = pipeline
        self.nodes: dict[KnowledgeNodeType, KnowledgeSource] = {}
        self.indexed = False

        logger.info("Knowledge Graph Manager initialized")

    def register_node(self, node: KnowledgeSource):
        """
        Register a knowledge node
        
        Args:
            node: Knowledge source to register
        """
        self.nodes[node.node_type] = node
        logger.info(f"Registered knowledge node: {node.node_type.value}")

    async def index_all(self) -> dict[str, int]:
        """
        Index all registered nodes
        
        Returns:
            Dictionary of node types and document counts
        """
        results = {}

        for node_type, node in self.nodes.items():
            try:
                count = await node.index()
                results[node_type.value] = count
                logger.info(f"Indexed {count} documents from {node_type.value}")
            except Exception as e:
                logger.error(f"Failed to index {node_type.value}: {e}")
                results[node_type.value] = 0

        self.indexed = True
        return results

    async def update_all(self) -> dict[str, int]:
        """
        Update all registered nodes
        
        Returns:
            Dictionary of node types and updated document counts
        """
        results = {}

        for node_type, node in self.nodes.items():
            if hasattr(node, 'update'):
                try:
                    count = await node.update()
                    results[node_type.value] = count
                except Exception as e:
                    logger.error(f"Failed to update {node_type.value}: {e}")
                    results[node_type.value] = 0

        return results

    async def query_specific(
        self,
        query: str,
        node_types: list[KnowledgeNodeType],
        k: int = 5
    ) -> dict[str, list[Document]]:
        """
        Query specific knowledge nodes
        
        Args:
            query: Query text
            node_types: Types of nodes to query
            k: Number of documents per node
            
        Returns:
            Dictionary of node types and retrieved documents
        """
        results = {}

        for node_type in node_types:
            if node_type in self.nodes:
                docs = await self.pipeline.retrieve_by_type(query, node_type, k)
                results[node_type.value] = docs

        return results

    def get_statistics(self) -> dict[str, Any]:
        """Get knowledge graph statistics"""
        stats = {
            "indexed": self.indexed,
            "node_count": len(self.nodes),
            "nodes": {}
        }

        for node_type, node in self.nodes.items():
            stats["nodes"][node_type.value] = {
                "indexed_count": node.indexed_count,
                "type": node.__class__.__name__
            }

        stats["pipeline"] = self.pipeline.get_statistics()

        return stats

# ==================== Default Knowledge Graph Setup ====================

async def setup_default_knowledge_graph(
    pipeline: LangGraphRAGPipeline,
    root_path: str = "."
) -> KnowledgeGraphManager:
    """
    Set up default knowledge graph with standard nodes
    
    Args:
        pipeline: RAG pipeline instance
        root_path: Root path for indexing
        
    Returns:
        Configured knowledge graph manager
    """
    manager = KnowledgeGraphManager(pipeline)

    # Register codebase node
    codebase_node = CodebaseNode(
        pipeline,
        root_path=root_path,
        file_patterns=["*.py", "*.md", "*.yaml"]
    )
    manager.register_node(codebase_node)

    # Register system logs node
    logs_node = SystemLogsNode(
        pipeline,
        log_paths=["./logs/*.log"],
        max_lines=500
    )
    manager.register_node(logs_node)

    # Register user docs node
    docs_node = UserDocsNode(
        pipeline,
        docs_path=f"{root_path}/docs"
    )
    manager.register_node(docs_node)

    # Register policy node
    policy_node = PolicyNode(
        pipeline,
        policy_files=[
            f"{root_path}/policies/*.yaml",
            f"{root_path}/security/*.md"
        ]
    )
    manager.register_node(policy_node)

    # Index all nodes
    await manager.index_all()

    return manager
