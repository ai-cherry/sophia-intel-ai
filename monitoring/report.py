"""
SOPHIA Monitoring Reports
Generate summaries of feedback and performance metrics for dashboards.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
import asyncio

# Import Sophia components
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sophia.core.feedback_master import SOPHIAFeedbackMaster, FeedbackSummary
from sophia.core.performance_monitor import SOPHIAPerformanceMonitor

logger = logging.getLogger(__name__)

class SOPHIAReportGenerator:
    """
    Generate comprehensive reports combining feedback and performance data.
    Outputs JSON and text reports for consumption by Grafana and other tools.
    """
    
    def __init__(self):
        """Initialize report generator."""
        self.feedback_master = SOPHIAFeedbackMaster()
        self.performance_monitor = SOPHIAPerformanceMonitor()
        
        logger.info("Initialized SOPHIAReportGenerator")
    
    async def generate_daily_report(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Generate comprehensive daily report.
        
        Args:
            date: Date for report (defaults to yesterday)
            
        Returns:
            Daily report data
        """
        if date is None:
            date = datetime.now(timezone.utc) - timedelta(days=1)
        
        try:
            # Get feedback summary for the day
            feedback_summary = await self.feedback_master.aggregate_feedback(days=1)
            
            # Get performance summary for the day
            performance_summary = self.performance_monitor.get_performance_summary(hours=24)
            
            # Get service health status
            health_status = self.performance_monitor.get_health_status()
            
            # Generate insights and recommendations
            insights = self._generate_insights(feedback_summary, performance_summary, health_status)
            
            report = {
                "report_type": "daily",
                "report_date": date.strftime("%Y-%m-%d"),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "summary": {
                    "total_feedback": feedback_summary.total_feedback,
                    "average_rating": feedback_summary.average_rating,
                    "total_api_calls": performance_summary["total_calls"],
                    "success_rate": performance_summary.get("success_rate", 0),
                    "average_response_time": performance_summary.get("average_duration_ms", 0),
                    "overall_health": health_status["overall_health"]
                },
                "feedback": {
                    "total_feedback": feedback_summary.total_feedback,
                    "average_rating": feedback_summary.average_rating,
                    "rating_distribution": feedback_summary.rating_distribution,
                    "common_issues": feedback_summary.common_issues,
                    "improvement_suggestions": feedback_summary.improvement_suggestions
                },
                "performance": performance_summary,
                "health": health_status,
                "insights": insights,
                "recommendations": self._generate_recommendations(feedback_summary, performance_summary, health_status)
            }
            
            logger.info(f"Generated daily report for {date.strftime('%Y-%m-%d')}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate daily report: {e}")
            raise
    
    async def generate_weekly_report(self) -> Dict[str, Any]:
        """Generate comprehensive weekly report."""
        try:
            # Get feedback summary for the week
            feedback_summary = await self.feedback_master.aggregate_feedback(days=7)
            
            # Get performance summary for the week
            performance_summary = self.performance_monitor.get_performance_summary(hours=168)  # 7 days
            
            # Get service health status
            health_status = self.performance_monitor.get_health_status()
            
            # Get trends over the week
            trends = await self._calculate_weekly_trends()
            
            report = {
                "report_type": "weekly",
                "report_period": f"{(datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')} to {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "summary": {
                    "total_feedback": feedback_summary.total_feedback,
                    "average_rating": feedback_summary.average_rating,
                    "total_api_calls": performance_summary["total_calls"],
                    "success_rate": performance_summary.get("success_rate", 0),
                    "average_response_time": performance_summary.get("average_duration_ms", 0),
                    "overall_health": health_status["overall_health"]
                },
                "feedback": {
                    "total_feedback": feedback_summary.total_feedback,
                    "average_rating": feedback_summary.average_rating,
                    "rating_distribution": feedback_summary.rating_distribution,
                    "common_issues": feedback_summary.common_issues,
                    "improvement_suggestions": feedback_summary.improvement_suggestions
                },
                "performance": performance_summary,
                "health": health_status,
                "trends": trends,
                "insights": self._generate_insights(feedback_summary, performance_summary, health_status),
                "recommendations": self._generate_recommendations(feedback_summary, performance_summary, health_status)
            }
            
            logger.info("Generated weekly report")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate weekly report: {e}")
            raise
    
    async def generate_service_report(self, service: str, days: int = 7) -> Dict[str, Any]:
        """
        Generate service-specific report.
        
        Args:
            service: Service name
            days: Number of days to analyze
            
        Returns:
            Service-specific report
        """
        try:
            # Get service performance stats
            service_stats = self.performance_monitor.get_service_stats(service)
            
            # Get service metrics
            service_metrics = self.performance_monitor.get_metrics(service=service, limit=1000)
            
            # Get feedback for tasks related to this service (if available)
            # This would require task-service mapping in production
            
            if not service_stats:
                return {
                    "service": service,
                    "status": "no_data",
                    "message": f"No performance data available for service {service}"
                }
            
            stats = service_stats[service]
            
            # Calculate service-specific insights
            recent_metrics = [m for m in service_metrics if 
                            (datetime.now(timezone.utc) - m.timestamp).days <= days]
            
            error_trends = self._calculate_error_trends(recent_metrics)
            performance_trends = self._calculate_performance_trends(recent_metrics)
            
            report = {
                "service": service,
                "report_period": f"Last {days} days",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "summary": {
                    "total_calls": stats.total_calls,
                    "successful_calls": stats.successful_calls,
                    "failed_calls": stats.failed_calls,
                    "success_rate": ((stats.successful_calls / stats.total_calls) * 100) if stats.total_calls > 0 else 0,
                    "average_duration_ms": stats.average_duration_ms,
                    "total_tokens": stats.total_tokens,
                    "error_rate": stats.error_rate,
                    "uptime_percentage": stats.uptime_percentage,
                    "last_call": stats.last_call.isoformat() if stats.last_call else None
                },
                "trends": {
                    "error_trend": error_trends,
                    "performance_trend": performance_trends
                },
                "recent_errors": self._get_recent_errors(recent_metrics),
                "recommendations": self._generate_service_recommendations(service, stats, recent_metrics)
            }
            
            logger.info(f"Generated service report for {service}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate service report for {service}: {e}")
            raise
    
    async def generate_grafana_metrics(self) -> Dict[str, Any]:
        """
        Generate metrics in format suitable for Grafana consumption.
        
        Returns:
            Grafana-compatible metrics
        """
        try:
            # Get current performance summary
            performance_summary = self.performance_monitor.get_performance_summary(hours=1)
            
            # Get feedback summary
            feedback_summary = await self.feedback_master.aggregate_feedback(days=1)
            
            # Get health status
            health_status = self.performance_monitor.get_health_status()
            
            # Format for Grafana
            grafana_metrics = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": [
                    {
                        "name": "sophia_total_api_calls",
                        "value": performance_summary["total_calls"],
                        "type": "counter",
                        "help": "Total number of API calls"
                    },
                    {
                        "name": "sophia_success_rate",
                        "value": performance_summary.get("success_rate", 0),
                        "type": "gauge",
                        "help": "API call success rate percentage"
                    },
                    {
                        "name": "sophia_average_response_time",
                        "value": performance_summary.get("average_duration_ms", 0),
                        "type": "gauge",
                        "help": "Average response time in milliseconds"
                    },
                    {
                        "name": "sophia_total_feedback",
                        "value": feedback_summary.total_feedback,
                        "type": "counter",
                        "help": "Total feedback received"
                    },
                    {
                        "name": "sophia_average_rating",
                        "value": feedback_summary.average_rating,
                        "type": "gauge",
                        "help": "Average user rating"
                    },
                    {
                        "name": "sophia_health_score",
                        "value": self._calculate_health_score(health_status),
                        "type": "gauge",
                        "help": "Overall health score (0-100)"
                    }
                ],
                "service_metrics": []
            }
            
            # Add per-service metrics
            for service, stats in self.performance_monitor.get_service_stats().items():
                grafana_metrics["service_metrics"].extend([
                    {
                        "name": f"sophia_service_calls",
                        "value": stats.total_calls,
                        "labels": {"service": service},
                        "type": "counter"
                    },
                    {
                        "name": f"sophia_service_error_rate",
                        "value": stats.error_rate,
                        "labels": {"service": service},
                        "type": "gauge"
                    },
                    {
                        "name": f"sophia_service_response_time",
                        "value": stats.average_duration_ms,
                        "labels": {"service": service},
                        "type": "gauge"
                    }
                ])
            
            return grafana_metrics
            
        except Exception as e:
            logger.error(f"Failed to generate Grafana metrics: {e}")
            raise
    
    def _generate_insights(
        self,
        feedback_summary: FeedbackSummary,
        performance_summary: Dict[str, Any],
        health_status: Dict[str, Any]
    ) -> List[str]:
        """Generate insights from feedback and performance data."""
        insights = []
        
        # Feedback insights
        if feedback_summary.average_rating < 3.0:
            insights.append("User satisfaction is below acceptable levels - immediate attention required")
        elif feedback_summary.average_rating > 4.5:
            insights.append("Excellent user satisfaction - current approach is working well")
        
        if feedback_summary.total_feedback > 0:
            low_ratings = feedback_summary.rating_distribution.get(1, 0) + feedback_summary.rating_distribution.get(2, 0)
            if low_ratings / feedback_summary.total_feedback > 0.2:
                insights.append("High percentage of negative feedback - investigate root causes")
        
        # Performance insights
        if performance_summary.get("success_rate", 100) < 95:
            insights.append("API reliability is below target - investigate failing services")
        
        if performance_summary.get("average_duration_ms", 0) > 2000:
            insights.append("Response times are slower than optimal - consider performance optimization")
        
        # Health insights
        if health_status["overall_health"] == "unhealthy":
            insights.append("System health is compromised - immediate intervention required")
        elif health_status["overall_health"] == "degraded":
            insights.append("System performance is degraded - monitor closely")
        
        # Service-specific insights
        unhealthy_services = [
            service for service, status in health_status["services"].items()
            if status["status"] in ["unhealthy", "degraded"]
        ]
        if unhealthy_services:
            insights.append(f"Services requiring attention: {', '.join(unhealthy_services)}")
        
        return insights
    
    def _generate_recommendations(
        self,
        feedback_summary: FeedbackSummary,
        performance_summary: Dict[str, Any],
        health_status: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Add feedback-based recommendations
        recommendations.extend(feedback_summary.improvement_suggestions)
        
        # Add performance-based recommendations
        if performance_summary.get("success_rate", 100) < 98:
            recommendations.append("Implement circuit breakers and retry logic for failing services")
        
        if performance_summary.get("average_duration_ms", 0) > 1000:
            recommendations.append("Optimize slow API endpoints and consider caching strategies")
        
        # Add health-based recommendations
        for alert in health_status.get("alerts", []):
            if "error rate" in alert:
                recommendations.append("Investigate and fix root causes of service errors")
            elif "response time" in alert:
                recommendations.append("Optimize performance of slow services")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _generate_service_recommendations(
        self,
        service: str,
        stats: Any,
        recent_metrics: List[Any]
    ) -> List[str]:
        """Generate service-specific recommendations."""
        recommendations = []
        
        if stats.error_rate > 5:
            recommendations.append(f"Investigate high error rate for {service}")
        
        if stats.average_duration_ms > 2000:
            recommendations.append(f"Optimize response time for {service}")
        
        if stats.total_calls == 0:
            recommendations.append(f"Service {service} appears to be unused - consider deprecation")
        
        # Analyze error patterns
        error_types = {}
        for metric in recent_metrics:
            if not metric.success and metric.error_type:
                error_types[metric.error_type] = error_types.get(metric.error_type, 0) + 1
        
        if error_types:
            most_common_error = max(error_types.keys(), key=lambda x: error_types[x])
            recommendations.append(f"Address common {most_common_error} errors in {service}")
        
        return recommendations
    
    async def _calculate_weekly_trends(self) -> Dict[str, Any]:
        """Calculate trends over the past week."""
        # This is a simplified implementation
        # In production, you'd want more sophisticated trend analysis
        
        current_week = await self.feedback_master.aggregate_feedback(days=7)
        previous_week = await self.feedback_master.aggregate_feedback(days=14)  # Last 14 days
        
        # Calculate changes
        rating_change = current_week.average_rating - (previous_week.average_rating if previous_week.total_feedback > 0 else current_week.average_rating)
        feedback_change = current_week.total_feedback - previous_week.total_feedback
        
        return {
            "rating_trend": "improving" if rating_change > 0.1 else "declining" if rating_change < -0.1 else "stable",
            "rating_change": rating_change,
            "feedback_volume_trend": "increasing" if feedback_change > 0 else "decreasing" if feedback_change < 0 else "stable",
            "feedback_volume_change": feedback_change
        }
    
    def _calculate_error_trends(self, metrics: List[Any]) -> str:
        """Calculate error trend from metrics."""
        if len(metrics) < 10:
            return "insufficient_data"
        
        # Simple trend calculation - compare first and second half
        mid_point = len(metrics) // 2
        first_half_errors = sum(1 for m in metrics[:mid_point] if not m.success)
        second_half_errors = sum(1 for m in metrics[mid_point:] if not m.success)
        
        first_half_rate = first_half_errors / mid_point if mid_point > 0 else 0
        second_half_rate = second_half_errors / (len(metrics) - mid_point) if (len(metrics) - mid_point) > 0 else 0
        
        if second_half_rate > first_half_rate * 1.2:
            return "increasing"
        elif second_half_rate < first_half_rate * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_performance_trends(self, metrics: List[Any]) -> str:
        """Calculate performance trend from metrics."""
        if len(metrics) < 10:
            return "insufficient_data"
        
        # Simple trend calculation - compare first and second half
        mid_point = len(metrics) // 2
        first_half_avg = sum(m.duration_ms for m in metrics[:mid_point]) / mid_point
        second_half_avg = sum(m.duration_ms for m in metrics[mid_point:]) / (len(metrics) - mid_point)
        
        if second_half_avg > first_half_avg * 1.2:
            return "degrading"
        elif second_half_avg < first_half_avg * 0.8:
            return "improving"
        else:
            return "stable"
    
    def _get_recent_errors(self, metrics: List[Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent error details."""
        error_metrics = [m for m in metrics if not m.success]
        error_metrics.sort(key=lambda x: x.timestamp, reverse=True)
        
        return [
            {
                "timestamp": m.timestamp.isoformat(),
                "operation": m.operation,
                "error_type": m.error_type,
                "error_message": m.error_message,
                "duration_ms": m.duration_ms
            }
            for m in error_metrics[:limit]
        ]
    
    def _calculate_health_score(self, health_status: Dict[str, Any]) -> float:
        """Calculate overall health score (0-100)."""
        if health_status["overall_health"] == "healthy":
            return 100.0
        elif health_status["overall_health"] == "degraded":
            return 75.0
        elif health_status["overall_health"] == "unhealthy":
            return 25.0
        else:
            return 50.0
    
    async def export_report(
        self,
        report_type: str = "daily",
        format: str = "json",
        output_file: Optional[str] = None
    ) -> str:
        """
        Export report to file or return as string.
        
        Args:
            report_type: Type of report (daily, weekly, service)
            format: Output format (json, text)
            output_file: Optional output file path
            
        Returns:
            Report content as string
        """
        try:
            if report_type == "daily":
                report_data = await self.generate_daily_report()
            elif report_type == "weekly":
                report_data = await self.generate_weekly_report()
            else:
                raise ValueError(f"Unsupported report type: {report_type}")
            
            if format == "json":
                content = json.dumps(report_data, indent=2, default=str)
            elif format == "text":
                content = self._format_text_report(report_data)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(content)
                logger.info(f"Exported {report_type} report to {output_file}")
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            raise
    
    def _format_text_report(self, report_data: Dict[str, Any]) -> str:
        """Format report data as human-readable text."""
        lines = []
        lines.append(f"SOPHIA AI ORCHESTRATOR - {report_data['report_type'].upper()} REPORT")
        lines.append("=" * 60)
        lines.append(f"Generated: {report_data['generated_at']}")
        lines.append("")
        
        # Summary section
        lines.append("SUMMARY")
        lines.append("-" * 20)
        summary = report_data['summary']
        lines.append(f"Total Feedback: {summary['total_feedback']}")
        lines.append(f"Average Rating: {summary['average_rating']:.2f}/5.0")
        lines.append(f"Total API Calls: {summary['total_api_calls']}")
        lines.append(f"Success Rate: {summary['success_rate']:.1f}%")
        lines.append(f"Avg Response Time: {summary['average_response_time']:.0f}ms")
        lines.append(f"Overall Health: {summary['overall_health'].upper()}")
        lines.append("")
        
        # Insights section
        if report_data.get('insights'):
            lines.append("KEY INSIGHTS")
            lines.append("-" * 20)
            for insight in report_data['insights']:
                lines.append(f"• {insight}")
            lines.append("")
        
        # Recommendations section
        if report_data.get('recommendations'):
            lines.append("RECOMMENDATIONS")
            lines.append("-" * 20)
            for rec in report_data['recommendations']:
                lines.append(f"• {rec}")
            lines.append("")
        
        return "\n".join(lines)

# CLI interface for generating reports
async def main():
    """CLI interface for report generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate SOPHIA monitoring reports")
    parser.add_argument("--type", choices=["daily", "weekly", "service"], default="daily",
                       help="Type of report to generate")
    parser.add_argument("--service", help="Service name (for service reports)")
    parser.add_argument("--format", choices=["json", "text"], default="json",
                       help="Output format")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    try:
        generator = SOPHIAReportGenerator()
        
        if args.type == "service":
            if not args.service:
                print("Service name required for service reports")
                return
            report = await generator.generate_service_report(args.service)
        else:
            content = await generator.export_report(
                report_type=args.type,
                format=args.format,
                output_file=args.output
            )
            
            if not args.output:
                print(content)
        
    except Exception as e:
        print(f"Error generating report: {e}")

if __name__ == "__main__":
    asyncio.run(main())

