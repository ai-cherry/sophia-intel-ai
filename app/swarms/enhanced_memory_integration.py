"""
Enhanced Swarm Memory Integration with Auto-Tagging
Implements automatic metadata extraction and tagging for swarm memories
Following AGNO and MCP conventions
"""

import hashlib
import logging
import os
import re
from datetime import datetime
from typing import Any

import aiohttp

from app.config.env_loader import get_env_config
from app.core.circuit_breaker import with_circuit_breaker
from app.memory.supermemory_mcp import MemoryType

logger = logging.getLogger(__name__)


class AutoTagExtractor:
    """Automatic tag extraction from content and context"""

    @staticmethod
    def extract_code_patterns(content: str) -> list[str]:
        """Extract programming patterns from code content"""
        tags = []

        # Language detection
        if "def " in content or "import " in content:
            tags.append("lang:python")
        elif "function " in content or "const " in content:
            tags.append("lang:javascript")
        elif "public class" in content or "private " in content:
            tags.append("lang:java")

        # Pattern detection
        patterns = {
            r"async\s+def": "pattern:async",
            r"@\w+": "pattern:decorator",
            r"class\s+\w+": "pattern:class",
            r"try:.*except": "pattern:error_handling",
            r"with\s+\w+": "pattern:context_manager",
            r"yield\s+": "pattern:generator",
            r"lambda\s+": "pattern:lambda",
        }

        for pattern, tag in patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                tags.append(tag)

        return tags

    @staticmethod
    def extract_semantic_tags(content: str) -> list[str]:
        """Extract semantic meaning from content"""
        tags = []

        # Keywords indicating specific domains
        domains = {
            "memory": ["memory", "store", "retrieve", "cache"],
            "api": ["endpoint", "request", "response", "http"],
            "database": ["query", "insert", "update", "delete", "sql"],
            "ai": ["model", "embedding", "llm", "agent", "swarm"],
            "testing": ["test", "assert", "mock", "fixture"],
            "security": ["auth", "token", "encrypt", "password"],
        }

        content_lower = content.lower()
        for domain, keywords in domains.items():
            if any(keyword in content_lower for keyword in keywords):
                tags.append(f"domain:{domain}")

        return tags

    @staticmethod
    def extract_metadata_tags(metadata: dict[str, Any]) -> list[str]:
        """Extract tags from metadata structure"""
        tags = []

        # Extract from execution context
        if metadata:
            # Performance metrics
            if 'execution_time' in metadata:
                exec_time = metadata['execution_time']
                if exec_time < 1:
                    tags.append("perf:fast")
                elif exec_time < 5:
                    tags.append("perf:normal")
                else:
                    tags.append("perf:slow")

            # Error states
            if metadata.get('error'):
                tags.append("status:error")
                error_type = metadata.get('error_type', 'unknown')
                tags.append(f"error:{error_type}")

            # Success metrics
            if 'success_rate' in metadata:
                rate = metadata['success_rate']
                if rate >= 0.95:
                    tags.append("quality:high")
                elif rate >= 0.8:
                    tags.append("quality:medium")
                else:
                    tags.append("quality:low")

        return tags


