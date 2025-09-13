"""
Core Prompt Library with Git-like versioning system
Advanced prompt management, version control, and A/B testing framework
"""
import difflib
import hashlib
import json
import logging
import time
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional
logger = logging.getLogger(__name__)
class PromptType(Enum):
    """Types of prompts in the system"""
    MYTHOLOGY_AGENT = "mythology_agent"
    TECHNICAL_AGENT = "technical_agent"
    SYSTEM_PROMPT = "system_prompt"
    TASK_PROMPT = "task_prompt"
    CONTEXT_PROMPT = "context_prompt"
class PromptStatus(Enum):
    """Status of prompt versions"""
    DRAFT = "draft"
    ACTIVE = "active"
    TESTING = "testing"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
class MergeStrategy(Enum):
    """Strategies for merging prompt branches"""
    FAST_FORWARD = "fast_forward"
    THREE_WAY = "three_way"
    MANUAL = "manual"
@dataclass
class PromptMetadata:
    """Metadata associated with prompts"""
    domain: str  # sophia, , etc.
    agent_name: Optional[str] = None
    task_type: Optional[str] = None
    business_context: Optional[list[str]] = None
    performance_tags: Optional[list[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author: Optional[str] = None
@dataclass
class PromptVersion:
    """A single version of a prompt"""
    id: str
    prompt_id: str
    branch: str
    version: str
    content: str
    metadata: PromptMetadata
    parent_version: Optional[str] = None
    commit_message: Optional[str] = None
    status: PromptStatus = PromptStatus.DRAFT
    created_at: Optional[datetime] = None
    performance_metrics: Optional[dict[str, float]] = None
    a_b_test_data: Optional[dict[str, Any]] = None
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.a_b_test_data is None:
            self.a_b_test_data = {}
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage"""
        return asdict(self)
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PromptVersion":
        """Create from dictionary"""
        # Handle datetime conversion
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        # Handle metadata conversion
        if "metadata" in data and isinstance(data["metadata"], dict):
            data["metadata"] = PromptMetadata(**data["metadata"])
        # Handle enums
        if "status" in data and isinstance(data["status"], str):
            try:
                data["status"] = PromptStatus(data["status"])
            except ValueError:
                # Default to DRAFT if invalid status
                data["status"] = PromptStatus.DRAFT
        return cls(**data)
@dataclass
class PromptBranch:
    """A branch in the prompt version tree"""
    name: str
    base_version: str
    head_version: str
    created_at: datetime
    description: Optional[str] = None
    is_merged: bool = False
    merged_at: Optional[datetime] = None
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage"""
        return asdict(self)
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PromptBranch":
        """Create from dictionary"""
        # Handle datetime conversion
        for field in ["created_at", "merged_at"]:
            if field in data and isinstance(data[field], str):
                data[field] = (
                    datetime.fromisoformat(data[field]) if data[field] else None
                )
        return cls(**data)
@dataclass
class PromptDiff:
    """Difference between two prompt versions"""
    from_version: str
    to_version: str
    content_diff: list[str]
    metadata_diff: dict[str, Any]
    similarity_score: float
    change_summary: str
    def to_html(self) -> str:
        """Generate HTML diff for UI display"""
        return "\n".join(self.content_diff)
@dataclass
class ABTestConfig:
    """Configuration for A/B testing prompts"""
    test_id: str
    name: str
    description: str
    control_version: str
    test_versions: list[str]
    traffic_split: dict[str, float]  # version_id -> percentage
    success_metrics: list[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "active"  # active, paused, completed
    minimum_sample_size: int = 100
    statistical_significance_threshold: float = 0.95
@dataclass
class ABTestResult:
    """Results from A/B testing"""
    test_id: str
    version_id: str
    sample_size: int
    success_rate: float
    confidence_interval: tuple[float, float]
    metrics: dict[str, float]
    statistical_significance: bool
    winner: bool = False
class PromptLibrary:
    """
    Comprehensive prompt management system with Git-like versioning
    Supports branching, merging, diffing, and A/B testing
    """
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or "data/prompts")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        # In-memory storage for fast access
        self.prompts: dict[str, list[PromptVersion]] = {}
        self.branches: dict[str, list[PromptBranch]] = {}
        self.ab_tests: dict[str, ABTestConfig] = {}
        self.ab_results: dict[str, list[ABTestResult]] = {}
        # Performance tracking
        self.performance_cache: dict[str, dict[str, float]] = {}
        # Load existing data
        self._load_from_storage()
    def _generate_version_id(self, content: str, metadata: PromptMetadata) -> str:
        """Generate unique version ID based on content and metadata"""
        hash_input = f"{content}|{metadata.domain}|{metadata.agent_name}|{time.time()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:12]
    def _load_from_storage(self):
        """Load prompt data from persistent storage"""
        try:
            prompts_file = self.storage_path / "prompts.json"
            if prompts_file.exists():
                with open(prompts_file) as f:
                    data = json.load(f)
                    for prompt_id, versions in data.items():
                        self.prompts[prompt_id] = [
                            PromptVersion.from_dict(v) for v in versions
                        ]
            branches_file = self.storage_path / "branches.json"
            if branches_file.exists():
                with open(branches_file) as f:
                    data = json.load(f)
                    for prompt_id, branches in data.items():
                        self.branches[prompt_id] = [
                            PromptBranch.from_dict(b) for b in branches
                        ]
            ab_tests_file = self.storage_path / "ab_tests.json"
            if ab_tests_file.exists():
                with open(ab_tests_file) as f:
                    data = json.load(f)
                    self.ab_tests = {k: ABTestConfig(**v) for k, v in data.items()}
            logger.info(f"Loaded {len(self.prompts)} prompts from storage")
        except Exception as e:
            logger.error(f"Error loading from storage: {e}")
    def _save_to_storage(self):
        """Save prompt data to persistent storage"""
        try:
            # Save prompts
            prompts_data = {}
            for prompt_id, versions in self.prompts.items():
                prompts_data[prompt_id] = [v.to_dict() for v in versions]
            with open(self.storage_path / "prompts.json", "w") as f:
                json.dump(prompts_data, f, indent=2, default=str)
            # Save branches
            branches_data = {}
            for prompt_id, branches in self.branches.items():
                branches_data[prompt_id] = [b.to_dict() for b in branches]
            with open(self.storage_path / "branches.json", "w") as f:
                json.dump(branches_data, f, indent=2, default=str)
            # Save A/B tests
            ab_tests_data = {k: asdict(v) for k, v in self.ab_tests.items()}
            with open(self.storage_path / "ab_tests.json", "w") as f:
                json.dump(ab_tests_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving to storage: {e}")
    def create_prompt(
        self,
        prompt_id: str,
        content: str,
        metadata: PromptMetadata,
        branch: str = "main",
        commit_message: Optional[str] = None,
    ) -> PromptVersion:
        """Create a new prompt or add version to existing prompt"""
        version_id = self._generate_version_id(content, metadata)
        version_str = (
            "1.0.0"
            if prompt_id not in self.prompts
            else self._get_next_version(prompt_id, branch)
        )
        # Get parent version if this isn't the first version
        parent_version = None
        if prompt_id in self.prompts and self.prompts[prompt_id]:
            parent_version = self._get_latest_version(prompt_id, branch).id
        prompt_version = PromptVersion(
            id=version_id,
            prompt_id=prompt_id,
            branch=branch,
            version=version_str,
            content=content,
            metadata=metadata,
            parent_version=parent_version,
            commit_message=commit_message,
            status=PromptStatus.DRAFT,
        )
        # Add to prompts
        if prompt_id not in self.prompts:
            self.prompts[prompt_id] = []
        self.prompts[prompt_id].append(prompt_version)
        # Create or update branch
        self._update_branch(prompt_id, branch, version_id)
        self._save_to_storage()
        logger.info(f"Created prompt version {version_str} for {prompt_id}")
        return prompt_version
    def _get_next_version(self, prompt_id: str, branch: str) -> str:
        """Generate next version number for a prompt"""
        versions = [v for v in self.prompts[prompt_id] if v.branch == branch]
        if not versions:
            return "1.0.0"
        latest = max(versions, key=lambda v: v.created_at)
        version_parts = latest.version.split(".")
        patch = int(version_parts[2]) + 1
        return f"{version_parts[0]}.{version_parts[1]}.{patch}"
    def _get_latest_version(
        self, prompt_id: str, branch: str = "main"
    ) -> Optional[PromptVersion]:
        """Get the latest version of a prompt on a specific branch"""
        if prompt_id not in self.prompts:
            return None
        versions = [v for v in self.prompts[prompt_id] if v.branch == branch]
        if not versions:
            return None
        return max(versions, key=lambda v: v.created_at)
    def _update_branch(self, prompt_id: str, branch_name: str, head_version: str):
        """Update or create a branch"""
        if prompt_id not in self.branches:
            self.branches[prompt_id] = []
        # Find existing branch
        branch = None
        for b in self.branches[prompt_id]:
            if b.name == branch_name:
                branch = b
                break
        if branch:
            branch.head_version = head_version
        else:
            # Create new branch
            base_version = (
                head_version
                if branch_name == "main"
                else self._get_latest_version(prompt_id, "main").id
            )
            new_branch = PromptBranch(
                name=branch_name,
                base_version=base_version,
                head_version=head_version,
                created_at=datetime.now(timezone.utc),
            )
            self.branches[prompt_id].append(new_branch)
    def create_branch(
        self,
        prompt_id: str,
        branch_name: str,
        from_branch: str = "main",
        description: Optional[str] = None,
    ) -> PromptBranch:
        """Create a new branch from existing branch"""
        if prompt_id not in self.prompts:
            raise ValueError(f"Prompt {prompt_id} does not exist")
        # Get the head version of the source branch
        source_version = self._get_latest_version(prompt_id, from_branch)
        if not source_version:
            raise ValueError(
                f"Branch {from_branch} does not exist for prompt {prompt_id}"
            )
        # Check if branch already exists
        if prompt_id in self.branches:
            for branch in self.branches[prompt_id]:
                if branch.name == branch_name:
                    raise ValueError(f"Branch {branch_name} already exists")
        branch = PromptBranch(
            name=branch_name,
            base_version=source_version.id,
            head_version=source_version.id,
            created_at=datetime.now(timezone.utc),
            description=description,
        )
        if prompt_id not in self.branches:
            self.branches[prompt_id] = []
        self.branches[prompt_id].append(branch)
        self._save_to_storage()
        logger.info(f"Created branch {branch_name} for prompt {prompt_id}")
        return branch
    def merge_branch(
        self,
        prompt_id: str,
        from_branch: str,
        to_branch: str = "main",
        strategy: MergeStrategy = MergeStrategy.FAST_FORWARD,
        commit_message: Optional[str] = None,
    ) -> PromptVersion:
        """Merge one branch into another"""
        if prompt_id not in self.prompts:
            raise ValueError(f"Prompt {prompt_id} does not exist")
        from_version = self._get_latest_version(prompt_id, from_branch)
        to_version = self._get_latest_version(prompt_id, to_branch)
        if not from_version:
            raise ValueError(f"Branch {from_branch} does not exist")
        if not to_version and to_branch != "main":
            raise ValueError(f"Branch {to_branch} does not exist")
        if strategy == MergeStrategy.FAST_FORWARD:
            # Create new version on target branch with content from source branch
            merge_version = PromptVersion(
                id=self._generate_version_id(
                    from_version.content, from_version.metadata
                ),
                prompt_id=prompt_id,
                branch=to_branch,
                version=self._get_next_version(prompt_id, to_branch),
                content=from_version.content,
                metadata=deepcopy(from_version.metadata),
                parent_version=to_version.id if to_version else None,
                commit_message=commit_message
                or f"Merge {from_branch} into {to_branch}",
                status=PromptStatus.ACTIVE,
            )
            self.prompts[prompt_id].append(merge_version)
            self._update_branch(prompt_id, to_branch, merge_version.id)
            # Mark source branch as merged
            for branch in self.branches[prompt_id]:
                if branch.name == from_branch:
                    branch.is_merged = True
                    branch.merged_at = datetime.now(timezone.utc)
                    break
        self._save_to_storage()
        logger.info(
            f"Merged branch {from_branch} into {to_branch} for prompt {prompt_id}"
        )
        return merge_version
    def diff_versions(
        self, prompt_id: str, from_version: str, to_version: str
    ) -> PromptDiff:
        """Generate diff between two versions"""
        if prompt_id not in self.prompts:
            raise ValueError(f"Prompt {prompt_id} does not exist")
        versions = {v.id: v for v in self.prompts[prompt_id]}
        if from_version not in versions or to_version not in versions:
            raise ValueError("One or both versions do not exist")
        from_v = versions[from_version]
        to_v = versions[to_version]
        # Generate content diff
        from_lines = from_v.content.splitlines()
        to_lines = to_v.content.splitlines()
        diff_lines = list(
            difflib.unified_diff(
                from_lines,
                to_lines,
                fromfile=f"Version {from_v.version}",
                tofile=f"Version {to_v.version}",
                lineterm="",
            )
        )
        # Calculate similarity
        similarity = difflib.SequenceMatcher(None, from_v.content, to_v.content).ratio()
        # Generate metadata diff
        metadata_diff = {}
        from_meta = asdict(from_v.metadata)
        to_meta = asdict(to_v.metadata)
        for key in set(from_meta.keys()) | set(to_meta.keys()):
            if from_meta.get(key) != to_meta.get(key):
                metadata_diff[key] = {
                    "from": from_meta.get(key),
                    "to": to_meta.get(key),
                }
        # Generate change summary
        if similarity > 0.9:
            change_summary = "Minor changes"
        elif similarity > 0.7:
            change_summary = "Moderate changes"
        elif similarity > 0.4:
            change_summary = "Major changes"
        else:
            change_summary = "Complete rewrite"
        return PromptDiff(
            from_version=from_version,
            to_version=to_version,
            content_diff=diff_lines,
            metadata_diff=metadata_diff,
            similarity_score=similarity,
            change_summary=change_summary,
        )
    def get_prompt_history(
        self, prompt_id: str, branch: Optional[str] = None
    ) -> list[PromptVersion]:
        """Get version history for a prompt"""
        if prompt_id not in self.prompts:
            return []
        versions = self.prompts[prompt_id]
        if branch:
            versions = [v for v in versions if v.branch == branch]
        return sorted(versions, key=lambda v: v.created_at, reverse=True)
    def get_branches(self, prompt_id: str) -> list[PromptBranch]:
        """Get all branches for a prompt"""
        if prompt_id not in self.branches:
            return []
        return self.branches[prompt_id]
    def search_prompts(
        self,
        query: str = "",
        domain: Optional[str] = None,
        agent_name: Optional[str] = None,
        prompt_type: Optional[PromptType] = None,
        tags: Optional[list[str]] = None,
    ) -> list[PromptVersion]:
        """Search prompts with various filters"""
        results = []
        for _prompt_id, versions in self.prompts.items():
            for version in versions:
                # Apply filters
                if domain and version.metadata.domain != domain:
                    continue
                if agent_name and version.metadata.agent_name != agent_name:
                    continue
                if tags and not any(
                    tag in (version.metadata.performance_tags or []) for tag in tags
                ):
                    continue
                # Text search
                if query:
                    searchable_text = f"{version.content} {version.metadata.domain} {version.metadata.agent_name}"
                    if query.lower() not in searchable_text.lower():
                        continue
                results.append(version)
        return sorted(results, key=lambda v: v.created_at, reverse=True)
    def start_ab_test(self, config: ABTestConfig) -> str:
        """Start an A/B test for prompt versions"""
        # Validate test configuration
        if sum(config.traffic_split.values()) != 1.0:
            raise ValueError("Traffic split must sum to 1.0")
        # Ensure all versions exist
        for version_id in [config.control_version] + config.test_versions:
            found = False
            for versions in self.prompts.values():
                if any(v.id == version_id for v in versions):
                    found = True
                    break
            if not found:
                raise ValueError(f"Version {version_id} does not exist")
        self.ab_tests[config.test_id] = config
        self.ab_results[config.test_id] = []
        self._save_to_storage()
        logger.info(f"Started A/B test {config.test_id}")
        return config.test_id
    def record_ab_test_result(
        self,
        test_id: str,
        version_id: str,
        success: bool,
        metrics: Optional[dict[str, float]] = None,
    ):
        """Record a single result for an A/B test"""
        if test_id not in self.ab_tests:
            raise ValueError(f"A/B test {test_id} does not exist")
        # Update results (simplified - in production would use proper statistical tracking)
        if test_id not in self.ab_results:
            self.ab_results[test_id] = []
        # For now, just store the result - in production would implement proper statistical analysis
        result_data = {
            "version_id": version_id,
            "success": success,
            "metrics": metrics or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.ab_results[test_id].append(result_data)
    def get_ab_test_results(self, test_id: str) -> dict[str, ABTestResult]:
        """Get current results for an A/B test"""
        if test_id not in self.ab_tests:
            raise ValueError(f"A/B test {test_id} does not exist")
        config = self.ab_tests[test_id]
        results = {}
        # Calculate results for each version (simplified implementation)
        for version_id in [config.control_version] + config.test_versions:
            version_results = [
                r
                for r in self.ab_results.get(test_id, [])
                if r["version_id"] == version_id
            ]
            if version_results:
                sample_size = len(version_results)
                success_count = sum(1 for r in version_results if r["success"])
                success_rate = success_count / sample_size if sample_size > 0 else 0.0
                # Simplified confidence interval calculation
                confidence_interval = (
                    max(0, success_rate - 0.1),
                    min(1, success_rate + 0.1),
                )
                results[version_id] = ABTestResult(
                    test_id=test_id,
                    version_id=version_id,
                    sample_size=sample_size,
                    success_rate=success_rate,
                    confidence_interval=confidence_interval,
                    metrics={},
                    statistical_significance=sample_size >= config.minimum_sample_size,
                )
        return results
    def update_performance_metrics(self, version_id: str, metrics: dict[str, float]):
        """Update performance metrics for a prompt version"""
        # Find the version and update its metrics
        for versions in self.prompts.values():
            for version in versions:
                if version.id == version_id:
                    if version.performance_metrics is None:
                        version.performance_metrics = {}
                    version.performance_metrics.update(metrics)
                    self._save_to_storage()
                    return
        raise ValueError(f"Version {version_id} not found")
    def get_performance_leaderboard(
        self,
        domain: Optional[str] = None,
        metric: str = "success_rate",
        limit: int = 10,
    ) -> list[tuple[PromptVersion, float]]:
        """Get top performing prompts by metric"""
        candidates = []
        for versions in self.prompts.values():
            for version in versions:
                if domain and version.metadata.domain != domain:
                    continue
                if (
                    version.performance_metrics
                    and metric in version.performance_metrics
                ):
                    candidates.append((version, version.performance_metrics[metric]))
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:limit]
    def export_prompts(self, prompt_ids: Optional[list[str]] = None) -> dict[str, Any]:
        """Export prompts to a portable format"""
        export_data = {
            "prompts": {},
            "branches": {},
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0",
        }
        prompts_to_export = prompt_ids if prompt_ids else list(self.prompts.keys())
        for prompt_id in prompts_to_export:
            if prompt_id in self.prompts:
                export_data["prompts"][prompt_id] = [
                    v.to_dict() for v in self.prompts[prompt_id]
                ]
            if prompt_id in self.branches:
                export_data["branches"][prompt_id] = [
                    b.to_dict() for b in self.branches[prompt_id]
                ]
        return export_data
    def import_prompts(self, import_data: dict[str, Any], overwrite: bool = False):
        """Import prompts from exported data"""
        for prompt_id, versions_data in import_data.get("prompts", {}).items():
            if prompt_id in self.prompts and not overwrite:
                logger.warning(f"Prompt {prompt_id} already exists, skipping")
                continue
            self.prompts[prompt_id] = [
                PromptVersion.from_dict(v) for v in versions_data
            ]
        for prompt_id, branches_data in import_data.get("branches", {}).items():
            if prompt_id in self.branches and not overwrite:
                continue
            self.branches[prompt_id] = [
                PromptBranch.from_dict(b) for b in branches_data
            ]
        self._save_to_storage()
        logger.info(f"Imported {len(import_data.get('prompts', {}))} prompts")
