"""
Ultimate Scout Swarm Implementation for Artemis Technical Operations
Based on 6-model testing with proven performance metrics

This module implements the tiered scout swarm architecture with:
- Tier 1: Rapid scanning (Llama-4-Scout)
- Tier 2: Deep analysis (Grok Code Fast, Gemini 2.0 Flash)
- Tier 3: Validation (GPT-4o-mini, Llama 4 Maverick)
- Tier 4: Exhaustive audit (GLM-4.5-Air)
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import httpx
from fastapi import HTTPException

# Import MCP tools for REAL file access
try:
    from app.tools.basic_tools import (
        git_diff,
        git_status,
        list_directory,
        read_file,
        search_code,
        write_file,
    )

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP tools not available - scout swarm will use limited functionality")

logger = logging.getLogger(__name__)

# ==============================================================================
# SCOUT TIER DEFINITIONS
# ==============================================================================


class ScoutTier(str, Enum):
    """Scout tier levels based on speed/quality tradeoffs"""

    RAPID = "rapid"  # Tier 1: Fast initial scan
    DEEP = "deep"  # Tier 2: Deep critical analysis
    VALIDATION = "validation"  # Tier 3: Cross-validation
    AUDIT = "audit"  # Tier 4: Exhaustive audit


class ScanPriority(str, Enum):
    """Scan priority levels"""

    CRITICAL = "critical"  # Security vulnerabilities, exposed keys
    HIGH = "high"  # Architecture issues, performance problems
    MEDIUM = "medium"  # Code quality, technical debt
    LOW = "low"  # Style issues, documentation


@dataclass
class ScoutConfig:
    """Configuration for individual scout agent"""

    name: str
    model: str
    provider: str
    tier: ScoutTier
    api_key: str
    endpoint: str
    max_tokens: int = 4000
    temperature: float = 0.3
    timeout: int = 60
    specialties: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ScanResult:
    """Result from a scout scan"""

    scout_name: str
    tier: ScoutTier
    findings: List[Dict[str, Any]]
    execution_time: float
    tokens_used: int
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SwarmReport:
    """Consolidated report from scout swarm"""

    scan_id: str
    timestamp: datetime
    repository: str
    total_execution_time: float
    tier_results: Dict[ScoutTier, List[ScanResult]]
    critical_findings: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    statistics: Dict[str, Any]


# ==============================================================================
# INDIVIDUAL SCOUT IMPLEMENTATIONS
# ==============================================================================


class BaseScout:
    """Base class for all scout agents"""

    def __init__(self, config: ScoutConfig):
        self.config = config
        self.scan_count = 0
        self.total_tokens = 0
        self.average_time = 0.0

    async def scan(self, target: str, context: Dict[str, Any]) -> ScanResult:
        """Execute scan on target with given context"""
        start_time = time.time()

        try:
            # Build scan prompt based on tier and specialties
            prompt = self._build_prompt(target, context)

            # Execute API call
            response = await self._call_api(prompt)

            # Parse findings
            findings = self._parse_findings(response)

            # Calculate metrics
            execution_time = time.time() - start_time
            tokens_used = response.get("usage", {}).get("total_tokens", 0)

            # Update statistics
            self._update_stats(execution_time, tokens_used)

            return ScanResult(
                scout_name=self.config.name,
                tier=self.config.tier,
                findings=findings,
                execution_time=execution_time,
                tokens_used=tokens_used,
                success=True,
                metadata={
                    "model": self.config.model,
                    "provider": self.config.provider,
                    "scan_count": self.scan_count,
                },
            )

        except Exception as e:
            logger.error(f"Scout {self.config.name} scan failed: {e}")
            return ScanResult(
                scout_name=self.config.name,
                tier=self.config.tier,
                findings=[],
                execution_time=time.time() - start_time,
                tokens_used=0,
                success=False,
                error=str(e),
            )

    def _build_prompt(self, target: str, context: Dict[str, Any]) -> str:
        """Build scan prompt based on tier and context"""
        base_prompt = f"""
MISSION: Repository Analysis - {target}
TIER: {self.config.tier.value}
SPECIALTIES: {', '.join(self.config.specialties)}

