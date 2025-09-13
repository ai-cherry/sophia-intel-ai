"""
HR Performance Management Agent - Advanced Performance Review and Development Automation
Comprehensive performance management, goal tracking, and employee development
This agent handles performance reviews, goal setting, feedback collection,
career development planning, and succession planning with AI-powered insights.
"""
import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from ..core.base_agent import (
    AgentCapability,
    AgentConfig,
    AgentResult,
    AgentTask,
    BaseAgent,
)
from ..mcp_servers.lattice.lattice_mcp_server import LatticeMCPServer
from ..shared.llm.portkey_gateway import PortkeyGateway
logger = logging.getLogger(__name__)
class ReviewCycle(Enum):
    """Performance review cycle types"""
    ANNUAL = "annual"
    SEMI_ANNUAL = "semi_annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    PROJECT_BASED = "project_based"
class PerformanceRating(Enum):
    """Performance rating scale"""
    EXCEEDS_EXPECTATIONS = "exceeds_expectations"
    MEETS_EXPECTATIONS = "meets_expectations"
    PARTIALLY_MEETS = "partially_meets_expectations"
    BELOW_EXPECTATIONS = "below_expectations"
    UNSATISFACTORY = "unsatisfactory"
class GoalStatus(Enum):
    """Goal tracking status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    COMPLETED = "completed"
    EXCEEDED = "exceeded"
    CANCELLED = "cancelled"
@dataclass
class PerformanceGoal:
    """Performance goal structure"""
    goal_id: str
    employee_id: str
    title: str
    description: str
    category: str  # performance, development, project
    target_date: datetime
    status: GoalStatus
    progress_percentage: int
    key_results: list[str]
    success_metrics: dict[str, Any]
    created_date: datetime
    last_updated: datetime
@dataclass
class PerformanceReview:
    """Performance review structure"""
    review_id: str
    employee_id: str
    reviewer_id: str
    review_period: str
    cycle_type: ReviewCycle
    status: str
    self_assessment: dict[str, Any]
    manager_assessment: dict[str, Any]
    peer_feedback: list[dict[str, Any]]
    goals_assessment: dict[str, Any]
    overall_rating: PerformanceRating
    development_plan: dict[str, Any]
    created_date: datetime
    completed_date: datetime | None
class PerformanceManagementAgent(BaseAgent):
    """
    Advanced Performance Management Agent
    Handles comprehensive performance reviews, goal tracking, and development planning
    """
    def __init__(self):
        config = AgentConfig(
            agent_id="performance_management",
            name="Performance Management AI",
            description="AI-powered performance management and employee development",
            capabilities=[
                AgentCapability.DATA_ANALYSIS,
                AgentCapability.DECISION_MAKING,
                AgentCapability.COMMUNICATION,
                AgentCapability.MONITORING,
                AgentCapability.REPORTING,
                AgentCapability.STRATEGIC_PLANNING,
            ],
            max_concurrent_tasks=20,
            timeout_seconds=600,
        )
        super().__init__(config)
        # Initialize integrations
        self.lattice_server = LatticeMCPServer()
        self.llm_gateway = PortkeyGateway()
        # Performance tracking
        self.active_reviews = {}
        self.employee_goals = {}
        self.development_plans = {}
        self.feedback_cycles = {}
        # AI models for different functions
        self.review_model = "gpt-4"
        self.analysis_model = "anthropic/claude-3-sonnet"
        self.coaching_model = "gpt-4"
        # Performance metrics
        self.metrics = {
            "reviews_completed": 0,
            "goals_tracked": 0,
            "development_plans_created": 0,
            "feedback_sessions": 0,
            "performance_improvements": 0,
            "retention_impact": 0.0,
            "engagement_correlation": 0.0,
        }
    async def initialize(self) -> bool:
        """Initialize performance management agent"""
        try:
            await super().initialize()
            # Initialize Lattice integration
            await self.lattice_server.initialize()
            # Load existing performance data
            await self._load_performance_data()
            logger.info("Performance Management Agent initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Performance Management Agent: {e}")
            return False
    async def process_task(self, task: AgentTask) -> AgentResult:
        """Process performance management tasks"""
        try:
            task_type = task.context.get("task_type", "general")
            if task_type == "conduct_review":
                result = await self.conduct_performance_review(task.context)
            elif task_type == "set_goals":
                result = await self.set_employee_goals(task.context)
            elif task_type == "track_goals":
                result = await self.track_goal_progress(task.context)
            elif task_type == "collect_feedback":
                result = await self.collect_360_feedback(task.context)
            elif task_type == "create_development_plan":
                result = await self.create_development_plan(task.context)
            elif task_type == "analyze_performance":
                result = await self.analyze_performance_trends(task.context)
            elif task_type == "succession_planning":
                result = await self.manage_succession_planning(task.context)
            elif task_type == "coaching_session":
                result = await self.conduct_ai_coaching(task.context)
            else:
                result = await self._handle_general_task(task)
            return AgentResult(
                task_id=task.task_id,
                success=True,
                result=result,
                metadata={"task_type": task_type},
            )
        except Exception as e:
            logger.error(f"Error processing performance management task: {e}")
            return AgentResult(task_id=task.task_id, success=False, error=str(e))
    async def conduct_performance_review(
        self, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Conduct comprehensive AI-powered performance review"""
        employee_id = context.get("employee_id")
        review_period = context.get("review_period")
        cycle_type = ReviewCycle(context.get("cycle_type", "quarterly"))
        # Get employee data from Lattice
        employee_data = await self.lattice_server.call_tool(
            "get_employee_data",
            {
                "employee_id": employee_id,
                "include_reviews": True,
                "include_goals": True,
            },
        )
        # Analyze performance data
        performance_analysis = await self._analyze_employee_performance(
            employee_data, review_period
        )
        # Generate self-assessment questions
        self_assessment_questions = await self._generate_self_assessment_questions(
            employee_data, cycle_type
        )
        # Collect and analyze goal achievements
        goal_analysis = await self._analyze_goal_achievements(
            employee_id, review_period
        )
        # Generate manager assessment framework
        manager_assessment = await self._generate_manager_assessment(
            employee_data, performance_analysis, goal_analysis
        )
        # Collect peer feedback
        peer_feedback = await self._collect_peer_feedback(employee_id, review_period)
        # Calculate overall performance rating
        overall_rating = await self._calculate_performance_rating(
            performance_analysis, goal_analysis, peer_feedback
        )
        # Generate development recommendations
        development_recommendations = await self._generate_development_recommendations(
            performance_analysis, overall_rating
        )
        # Create performance review record
        review = PerformanceReview(
            review_id=f"review_{employee_id}_{datetime.now().strftime('%Y%m%d')}",
            employee_id=employee_id,
            reviewer_id="ai_system",
            review_period=review_period,
            cycle_type=cycle_type,
            status="completed",
            self_assessment={"questions": self_assessment_questions},
            manager_assessment=manager_assessment,
            peer_feedback=peer_feedback,
            goals_assessment=goal_analysis,
            overall_rating=overall_rating,
            development_plan=development_recommendations,
            created_date=datetime.now(),
            completed_date=datetime.now(),
        )
        # Store review
        self.active_reviews[review.review_id] = review
        # Update metrics
        self.metrics["reviews_completed"] += 1
        return {
            "review_id": review.review_id,
            "employee_id": employee_id,
            "performance_analysis": performance_analysis,
            "goal_analysis": goal_analysis,
            "overall_rating": overall_rating.value,
            "development_recommendations": development_recommendations,
            "next_steps": await self._generate_review_next_steps(review),
            "review_summary": await self._generate_review_summary(review),
        }
    async def set_employee_goals(self, context: dict[str, Any]) -> dict[str, Any]:
        """Set and align employee goals with business objectives"""
        employee_id = context.get("employee_id")
        business_objectives = context.get("business_objectives", {})
        role_expectations = context.get("role_expectations", {})
        # Get employee context
        employee_data = await self.lattice_server.call_tool(
            "get_employee_data", {"employee_id": employee_id}
        )
        # Generate SMART goals aligned with business objectives
        smart_goals = await self._generate_smart_goals(
            employee_data, business_objectives, role_expectations
        )
        # Create goal tracking structure
        goal_tracking = await self._create_goal_tracking_structure(smart_goals)
        # Set up goal milestones and checkpoints
        milestones = await self._create_goal_milestones(smart_goals)
        # Generate success metrics
        success_metrics = await self._define_goal_success_metrics(smart_goals)
        # Store goals in Lattice
        lattice_goals = []
        for goal in smart_goals:
            lattice_response = await self.lattice_server.call_tool(
                "manage_okrs",
                {"action": "create", "employee_id": employee_id, "goal_data": goal},
            )
            lattice_goals.append(lattice_response)
        # Update local tracking
        if employee_id not in self.employee_goals:
            self.employee_goals[employee_id] = []
        self.employee_goals[employee_id].extend(smart_goals)
        # Update metrics
        self.metrics["goals_tracked"] += len(smart_goals)
        return {
            "employee_id": employee_id,
            "goals_set": len(smart_goals),
            "smart_goals": smart_goals,
            "goal_tracking": goal_tracking,
            "milestones": milestones,
            "success_metrics": success_metrics,
            "lattice_integration": lattice_goals,
            "alignment_score": await self._calculate_goal_alignment_score(
                smart_goals, business_objectives
            ),
        }
    async def track_goal_progress(self, context: dict[str, Any]) -> dict[str, Any]:
        """Track and analyze goal progress with AI insights"""
        employee_id = context.get("employee_id")
        context.get("goal_id")
        # Get current goal data from Lattice
        goals_data = await self.lattice_server.call_tool(
            "manage_okrs", {"action": "track", "employee_id": employee_id}
        )
        # Analyze progress patterns
        progress_analysis = await self._analyze_goal_progress_patterns(goals_data)
        # Identify at-risk goals
        at_risk_goals = await self._identify_at_risk_goals(goals_data)
        # Generate progress insights
        progress_insights = await self._generate_progress_insights(
            goals_data, progress_analysis
        )
        # Recommend interventions for at-risk goals
        interventions = await self._recommend_goal_interventions(at_risk_goals)
        # Update goal status and progress
        updated_goals = await self._update_goal_status(goals_data, progress_analysis)
        # Generate progress report
        progress_report = await self._generate_progress_report(
            employee_id, updated_goals, progress_insights
        )
        return {
            "employee_id": employee_id,
            "goals_tracked": len(goals_data.get("goals", [])),
            "progress_analysis": progress_analysis,
            "at_risk_goals": at_risk_goals,
            "progress_insights": progress_insights,
            "recommended_interventions": interventions,
            "updated_goals": updated_goals,
            "progress_report": progress_report,
            "next_review_date": await self._calculate_next_review_date(updated_goals),
        }
    async def collect_360_feedback(self, context: dict[str, Any]) -> dict[str, Any]:
        """Collect and analyze 360-degree feedback"""
        employee_id = context.get("employee_id")
        feedback_cycle_id = context.get("feedback_cycle_id")
        # Design feedback collection strategy
        feedback_strategy = await self._design_feedback_strategy(employee_id)
        # Generate feedback questions
        feedback_questions = await self._generate_feedback_questions(
            employee_id, feedback_strategy
        )
        # Collect feedback from multiple sources
        feedback_collection = await self._collect_multi_source_feedback(
            employee_id, feedback_questions
        )
        # Analyze feedback themes and patterns
        feedback_analysis = await self._analyze_feedback_themes(feedback_collection)
        # Generate feedback insights
        feedback_insights = await self._generate_feedback_insights(
            feedback_analysis, employee_id
        )
        # Create feedback report
        feedback_report = await self._create_feedback_report(
            employee_id, feedback_insights, feedback_analysis
        )
        # Generate action items
        action_items = await self._generate_feedback_action_items(feedback_insights)
        # Store in Lattice
        lattice_feedback = await self.lattice_server.call_tool(
            "manage_feedback_cycle",
            {
                "action": "create",
                "employee_id": employee_id,
                "feedback_type": "360",
                "cycle_id": feedback_cycle_id,
            },
        )
        # Update metrics
        self.metrics["feedback_sessions"] += 1
        return {
            "employee_id": employee_id,
            "feedback_cycle_id": feedback_cycle_id,
            "feedback_strategy": feedback_strategy,
            "feedback_collection": feedback_collection,
            "feedback_analysis": feedback_analysis,
            "feedback_insights": feedback_insights,
            "feedback_report": feedback_report,
            "action_items": action_items,
            "lattice_integration": lattice_feedback,
        }
    async def create_development_plan(self, context: dict[str, Any]) -> dict[str, Any]:
        """Create personalized employee development plan"""
        employee_id = context.get("employee_id")
        career_aspirations = context.get("career_aspirations", {})
        skill_gaps = context.get("skill_gaps", [])
        # Assess current competencies
        competency_assessment = await self._assess_employee_competencies(employee_id)
        # Identify development opportunities
        development_opportunities = await self._identify_development_opportunities(
            competency_assessment, career_aspirations, skill_gaps
        )
        # Create learning pathways
        learning_pathways = await self._create_learning_pathways(
            development_opportunities, employee_id
        )
        # Design mentorship recommendations
        mentorship_plan = await self._design_mentorship_plan(
            employee_id, development_opportunities
        )
        # Create stretch assignments
        stretch_assignments = await self._create_stretch_assignments(
            employee_id, development_opportunities
        )
        # Generate development timeline
        development_timeline = await self._create_development_timeline(
            learning_pathways, mentorship_plan, stretch_assignments
        )
        # Calculate development ROI
        development_roi = await self._calculate_development_roi(
            development_timeline, employee_id
        )
        # Create development plan
        development_plan = {
            "plan_id": f"dev_plan_{employee_id}_{datetime.now().strftime('%Y%m%d')}",
            "employee_id": employee_id,
            "competency_assessment": competency_assessment,
            "development_opportunities": development_opportunities,
            "learning_pathways": learning_pathways,
            "mentorship_plan": mentorship_plan,
            "stretch_assignments": stretch_assignments,
            "timeline": development_timeline,
            "success_metrics": await self._define_development_success_metrics(
                development_timeline
            ),
            "roi_projection": development_roi,
            "created_date": datetime.now(),
        }
        # Store development plan
        self.development_plans[development_plan["plan_id"]] = development_plan
        # Update metrics
        self.metrics["development_plans_created"] += 1
        return development_plan
    async def analyze_performance_trends(
        self, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze performance trends and patterns across the organization"""
        analysis_scope = context.get(
            "scope", "organization"
        )  # individual, team, department, organization
        time_period = context.get("time_period", "last_year")
        # Gather performance data
        performance_data = await self._gather_performance_data(
            analysis_scope, time_period
        )
        # Analyze performance trends
        trend_analysis = await self._analyze_performance_trends_data(performance_data)
        # Identify performance patterns
        performance_patterns = await self._identify_performance_patterns(
            performance_data
        )
        # Correlate with business metrics
        business_correlation = await self._correlate_performance_with_business_metrics(
            performance_data, trend_analysis
        )
        # Predict future performance
        performance_predictions = await self._predict_future_performance(
            trend_analysis, performance_patterns
        )
        # Generate insights and recommendations
        performance_insights = await self._generate_performance_insights(
            trend_analysis, performance_patterns, business_correlation
        )
        # Create action plan
        action_plan = await self._create_performance_action_plan(
            performance_insights, performance_predictions
        )
        return {
            "analysis_scope": analysis_scope,
            "time_period": time_period,
            "performance_data": performance_data,
            "trend_analysis": trend_analysis,
            "performance_patterns": performance_patterns,
            "business_correlation": business_correlation,
            "performance_predictions": performance_predictions,
            "insights": performance_insights,
            "action_plan": action_plan,
            "roi_impact": await self._calculate_performance_improvement_roi(
                action_plan
            ),
        }
    async def manage_succession_planning(
        self, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Manage succession planning and talent pipeline"""
        role_id = context.get("role_id")
        department = context.get("department")
        urgency = context.get("urgency", "medium")
        # Identify critical roles
        critical_roles = await self._identify_critical_roles(department)
        # Assess succession readiness
        succession_readiness = await self._assess_succession_readiness(critical_roles)
        # Identify high-potential employees
        high_potential_employees = await self._identify_high_potential_employees(
            department, critical_roles
        )
        # Create succession matrix
        succession_matrix = await self._create_succession_matrix(
            critical_roles, high_potential_employees, succession_readiness
        )
        # Generate development plans for successors
        successor_development_plans = await self._create_successor_development_plans(
            succession_matrix
        )
        # Calculate succession risk
        succession_risk = await self._calculate_succession_risk(
            succession_matrix, succession_readiness
        )
        # Create succession timeline
        succession_timeline = await self._create_succession_timeline(
            succession_matrix, urgency
        )
        return {
            "role_id": role_id,
            "department": department,
            "critical_roles": critical_roles,
            "succession_readiness": succession_readiness,
            "high_potential_employees": high_potential_employees,
            "succession_matrix": succession_matrix,
            "successor_development_plans": successor_development_plans,
            "succession_risk": succession_risk,
            "succession_timeline": succession_timeline,
            "recommendations": await self._generate_succession_recommendations(
                succession_matrix, succession_risk
            ),
        }
    async def conduct_ai_coaching(self, context: dict[str, Any]) -> dict[str, Any]:
        """Conduct AI-powered coaching session"""
        employee_id = context.get("employee_id")
        coaching_focus = context.get("coaching_focus", "performance")
        session_type = context.get("session_type", "development")
        # Prepare coaching context
        coaching_context = await self._prepare_coaching_context(
            employee_id, coaching_focus
        )
        # Generate coaching questions
        coaching_questions = await self._generate_coaching_questions(
            coaching_context, session_type
        )
        # Conduct coaching conversation
        coaching_conversation = await self._conduct_coaching_conversation(
            employee_id, coaching_questions, coaching_context
        )
        # Analyze coaching insights
        coaching_insights = await self._analyze_coaching_insights(
            coaching_conversation, coaching_focus
        )
        # Generate action plan
        coaching_action_plan = await self._generate_coaching_action_plan(
            coaching_insights, employee_id
        )
        # Create follow-up schedule
        follow_up_schedule = await self._create_coaching_follow_up_schedule(
            coaching_action_plan, employee_id
        )
        return {
            "employee_id": employee_id,
            "coaching_focus": coaching_focus,
            "session_type": session_type,
            "coaching_context": coaching_context,
            "coaching_questions": coaching_questions,
            "coaching_conversation": coaching_conversation,
            "coaching_insights": coaching_insights,
            "action_plan": coaching_action_plan,
            "follow_up_schedule": follow_up_schedule,
            "session_summary": await self._generate_coaching_session_summary(
                coaching_conversation, coaching_insights
            ),
        }
    # Helper methods for AI-powered operations
    async def _analyze_employee_performance(
        self, employee_data: dict, review_period: str
    ) -> dict[str, Any]:
        """Analyze employee performance using AI"""
        analysis_prompt = f"""
        Analyze this employee's performance for the {review_period} period:
        Employee Data: {json.dumps(employee_data, default=str)}
        Provide comprehensive analysis including:
        1. Key achievements and accomplishments
        2. Areas of strength
        3. Areas for improvement
        4. Performance trends
        5. Goal achievement rate
        6. Collaboration and teamwork
        7. Innovation and initiative
        8. Overall performance assessment
        Format as JSON with scores 0-100 for each area.
        """
        response = await self.llm_gateway.generate_completion(
            messages=[{"role": "user", "content": analysis_prompt}],
            model=self.analysis_model,
        )
        try:
            return json.loads(response)
        except:
            return {"analysis": response}
    async def _generate_smart_goals(
        self, employee_data: dict, business_objectives: dict, role_expectations: dict
    ) -> list[dict[str, Any]]:
        """Generate SMART goals aligned with business objectives"""
        goals_prompt = f"""
        Generate 3-5 SMART goals for this employee aligned with business objectives:
        Employee: {employee_data.get('basic_info', {})}
        Business Objectives: {business_objectives}
        Role Expectations: {role_expectations}
        Each goal should be:
        - Specific: Clear and well-defined
        - Measurable: Quantifiable metrics
        - Achievable: Realistic and attainable
        - Relevant: Aligned with role and business objectives
        - Time-bound: Clear deadlines
        Format as JSON array with title, description, success_metrics, target_date, category.
        """
        response = await self.llm_gateway.generate_completion(
            messages=[{"role": "user", "content": goals_prompt}],
            model=self.review_model,
        )
        try:
            return json.loads(response)
        except:
            return [{"title": "Performance Goal", "description": "Improve performance"}]
    async def _calculate_performance_rating(
        self, performance_analysis: dict, goal_analysis: dict, peer_feedback: list[dict]
    ) -> PerformanceRating:
        """Calculate overall performance rating"""
        # Weighted scoring algorithm
        weights = {"performance": 0.4, "goals": 0.3, "feedback": 0.3}
        performance_score = performance_analysis.get("overall_score", 0)
        goal_score = goal_analysis.get("achievement_rate", 0) * 100
        feedback_score = (
            sum(f.get("rating", 0) for f in peer_feedback) / len(peer_feedback)
            if peer_feedback
            else 0
        )
        overall_score = (
            performance_score * weights["performance"]
            + goal_score * weights["goals"]
            + feedback_score * weights["feedback"]
        )
        # Map to rating scale
        if overall_score >= 90:
            return PerformanceRating.EXCEEDS_EXPECTATIONS
        elif overall_score >= 75:
            return PerformanceRating.MEETS_EXPECTATIONS
        elif overall_score >= 60:
            return PerformanceRating.PARTIALLY_MEETS
        elif overall_score >= 40:
            return PerformanceRating.BELOW_EXPECTATIONS
        else:
            return PerformanceRating.UNSATISFACTORY
    async def _load_performance_data(self):
        """Load existing performance data"""
        # This would load from Lattice and database
    # Additional helper methods would be implemented here...
    async def _generate_self_assessment_questions(
        self, employee_data: dict, cycle_type: ReviewCycle
    ) -> list[dict]:
        """Generate self-assessment questions"""
        return [
            {
                "question": "What were your key achievements this period?",
                "type": "text",
            },
            {"question": "Rate your goal achievement", "type": "scale", "scale": "1-5"},
        ]
    async def _analyze_goal_achievements(
        self, employee_id: str, review_period: str
    ) -> dict[str, Any]:
        """Analyze goal achievements"""
        return {"achievement_rate": 0.85, "completed_goals": 4, "total_goals": 5}
    async def _generate_manager_assessment(
        self, employee_data: dict, performance_analysis: dict, goal_analysis: dict
    ) -> dict[str, Any]:
        """Generate manager assessment framework"""
        return {"assessment_areas": [], "rating_scale": "1-5", "comments": ""}
# Export the agent
performance_management_agent = PerformanceManagementAgent()
async def main():
    """Main function for testing"""
    await performance_management_agent.initialize()
    # Test performance review
    review_result = await performance_management_agent.conduct_performance_review(
        {
            "employee_id": "emp_001",
            "review_period": "Q4_2024",
            "cycle_type": "quarterly",
        }
    )
    print(f"Review Result: {review_result}")
if __name__ == "__main__":
    asyncio.run(main())
