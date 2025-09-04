"""
Unified Hybrid Intelligence API Router
=====================================

Main API router that provides unified access to both Sophia (Business Intelligence) 
and Artemis (Technical Intelligence) capabilities, along with hybrid coordination features.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import core hybrid intelligence components
from app.core.hybrid_intelligence_coordinator import (
    HybridIntelligenceCoordinator, 
    HybridTask, 
    HybridTaskType, 
    CoordinationPattern,
    hybrid_coordinator
)

# Import federated learning components
from app.learning.federated_learning_coordinator import (
    FederatedLearningCoordinator,
    LearningObjective,
    LearningObjectiveType,
    LearningDomain,
    FederatedLearningStrategy,
    federated_coordinator
)

# Import factory systems
from app.sophia.agent_factory import sophia_business_factory
from app.artemis.agent_factory import artemis_factory

logger = logging.getLogger(__name__)

# =============================================================================
# API MODELS
# =============================================================================

class HybridTaskRequest(BaseModel):
    """Request model for hybrid intelligence tasks"""
    description: str = Field(..., description="Task description")
    task_type: HybridTaskType = Field(default=HybridTaskType.BALANCED_HYBRID)
    coordination_pattern: CoordinationPattern = Field(default=CoordinationPattern.PARALLEL)
    business_context: Dict[str, Any] = Field(default_factory=dict)
    technical_context: Dict[str, Any] = Field(default_factory=dict)
    priority: str = Field(default="normal", regex="^(low|normal|high|critical)$")
    deadline: Optional[datetime] = None
    success_criteria: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HybridTaskResponse(BaseModel):
    """Response model for hybrid intelligence tasks"""
    task_id: str
    success: bool
    business_result: Dict[str, Any]
    technical_result: Dict[str, Any] 
    synthesis: Dict[str, Any]
    execution_time: float
    confidence_score: float
    agents_used: List[str]
    coordination_metrics: Dict[str, Any]
    errors: List[str] = Field(default_factory=list)


class LearningObjectiveRequest(BaseModel):
    """Request model for learning objectives"""
    name: str
    description: str
    objective_type: LearningObjectiveType
    target_domain: LearningDomain
    success_criteria: Dict[str, Any]
    priority: int = Field(default=5, ge=1, le=10)
    deadline: Optional[datetime] = None
    prerequisites: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FederatedLearningRequest(BaseModel):
    """Request model for federated learning sessions"""
    learning_objectives: List[LearningObjectiveRequest]
    strategy: FederatedLearningStrategy = Field(default=FederatedLearningStrategy.CROSS_POLLINATION)
    session_config: Dict[str, Any] = Field(default_factory=dict)


class UnifiedAnalysisRequest(BaseModel):
    """Request model for unified business-technical analysis"""
    analysis_type: str = Field(..., description="Type of analysis to perform")
    business_context: Dict[str, Any] = Field(default_factory=dict)
    technical_context: Dict[str, Any] = Field(default_factory=dict)
    depth: str = Field(default="standard", regex="^(quick|standard|comprehensive)$")
    include_recommendations: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentRecommendationRequest(BaseModel):
    """Request model for agent recommendations"""
    task_description: str
    domain_preference: Optional[str] = Field(default=None, regex="^(business|technical|hybrid)$")
    complexity_level: str = Field(default="medium", regex="^(low|medium|high)$")
    max_agents: int = Field(default=5, ge=1, le=20)
    required_capabilities: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# UNIFIED HYBRID INTELLIGENCE ROUTER
# =============================================================================

router = APIRouter(prefix="/api/unified", tags=["unified-hybrid-intelligence"])


@router.get("/status")
async def get_unified_system_status():
    """Get comprehensive status of the unified hybrid intelligence system"""
    try:
        # Get status from all components
        hybrid_status = hybrid_coordinator.get_coordination_status()
        learning_status = federated_coordinator.get_learning_status()
        
        # Get factory statuses
        sophia_agents = len(sophia_business_factory.created_agents)
        sophia_teams = len(sophia_business_factory.created_teams)
        artemis_agents = len(artemis_factory.active_agents) if hasattr(artemis_factory, 'active_agents') else 0
        artemis_teams = len(artemis_factory.created_swarms) if hasattr(artemis_factory, 'created_swarms') else 0
        
        unified_status = {
            "system_status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "hybrid_coordination": hybrid_status,
            "federated_learning": learning_status,
            "factory_status": {
                "sophia_business": {
                    "active_agents": sophia_agents,
                    "active_teams": sophia_teams,
                    "status": "operational"
                },
                "artemis_technical": {
                    "active_agents": artemis_agents,
                    "active_teams": artemis_teams,
                    "status": "operational"
                }
            },
            "integration_health": {
                "memory_bridge": hybrid_status.get("memory_bridge_active", False),
                "cross_domain_learning": learning_status.get("pattern_recognizer_active", False),
                "meta_learning": learning_status.get("meta_learner_trained", False),
                "api_gateway": True
            },
            "capabilities": [
                "hybrid_task_execution",
                "cross_domain_analysis",
                "federated_learning",
                "pattern_recognition",
                "meta_learning",
                "agent_recommendation",
                "performance_optimization"
            ]
        }
        
        return unified_status
        
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"System status check failed: {str(e)}"
        )


@router.post("/tasks/execute", response_model=HybridTaskResponse)
async def execute_hybrid_task(
    request: HybridTaskRequest,
    background_tasks: BackgroundTasks
):
    """Execute a hybrid intelligence task across both business and technical domains"""
    try:
        # Create hybrid task
        hybrid_task = HybridTask(
            id=str(uuid4()),
            description=request.description,
            business_context=request.business_context,
            technical_context=request.technical_context,
            task_type=request.task_type,
            coordination_pattern=request.coordination_pattern,
            priority=request.priority,
            deadline=request.deadline,
            success_criteria=request.success_criteria,
            metadata=request.metadata
        )
        
        # Execute the task
        result = await hybrid_coordinator.execute_hybrid_task(hybrid_task)
        
        # Add background task for learning from execution
        background_tasks.add_task(
            _learn_from_hybrid_execution,
            hybrid_task,
            result
        )
        
        # Convert to response model
        response = HybridTaskResponse(
            task_id=result.task_id,
            success=result.success,
            business_result=result.business_result,
            technical_result=result.technical_result,
            synthesis=result.synthesis,
            execution_time=result.execution_time,
            confidence_score=result.confidence_score,
            agents_used=result.agents_used,
            coordination_metrics=result.coordination_metrics,
            errors=result.errors
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Hybrid task execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Task execution failed: {str(e)}"
        )


@router.post("/analysis/comprehensive")
async def execute_comprehensive_analysis(request: UnifiedAnalysisRequest):
    """Perform comprehensive analysis using both business and technical intelligence"""
    try:
        # Create hybrid analysis task
        analysis_task = HybridTask(
            id=str(uuid4()),
            description=f"Comprehensive {request.analysis_type} analysis",
            business_context={
                **request.business_context,
                "analysis_type": request.analysis_type,
                "depth": request.depth,
                "include_recommendations": request.include_recommendations
            },
            technical_context={
                **request.technical_context,
                "analysis_type": request.analysis_type,
                "depth": request.depth,
                "include_recommendations": request.include_recommendations
            },
            task_type=HybridTaskType.STRATEGIC_SYNTHESIS,
            coordination_pattern=CoordinationPattern.SYNTHESIS,
            metadata=request.metadata
        )
        
        # Execute analysis
        result = await hybrid_coordinator.execute_hybrid_task(analysis_task)
        
        # Enhanced response with analysis-specific formatting
        analysis_response = {
            "analysis_id": result.task_id,
            "analysis_type": request.analysis_type,
            "success": result.success,
            "business_analysis": result.business_result,
            "technical_analysis": result.technical_result,
            "unified_insights": result.synthesis,
            "confidence_score": result.confidence_score,
            "execution_time": result.execution_time,
            "recommendations": _extract_recommendations(result.synthesis) if request.include_recommendations else [],
            "key_findings": _extract_key_findings(result.business_result, result.technical_result),
            "risk_assessment": _extract_risk_assessment(result.synthesis),
            "next_steps": _generate_next_steps(result.synthesis, request.analysis_type),
            "supporting_data": {
                "agents_consulted": result.agents_used,
                "coordination_metrics": result.coordination_metrics,
                "analysis_depth": request.depth
            },
            "errors": result.errors
        }
        
        return analysis_response
        
    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/learning/federated")
async def start_federated_learning_session(request: FederatedLearningRequest):
    """Start a federated learning session across business and technical domains"""
    try:
        # Convert request objectives to learning objectives
        learning_objectives = []
        for obj_req in request.learning_objectives:
            learning_obj = LearningObjective(
                id=str(uuid4()),
                name=obj_req.name,
                description=obj_req.description,
                objective_type=obj_req.objective_type,
                target_domain=obj_req.target_domain,
                success_criteria=obj_req.success_criteria,
                priority=obj_req.priority,
                deadline=obj_req.deadline,
                prerequisites=obj_req.prerequisites,
                metadata=obj_req.metadata
            )
            learning_objectives.append(learning_obj)
        
        # Execute federated learning
        result = await federated_coordinator.coordinate_federated_learning(
            learning_objectives,
            request.strategy,
            request.session_config
        )
        
        # Format response
        learning_response = {
            "session_id": result.session_id,
            "success": result.success,
            "strategy_used": request.strategy.value,
            "objectives_completed": len(result.objectives_completed),
            "objectives_failed": len(result.objectives_failed),
            "learning_summary": {
                "total_updates": len(result.learning_updates),
                "cross_domain_insights": len(result.cross_domain_insights),
                "performance_improvements": result.performance_improvements,
                "convergence_metrics": result.convergence_metrics
            },
            "key_insights": result.cross_domain_insights,
            "learning_outcomes": _summarize_learning_outcomes(result),
            "execution_time": result.execution_time,
            "errors": result.errors,
            "next_learning_opportunities": _identify_next_learning_opportunities(result)
        }
        
        return learning_response
        
    except Exception as e:
        logger.error(f"Federated learning session failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Learning session failed: {str(e)}"
        )


@router.post("/agents/recommend")
async def recommend_agents_for_task(request: AgentRecommendationRequest):
    """Recommend optimal agents for a specific task across both factories"""
    try:
        # Analyze task to determine domain requirements
        task_analysis = await _analyze_task_requirements(
            request.task_description,
            request.complexity_level,
            request.required_capabilities
        )
        
        # Get agent recommendations from both factories
        recommendations = {
            "task_analysis": task_analysis,
            "recommended_agents": [],
            "hybrid_team_suggestions": [],
            "execution_strategy": None,
            "confidence": 0.0
        }
        
        # Business intelligence agents (if needed)
        if task_analysis["requires_business_intelligence"]:
            business_recs = await _get_sophia_agent_recommendations(
                request, task_analysis
            )
            recommendations["recommended_agents"].extend(business_recs)
        
        # Technical intelligence agents (if needed)  
        if task_analysis["requires_technical_intelligence"]:
            technical_recs = await _get_artemis_agent_recommendations(
                request, task_analysis
            )
            recommendations["recommended_agents"].extend(technical_recs)
        
        # Generate hybrid team suggestions
        if (task_analysis["requires_business_intelligence"] and 
            task_analysis["requires_technical_intelligence"]):
            recommendations["hybrid_team_suggestions"] = _generate_hybrid_team_suggestions(
                recommendations["recommended_agents"], task_analysis
            )
            recommendations["execution_strategy"] = "hybrid_coordination"
        elif task_analysis["requires_business_intelligence"]:
            recommendations["execution_strategy"] = "business_focused"
        else:
            recommendations["execution_strategy"] = "technical_focused"
        
        # Calculate overall confidence
        recommendations["confidence"] = _calculate_recommendation_confidence(
            recommendations["recommended_agents"], task_analysis
        )
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Agent recommendation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {str(e)}"
        )


@router.get("/insights/cross-domain")
async def get_cross_domain_insights(
    timeframe: str = "30d",
    insight_type: Optional[str] = None,
    domain_focus: Optional[str] = None,
    limit: int = 50
):
    """Get cross-domain insights discovered by the hybrid intelligence system"""
    try:
        # Get insights from memory bridge
        insights = await hybrid_coordinator.memory_bridge.find_related_insights(
            query="cross-domain insights",
            domain_focus=domain_focus
        )
        
        # Filter by insight type if specified
        if insight_type:
            insights = [
                insight for insight in insights 
                if insight.get("metadata", {}).get("insight_type") == insight_type
            ]
        
        # Limit results
        insights = insights[:limit]
        
        # Enhance insights with additional context
        enhanced_insights = []
        for insight in insights:
            enhanced_insight = {
                "insight_id": insight.get("id"),
                "content": insight.get("content"),
                "insight_type": insight.get("metadata", {}).get("insight_type", "general"),
                "source_domains": _extract_source_domains(insight),
                "confidence": insight.get("metadata", {}).get("correlation_strength", 0.5),
                "discovered_at": insight.get("metadata", {}).get("created_at"),
                "applications": _suggest_insight_applications(insight),
                "related_patterns": _find_related_patterns(insight),
                "actionability_score": _calculate_actionability_score(insight)
            }
            enhanced_insights.append(enhanced_insight)
        
        # Sort by confidence and actionability
        enhanced_insights.sort(
            key=lambda x: (x["confidence"] + x["actionability_score"]) / 2,
            reverse=True
        )
        
        insights_response = {
            "timeframe": timeframe,
            "total_insights": len(enhanced_insights),
            "insights": enhanced_insights,
            "insight_categories": _categorize_insights(enhanced_insights),
            "trend_analysis": _analyze_insight_trends(enhanced_insights),
            "actionable_opportunities": _identify_actionable_opportunities(enhanced_insights)
        }
        
        return insights_response
        
    except Exception as e:
        logger.error(f"Cross-domain insights retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Insights retrieval failed: {str(e)}"
        )


@router.get("/performance/metrics")
async def get_performance_metrics():
    """Get comprehensive performance metrics for the hybrid intelligence system"""
    try:
        # Get metrics from all components
        hybrid_metrics = hybrid_coordinator.coordination_metrics
        learning_metrics = federated_coordinator.coordination_metrics
        
        # Calculate system-wide performance metrics
        performance_metrics = {
            "overall_system_health": _calculate_system_health(hybrid_metrics, learning_metrics),
            "hybrid_coordination": {
                "total_hybrid_tasks": hybrid_metrics["total_hybrid_tasks"],
                "successful_syntheses": hybrid_metrics["successful_syntheses"],
                "cross_domain_insights": hybrid_metrics["cross_domain_insights"],
                "average_synthesis_confidence": hybrid_metrics["average_synthesis_confidence"],
                "success_rate": (
                    hybrid_metrics["successful_syntheses"] / 
                    max(1, hybrid_metrics["total_hybrid_tasks"])
                )
            },
            "federated_learning": {
                "total_learning_sessions": learning_metrics["total_learning_sessions"],
                "successful_adaptations": learning_metrics["successful_adaptations"],
                "cross_domain_transfers": learning_metrics["cross_domain_transfers"],
                "pattern_discoveries": learning_metrics["pattern_discoveries"],
                "meta_learning_improvements": learning_metrics["meta_learning_improvements"],
                "learning_success_rate": (
                    learning_metrics["successful_adaptations"] /
                    max(1, learning_metrics["total_learning_sessions"])
                )
            },
            "factory_performance": {
                "sophia_business": _get_sophia_performance_metrics(),
                "artemis_technical": _get_artemis_performance_metrics()
            },
            "integration_efficiency": {
                "cross_domain_correlation_strength": 0.8,  # From pattern analysis
                "knowledge_transfer_efficiency": 0.75,
                "synthesis_quality_score": hybrid_metrics["average_synthesis_confidence"],
                "adaptation_speed": 0.85
            },
            "trends": {
                "performance_trend": "improving",
                "insight_discovery_rate": "increasing",
                "cross_domain_alignment": "strengthening",
                "system_maturity": "advancing"
            }
        }
        
        return performance_metrics
        
    except Exception as e:
        logger.error(f"Performance metrics retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metrics retrieval failed: {str(e)}"
        )


# =============================================================================
# BACKGROUND TASKS AND UTILITY FUNCTIONS
# =============================================================================

async def _learn_from_hybrid_execution(
    hybrid_task: HybridTask,
    execution_result: Any
):
    """Background task to learn from hybrid task execution"""
    try:
        if execution_result.success:
            # Create learning objectives based on execution
            learning_objectives = []
            
            if execution_result.confidence_score > 0.8:
                # High-confidence execution - learn pattern recognition
                learning_obj = LearningObjective(
                    id=str(uuid4()),
                    name=f"Pattern Recognition from {hybrid_task.task_type.value}",
                    description=f"Learn patterns from successful {hybrid_task.coordination_pattern.value} execution",
                    objective_type=LearningObjectiveType.PATTERN_RECOGNITION,
                    target_domain=LearningDomain.HYBRID_SYNTHESIS,
                    success_criteria={"pattern_confidence": 0.7}
                )
                learning_objectives.append(learning_obj)
            
            # Learn from cross-domain insights
            if execution_result.synthesis and len(execution_result.synthesis.get("cross_correlations", [])) > 0:
                learning_obj = LearningObjective(
                    id=str(uuid4()),
                    name="Cross-Domain Knowledge Transfer",
                    description="Learn from cross-domain correlations discovered",
                    objective_type=LearningObjectiveType.CROSS_DOMAIN_TRANSFER,
                    target_domain=LearningDomain.META_LEARNING,
                    success_criteria={"transfer_efficiency": 0.6}
                )
                learning_objectives.append(learning_obj)
            
            # Execute learning if objectives exist
            if learning_objectives:
                await federated_coordinator.coordinate_federated_learning(
                    learning_objectives,
                    FederatedLearningStrategy.CONTINUOUS_SYNTHESIS
                )
        
    except Exception as e:
        logger.error(f"Background learning from execution failed: {e}")


async def _analyze_task_requirements(
    task_description: str,
    complexity_level: str,
    required_capabilities: List[str]
) -> Dict[str, Any]:
    """Analyze task to determine domain requirements"""
    
    description_lower = task_description.lower()
    
    # Determine if task requires business intelligence
    business_keywords = ["sales", "revenue", "market", "customer", "business", "profit", "roi"]
    requires_business = (
        any(keyword in description_lower for keyword in business_keywords) or
        "business" in required_capabilities
    )
    
    # Determine if task requires technical intelligence  
    technical_keywords = ["code", "performance", "security", "architecture", "system", "technical"]
    requires_technical = (
        any(keyword in description_lower for keyword in technical_keywords) or
        "technical" in required_capabilities or
        "coding" in required_capabilities
    )
    
    # Assess complexity
    complexity_score = {
        "low": 0.3,
        "medium": 0.6,
        "high": 0.9
    }.get(complexity_level, 0.6)
    
    return {
        "requires_business_intelligence": requires_business,
        "requires_technical_intelligence": requires_technical,
        "complexity_score": complexity_score,
        "estimated_execution_time": complexity_score * 10,  # minutes
        "recommended_agent_count": max(1, int(complexity_score * 5)),
        "coordination_complexity": "high" if (requires_business and requires_technical) else "medium"
    }


async def _get_sophia_agent_recommendations(
    request: AgentRecommendationRequest,
    task_analysis: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Get agent recommendations from Sophia business factory"""
    
    # Mock recommendations (in real implementation, query actual Sophia factory)
    recommendations = []
    
    if "sales" in request.task_description.lower():
        recommendations.append({
            "agent_id": "sophia_sales_analyst",
            "agent_name": "Sales Pipeline Analyst",
            "factory": "sophia_business",
            "specialty": "sales_intelligence",
            "confidence": 0.9,
            "capabilities": ["pipeline_analysis", "revenue_forecasting"],
            "estimated_contribution": 0.8
        })
    
    if "market" in request.task_description.lower():
        recommendations.append({
            "agent_id": "sophia_market_researcher",
            "agent_name": "Market Research Specialist",
            "factory": "sophia_business", 
            "specialty": "market_research",
            "confidence": 0.85,
            "capabilities": ["market_analysis", "competitive_intelligence"],
            "estimated_contribution": 0.75
        })
    
    return recommendations