class EnhancedSwarmMemoryClient:
    """
    Enhanced memory client with automatic tagging and metadata extraction
    """

    def __init__(self, swarm_type: str, swarm_id: str):
        self.swarm_type = swarm_type
        self.swarm_id = swarm_id
        self.config = get_env_config()
        self.mcp_server_url = self.config.mcp_server_url
        self.session: aiohttp.ClientSession | None = None
        self.tag_extractor = AutoTagExtractor()
        self.context_stack = []  # Track execution context

    def push_context(self, context: dict[str, Any]):
        """Push execution context for auto-tagging"""
        self.context_stack.append(context)

    def pop_context(self) -> dict[str, Any] | None:
        """Pop execution context"""
        return self.context_stack.pop() if self.context_stack else None

    def get_current_context(self) -> dict[str, Any]:
        """Get merged current context"""
        merged = {}
        for context in self.context_stack:
            merged.update(context)
        return merged

    async def store_memory(
        self,
        topic: str,
        content: str,
        memory_type: MemoryType = MemoryType.EPISODIC,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        auto_tag: bool = True,
        context_aware: bool = True
    ) -> dict[str, Any]:
        """
        Store memory with automatic tagging and context awareness
        
        Args:
            topic: Memory topic
            content: Memory content
            memory_type: Type of memory
            tags: Manual tags
            metadata: Additional metadata
            auto_tag: Enable automatic tag extraction
            context_aware: Use execution context for tagging
        """

        # Merge with current context if enabled
        if context_aware:
            current_context = self.get_current_context()
            metadata = {**current_context, **(metadata or {})}

        # Initialize tags list
        tags_list = list(tags or [])

        # Add base tags
        tags_list.extend([
            self.swarm_type,
            "swarm_memory",
            f"swarm_id:{self.swarm_id}",
            f"memory_type:{memory_type.value}"
        ])

        # Auto-tag extraction
        if auto_tag:
            # Extract from content
            tags_list.extend(self.tag_extractor.extract_code_patterns(content))
            tags_list.extend(self.tag_extractor.extract_semantic_tags(content))

            # Extract from metadata
            if metadata:
                tags_list.extend(self.tag_extractor.extract_metadata_tags(metadata))

        # Process required metadata fields
        if metadata:
            # Required fields with hierarchical tagging
            field_processors = {
                'task_id': lambda v: [f"task:{v}", f"task_hash:{hashlib.md5(v.encode()).hexdigest()[:8]}"],
                'agent_role': lambda v: [f"role:{v}", f"team:{metadata.get('team', 'default')}"],
                'repo_path': lambda v: [f"repo:{os.path.basename(v)}", "vcs:git"],
                'file_path': lambda v: self._process_file_path(v),
                'execution_pattern': lambda v: [f"pattern:{v}", f"strategy:{metadata.get('strategy', 'default')}"],
                'model_used': lambda v: [f"model:{v}", f"provider:{v.split('/')[0] if '/' in v else 'unknown'}"]
            }

            for field, processor in field_processors.items():
                if field in metadata:
                    tags_list.extend(processor(str(metadata[field])))

        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in tags_list:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        # Create memory entry
        entry_data = {
            "topic": topic,
            "content": content,
            "source": f"swarm_{self.swarm_type}_{self.swarm_id}",
            "tags": unique_tags,
            "memory_type": memory_type.value,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
            "swarm_context": {
                "swarm_type": self.swarm_type,
                "swarm_id": self.swarm_id,
                "context_depth": len(self.context_stack)
            }
        }

        # Store via MCP server
        return await self._store_to_mcp(entry_data)

    def _process_file_path(self, file_path: str) -> list[str]:
        """Process file path into hierarchical tags"""
        tags = []

        # Basic file info
        basename = os.path.basename(file_path)
        dirname = os.path.dirname(file_path)
        ext = os.path.splitext(file_path)[1]

        tags.append(f"file:{basename}")

        if ext:
            tags.append(f"ext:{ext}")
            # Language mapping
            lang_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.java': 'java',
                '.go': 'go',
                '.rs': 'rust'
            }
            if ext in lang_map:
                tags.append(f"lang:{lang_map[ext]}")

        # Directory hierarchy
        if dirname:
            parts = dirname.split(os.sep)
            if parts:
                tags.append(f"module:{parts[-1]}")
                if len(parts) > 1:
                    tags.append(f"package:{parts[-2]}")

        return tags

    @with_circuit_breaker("mcp_server")
    async def _store_to_mcp(self, entry_data: dict[str, Any]) -> dict[str, Any]:
        """Store entry to MCP server with circuit breaker"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.post(
                f"{self.mcp_server_url}/memory/store",
                json=entry_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Stored memory with {len(entry_data['tags'])} tags")
                    return result
                else:
                    error = await response.text()
                    logger.error(f"Failed to store memory: {error}")
                    return {"error": error, "status": response.status}
        except Exception as e:
            logger.error(f"MCP storage error: {e}")
            return {"error": str(e)}

    async def search_memories(
        self,
        query: str,
        tags: list[str] | None = None,
        limit: int = 10,
        memory_type: MemoryType | None = None
    ) -> list[dict[str, Any]]:
        """Search memories with tag filtering"""
        search_params = {
            "query": query,
            "limit": limit,
            "filters": {}
        }

        # Add tag filters
        if tags:
            search_params["filters"]["tags"] = tags

        # Add memory type filter
        if memory_type:
            search_params["filters"]["memory_type"] = memory_type.value

        # Add swarm context
        search_params["filters"]["swarm_type"] = self.swarm_type

        try:
            async with self.session.post(
                f"{self.mcp_server_url}/memory/search",
                json=search_params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Search failed: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []


# Helper functions for orchestrator integration
def create_swarm_context(
    task_id: str,
    agent_role: str,
    repo_path: str,
    file_path: str | None = None,
    **kwargs
) -> dict[str, Any]:
    """Create standard swarm execution context"""
    context = {
        "task_id": task_id,
        "agent_role": agent_role,
        "repo_path": repo_path,
        "timestamp": datetime.utcnow().isoformat()
    }

    if file_path:
        context["file_path"] = file_path

    # Add any additional context
    context.update(kwargs)

    return context


async def auto_tag_and_store(
    memory_client: EnhancedSwarmMemoryClient,
    content: str,
    topic: str,
    execution_context: dict[str, Any]
) -> dict[str, Any]:
    """Helper to auto-tag and store with context"""

    # Push context
    memory_client.push_context(execution_context)

    try:
        # Store with auto-tagging
        result = await memory_client.store_memory(
            topic=topic,
            content=content,
            auto_tag=True,
            context_aware=True
        )
        return result
    finally:
        # Always pop context
        memory_client.pop_context()