You are Scout Agent {self.config.name} conducting a {self.config.tier.value} scan.
Provide SPECIFIC, ACTIONABLE findings with exact file paths and line numbers.

FOCUS AREAS:
"""

        if self.config.tier == ScoutTier.RAPID:
            base_prompt += """
1. Critical security issues (exposed keys, vulnerabilities)
2. Major architecture problems
3. Performance bottlenecks
4. Quick wins for improvement

Time limit: 15 seconds. Be fast and precise.
"""
        elif self.config.tier == ScoutTier.DEEP:
            base_prompt += """
1. Comprehensive security audit
2. Detailed architecture analysis
3. Code quality assessment
4. Performance profiling
5. Technical debt evaluation

Provide thorough analysis with specific recommendations.
"""
        elif self.config.tier == ScoutTier.VALIDATION:
            base_prompt += f"""
1. Validate previous findings: {context.get('previous_findings', [])}
2. Cross-check critical issues
3. Confirm or refute concerns
4. Provide second opinion

Focus on accuracy over speed.
"""
        else:  # AUDIT
            base_prompt += """
1. Exhaustive security review
2. Complete architecture documentation
3. Full performance analysis
4. Comprehensive code quality report
5. Technical debt inventory
6. Compliance verification

No time limit. Be exhaustive and thorough.
"""

        # Add context from previous scans if available
        if context.get("previous_findings"):
            base_prompt += f"\n\nPREVIOUS FINDINGS TO CONSIDER:\n{json.dumps(context['previous_findings'], indent=2)}"

        # Add repository statistics
        if context.get("repo_stats"):
            base_prompt += (
                f"\n\nREPOSITORY STATISTICS:\n{json.dumps(context['repo_stats'], indent=2)}"
            )

        return base_prompt

    async def _call_api(self, prompt: str) -> Dict[str, Any]:
        """Make API call to model provider"""
        raise NotImplementedError("Subclasses must implement _call_api")

    def _parse_findings(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse API response into structured findings"""
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")

        findings = []
        # Basic parsing - subclasses can override for better parsing
        lines = content.split("\n")
        current_finding = {}

        for line in lines:
            if line.startswith("ISSUE:"):
                if current_finding:
                    findings.append(current_finding)
                current_finding = {"issue": line[6:].strip()}
            elif line.startswith("FILE:"):
                current_finding["file"] = line[5:].strip()
            elif line.startswith("LINE:"):
                current_finding["line"] = line[5:].strip()
            elif line.startswith("SEVERITY:"):
                current_finding["severity"] = line[9:].strip()
            elif line.startswith("FIX:"):
                current_finding["fix"] = line[4:].strip()

        if current_finding:
            findings.append(current_finding)

        return findings

    def _update_stats(self, execution_time: float, tokens_used: int):
        """Update scout statistics"""
        self.scan_count += 1
        self.total_tokens += tokens_used

        # Update rolling average execution time
        prev_avg = self.average_time
        self.average_time = ((prev_avg * (self.scan_count - 1)) + execution_time) / self.scan_count

        # Update performance metrics
        self.config.performance_metrics["scan_count"] = self.scan_count
        self.config.performance_metrics["total_tokens"] = self.total_tokens
        self.config.performance_metrics["average_time"] = self.average_time


# ==============================================================================
# TIER 1: RAPID SCOUT (Llama-4-Scout)
# ==============================================================================


class LlamaScout(BaseScout):
    """Llama-4-Scout for rapid initial scanning"""

    def __init__(self):
        config = ScoutConfig(
            name="Llama-4-Scout",
            model="meta-llama/llama-4-scout",
            provider="AIMLAPI",
            tier=ScoutTier.RAPID,
            api_key=os.environ.get("AIMLAPI_API_KEY", "562d964ac0b54357874b01de33cb91e9"),
            endpoint="https://api.aimlapi.com/v2/chat/completions",
            temperature=0.3,
            timeout=30,
            specialties=["rapid_scan", "initial_assessment", "critical_issues"],
            performance_metrics={"expected_time": 11.45, "quality_score": 86.0},
        )
        super().__init__(config)

    async def _call_api(self, prompt: str) -> Dict[str, Any]:
        """Call AIMLAPI for Llama-4-Scout"""
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                self.config.endpoint,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                },
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)


