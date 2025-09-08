#!/usr/bin/env python3
"""
PM Unification MCP Server
Unified Project Management Intelligence with Notion-Centric Architecture

This MCP server provides comprehensive project management intelligence by integrating
Notion strategic planning with operational tools (Asana, Linear, Gong) through
advanced AI agents and real-time data processing.

Author: Sophia AI V9.7
Version: 1.0.0
Last Updated: January 8, 2025
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import asana
import linear_sdk
import numpy as np
from gong_api import GongClient
from mcp import MCPServer
from mcp.cache import IntelligentCache
from mcp.rate_limit import AdaptiveRateLimit

# Third-party integrations
from notion_client import AsyncClient as NotionClient
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProjectStatus(Enum):
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    BLOCKED = "blocked"
    CRITICAL = "critical"
    COMPLETED = "completed"


class UrgencyLevel(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class OKRAlignment:
    objective_id: str
    objective_title: str
    key_results: List[Dict[str, Any]]
    alignment_score: float
    strategic_context: str
    last_updated: datetime
    owner: str
    department: str


@dataclass
class ProjectIntelligence:
    project_id: str
    title: str
    status: ProjectStatus
    urgency: UrgencyLevel
    okr_alignment: float
    blockers: List[Dict[str, Any]]
    stakeholders: List[str]
    last_activity: datetime
    platform_sources: List[str]
    strategic_context: Dict[str, Any]
    recommendations: List[Dict[str, Any]]


@dataclass
class EscalationTrigger:
    trigger_id: str
    project_id: str
    trigger_type: str
    severity: UrgencyLevel
    description: str
    recommended_actions: List[str]
    stakeholders_to_notify: List[str]
    escalation_deadline: datetime


class PMUnificationMCPServer(MCPServer):
    """
    Unified Project Management Intelligence MCP Server

    Provides comprehensive project management intelligence through integration
    of Notion strategic planning with operational tools and AI-powered analysis.
    """

    def __init__(self):
        super().__init__(
            name="pm-unification",
            version="1.0.0",
            description="Unified Project Management Intelligence with Notion-Centric Architecture",
        )

        # Initialize configuration from environment variables
        self.config = self._load_configuration()

        # Initialize platform clients
        self.notion_client = NotionClient(auth=self.config["notion_token"])
        self.asana_client = asana.Client.access_token(self.config["asana_token"])
        self.linear_client = linear_sdk.LinearClient(self.config["linear_token"])
        self.gong_client = GongClient(
            access_key=self.config["gong_access_key"], access_key_secret=self.config["gong_secret"]
        )

        # Initialize AI components
        self.semantic_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.cache = IntelligentCache(ttl=300, max_size=1000)
        self.rate_limiter = AdaptiveRateLimit(requests_per_minute=100)

        # Register MCP tools and resources
        self._register_tools()
        self._register_resources()

        logger.info("PM Unification MCP Server initialized successfully")

    def _load_configuration(self) -> Dict[str, str]:
        """Load configuration from environment variables with Pulumi ESC integration"""
        required_vars = [
            "NOTION_API_TOKEN",
            "ASANA_ACCESS_TOKEN",
            "LINEAR_API_KEY",
            "GONG_ACCESS_KEY",
            "GONG_ACCESS_KEY_SECRET",
            "SLACK_BOT_TOKEN",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
        ]

        config = {}
        missing_vars = []

        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
            else:
                # Map to internal config keys
                key_mapping = {
                    "NOTION_API_TOKEN": "notion_token",
                    "ASANA_ACCESS_TOKEN": "asana_token",
                    "LINEAR_API_KEY": "linear_token",
                    "GONG_ACCESS_KEY": "gong_access_key",
                    "GONG_ACCESS_KEY_SECRET": "gong_secret",
                    "SLACK_BOT_TOKEN": "slack_token",
                    "OPENAI_API_KEY": "openai_key",
                    "ANTHROPIC_API_KEY": "anthropic_key",
                }
                config[key_mapping[var]] = value

        if missing_vars:
            logger.warning(f"Missing environment variables: {missing_vars}")
            # Provide fallback configuration for development
            for var in missing_vars:
                config[key_mapping.get(var, var.lower())] = "development_placeholder"

        return config

    def _register_tools(self):
        """Register MCP tools for project management intelligence"""

        @self.tool("analyze_project_health")
        async def analyze_project_health(
            project_filter: Optional[Dict[str, Any]] = None,
            include_predictions: bool = True,
            executive_view: bool = False,
        ) -> Dict[str, Any]:
            """
            Comprehensive project health analysis across all platforms

            Args:
                project_filter: Optional filter criteria for projects
                include_predictions: Whether to include predictive analysis
                executive_view: Whether to provide executive-level insights

            Returns:
                Comprehensive project health analysis with intelligence and recommendations
            """
            try:
                logger.info("Starting comprehensive project health analysis")

                # Gather data from all integrated platforms
                platform_data = await self._gather_platform_data(project_filter)

                # Perform cross-platform analysis
                health_analysis = await self._analyze_cross_platform_health(platform_data)

                # Generate strategic insights
                strategic_insights = await self._generate_strategic_insights(
                    health_analysis, platform_data
                )

                # Identify escalation triggers
                escalations = await self._identify_escalation_triggers(health_analysis)

                # Generate predictive analysis if requested
                predictions = {}
                if include_predictions:
                    predictions = await self._generate_predictive_analysis(
                        health_analysis, platform_data
                    )

                # Generate executive briefing if requested
                executive_briefing = {}
                if executive_view:
                    executive_briefing = await self._generate_executive_briefing(
                        health_analysis, strategic_insights, predictions
                    )

                result = {
                    "health_summary": health_analysis["summary"],
                    "project_intelligence": health_analysis["projects"],
                    "strategic_insights": strategic_insights,
                    "escalation_triggers": escalations,
                    "predictions": predictions,
                    "executive_briefing": executive_briefing,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "data_sources": list(platform_data.keys()),
                }

                logger.info("Project health analysis completed successfully")
                return result

            except Exception as e:
                logger.error(f"Project health analysis failed: {e}")
                return {"error": str(e), "analysis_timestamp": datetime.now().isoformat()}

        @self.tool("analyze_okr_alignment")
        async def analyze_okr_alignment(
            project_data: Dict[str, Any],
            department: Optional[str] = None,
            include_recommendations: bool = True,
        ) -> Dict[str, Any]:
            """
            Analyze project alignment with strategic OKRs

            Args:
                project_data: Project information for alignment analysis
                department: Optional department filter for OKR analysis
                include_recommendations: Whether to include strategic recommendations

            Returns:
                OKR alignment analysis with scores and recommendations
            """
            try:
                logger.info(
                    f"Analyzing OKR alignment for project: {project_data.get('title', 'Unknown')}"
                )

                # Retrieve relevant OKRs from Notion
                okrs = await self._get_department_okrs(department)

                if not okrs:
                    return {"error": "No OKRs found for analysis", "alignment_score": 0.0}

                # Perform semantic alignment analysis
                alignment_results = await self._calculate_alignment_scores(project_data, okrs)

                # Generate strategic recommendations if requested
                recommendations = []
                if include_recommendations:
                    recommendations = await self._generate_alignment_recommendations(
                        alignment_results, okrs
                    )

                result = {
                    "alignment_score": alignment_results["overall_score"],
                    "okr_matches": alignment_results["matches"],
                    "recommendations": recommendations,
                    "strategic_context": alignment_results["context"],
                    "department_focus": department,
                    "analysis_timestamp": datetime.now().isoformat(),
                }

                logger.info(
                    f"OKR alignment analysis completed with score: {alignment_results['overall_score']:.2f}"
                )
                return result

            except Exception as e:
                logger.error(f"OKR alignment analysis failed: {e}")
                return {
                    "error": str(e),
                    "alignment_score": 0.0,
                    "analysis_timestamp": datetime.now().isoformat(),
                }

        @self.tool("process_escalation")
        async def process_escalation(
            trigger_data: Dict[str, Any],
            auto_execute: bool = False,
            notify_stakeholders: bool = True,
        ) -> Dict[str, Any]:
            """
            Process and respond to project escalation triggers

            Args:
                trigger_data: Escalation trigger information
                auto_execute: Whether to automatically execute recommended actions
                notify_stakeholders: Whether to notify relevant stakeholders

            Returns:
                Escalation processing results with response strategy
            """
            try:
                logger.info(f"Processing escalation: {trigger_data.get('trigger_type', 'Unknown')}")

                # Create escalation trigger object
                trigger = EscalationTrigger(
                    trigger_id=trigger_data.get("trigger_id", f"esc_{datetime.now().timestamp()}"),
                    project_id=trigger_data["project_id"],
                    trigger_type=trigger_data["trigger_type"],
                    severity=UrgencyLevel(trigger_data.get("severity", 2)),
                    description=trigger_data["description"],
                    recommended_actions=trigger_data.get("recommended_actions", []),
                    stakeholders_to_notify=trigger_data.get("stakeholders", []),
                    escalation_deadline=datetime.fromisoformat(
                        trigger_data.get(
                            "deadline", (datetime.now() + timedelta(hours=24)).isoformat()
                        )
                    ),
                )

                # Analyze escalation context
                context_analysis = await self._analyze_escalation_context(trigger)

                # Generate response strategy
                response_strategy = await self._generate_escalation_response(
                    trigger, context_analysis
                )

                # Execute automatic actions if enabled
                execution_results = {}
                if auto_execute and response_strategy.get("auto_actions"):
                    execution_results = await self._execute_escalation_actions(
                        response_strategy["auto_actions"]
                    )

                # Notify stakeholders if enabled
                notification_results = {}
                if notify_stakeholders:
                    notification_results = await self._notify_escalation_stakeholders(
                        trigger, response_strategy
                    )

                result = {
                    "escalation_id": trigger.trigger_id,
                    "response_strategy": response_strategy,
                    "execution_results": execution_results,
                    "notification_results": notification_results,
                    "next_review": response_strategy.get("next_review"),
                    "processing_timestamp": datetime.now().isoformat(),
                }

                logger.info(f"Escalation processing completed: {trigger.trigger_id}")
                return result

            except Exception as e:
                logger.error(f"Escalation processing failed: {e}")
                return {
                    "error": str(e),
                    "escalation_id": trigger_data.get("trigger_id", "unknown"),
                    "processing_timestamp": datetime.now().isoformat(),
                }

        @self.tool("generate_executive_briefing")
        async def generate_executive_briefing(
            timeframe: str = "weekly",
            focus_areas: Optional[List[str]] = None,
            include_predictions: bool = True,
        ) -> Dict[str, Any]:
            """
            Generate executive briefing with strategic project intelligence

            Args:
                timeframe: Briefing timeframe (daily, weekly, monthly, quarterly)
                focus_areas: Optional focus areas for the briefing
                include_predictions: Whether to include predictive analytics

            Returns:
                Executive briefing with strategic insights and recommendations
            """
            try:
                logger.info(f"Generating executive briefing for {timeframe} timeframe")

                # Determine briefing scope based on timeframe
                briefing_scope = await self._determine_briefing_scope(timeframe)

                # Gather comprehensive project data
                project_data = await self._gather_executive_data(briefing_scope)

                # Analyze OKR alignment across all projects
                okr_analysis = await self._analyze_okr_alignment_trends(project_data)

                # Identify strategic risks and opportunities
                strategic_analysis = await self._analyze_strategic_landscape(
                    project_data, focus_areas
                )

                # Generate resource allocation insights
                resource_insights = await self._analyze_resource_allocation(project_data)

                # Create executive recommendations
                recommendations = await self._generate_executive_recommendations(
                    okr_analysis, strategic_analysis, resource_insights
                )

                # Generate predictive analysis if requested
                predictions = {}
                if include_predictions:
                    predictions = await self._generate_executive_predictions(
                        project_data, okr_analysis
                    )

                # Format briefing for executive consumption
                briefing = {
                    "briefing_summary": {
                        "timeframe": timeframe,
                        "scope": briefing_scope,
                        "total_projects": len(project_data.get("projects", [])),
                        "critical_issues": len(strategic_analysis.get("critical_risks", [])),
                        "strategic_opportunities": len(strategic_analysis.get("opportunities", [])),
                    },
                    "okr_analysis": okr_analysis,
                    "strategic_analysis": strategic_analysis,
                    "resource_insights": resource_insights,
                    "recommendations": recommendations,
                    "predictions": predictions,
                    "generation_timestamp": datetime.now().isoformat(),
                }

                logger.info("Executive briefing generated successfully")
                return briefing

            except Exception as e:
                logger.error(f"Executive briefing generation failed: {e}")
                return {
                    "error": str(e),
                    "briefing_type": "executive",
                    "generation_timestamp": datetime.now().isoformat(),
                }

        @self.tool("sync_platform_data")
        async def sync_platform_data(
            platforms: Optional[List[str]] = None, force_refresh: bool = False
        ) -> Dict[str, Any]:
            """
            Synchronize data across integrated platforms

            Args:
                platforms: Optional list of platforms to sync (notion, asana, linear, gong)
                force_refresh: Whether to force cache refresh

            Returns:
                Synchronization results with status and metrics
            """
            try:
                logger.info("Starting platform data synchronization")

                if platforms is None:
                    platforms = ["notion", "asana", "linear", "gong"]

                sync_results = {}

                for platform in platforms:
                    try:
                        if force_refresh:
                            self.cache.clear_pattern(f"{platform}_*")

                        sync_result = await self._sync_platform_data(platform)
                        sync_results[platform] = sync_result

                    except Exception as e:
                        logger.error(f"Failed to sync {platform}: {e}")
                        sync_results[platform] = {"status": "error", "error": str(e)}

                # Generate synchronization summary
                successful_syncs = len(
                    [r for r in sync_results.values() if r.get("status") == "success"]
                )
                total_syncs = len(sync_results)

                result = {
                    "sync_summary": {
                        "successful": successful_syncs,
                        "total": total_syncs,
                        "success_rate": (
                            (successful_syncs / total_syncs) * 100 if total_syncs > 0 else 0
                        ),
                    },
                    "platform_results": sync_results,
                    "sync_timestamp": datetime.now().isoformat(),
                }

                logger.info(
                    f"Platform synchronization completed: {successful_syncs}/{total_syncs} successful"
                )
                return result

            except Exception as e:
                logger.error(f"Platform synchronization failed: {e}")
                return {"error": str(e), "sync_timestamp": datetime.now().isoformat()}

    def _register_resources(self):
        """Register MCP resources for project management data"""

        @self.resource("project_intelligence")
        async def get_project_intelligence(project_id: str) -> Dict[str, Any]:
            """Get comprehensive intelligence for a specific project"""
            try:
                # Gather project data from all platforms
                project_data = await self._get_unified_project_data(project_id)

                if not project_data:
                    return {"error": f"Project {project_id} not found"}

                # Analyze project health and alignment
                health_analysis = await self._analyze_project_health_single(project_data)
                okr_alignment = await self._analyze_project_okr_alignment(project_data)

                return {
                    "project_data": project_data,
                    "health_analysis": health_analysis,
                    "okr_alignment": okr_alignment,
                    "last_updated": datetime.now().isoformat(),
                }

            except Exception as e:
                logger.error(f"Failed to get project intelligence for {project_id}: {e}")
                return {"error": str(e)}

        @self.resource("okr_database")
        async def get_okr_database(department: Optional[str] = None) -> Dict[str, Any]:
            """Get OKR database with alignment analysis"""
            try:
                okrs = await self._get_department_okrs(department)

                # Enhance OKRs with project alignment data
                enhanced_okrs = []
                for okr in okrs:
                    aligned_projects = await self._get_okr_aligned_projects(okr["id"])
                    okr["aligned_projects"] = aligned_projects
                    okr["alignment_strength"] = len(aligned_projects)
                    enhanced_okrs.append(okr)

                return {
                    "okrs": enhanced_okrs,
                    "department": department,
                    "total_okrs": len(enhanced_okrs),
                    "last_updated": datetime.now().isoformat(),
                }

            except Exception as e:
                logger.error(f"Failed to get OKR database: {e}")
                return {"error": str(e)}

    async def _gather_platform_data(
        self, project_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Gather data from all integrated platforms"""
        platform_data = {}

        # Gather Notion strategic data
        try:
            notion_data = await self._get_notion_projects(project_filter)
            platform_data["notion"] = notion_data
        except Exception as e:
            logger.warning(f"Notion data gathering failed: {e}")
            platform_data["notion"] = {"error": str(e), "projects": []}

        # Gather Asana project data
        try:
            asana_data = await self._get_asana_projects(project_filter)
            platform_data["asana"] = asana_data
        except Exception as e:
            logger.warning(f"Asana data gathering failed: {e}")
            platform_data["asana"] = {"error": str(e), "projects": []}

        # Gather Linear engineering data
        try:
            linear_data = await self._get_linear_issues(project_filter)
            platform_data["linear"] = linear_data
        except Exception as e:
            logger.warning(f"Linear data gathering failed: {e}")
            platform_data["linear"] = {"error": str(e), "issues": []}

        # Gather Gong client signals
        try:
            gong_data = await self._get_gong_signals()
            platform_data["gong"] = gong_data
        except Exception as e:
            logger.warning(f"Gong data gathering failed: {e}")
            platform_data["gong"] = {"error": str(e), "signals": []}

        return platform_data

    async def _get_notion_projects(
        self, project_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Retrieve projects and OKRs from Notion"""
        cache_key = f"notion_projects_{hash(str(project_filter))}"

        if cached_data := self.cache.get(cache_key):
            return cached_data

        try:
            # Query Notion database for projects
            query_filter = {
                "and": [
                    {"property": "Type", "select": {"equals": "Project"}},
                    {"property": "Status", "select": {"does_not_equal": "Archived"}},
                ]
            }

            # Add additional filters if provided
            if project_filter:
                if "department" in project_filter:
                    query_filter["and"].append(
                        {
                            "property": "Department",
                            "select": {"equals": project_filter["department"]},
                        }
                    )

                if "priority" in project_filter:
                    query_filter["and"].append(
                        {"property": "Priority", "select": {"equals": project_filter["priority"]}}
                    )

            # Execute Notion query
            response = await self.notion_client.databases.query(
                database_id=os.getenv("NOTION_DATABASE_ID", "default_db_id"),
                filter=query_filter,
                sorts=[
                    {"property": "Priority", "direction": "descending"},
                    {"property": "Last edited time", "direction": "descending"},
                ],
            )

            projects = []
            for page in response["results"]:
                project_data = await self._extract_notion_project_data(page)
                if project_data:
                    projects.append(project_data)

            result = {
                "projects": projects,
                "total_count": len(projects),
                "last_updated": datetime.now().isoformat(),
            }

            self.cache.set(cache_key, result)
            return result

        except Exception as e:
            logger.error(f"Failed to retrieve Notion projects: {e}")
            return {"error": str(e), "projects": []}

    async def _get_department_okrs(self, department: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve OKRs for specific department or all OKRs"""
        cache_key = f"okrs_{department or 'all'}"

        if cached_okrs := self.cache.get(cache_key):
            return cached_okrs

        try:
            # Query Notion database for OKRs
            query_filter = {
                "and": [
                    {"property": "Type", "select": {"equals": "OKR"}},
                    {"property": "Status", "select": {"does_not_equal": "Archived"}},
                ]
            }

            if department:
                query_filter["and"].append(
                    {"property": "Department", "select": {"equals": department}}
                )

            response = await self.notion_client.databases.query(
                database_id=os.getenv("NOTION_DATABASE_ID", "default_db_id"),
                filter=query_filter,
                sorts=[
                    {"property": "Priority", "direction": "descending"},
                    {"property": "Last edited time", "direction": "descending"},
                ],
            )

            okrs = []
            for page in response["results"]:
                okr_data = await self._extract_okr_data(page)
                if okr_data:
                    okrs.append(okr_data)

            self.cache.set(cache_key, okrs)
            return okrs

        except Exception as e:
            logger.error(f"Failed to retrieve OKRs: {e}")
            return []

    async def _calculate_alignment_scores(
        self, project_data: Dict[str, Any], okrs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate semantic alignment scores between project and OKRs"""
        try:
            # Extract project description and goals
            project_text = f"{project_data.get('title', '')} {project_data.get('description', '')}"
            project_embedding = self.semantic_model.encode([project_text])

            alignment_results = []
            for okr in okrs:
                # Create OKR text representation
                okr_text = f"{okr['objective']} {' '.join([kr.get('description', '') for kr in okr.get('key_results', [])])}"
                okr_embedding = self.semantic_model.encode([okr_text])

                # Calculate semantic similarity
                similarity = np.dot(project_embedding[0], okr_embedding[0]) / (
                    np.linalg.norm(project_embedding[0]) * np.linalg.norm(okr_embedding[0])
                )

                alignment_results.append(
                    {
                        "okr_id": okr["id"],
                        "okr_title": okr["objective"],
                        "alignment_score": float(similarity),
                        "strategic_weight": okr.get("weight", 1.0),
                        "department": okr.get("department", "unknown"),
                    }
                )

            # Sort by alignment score and calculate overall alignment
            alignment_results.sort(key=lambda x: x["alignment_score"], reverse=True)

            # Calculate weighted overall score
            if alignment_results:
                top_alignments = alignment_results[:3]  # Top 3 alignments
                overall_score = sum(
                    r["alignment_score"] * r["strategic_weight"] for r in top_alignments
                ) / sum(r["strategic_weight"] for r in top_alignments)
            else:
                overall_score = 0.0

            return {
                "overall_score": overall_score,
                "matches": alignment_results[:5],  # Top 5 matches
                "context": self._generate_alignment_context(alignment_results),
            }

        except Exception as e:
            logger.error(f"Alignment score calculation failed: {e}")
            return {"overall_score": 0.0, "matches": [], "context": "Alignment analysis failed"}

    async def _generate_alignment_recommendations(
        self, alignment_results: Dict[str, Any], okrs: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Generate strategic recommendations based on alignment analysis"""
        recommendations = []

        overall_score = alignment_results["overall_score"]
        top_matches = alignment_results["matches"][:3]

        if overall_score < 0.3:
            recommendations.append(
                {
                    "type": "strategic_misalignment",
                    "priority": "high",
                    "recommendation": "Project shows low strategic alignment. Consider reviewing project scope against current OKRs or updating strategic priorities.",
                    "action": "Schedule strategic review meeting with stakeholders",
                    "impact": "high",
                }
            )

        elif overall_score < 0.6:
            if top_matches:
                recommendations.append(
                    {
                        "type": "partial_alignment",
                        "priority": "medium",
                        "recommendation": f"Project partially aligns with {top_matches[0]['okr_title']}. Consider strengthening connection to strategic objectives.",
                        "action": "Refine project goals to better align with strategic priorities",
                        "impact": "medium",
                    }
                )

        else:
            if top_matches:
                recommendations.append(
                    {
                        "type": "strong_alignment",
                        "priority": "low",
                        "recommendation": f"Project strongly aligns with strategic objectives, particularly {top_matches[0]['okr_title']}.",
                        "action": "Maintain current strategic direction and monitor progress",
                        "impact": "positive",
                    }
                )

        # Add department-specific recommendations
        if top_matches:
            departments = set(match["department"] for match in top_matches)
            if len(departments) > 1:
                recommendations.append(
                    {
                        "type": "cross_functional",
                        "priority": "medium",
                        "recommendation": f"Project impacts multiple departments: {', '.join(departments)}. Ensure cross-functional coordination.",
                        "action": "Establish cross-departmental communication protocols",
                        "impact": "medium",
                    }
                )

        return recommendations

    def _generate_alignment_context(self, alignment_results: List[Dict[str, Any]]) -> str:
        """Generate contextual description of alignment analysis"""
        if not alignment_results:
            return "No strategic alignment data available"

        top_match = alignment_results[0]
        alignment_level = (
            "strong"
            if top_match["alignment_score"] > 0.7
            else "moderate" if top_match["alignment_score"] > 0.4 else "weak"
        )

        context = f"Project shows {alignment_level} alignment with strategic objectives. "
        context += f"Strongest alignment is with '{top_match['okr_title']}' "
        context += f"({top_match['department']} department) with a score of {top_match['alignment_score']:.2f}."

        if len(alignment_results) > 1:
            context += f" Secondary alignments include {len(alignment_results) - 1} additional strategic objectives."

        return context


# Additional implementation methods would continue here...
# This includes platform-specific data gathering, analysis methods, and utility functions

if __name__ == "__main__":
    # Initialize and run the MCP server
    server = PMUnificationMCPServer()

    # Start the server
    asyncio.run(server.run())
