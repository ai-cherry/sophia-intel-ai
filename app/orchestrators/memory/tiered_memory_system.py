"""
Tiered Contextual Memory System for AI Orchestrators
=====================================================
Implements a hierarchical memory system with multiple tiers for
context-aware AI interactions.
"""

import json
import logging
import pickle
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import redis.asyncio as aioredis

from app.orchestrators.memory.memory_config import memory_config

logger = logging.getLogger(__name__)


class MemoryTier(Enum):
    """Memory hierarchy levels"""

    WORKING = "working"  # Current conversation (5-10 messages)
    SESSION = "session"  # Current session context (full conversation)
    PROJECT = "project"  # Project-specific knowledge (persistent)
    GLOBAL = "global"  # Cross-project patterns and learnings
    SEMANTIC = "semantic"  # Vector-indexed knowledge base


@dataclass
class MemoryEntry:
    """Base memory entry structure"""

    id: str
    content: Any
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    tier: MemoryTier = MemoryTier.WORKING
    ttl: Optional[int] = None  # Time to live in seconds


@dataclass
class ConversationContext:
    """Current conversation context"""

    session_id: str
    user_id: Optional[str] = None
    project_path: Optional[str] = None
    active_files: list[str] = field(default_factory=list)
    active_functions: list[str] = field(default_factory=list)
    current_task: Optional[str] = None
    entities: dict[str, Any] = field(default_factory=dict)


class WorkingMemory:
    """
    Immediate context for current interaction
    - Last 5-10 messages
    - Current task context
    - Active variables/entities
    """

    def __init__(self, max_messages: int = 10):
        self.message_buffer = deque(maxlen=max_messages)
        self.entities: dict[str, Any] = {}
        self.current_task: Optional[str] = None
        self.active_files: list[str] = []
        self.active_functions: list[str] = []
        self.context_switches: int = 0

    def add_message(self, role: str, content: str, metadata: Optional[dict] = None):
        """Add a message to working memory"""
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self.message_buffer.append(entry)
        self._extract_entities(content)

    def _extract_entities(self, content: str):
        """Extract named entities from content"""
        # Simple extraction - can be enhanced with NLP
        import re

        # Extract file paths
        file_pattern = r"(?:[./][\w/.-]+\.(?:py|js|ts|jsx|tsx|md|json|yaml|yml))"
        files = re.findall(file_pattern, content)
        self.active_files.extend(files)
        self.active_files = list(set(self.active_files[-10:]))  # Keep last 10 unique

        # Extract function/class names
        func_pattern = r"(?:def|class|function|const|let|var)\s+(\w+)"
        functions = re.findall(func_pattern, content)
        self.active_functions.extend(functions)
        self.active_functions = list(set(self.active_functions[-10:]))

    def set_task(self, task: str):
        """Set current task context"""
        if self.current_task and self.current_task != task:
            self.context_switches += 1
        self.current_task = task

    def get_recent_context(self, n: int = 5) -> list[dict]:
        """Get recent messages for context"""
        return list(self.message_buffer)[-n:]

    def clear(self):
        """Clear working memory"""
        self.message_buffer.clear()
        self.entities.clear()
        self.current_task = None
        self.active_files.clear()
        self.active_functions.clear()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "messages": list(self.message_buffer),
            "entities": self.entities,
            "current_task": self.current_task,
            "active_files": self.active_files,
            "active_functions": self.active_functions,
            "context_switches": self.context_switches,
        }