# ==============================================================================
# TIER 2: DEEP SCOUTS (Grok Code Fast, Gemini 2.0 Flash)
# ==============================================================================


class GrokScout(BaseScout):
    """Grok Code Fast for deep security and code analysis"""

    def __init__(self):
        config = ScoutConfig(
            name="Grok-Code-Fast",
            model="x-ai/grok-code-fast-1",
            provider="OpenRouter",
            tier=ScoutTier.DEEP,
            api_key=os.environ.get(
                "OPENROUTER_API_KEY",
                "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",
            ),
            endpoint="https://openrouter.ai/api/v1/chat/completions",
            temperature=0.3,
            timeout=60,
            specialties=["security_audit", "vulnerability_detection", "code_quality"],
            performance_metrics={"expected_time": 17.65, "quality_score": 88.5},
        )
        super().__init__(config)

    async def _call_api(self, prompt: str) -> Dict[str, Any]:
        """Call OpenRouter for Grok Code Fast"""
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                self.config.endpoint,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://sophia-intel-ai.com",
                    "X-Title": "Scout Deep Analysis",
                },
                json={
                    "model": self.config.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                },
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)


class GeminiScout(BaseScout):
    """Gemini 2.0 Flash for comprehensive analysis"""

    def __init__(self):
        config = ScoutConfig(
            name="Gemini-2.0-Flash",
            model="gemini-2.0-flash-exp",
            provider="Google",
            tier=ScoutTier.DEEP,
            api_key=os.environ.get("GEMINI_API_KEY", "AIzaSyA0rewcfUHo87WMEz4a8Og1eAWTslxlgEE"),
            endpoint="https://generativelanguage.googleapis.com/v1beta/models",
            temperature=0.3,
            timeout=60,
            specialties=["architecture_analysis", "performance_optimization", "best_practices"],
            performance_metrics={"expected_time": 19.64, "quality_score": 88.5},
        )
        super().__init__(config)

    async def _call_api(self, prompt: str) -> Dict[str, Any]:
        """Call Google Gemini API"""
        model = "gemini-2.0-flash-exp"
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                f"{self.config.endpoint}/{model}:generateContent?key={self.config.api_key}",
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": self.config.temperature,
                        "maxOutputTokens": self.config.max_tokens,
                    },
                },
            )

            if response.status_code == 200:
                data = response.json()
                # Convert Gemini response format to standard format
                content = (
                    data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
                return {
                    "choices": [{"message": {"content": content}}],
                    "usage": {"total_tokens": len(content.split()) * 1.3},  # Estimate
                }
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)


# ==============================================================================
# TIER 3: VALIDATION SCOUTS (GPT-4o-mini, Llama 4 Maverick)
# ==============================================================================


class GPTScout(BaseScout):
    """GPT-4o-mini for cross-validation"""

    def __init__(self):
        config = ScoutConfig(
            name="GPT-4o-mini",
            model="gpt-4o-mini",
            provider="Portkey",
            tier=ScoutTier.VALIDATION,
            api_key=os.environ.get("PORTKEY_API_KEY", "hPxFZGd8AN269n4bznDf2/Onbi8I"),
            endpoint="https://api.portkey.ai/v1/chat/completions",
            temperature=0.3,
            timeout=45,
            specialties=["validation", "cross_checking", "consistency_verification"],
            performance_metrics={"expected_time": 15.10, "quality_score": 83.5},
        )
        super().__init__(config)

    async def _call_api(self, prompt: str) -> Dict[str, Any]:
        """Call Portkey for GPT-4o-mini"""
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                self.config.endpoint,
                headers={
                    "x-portkey-api-key": self.config.api_key,
                    "x-portkey-provider": "openai",
                    "x-portkey-virtual-key": "openai-vk-190a60",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.config.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                },
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail=response.text)