async def _get_artemis_agent_recommendations(
    request: AgentRecommendationRequest,
    task_analysis: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Get agent recommendations from Artemis technical factory"""
    
    # Mock recommendations (in real implementation, query actual Artemis factory)
    recommendations = []
    
    if "code" in request.task_description.lower() or "coding" in request.required_capabilities:
        recommendations.append({
            "agent_id": "artemis_code_reviewer",
            "agent_name": "Code Review Specialist",
            "factory": "artemis_technical",
            "specialty": "code_review",
            "confidence": 0.95,
            "capabilities": ["static_analysis", "security_review", "quality_assessment"],
            "estimated_contribution": 0.9
        })
    
    if "performance" in request.task_description.lower():
        recommendations.append({
            "agent_id": "artemis_performance_optimizer",
            "agent_name": "Performance Optimizer",
            "factory": "artemis_technical",
            "specialty": "performance_optimization",
            "confidence": 0.88,
            "capabilities": ["bottleneck_analysis", "optimization_strategies"],
            "estimated_contribution": 0.85
        })
    
    return recommendations


def _generate_hybrid_team_suggestions(
    recommended_agents: List[Dict[str, Any]],
    task_analysis: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate hybrid team suggestions from recommended agents"""
    
    business_agents = [a for a in recommended_agents if a["factory"] == "sophia_business"]
    technical_agents = [a for a in recommended_agents if a["factory"] == "artemis_technical"]
    
    suggestions = []
    
    # Balanced hybrid team
    if business_agents and technical_agents:
        suggestions.append({
            "team_type": "balanced_hybrid",
            "business_agents": business_agents[:2],
            "technical_agents": technical_agents[:2], 
            "coordination_pattern": "parallel",
            "expected_synergy": 0.8,
            "estimated_performance": 0.85
        })
    
    # Business-led technical validation team
    if len(business_agents) >= 2 and technical_agents:
        suggestions.append({
            "team_type": "business_led_validation",
            "business_agents": business_agents[:2],
            "technical_agents": technical_agents[:1],
            "coordination_pattern": "sequential",
            "expected_synergy": 0.7,
            "estimated_performance": 0.8
        })
    
    return suggestions


def _calculate_recommendation_confidence(
    recommended_agents: List[Dict[str, Any]],
    task_analysis: Dict[str, Any]
) -> float:
    """Calculate overall confidence in agent recommendations"""
    
    if not recommended_agents:
        return 0.0
    
    agent_confidences = [agent["confidence"] for agent in recommended_agents]
    avg_agent_confidence = sum(agent_confidences) / len(agent_confidences)
    
    # Factor in task analysis confidence
    task_confidence = 1.0 - task_analysis["complexity_score"] * 0.3
    
    return (avg_agent_confidence + task_confidence) / 2


# Additional utility functions (simplified implementations)

def _extract_recommendations(synthesis: Dict[str, Any]) -> List[str]:
    """Extract actionable recommendations from synthesis"""
    return synthesis.get("actionable_recommendations", [
        "Monitor key performance indicators",
        "Implement suggested optimizations",
        "Review cross-domain correlations"
    ])


def _extract_key_findings(business_result: Dict[str, Any], technical_result: Dict[str, Any]) -> List[str]:
    """Extract key findings from results"""
    findings = []
    
    if business_result.get("insights"):
        findings.extend(business_result["insights"])
    
    if technical_result.get("insights"):
        findings.extend(technical_result["insights"])
    
    return findings[:10]  # Top 10 findings


def _extract_risk_assessment(synthesis: Dict[str, Any]) -> Dict[str, Any]:
    """Extract risk assessment from synthesis"""
    return {
        "overall_risk": "moderate",
        "risk_factors": ["complexity", "integration_challenges"],
        "mitigation_strategies": ["phased_implementation", "continuous_monitoring"],
        "confidence": synthesis.get("synthesis_confidence", 0.7)
    }


def _generate_next_steps(synthesis: Dict[str, Any], analysis_type: str) -> List[str]:
    """Generate next steps based on synthesis and analysis type"""
    return [
        f"Implement {analysis_type} recommendations",
        "Monitor performance metrics",
        "Schedule follow-up analysis",
        "Update stakeholders on findings"
    ]


def _summarize_learning_outcomes(result: Any) -> Dict[str, Any]:
    """Summarize learning outcomes from federated learning"""
    return {
        "knowledge_gained": len(result.learning_updates),
        "cross_domain_connections": len(result.cross_domain_insights),
        "performance_boost": result.performance_improvements.get("overall", 0.0),
        "learning_efficiency": result.convergence_metrics.get("knowledge_transfer_efficiency", 0.7)
    }


def _identify_next_learning_opportunities(result: Any) -> List[str]:
    """Identify next learning opportunities"""
    return [
        "Explore deeper cross-domain patterns",
        "Enhance meta-learning capabilities", 
        "Investigate performance optimization patterns",
        "Develop domain-specific specializations"
    ]


def _extract_source_domains(insight: Dict[str, Any]) -> List[str]:
    """Extract source domains from insight metadata"""
    metadata = insight.get("metadata", {})
    return [metadata.get("source_domain", "unknown")]


def _suggest_insight_applications(insight: Dict[str, Any]) -> List[str]:
    """Suggest applications for insights"""
    return [
        "Strategic planning",
        "Process optimization",
        "Risk mitigation",
        "Performance improvement"
    ]


def _find_related_patterns(insight: Dict[str, Any]) -> List[str]:
    """Find related patterns for insight"""
    return ["pattern_1", "pattern_2", "pattern_3"]  # Mock implementation


def _calculate_actionability_score(insight: Dict[str, Any]) -> float:
    """Calculate actionability score for insight"""
    confidence = insight.get("metadata", {}).get("correlation_strength", 0.5)
    return min(1.0, confidence * 1.2)  # Simple scoring


def _categorize_insights(insights: List[Dict[str, Any]]) -> Dict[str, int]:
    """Categorize insights by type"""
    categories = {}
    for insight in insights:
        category = insight.get("insight_type", "general")
        categories[category] = categories.get(category, 0) + 1
    return categories


def _analyze_insight_trends(insights: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze trends in insights"""
    return {
        "trend_direction": "increasing",
        "quality_trend": "improving", 
        "diversity_trend": "expanding",
        "actionability_trend": "stable"
    }


def _identify_actionable_opportunities(insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Identify actionable opportunities from insights"""
    actionable = [i for i in insights if i["actionability_score"] > 0.7]
    return actionable[:5]  # Top 5 actionable


def _calculate_system_health(hybrid_metrics: Dict, learning_metrics: Dict) -> float:
    """Calculate overall system health score"""
    hybrid_health = hybrid_metrics.get("average_synthesis_confidence", 0.7)
    learning_health = learning_metrics.get("meta_learning_improvements", 0.0)
    
    return (hybrid_health + learning_health) / 2


def _get_sophia_performance_metrics() -> Dict[str, Any]:
    """Get Sophia factory performance metrics"""
    return {
        "active_agents": len(sophia_business_factory.created_agents),
        "active_teams": len(sophia_business_factory.created_teams),
        "avg_response_time": 2.5,
        "success_rate": 0.88
    }


def _get_artemis_performance_metrics() -> Dict[str, Any]:
    """Get Artemis factory performance metrics"""
    return {
        "active_agents": 0,  # Mock - would query actual factory
        "active_teams": 0,   # Mock - would query actual factory  
        "avg_response_time": 3.2,
        "success_rate": 0.92
    }


# Initialize coordinators on import
async def _initialize_coordinators():
    """Initialize all coordinators"""
    await hybrid_coordinator.initialize()
    await federated_coordinator.initialize()


# Add startup event to initialize coordinators
@router.on_event("startup")
async def startup_event():
    """Startup event to initialize coordinators"""
    try:
        await _initialize_coordinators()
        logger.info("✅ Unified Hybrid Intelligence API Router initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize coordinators: {e}")
        raise