"""
SOPHIA Business Master
Orchestrates business intelligence operations and integrations.
"""

import os
import logging
from typing import Dict, List, Optional, Any
import asyncio
from datetime import datetime, timezone, timedelta

from .api_manager import SOPHIAAPIManager
from .ultimate_model_router import UltimateModelRouter
from .mcp_client import SOPHIAMCPClient

logger = logging.getLogger(__name__)

class SOPHIABusinessMaster:
    """
    Master class for business intelligence operations.
    Orchestrates data collection, analysis, and insights from business tools.
    """
    
    def __init__(self):
        """Initialize business master with required components."""
        self.api_manager = SOPHIAAPIManager()
        self.model_router = UltimateModelRouter()
        self.mcp_client = None  # Will be initialized when needed
        
        # Business configuration
        self.supported_sources = ["gong", "hubspot", "slack", "salesforce", "notion"]
        self.default_date_range = 30  # days
        
        logger.info("Initialized SOPHIABusinessMaster")
    
    async def _get_mcp_client(self) -> SOPHIAMCPClient:
        """Get or create MCP client."""
        if self.mcp_client is None:
            self.mcp_client = SOPHIAMCPClient()
        return self.mcp_client
    
    async def get_customer_360(
        self,
        customer_email: str,
        customer_id: Optional[str] = None,
        include_calls: bool = True,
        include_emails: bool = True,
        include_deals: bool = True,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive 360-degree customer view.
        
        Args:
            customer_email: Customer email address
            customer_id: Optional customer ID
            include_calls: Include call data from Gong
            include_emails: Include email interactions
            include_deals: Include deal information
            days_back: Number of days to look back
            
        Returns:
            Comprehensive customer insights
        """
        try:
            logger.info(f"Getting customer 360 view for: {customer_email}")
            
            mcp_client = await self._get_mcp_client()
            
            try:
                # Try MCP server first
                result = await mcp_client.get_customer_insights(
                    customer_id=customer_id,
                    customer_email=customer_email,
                    include_calls=include_calls,
                    include_emails=include_emails,
                    include_deals=include_deals,
                    days_back=days_back
                )
                
                # Store insights in memory
                await self._store_customer_memory(customer_email, result)
                
                return result
                
            except Exception as mcp_error:
                logger.warning(f"MCP customer insights failed, falling back: {mcp_error}")
                
                # Fallback to direct API calls
                return await self._direct_customer_360(
                    customer_email, customer_id, include_calls, include_emails, include_deals, days_back
                )
                
        except Exception as e:
            logger.error(f"Customer 360 view failed: {e}")
            raise
    
    async def get_sales_dashboard(
        self,
        time_period: str = "monthly",
        metric_types: Optional[List[str]] = None,
        team_members: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive sales dashboard.
        
        Args:
            time_period: Time period for metrics (daily, weekly, monthly, quarterly)
            metric_types: Specific metrics to include
            team_members: Specific team members to analyze
            
        Returns:
            Sales dashboard data
        """
        try:
            logger.info(f"Generating sales dashboard for {time_period}")
            
            metric_types = metric_types or [
                "revenue", "deals_closed", "call_volume", "pipeline_value", "conversion_rate"
            ]
            
            mcp_client = await self._get_mcp_client()
            
            try:
                # Get sales metrics from MCP server
                result = await mcp_client.get_sales_metrics(
                    metric_types=metric_types,
                    time_period=time_period
                )
                
                # Enhance with additional analysis
                enhanced_result = await self._enhance_sales_dashboard(result, team_members)
                
                return enhanced_result
                
            except Exception as mcp_error:
                logger.warning(f"MCP sales dashboard failed, falling back: {mcp_error}")
                
                # Fallback to direct calculation
                return await self._direct_sales_dashboard(time_period, metric_types, team_members)
                
        except Exception as e:
            logger.error(f"Sales dashboard generation failed: {e}")
            raise
    
    async def analyze_team_performance(
        self,
        team_members: Optional[List[str]] = None,
        metrics: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze team performance across multiple dimensions.
        
        Args:
            team_members: List of team member IDs/emails
            metrics: Performance metrics to analyze
            date_range: Date range for analysis
            
        Returns:
            Team performance analysis
        """
        try:
            logger.info("Analyzing team performance")
            
            metrics = metrics or [
                "calls_made", "deals_closed", "revenue_generated", "response_time", "customer_satisfaction"
            ]
            
            # Collect data from multiple sources
            performance_data = {}
            
            # Get call data from Gong
            if "calls_made" in metrics:
                call_data = await self._get_call_performance(team_members, date_range)
                performance_data["calls"] = call_data
            
            # Get deal data from HubSpot/Salesforce
            if "deals_closed" in metrics or "revenue_generated" in metrics:
                deal_data = await self._get_deal_performance(team_members, date_range)
                performance_data["deals"] = deal_data
            
            # Get communication data from Slack
            if "response_time" in metrics:
                comm_data = await self._get_communication_performance(team_members, date_range)
                performance_data["communication"] = comm_data
            
            # Generate AI-powered insights
            insights = await self._generate_team_insights(performance_data, metrics)
            
            result = {
                "team_members": team_members,
                "metrics": metrics,
                "date_range": date_range,
                "performance_data": performance_data,
                "insights": insights,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store in memory
            await self._store_team_performance_memory(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Team performance analysis failed: {e}")
            raise
    
    async def get_business_intelligence_report(
        self,
        report_type: str = "comprehensive",
        date_range: Optional[Dict[str, str]] = None,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive business intelligence report.
        
        Args:
            report_type: Type of report (summary, comprehensive, executive)
            date_range: Date range for the report
            focus_areas: Specific areas to focus on
            
        Returns:
            Business intelligence report
        """
        try:
            logger.info(f"Generating {report_type} business intelligence report")
            
            # Collect data from all sources
            report_data = {}
            
            # Sales data
            sales_data = await self.get_sales_dashboard("monthly")
            report_data["sales"] = sales_data
            
            # Customer data
            customer_data = await self._get_customer_overview(date_range)
            report_data["customers"] = customer_data
            
            # Team performance
            team_data = await self.analyze_team_performance(date_range=date_range)
            report_data["team"] = team_data
            
            # Market insights (if research is available)
            if focus_areas:
                market_data = await self._get_market_insights(focus_areas)
                report_data["market"] = market_data
            
            # Generate comprehensive report using AI
            report = await self._generate_bi_report(report_data, report_type, focus_areas)
            
            return report
            
        except Exception as e:
            logger.error(f"Business intelligence report generation failed: {e}")
            raise
    
    async def _direct_customer_360(
        self,
        customer_email: str,
        customer_id: Optional[str],
        include_calls: bool,
        include_emails: bool,
        include_deals: bool,
        days_back: int
    ) -> Dict[str, Any]:
        """Direct customer 360 view fallback."""
        try:
            interactions = []
            
            # Get call data from Gong
            if include_calls:
                # TODO: Implement direct Gong API calls
                logger.warning("Direct Gong integration not implemented")
            
            # Get contact/deal data from HubSpot
            if include_emails or include_deals:
                # TODO: Implement direct HubSpot API calls
                logger.warning("Direct HubSpot integration not implemented")
            
            # Mock customer insights for now
            result = {
                "customer_id": customer_id or "unknown",
                "customer_name": "Customer Name",
                "customer_email": customer_email,
                "recent_interactions": interactions,
                "deal_status": None,
                "engagement_score": 0.5,
                "insights": ["Direct API integration not yet implemented"],
                "last_interaction": None
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Direct customer 360 failed: {e}")
            raise
    
    async def _direct_sales_dashboard(
        self,
        time_period: str,
        metric_types: List[str],
        team_members: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Direct sales dashboard fallback."""
        try:
            # TODO: Implement direct API calls to business systems
            logger.warning("Direct sales dashboard not implemented")
            
            # Mock metrics for now
            metrics = {}
            
            if "revenue" in metric_types:
                metrics["revenue"] = {
                    "current_period": 125000,
                    "previous_period": 110000,
                    "growth_rate": 0.136
                }
            
            if "deals_closed" in metric_types:
                metrics["deals_closed"] = {
                    "current_period": 15,
                    "previous_period": 12,
                    "growth_rate": 0.25
                }
            
            return {
                "metrics": metrics,
                "time_period": time_period,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Direct sales dashboard failed: {e}")
            raise
    
    async def _enhance_sales_dashboard(
        self,
        base_metrics: Dict[str, Any],
        team_members: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Enhance sales dashboard with additional analysis."""
        try:
            # Add trend analysis
            enhanced = dict(base_metrics)
            
            # TODO: Add trend analysis, forecasting, and team breakdowns
            enhanced["trends"] = "Trend analysis not yet implemented"
            enhanced["forecasts"] = "Forecasting not yet implemented"
            
            if team_members:
                enhanced["team_breakdown"] = "Team analysis not yet implemented"
            
            return enhanced
            
        except Exception as e:
            logger.error(f"Dashboard enhancement failed: {e}")
            return base_metrics
    
    async def _get_call_performance(
        self,
        team_members: Optional[List[str]],
        date_range: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Get call performance data from Gong."""
        # TODO: Implement Gong API integration
        logger.warning("Call performance data not implemented")
        return {"status": "not_implemented"}
    
    async def _get_deal_performance(
        self,
        team_members: Optional[List[str]],
        date_range: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Get deal performance data from CRM."""
        # TODO: Implement CRM API integration
        logger.warning("Deal performance data not implemented")
        return {"status": "not_implemented"}
    
    async def _get_communication_performance(
        self,
        team_members: Optional[List[str]],
        date_range: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Get communication performance from Slack."""
        # TODO: Implement Slack API integration
        logger.warning("Communication performance data not implemented")
        return {"status": "not_implemented"}
    
    async def _generate_team_insights(
        self,
        performance_data: Dict[str, Any],
        metrics: List[str]
    ) -> List[str]:
        """Generate AI-powered team insights."""
        try:
            model_config = self.model_router.select_model("analysis")
            
            data_summary = f"Team Performance Analysis\n\n"
            data_summary += f"Metrics Analyzed: {', '.join(metrics)}\n\n"
            
            for category, data in performance_data.items():
                data_summary += f"{category.title()}: {data}\n"
            
            insights_prompt = f"""
Analyze the following team performance data and provide actionable insights:

{data_summary}

Please provide 3-5 specific insights about:
1. Team strengths and areas for improvement
2. Performance trends and patterns
3. Individual vs team performance
4. Recommended actions for improvement
5. Risk factors and opportunities

Insights:
"""
            
            response = await self.model_router.call_model(
                model_config,
                insights_prompt,
                temperature=0.3,
                max_tokens=1024
            )
            
            # Parse insights
            insights = []
            for line in response.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                    insights.append(line.lstrip('-•0123456789. '))
            
            return insights if insights else ["Team analysis completed"]
            
        except Exception as e:
            logger.error(f"Team insights generation failed: {e}")
            return ["Insight generation failed"]
    
    async def _get_customer_overview(self, date_range: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """Get customer overview data."""
        # TODO: Implement customer data aggregation
        logger.warning("Customer overview not implemented")
        return {"status": "not_implemented"}
    
    async def _get_market_insights(self, focus_areas: List[str]) -> Dict[str, Any]:
        """Get market insights through research."""
        # TODO: Integrate with research master
        logger.warning("Market insights not implemented")
        return {"status": "not_implemented"}
    
    async def _generate_bi_report(
        self,
        report_data: Dict[str, Any],
        report_type: str,
        focus_areas: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Generate comprehensive BI report using AI."""
        try:
            model_config = self.model_router.select_model("analysis")
            
            # Prepare report data
            data_summary = f"Business Intelligence Report ({report_type})\n\n"
            
            for category, data in report_data.items():
                data_summary += f"{category.title()} Data:\n{data}\n\n"
            
            if focus_areas:
                data_summary += f"Focus Areas: {', '.join(focus_areas)}\n\n"
            
            report_prompt = f"""
Generate a comprehensive business intelligence report based on the following data:

{data_summary}

Report Type: {report_type}

Please provide:
1. Executive Summary
2. Key Performance Indicators
3. Trends and Patterns Analysis
4. Opportunities and Risks
5. Strategic Recommendations
6. Action Items

Report:
"""
            
            report_content = await self.model_router.call_model(
                model_config,
                report_prompt,
                temperature=0.2,
                max_tokens=4096
            )
            
            return {
                "report_type": report_type,
                "content": report_content,
                "data_sources": list(report_data.keys()),
                "focus_areas": focus_areas,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"BI report generation failed: {e}")
            return {
                "report_type": report_type,
                "content": "Report generation failed",
                "error": str(e)
            }
    
    async def _store_customer_memory(self, customer_email: str, insights: Dict[str, Any]):
        """Store customer insights in memory."""
        try:
            mcp_client = await self._get_mcp_client()
            
            content = f"Customer: {customer_email}\n"
            content += f"Engagement Score: {insights.get('engagement_score', 'N/A')}\n"
            content += f"Recent Interactions: {len(insights.get('recent_interactions', []))}\n"
            
            if insights.get('insights'):
                content += f"Key Insights: {'; '.join(insights['insights'][:3])}\n"
            
            await mcp_client.store_memory(
                content=content,
                memory_type="customer_insights",
                metadata={
                    "customer_email": customer_email,
                    "engagement_score": insights.get("engagement_score"),
                    "interaction_count": len(insights.get("recent_interactions", []))
                }
            )
            
            logger.info(f"Stored customer memory for: {customer_email}")
            
        except Exception as e:
            logger.error(f"Failed to store customer memory: {e}")
    
    async def _store_team_performance_memory(self, performance_data: Dict[str, Any]):
        """Store team performance data in memory."""
        try:
            mcp_client = await self._get_mcp_client()
            
            content = f"Team Performance Analysis\n"
            content += f"Metrics: {', '.join(performance_data.get('metrics', []))}\n"
            content += f"Team Members: {len(performance_data.get('team_members', []) or [])}\n"
            
            if performance_data.get('insights'):
                content += f"Key Insights: {'; '.join(performance_data['insights'][:3])}\n"
            
            await mcp_client.store_memory(
                content=content,
                memory_type="team_performance",
                metadata={
                    "analysis_date": performance_data.get("generated_at"),
                    "metrics_count": len(performance_data.get("metrics", [])),
                    "team_size": len(performance_data.get("team_members", []) or [])
                }
            )
            
            logger.info("Stored team performance memory")
            
        except Exception as e:
            logger.error(f"Failed to store team performance memory: {e}")
    
    async def get_integration_status(self) -> Dict[str, Any]:
        """Get status of all business integrations."""
        try:
            mcp_client = await self._get_mcp_client()
            
            # Try to get status from MCP server
            try:
                response = await mcp_client.client.get(f"{mcp_client.base_url}/business/integrations/status")
                if response.status_code == 200:
                    return response.json()
            except Exception as mcp_error:
                logger.warning(f"MCP integration status failed: {mcp_error}")
            
            # Fallback to direct check
            return {
                "integrations": {
                    "gong": {
                        "status": "configured" if os.getenv("GONG_ACCESS_KEY") else "not_configured",
                        "capabilities": ["calls", "recordings", "analytics"]
                    },
                    "hubspot": {
                        "status": "configured" if os.getenv("HUBSPOT_API_KEY") else "not_configured",
                        "capabilities": ["contacts", "deals", "companies"]
                    },
                    "slack": {
                        "status": "configured" if os.getenv("SLACK_BOT_TOKEN") else "not_configured",
                        "capabilities": ["messages", "channels", "users"]
                    },
                    "salesforce": {
                        "status": "not_implemented",
                        "capabilities": ["leads", "opportunities", "accounts"]
                    },
                    "notion": {
                        "status": "configured" if os.getenv("NOTION_API_KEY") else "not_configured",
                        "capabilities": ["pages", "databases", "blocks"]
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Integration status check failed: {e}")
            raise
    
    async def close(self):
        """Close connections."""
        if self.mcp_client:
            await self.mcp_client.close()