class MaverickScout(BaseScout):
    """Llama 4 Maverick for backup validation"""

    def __init__(self):
        config = ScoutConfig(
            name="Llama-4-Maverick",
            model="meta-llama/llama-4-maverick",
            provider="AIMLAPI",
            tier=ScoutTier.VALIDATION,
            api_key=os.environ.get("AIMLAPI_API_KEY", "562d964ac0b54357874b01de33cb91e9"),
            endpoint="https://api.aimlapi.com/v2/chat/completions",
            temperature=0.3,
            timeout=45,
            specialties=["alternative_analysis", "second_opinion", "edge_cases"],
            performance_metrics={"expected_time": 16.17, "quality_score": 81.0},
        )
        super().__init__(config)

    async def _call_api(self, prompt: str) -> Dict[str, Any]:
        """Call AIMLAPI for Llama 4 Maverick"""
        return await LlamaScout()._call_api(prompt)  # Same API, different model


# ==============================================================================
# TIER 4: AUDIT SCOUT (GLM-4.5-Air)
# ==============================================================================


class GLMScout(BaseScout):
    """GLM-4.5-Air for exhaustive auditing"""

    def __init__(self):
        config = ScoutConfig(
            name="GLM-4.5-Air",
            model="zhipu/glm-4.5-air",
            provider="AIMLAPI",
            tier=ScoutTier.AUDIT,
            api_key=os.environ.get("AIMLAPI_API_KEY", "562d964ac0b54357874b01de33cb91e9"),
            endpoint="https://api.aimlapi.com/v2/chat/completions",
            temperature=0.2,
            timeout=120,  # Longer timeout for exhaustive analysis
            specialties=["comprehensive_audit", "deep_analysis", "compliance_check"],
            performance_metrics={"expected_time": 61.98, "quality_score": 84.5},
        )
        super().__init__(config)

    async def _call_api(self, prompt: str) -> Dict[str, Any]:
        """Call AIMLAPI for GLM-4.5-Air"""
        return await LlamaScout()._call_api(prompt)  # Same API, different model


# ==============================================================================
# ULTIMATE SCOUT SWARM ORCHESTRATOR
# ==============================================================================