class SessionMemory:
    """
    Full conversation history for current session
    - Complete message history
    - Decisions made
    - Code changes tracked
    - User preferences learned
    """

    def __init__(self, session_id: str, redis_url: Optional[str] = None):
        self.session_id = session_id
        self.start_time = datetime.now()
        self.messages: list[dict] = []
        self.decisions: list[dict] = []
        self.code_changes: list[dict] = []
        self.user_patterns: dict[str, Any] = {}
        # Use config or provided URL
        self.redis_url = redis_url or memory_config.redis_url
        self.redis_client: Optional[aioredis.Redis] = None
        self._initialized = False
        self.is_cloud = memory_config.is_cloud_deployment()

    async def initialize(self):
        """Initialize Redis connection"""
        if not self._initialized:
            self.redis_client = await aioredis.from_url(self.redis_url)
            await self._load_from_redis()
            self._initialized = True

    async def _load_from_redis(self):
        """Load session from Redis if exists"""
        if not self.redis_client:
            return

        key = f"session:{self.session_id}"
        try:
            data = await self.redis_client.get(key)
            if data:
                session_data = json.loads(data)
                self.messages = session_data.get("messages", [])
                self.decisions = session_data.get("decisions", [])
                self.code_changes = session_data.get("code_changes", [])
                self.user_patterns = session_data.get("user_patterns", {})
                self.start_time = datetime.fromisoformat(session_data.get("start_time"))
                logger.info(f"Loaded session {self.session_id} from Redis")
        except Exception as e:
            logger.error(f"Error loading session from Redis: {e}")

    async def save_to_redis(self):
        """Persist session to Redis"""
        if not self.redis_client:
            return

        key = f"session:{self.session_id}"
        session_data = {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "messages": self.messages,
            "decisions": self.decisions,
            "code_changes": self.code_changes,
            "user_patterns": self.user_patterns,
        }

        try:
            # Set with 24 hour TTL
            await self.redis_client.setex(
                key, 86400, json.dumps(session_data)  # 24 hours in seconds
            )
            logger.debug(f"Saved session {self.session_id} to Redis")
        except Exception as e:
            logger.error(f"Error saving session to Redis: {e}")

    def add_message(self, role: str, content: str, metadata: Optional[dict] = None):
        """Add message to session history"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self.messages.append(message)
        self._learn_patterns(message)

    def add_decision(self, decision: str, context: dict, outcome: Optional[str] = None):
        """Track decision made during session"""
        self.decisions.append(
            {
                "decision": decision,
                "context": context,
                "outcome": outcome,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def add_code_change(self, file_path: str, change_type: str, details: dict):
        """Track code modifications"""
        self.code_changes.append(
            {
                "file_path": file_path,
                "change_type": change_type,  # create, modify, delete
                "details": details,
                "timestamp": datetime.now().isoformat(),
            }
        )

    def _learn_patterns(self, message: dict):
        """Extract user patterns from messages"""
        content = message.get("content", "").lower()

        # Track command preferences
        if message.get("role") == "user":
            # Track time patterns
            hour = datetime.now().hour
            time_category = (
                "morning" if hour < 12 else "afternoon" if hour < 18 else "evening"
            )

            if "time_preferences" not in self.user_patterns:
                self.user_patterns["time_preferences"] = {}

            self.user_patterns["time_preferences"][time_category] = (
                self.user_patterns["time_preferences"].get(time_category, 0) + 1
            )

            # Track command style
            if content.startswith(("please", "could you", "can you")):
                self.user_patterns["polite_style"] = (
                    self.user_patterns.get("polite_style", 0) + 1
                )
            elif len(content.split()) <= 3:
                self.user_patterns["concise_style"] = (
                    self.user_patterns.get("concise_style", 0) + 1
                )

    def get_session_summary(self) -> dict:
        """Get session summary"""
        duration = datetime.now() - self.start_time
        return {
            "session_id": self.session_id,
            "duration_minutes": duration.total_seconds() / 60,
            "message_count": len(self.messages),
            "decision_count": len(self.decisions),
            "code_changes_count": len(self.code_changes),
            "user_patterns": self.user_patterns,
            "start_time": self.start_time.isoformat(),
        }

    async def cleanup(self):
        """Clean up resources"""
        await self.save_to_redis()
        if self.redis_client:
            await self.redis_client.close()


class ProjectMemory:
    """
    Persistent project-specific knowledge
    - Codebase structure understanding
    - Architecture decisions
    - Common issues and solutions
    - Team conventions
    """

    def __init__(self, project_path: str, cache_dir: Optional[str] = None):
        self.project_path = Path(project_path)
        self.cache_dir = Path(cache_dir or f"{project_path}/.ai_memory")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.architecture_map: dict[str, Any] = {}
        self.convention_patterns: dict[str, Any] = {}
        self.known_issues: dict[str, Any] = {}
        self.dependency_graph: dict[str, list[str]] = {}
        self.frequent_files: list[str] = []
        self.tech_stack: dict[str, Any] = {}

        self._load_from_cache()

    def _load_from_cache(self):
        """Load project memory from cache"""
        cache_file = self.cache_dir / "project_memory.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, "rb") as f:
                    data = pickle.load(f)
                    self.architecture_map = data.get("architecture_map", {})
                    self.convention_patterns = data.get("convention_patterns", {})
                    self.known_issues = data.get("known_issues", {})
                    self.dependency_graph = data.get("dependency_graph", {})
                    self.frequent_files = data.get("frequent_files", [])
                    self.tech_stack = data.get("tech_stack", {})
                logger.info(f"Loaded project memory for {self.project_path}")
            except Exception as e:
                logger.error(f"Error loading project memory: {e}")

    def save_to_cache(self):
        """Persist project memory to cache"""
        cache_file = self.cache_dir / "project_memory.pkl"
        try:
            data = {
                "architecture_map": self.architecture_map,
                "convention_patterns": self.convention_patterns,
                "known_issues": self.known_issues,
                "dependency_graph": self.dependency_graph,
                "frequent_files": self.frequent_files,
                "tech_stack": self.tech_stack,
            }
            with open(cache_file, "wb") as f:
                pickle.dump(data, f)
            logger.debug(f"Saved project memory for {self.project_path}")
        except Exception as e:
            logger.error(f"Error saving project memory: {e}")

    def update_architecture(self, module: str, info: dict):
        """Update architecture understanding"""
        self.architecture_map[module] = {
            **self.architecture_map.get(module, {}),
            **info,
            "last_updated": datetime.now().isoformat(),
        }

    def add_known_issue(
        self,
        issue_id: str,
        description: str,
        solution: Optional[str] = None,
        tags: list[str] = None,
    ):
        """Add a known issue and solution"""
        self.known_issues[issue_id] = {
            "description": description,
            "solution": solution,
            "tags": tags or [],
            "occurrences": self.known_issues.get(issue_id, {}).get("occurrences", 0)
            + 1,
            "last_seen": datetime.now().isoformat(),
        }

    def learn_convention(self, pattern_type: str, pattern: str, examples: list[str]):
        """Learn coding conventions from examples"""
        if pattern_type not in self.convention_patterns:
            self.convention_patterns[pattern_type] = []

        self.convention_patterns[pattern_type].append(
            {
                "pattern": pattern,
                "examples": examples,
                "confidence": len(examples) / 10.0,  # Simple confidence metric
                "learned_at": datetime.now().isoformat(),
            }
        )

    def update_dependency_graph(self, file: str, dependencies: list[str]):
        """Update file dependency graph"""
        self.dependency_graph[file] = dependencies

    def track_file_access(self, file_path: str):
        """Track frequently accessed files"""
        if file_path not in self.frequent_files:
            self.frequent_files.append(file_path)
        # Move to front (LRU style)
        self.frequent_files.remove(file_path)
        self.frequent_files.insert(0, file_path)
        # Keep only top 100
        self.frequent_files = self.frequent_files[:100]

    def detect_tech_stack(self):
        """Auto-detect technology stack from project files"""
        tech_indicators = {
            "requirements.txt": "Python",
            "package.json": "JavaScript/TypeScript",
            "Cargo.toml": "Rust",
            "go.mod": "Go",
            "pom.xml": "Java/Maven",
            "build.gradle": "Java/Gradle",
            "Gemfile": "Ruby",
            "composer.json": "PHP",
        }

        for file, tech in tech_indicators.items():
            if (self.project_path / file).exists():
                self.tech_stack[tech] = True

        # Detect frameworks
        if (self.project_path / "package.json").exists():
            # Could parse package.json for more details
            pass

        return self.tech_stack

    def get_relevant_context(self, query: str) -> dict[str, Any]:
        """Get relevant project context for a query"""
        context = {
            "frequent_files": self.frequent_files[:10],
            "tech_stack": self.tech_stack,
            "recent_issues": [],
            "relevant_conventions": [],
        }

        # Find relevant issues
        query_lower = query.lower()
        for _issue_id, issue_data in self.known_issues.items():
            if any(tag in query_lower for tag in issue_data.get("tags", [])):
                context["recent_issues"].append(issue_data)

        # Find relevant conventions
        for pattern_type, patterns in self.convention_patterns.items():
            if pattern_type.lower() in query_lower:
                context["relevant_conventions"].extend(patterns)

        return context


class GlobalMemory:
    """
    Cross-project learnings and patterns
    - Best practices database
    - Common architectural patterns
    - Industry knowledge
    - User interaction patterns
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or "~/.ai_global_memory").expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.best_practices: dict[str, list[dict]] = {}
        self.design_patterns: dict[str, dict] = {}
        self.tech_stack_knowledge: dict[str, dict] = {}
        self.interaction_patterns: dict[str, Any] = {}
        self.success_metrics: dict[str, float] = {}

        self._load_global_knowledge()

    def _load_global_knowledge(self):
        """Load global knowledge base"""
        knowledge_file = self.storage_path / "global_knowledge.json"
        if knowledge_file.exists():
            try:
                with open(knowledge_file) as f:
                    data = json.load(f)
                    self.best_practices = data.get("best_practices", {})
                    self.design_patterns = data.get("design_patterns", {})
                    self.tech_stack_knowledge = data.get("tech_stack_knowledge", {})
                    self.interaction_patterns = data.get("interaction_patterns", {})
                    self.success_metrics = data.get("success_metrics", {})
                logger.info("Loaded global knowledge base")
            except Exception as e:
                logger.error(f"Error loading global knowledge: {e}")

    def save_global_knowledge(self):
        """Persist global knowledge"""
        knowledge_file = self.storage_path / "global_knowledge.json"
        try:
            data = {
                "best_practices": self.best_practices,
                "design_patterns": self.design_patterns,
                "tech_stack_knowledge": self.tech_stack_knowledge,
                "interaction_patterns": self.interaction_patterns,
                "success_metrics": self.success_metrics,
                "last_updated": datetime.now().isoformat(),
            }
            with open(knowledge_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug("Saved global knowledge base")
        except Exception as e:
            logger.error(f"Error saving global knowledge: {e}")

    def learn_best_practice(self, category: str, practice: dict, success_rate: float):
        """Learn a new best practice"""
        if category not in self.best_practices:
            self.best_practices[category] = []

        practice["success_rate"] = success_rate
        practice["learned_at"] = datetime.now().isoformat()
        self.best_practices[category].append(practice)

        # Keep only top 10 practices per category
        self.best_practices[category] = sorted(
            self.best_practices[category],
            key=lambda x: x.get("success_rate", 0),
            reverse=True,
        )[:10]

    def record_pattern_usage(self, pattern_name: str, context: dict, success: bool):
        """Record usage of a design pattern"""
        if pattern_name not in self.design_patterns:
            self.design_patterns[pattern_name] = {
                "usage_count": 0,
                "success_count": 0,
                "contexts": [],
            }

        self.design_patterns[pattern_name]["usage_count"] += 1
        if success:
            self.design_patterns[pattern_name]["success_count"] += 1

        self.design_patterns[pattern_name]["contexts"].append(
            {
                "context": context,
                "success": success,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Keep only last 20 contexts
        self.design_patterns[pattern_name]["contexts"] = self.design_patterns[
            pattern_name
        ]["contexts"][-20:]

    def update_tech_knowledge(self, technology: str, knowledge: dict):
        """Update technology-specific knowledge"""
        if technology not in self.tech_stack_knowledge:
            self.tech_stack_knowledge[technology] = {}

        self.tech_stack_knowledge[technology].update(knowledge)
        self.tech_stack_knowledge[technology][
            "last_updated"
        ] = datetime.now().isoformat()

    def get_recommendations(self, context: dict) -> list[dict]:
        """Get recommendations based on global knowledge"""
        recommendations = []

        # Check for relevant best practices
        for category, practices in self.best_practices.items():
            if category in str(context).lower():
                for practice in practices[:3]:  # Top 3 practices
                    if practice.get("success_rate", 0) > 0.7:
                        recommendations.append(
                            {
                                "type": "best_practice",
                                "category": category,
                                "recommendation": practice,
                                "confidence": practice.get("success_rate", 0),
                            }
                        )

        # Check for relevant design patterns
        for pattern_name, pattern_data in self.design_patterns.items():
            if pattern_data["usage_count"] > 5:
                success_rate = (
                    pattern_data["success_count"] / pattern_data["usage_count"]
                )
                if success_rate > 0.7:
                    recommendations.append(
                        {
                            "type": "design_pattern",
                            "pattern": pattern_name,
                            "success_rate": success_rate,
                            "usage_count": pattern_data["usage_count"],
                        }
                    )

        return recommendations


class MemorySystem:
    """
    Unified memory system orchestrating all tiers
    """

    def __init__(
        self,
        session_id: str,
        project_path: Optional[str] = None,
        redis_url: Optional[str] = None,
    ):
        self.session_id = session_id
        self.project_path = project_path

        # Initialize memory tiers
        self.working = WorkingMemory()
        self.session = SessionMemory(session_id, redis_url)
        self.project = ProjectMemory(project_path) if project_path else None
        self.global_memory = GlobalMemory()

        self._initialized = False

    async def initialize(self):
        """Initialize async components"""
        if not self._initialized:
            await self.session.initialize()
            self._initialized = True

    async def add_interaction(
        self, role: str, content: str, metadata: Optional[dict] = None
    ):
        """Add an interaction to memory system"""
        # Add to working memory
        self.working.add_message(role, content, metadata)

        # Add to session memory
        self.session.add_message(role, content, metadata)

        # Track file access in project memory
        if self.project:
            for file in self.working.active_files:
                self.project.track_file_access(file)

        # Save periodically
        if len(self.session.messages) % 10 == 0:
            await self.session.save_to_redis()
            if self.project:
                self.project.save_to_cache()

    async def get_context(
        self, query: str, include_tiers: list[MemoryTier] = None
    ) -> dict:
        """Get relevant context from specified memory tiers"""
        context = {"query": query, "timestamp": datetime.now().isoformat()}

        include_tiers = include_tiers or list(MemoryTier)

        if MemoryTier.WORKING in include_tiers:
            context["working_memory"] = self.working.to_dict()

        if MemoryTier.SESSION in include_tiers:
            context["session_summary"] = self.session.get_session_summary()
            context["recent_decisions"] = self.session.decisions[-5:]

        if MemoryTier.PROJECT in include_tiers and self.project:
            context["project_context"] = self.project.get_relevant_context(query)

        if MemoryTier.GLOBAL in include_tiers:
            context["recommendations"] = self.global_memory.get_recommendations(context)

        return context

    async def learn_from_outcome(self, action: str, outcome: dict, success: bool):
        """Learn from action outcomes"""
        # Record in session
        self.session.add_decision(action, self.working.to_dict(), str(outcome))

        # Update global knowledge
        if success:
            self.global_memory.success_metrics[action] = (
                self.global_memory.success_metrics.get(action, 0) * 0.9 + 0.1
            )
        else:
            self.global_memory.success_metrics[action] = (
                self.global_memory.success_metrics.get(action, 0) * 0.9
            )

    async def cleanup(self):
        """Clean up resources"""
        await self.session.cleanup()
        if self.project:
            self.project.save_to_cache()
        self.global_memory.save_global_knowledge()

    def get_memory_stats(self) -> dict:
        """Get memory system statistics"""
        return {
            "working_memory": {
                "message_count": len(self.working.message_buffer),
                "active_files": len(self.working.active_files),
                "context_switches": self.working.context_switches,
            },
            "session_memory": self.session.get_session_summary(),
            "project_memory": {
                "architecture_modules": (
                    len(self.project.architecture_map) if self.project else 0
                ),
                "known_issues": len(self.project.known_issues) if self.project else 0,
                "conventions": (
                    len(self.project.convention_patterns) if self.project else 0
                ),
            },
            "global_memory": {
                "best_practices": sum(
                    len(p) for p in self.global_memory.best_practices.values()
                ),
                "design_patterns": len(self.global_memory.design_patterns),
                "tech_knowledge": len(self.global_memory.tech_stack_knowledge),
            },
        }