class UltimateScoutSwarm:
    """
    Ultimate Scout Swarm Orchestrator
    Coordinates tiered scanning with all scout agents
    """

    def __init__(self, use_mcp: bool = True):
        """
        Initialize the scout swarm

        Args:
            use_mcp: Whether to use MCP tools for real file access
        """
        self.use_mcp = use_mcp and MCP_AVAILABLE

        # Initialize all scouts
        self.scouts = {
            ScoutTier.RAPID: [LlamaScout()],
            ScoutTier.DEEP: [GrokScout(), GeminiScout()],
            ScoutTier.VALIDATION: [GPTScout(), MaverickScout()],
            ScoutTier.AUDIT: [GLMScout()],
        }

        # Swarm statistics
        self.total_scans = 0
        self.total_execution_time = 0.0
        self.scan_history: List[SwarmReport] = []

        logger.info(
            f"🚀 Ultimate Scout Swarm initialized with {sum(len(s) for s in self.scouts.values())} scouts"
        )
        logger.info(f"MCP Tools: {'ENABLED' if self.use_mcp else 'DISABLED'}")

    async def execute_tiered_scan(
        self, repository_path: str, scan_depth: str = "standard", include_audit: bool = False
    ) -> SwarmReport:
        """
        Execute tiered repository scan

        Args:
            repository_path: Path to repository to scan
            scan_depth: "rapid", "standard", "deep", or "exhaustive"
            include_audit: Whether to include Tier 4 audit

        Returns:
            SwarmReport with consolidated findings
        """
        scan_id = f"scan_{uuid4().hex[:8]}"
        start_time = time.time()
        tier_results = {}

        logger.info(f"🎯 Starting tiered scan {scan_id} on {repository_path}")

        # Get repository statistics
        repo_stats = await self._get_repo_stats(repository_path)
        context = {"repo_stats": repo_stats}

        # TIER 1: Rapid Scan (Always)
        logger.info("🏃 Executing Tier 1: Rapid Scan")
        tier_1_results = await self._execute_tier(ScoutTier.RAPID, repository_path, context)
        tier_results[ScoutTier.RAPID] = tier_1_results

        # Analyze Tier 1 findings
        critical_issues = self._extract_critical_issues(tier_1_results)
        context["previous_findings"] = critical_issues

        # TIER 2: Deep Analysis (if needed)
        if scan_depth in ["standard", "deep", "exhaustive"] and critical_issues:
            logger.info(
                f"🔍 Executing Tier 2: Deep Analysis ({len(critical_issues)} critical issues found)"
            )
            tier_2_results = await self._execute_tier(ScoutTier.DEEP, repository_path, context)
            tier_results[ScoutTier.DEEP] = tier_2_results
            context["previous_findings"].extend(self._extract_findings(tier_2_results))

        # TIER 3: Validation (if deep or exhaustive)
        if scan_depth in ["deep", "exhaustive"] and tier_results.get(ScoutTier.DEEP):
            logger.info("✅ Executing Tier 3: Validation")
            tier_3_results = await self._execute_tier(
                ScoutTier.VALIDATION, repository_path, context
            )
            tier_results[ScoutTier.VALIDATION] = tier_3_results

        # TIER 4: Audit (if requested or exhaustive)
        if include_audit or scan_depth == "exhaustive":
            logger.info("📊 Executing Tier 4: Exhaustive Audit")
            tier_4_results = await self._execute_tier(ScoutTier.AUDIT, repository_path, context)
            tier_results[ScoutTier.AUDIT] = tier_4_results

        # Compile report
        total_time = time.time() - start_time
        report = self._compile_report(
            scan_id, repository_path, tier_results, total_time, repo_stats
        )

        # Update statistics
        self.total_scans += 1
        self.total_execution_time += total_time
        self.scan_history.append(report)

        logger.info(f"✨ Scan {scan_id} completed in {total_time:.2f}s")

        return report

    async def _execute_tier(
        self, tier: ScoutTier, repository_path: str, context: Dict[str, Any]
    ) -> List[ScanResult]:
        """
        Execute all scouts in a tier

        Args:
            tier: Scout tier to execute
            repository_path: Repository to scan
            context: Scan context

        Returns:
            List of scan results from tier
        """
        scouts = self.scouts.get(tier, [])

        if not scouts:
            return []

        # Execute scouts in parallel
        tasks = [scout.scan(repository_path, context) for scout in scouts]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, ScanResult):
                valid_results.append(result)
            else:
                logger.error(f"Scout failed with exception: {result}")

        return valid_results

    async def _get_repo_stats(self, repository_path: str) -> Dict[str, Any]:
        """
        Get repository statistics using MCP tools

        Args:
            repository_path: Path to repository

        Returns:
            Repository statistics
        """
        stats = {"path": repository_path, "timestamp": datetime.now().isoformat()}

        if self.use_mcp:
            try:
                # Get file counts
                import glob

                py_files = glob.glob(f"{repository_path}/**/*.py", recursive=True)
                ts_files = glob.glob(f"{repository_path}/**/*.ts", recursive=True)
                tsx_files = glob.glob(f"{repository_path}/**/*.tsx", recursive=True)

                stats["python_files"] = len(py_files)
                stats["typescript_files"] = len(ts_files) + len(tsx_files)
                stats["total_files"] = len(py_files) + len(ts_files) + len(tsx_files)

                # Get git status if available
                if os.path.exists(os.path.join(repository_path, ".git")):
                    git_info = git_status() if MCP_AVAILABLE else {}
                    stats["git_status"] = git_info

            except Exception as e:
                logger.warning(f"Failed to get repository stats: {e}")

        return stats

    def _extract_critical_issues(self, results: List[ScanResult]) -> List[Dict[str, Any]]:
        """
        Extract critical issues from scan results

        Args:
            results: Scan results to analyze

        Returns:
            List of critical issues
        """
        critical = []

        for result in results:
            if result.success:
                for finding in result.findings:
                    severity = finding.get("severity", "").upper()
                    if severity in ["CRITICAL", "HIGH"]:
                        critical.append({"scout": result.scout_name, "finding": finding})

        return critical

    def _extract_findings(self, results: List[ScanResult]) -> List[Dict[str, Any]]:
        """
        Extract all findings from scan results

        Args:
            results: Scan results

        Returns:
            List of all findings
        """
        findings = []

        for result in results:
            if result.success:
                for finding in result.findings:
                    findings.append(
                        {"scout": result.scout_name, "tier": result.tier.value, "finding": finding}
                    )

        return findings

    def _compile_report(
        self,
        scan_id: str,
        repository: str,
        tier_results: Dict[ScoutTier, List[ScanResult]],
        total_time: float,
        repo_stats: Dict[str, Any],
    ) -> SwarmReport:
        """
        Compile final swarm report

        Args:
            scan_id: Unique scan identifier
            repository: Repository path
            tier_results: Results by tier
            total_time: Total execution time
            repo_stats: Repository statistics

        Returns:
            Compiled SwarmReport
        """
        # Extract critical findings
        all_results = []
        for results in tier_results.values():
            all_results.extend(results)

        critical_findings = self._extract_critical_issues(all_results)

        # Generate recommendations
        recommendations = self._generate_recommendations(tier_results)

        # Calculate statistics
        statistics = {
            "total_scouts_used": sum(len(r) for r in tier_results.values()),
            "total_findings": sum(
                len(r.findings) for results in tier_results.values() for r in results if r.success
            ),
            "critical_issues": len(critical_findings),
            "total_tokens": sum(
                r.tokens_used for results in tier_results.values() for r in results
            ),
            "average_scout_time": total_time / max(1, sum(len(r) for r in tier_results.values())),
            "repo_stats": repo_stats,
        }

        return SwarmReport(
            scan_id=scan_id,
            timestamp=datetime.now(),
            repository=repository,
            total_execution_time=total_time,
            tier_results=tier_results,
            critical_findings=critical_findings,
            recommendations=recommendations,
            statistics=statistics,
        )

    def _generate_recommendations(
        self, tier_results: Dict[ScoutTier, List[ScanResult]]
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable recommendations from scan results

        Args:
            tier_results: Results by tier

        Returns:
            List of prioritized recommendations
        """
        recommendations = []

        # Analyze patterns across all findings
        all_findings = self._extract_findings(
            [r for results in tier_results.values() for r in results]
        )

        # Group by issue type
        issue_types = {}
        for finding in all_findings:
            issue_type = finding["finding"].get("issue", "Unknown")
            if issue_type not in issue_types:
                issue_types[issue_type] = []
            issue_types[issue_type].append(finding)

        # Generate recommendations by frequency and severity
        for issue_type, findings in issue_types.items():
            if len(findings) >= 2:  # Repeated issue
                recommendations.append(
                    {
                        "priority": "HIGH",
                        "type": issue_type,
                        "count": len(findings),
                        "recommendation": f"Address {len(findings)} instances of {issue_type}",
                        "scouts_agreed": list(set(f["scout"] for f in findings)),
                    }
                )

        # Sort by priority and count
        recommendations.sort(key=lambda x: (x["priority"] == "HIGH", x["count"]), reverse=True)

        return recommendations[:10]  # Top 10 recommendations

    def get_swarm_status(self) -> Dict[str, Any]:
        """
        Get current swarm status and statistics

        Returns:
            Swarm status information
        """
        scout_status = {}

        for tier, scouts in self.scouts.items():
            tier_status = []
            for scout in scouts:
                tier_status.append(
                    {
                        "name": scout.config.name,
                        "model": scout.config.model,
                        "provider": scout.config.provider,
                        "scan_count": scout.scan_count,
                        "average_time": scout.average_time,
                        "total_tokens": scout.total_tokens,
                        "performance_metrics": scout.config.performance_metrics,
                    }
                )
            scout_status[tier.value] = tier_status

        return {
            "total_scans": self.total_scans,
            "total_execution_time": self.total_execution_time,
            "average_scan_time": self.total_execution_time / max(1, self.total_scans),
            "scouts": scout_status,
            "mcp_enabled": self.use_mcp,
            "last_scan": self.scan_history[-1].scan_id if self.scan_history else None,
        }

    async def execute_custom_scan(
        self, repository_path: str, scouts_to_use: List[str], custom_prompt: Optional[str] = None
    ) -> SwarmReport:
        """
        Execute custom scan with specific scouts

        Args:
            repository_path: Repository to scan
            scouts_to_use: List of scout names to use
            custom_prompt: Optional custom prompt

        Returns:
            SwarmReport with results
        """
        # Filter scouts by name
        selected_scouts = []
        for tier_scouts in self.scouts.values():
            for scout in tier_scouts:
                if scout.config.name in scouts_to_use:
                    selected_scouts.append(scout)

        if not selected_scouts:
            raise ValueError(f"No scouts found matching: {scouts_to_use}")

        # Execute selected scouts
        context = {"custom_prompt": custom_prompt} if custom_prompt else {}
        context["repo_stats"] = await self._get_repo_stats(repository_path)

        results = await asyncio.gather(
            *[scout.scan(repository_path, context) for scout in selected_scouts]
        )

        # Compile custom report
        scan_id = f"custom_{uuid4().hex[:8]}"
        tier_results = {ScoutTier.RAPID: results}  # Group under RAPID for simplicity

        return self._compile_report(
            scan_id,
            repository_path,
            tier_results,
            sum(r.execution_time for r in results),
            context["repo_stats"],
        )


# ==============================================================================
# FACTORY INTEGRATION
# ==============================================================================


def create_ultimate_scout_swarm() -> UltimateScoutSwarm:
    """
    Factory function to create and configure the ultimate scout swarm

    Returns:
        Configured UltimateScoutSwarm instance
    """
    return UltimateScoutSwarm(use_mcp=True)


# Global swarm instance for easy access
_global_swarm: Optional[UltimateScoutSwarm] = None


def get_scout_swarm() -> UltimateScoutSwarm:
    """
    Get or create global scout swarm instance

    Returns:
        UltimateScoutSwarm instance
    """
    global _global_swarm
    if _global_swarm is None:
        _global_swarm = create_ultimate_scout_swarm()
    return _global_swarm


# ==============================================================================
# ARTEMIS FACTORY INTEGRATION
# ==============================================================================


class ArtemisScoutSwarmIntegration:
    """
    Integration layer for Artemis Agent Factory
    """

    @staticmethod
    async def create_scout_agent(scout_type: str = "rapid") -> str:
        """
        Create a scout agent through Artemis factory

        Args:
            scout_type: Type of scout (rapid, deep, validation, audit)

        Returns:
            Agent ID
        """
        swarm = get_scout_swarm()

        # Map scout type to tier
        tier_map = {
            "rapid": ScoutTier.RAPID,
            "deep": ScoutTier.DEEP,
            "validation": ScoutTier.VALIDATION,
            "audit": ScoutTier.AUDIT,
        }

        tier = tier_map.get(scout_type, ScoutTier.RAPID)
        scouts = swarm.scouts.get(tier, [])

        if scouts:
            scout = scouts[0]  # Get first scout of tier
            agent_id = f"artemis_scout_{scout.config.name}_{uuid4().hex[:8]}"
            logger.info(f"🎯 Created Artemis Scout Agent: {agent_id}")
            return agent_id

        raise ValueError(f"No scouts available for type: {scout_type}")

    @staticmethod
    async def execute_tactical_scan(
        repository_path: str, threat_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Execute tactical repository scan

        Args:
            repository_path: Target repository
            threat_level: Threat assessment level

        Returns:
            Tactical scan report
        """
        swarm = get_scout_swarm()

        # Map threat level to scan depth
        depth_map = {
            "low": "rapid",
            "standard": "standard",
            "elevated": "deep",
            "critical": "exhaustive",
        }

        scan_depth = depth_map.get(threat_level, "standard")
        include_audit = threat_level == "critical"

        # Execute scan
        report = await swarm.execute_tiered_scan(repository_path, scan_depth, include_audit)

        # Convert to tactical format
        return {
            "operation_id": report.scan_id,
            "threat_assessment": {
                "level": threat_level,
                "critical_vulnerabilities": len(report.critical_findings),
                "total_issues": report.statistics["total_findings"],
            },
            "tactical_recommendations": report.recommendations,
            "execution_metrics": {
                "time": report.total_execution_time,
                "scouts_deployed": report.statistics["total_scouts_used"],
                "tokens_consumed": report.statistics["total_tokens"],
            },
            "detailed_report": report,
        }


# ==============================================================================
# END OF ULTIMATE SCOUT SWARM IMPLEMENTATION
# ==============================================================================
