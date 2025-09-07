"""
Sales Coach Agent - Marcus "The Catalyst" Rodriguez

A persistent AI sales coach with 15+ years of enterprise sales experience.
Known for turning underperformers into top performers through personalized
coaching, strategic deal guidance, and motivational leadership.

Personality: Energetic, results-driven, empathetic mentor who combines
tough love with genuine care for team development.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from .base_persona import BasePersonaAgent, ConversationStyle, PersonalityTrait, PersonaProfile


@dataclass
class SalesMetric:
    """Sales performance metric tracking"""

    rep_id: str
    metric_name: str
    current_value: float
    target_value: float
    trend: str  # "improving", "declining", "stable"
    last_updated: datetime
    benchmark_percentile: Optional[float] = None


@dataclass
class DealCoaching:
    """Deal-specific coaching recommendation"""

    deal_id: str
    stage: str
    risk_level: str
    coaching_points: list[str]
    recommended_actions: list[str]
    confidence_score: float
    created_at: datetime


@dataclass
class SalesSkillAssessment:
    """Individual sales skill assessment"""

    rep_id: str
    skill_category: str
    current_level: float  # 1.0-10.0
    target_level: float
    improvement_plan: list[str]
    practice_exercises: list[str]
    assessment_date: datetime


class SalesCoachAgent(BasePersonaAgent):
    """
    Marcus "The Catalyst" Rodriguez - AI Sales Coach

    A motivational sales mentor with deep enterprise sales experience.
    Specializes in:
    - Deal coaching and strategy
    - Sales skill development
    - Performance improvement
    - Team motivation and morale
    - CRM data analysis for coaching insights
    """

    def __init__(self):
        # Create Marcus's persona profile
        profile = PersonaProfile(
            name="Marcus Rodriguez",
            role="Senior Sales Coach & Performance Catalyst",
            backstory="""
            Marcus "The Catalyst" Rodriguez brings 15+ years of enterprise sales experience
            to Sophia Intel AI. Starting as a struggling SDR who missed his first 6 months
            of quota, Marcus transformed himself into a top performer and eventually VP of Sales
            at two Fortune 500 companies.

            Known for his "Catalyst Method" - turning sales challenges into breakthrough moments
            through personalized coaching and strategic thinking. Marcus has coached over 200
            sales professionals, with 85% achieving quota attainment within 90 days of coaching.

            His philosophy: "Every 'no' is data, every objection is an opportunity, and every
            rep has untapped potential waiting to be unleashed."

            Specialties: Enterprise B2B sales, consultative selling, objection handling,
            deal strategy, pipeline management, and team leadership.
            """,
            avatar_url="/images/personas/marcus-rodriguez.jpg",
            personality_traits=[
                PersonalityTrait.MOTIVATIONAL,
                PersonalityTrait.RESULTS_DRIVEN,
                PersonalityTrait.STRATEGIC,
                PersonalityTrait.SUPPORTIVE,
                PersonalityTrait.ANALYTICAL,
            ],
            conversation_styles={
                "coaching": ConversationStyle.COACHING,
                "deal_review": ConversationStyle.ANALYTICAL,
                "motivation": ConversationStyle.ENCOURAGING,
                "strategy": ConversationStyle.CONSULTING,
                "casual": ConversationStyle.CASUAL,
            },
            expertise_areas=[
                "Enterprise B2B Sales",
                "Consultative Selling",
                "Deal Strategy & Negotiation",
                "Sales Process Optimization",
                "Objection Handling",
                "Pipeline Management",
                "Sales Team Leadership",
                "CRM Analytics",
                "Sales Forecasting",
                "Competitive Intelligence",
            ],
            catchphrases=[
                "Let's turn that challenge into your next breakthrough!",
                "Every great deal starts with understanding the real problem.",
                "Data tells us what happened, coaching tells us what happens next.",
                "Your pipeline is only as strong as your process.",
                "Champions are made in the follow-up, not the first call.",
            ],
            values=[
                "Authentic relationship building",
                "Continuous learning and improvement",
                "Data-driven decision making",
                "Team success over individual glory",
                "Ethical selling practices",
            ],
            communication_preferences={
                "style": "Direct but encouraging",
                "feedback_approach": "Constructive with actionable insights",
                "motivation_method": "Challenge-based growth",
                "data_presentation": "Visual with storytelling",
                "coaching_frequency": "Weekly check-ins with ad-hoc support",
            },
        )

        super().__init__(profile, memory_capacity=15000)

        # Sales-specific attributes
        self.rep_assessments: dict[str, SalesSkillAssessment] = {}
        self.deal_coaching_history: list[DealCoaching] = []
        self.sales_methodologies: dict[str, dict[str, Any]] = self._initialize_methodologies()
        self.performance_trends: dict[str, list[SalesMetric]] = {}
        self.coaching_templates: dict[str, str] = self._initialize_coaching_templates()

        # Learning and adaptation
        self.successful_coaching_patterns: list[str] = []
        self.rep_learning_styles: dict[str, str] = {}  # Visual, auditory, kinesthetic
        self.industry_insights: dict[str, Any] = {}

    async def process_interaction(self, user_input: str, context: dict[str, Any]) -> dict[str, Any]:
        """Process sales coaching interaction"""
        interaction_type = context.get("type", "general_coaching")
        rep_id = context.get("rep_id")

        # Store interaction in memory
        self.store_memory(
            content=f"Coaching interaction: {user_input}",
            context=f"rep_{rep_id}_{interaction_type}",
            importance_score=0.7,
            metadata={"rep_id": rep_id, "interaction_type": interaction_type, "context": context},
        )

        # Route to appropriate coaching method
        if interaction_type == "deal_coaching":
            return await self._provide_deal_coaching(user_input, context)
        elif interaction_type == "skill_development":
            return await self._provide_skill_coaching(user_input, context)
        elif interaction_type == "performance_review":
            return await self._conduct_performance_review(user_input, context)
        elif interaction_type == "motivation":
            return await self._provide_motivation(user_input, context)
        else:
            return await self._general_coaching(user_input, context)

    def get_persona_greeting(self, user_name: Optional[str] = None) -> str:
        """Generate Marcus's signature greeting"""
        greetings = [
            f"Hey {user_name or 'there'}! Ready to turn today's challenges into tomorrow's victories?",
            f"What's up, {user_name or 'champion'}? Let's see what opportunities are hiding in your pipeline!",
            f"Marcus here! {user_name or 'Team'}, what deals are we going to close today?",
            f"Good to see you, {user_name or 'superstar'}! What's the play we're calling today?",
        ]

        import random

        base_greeting = random.choice(greetings)

        # Add context based on time of day
        hour = datetime.now().hour
        if hour < 10:
            time_context = " Hope you're starting strong this morning!"
        elif hour > 17:
            time_context = " Let's finish the day on a high note!"
        else:
            time_context = " Let's keep the momentum going!"

        return f"{base_greeting}{time_context}"

    async def analyze_domain_specific_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Analyze sales data for coaching insights"""
        analysis_type = data.get("type", "performance")

        if analysis_type == "crm_data":
            return await self._analyze_crm_data(data)
        elif analysis_type == "deal_analysis":
            return await self._analyze_deal_data(data)
        elif analysis_type == "rep_performance":
            return await self._analyze_rep_performance(data)
        elif analysis_type == "pipeline_health":
            return await self._analyze_pipeline_health(data)
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}

    async def _provide_deal_coaching(
        self, user_input: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Provide specific deal coaching"""
        deal_data = context.get("deal_data", {})
        deal_stage = deal_data.get("stage", "unknown")
        deal_data.get("value", 0)

        # Retrieve relevant coaching patterns
        relevant_memories = self.retrieve_memories(
            f"deal coaching {deal_stage} {user_input}", limit=5
        )

        # Generate coaching recommendations
        coaching_points = await self._generate_deal_coaching_points(deal_data, user_input)
        risk_assessment = self._assess_deal_risk(deal_data)
        next_actions = await self._recommend_next_actions(deal_data, user_input)

        # Learn from this coaching session
        self.learn_pattern(
            pattern_type="deal_coaching",
            description=f"Deal in {deal_stage} stage requiring {user_input} guidance",
            supporting_evidence=[mem.id for mem in relevant_memories],
        )

        response = self._format_deal_coaching_response(
            coaching_points, risk_assessment, next_actions, deal_data
        )

        return {
            "response": self.generate_response_with_personality(response, context),
            "coaching_type": "deal_specific",
            "deal_risk": risk_assessment,
            "recommended_actions": next_actions,
            "follow_up_needed": len(next_actions) > 0,
        }

    async def _provide_skill_coaching(
        self, user_input: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Provide sales skill development coaching"""
        rep_id = context.get("rep_id")
        skill_area = context.get("skill_area", "general")

        # Get or create skill assessment
        if rep_id not in self.rep_assessments:
            self.rep_assessments[rep_id] = await self._assess_rep_skills(rep_id, context)

        assessment = self.rep_assessments[rep_id]

        # Generate personalized skill development plan
        development_plan = await self._create_skill_development_plan(
            assessment, skill_area, user_input
        )

        # Create practice exercises
        exercises = self._generate_practice_exercises(skill_area, assessment.current_level)

        response = self._format_skill_coaching_response(development_plan, exercises, assessment)

        return {
            "response": self.generate_response_with_personality(response, context),
            "coaching_type": "skill_development",
            "development_plan": development_plan,
            "practice_exercises": exercises,
            "current_skill_level": assessment.current_level,
            "target_skill_level": assessment.target_level,
        }

    async def _conduct_performance_review(
        self, user_input: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Conduct comprehensive performance review"""
        rep_id = context.get("rep_id")
        performance_data = context.get("performance_data", {})

        # Analyze performance trends
        trends = self._analyze_performance_trends(rep_id, performance_data)

        # Identify strengths and improvement areas
        strengths = self._identify_strengths(performance_data)
        improvement_areas = self._identify_improvement_areas(performance_data)

        # Generate specific recommendations
        recommendations = await self._generate_performance_recommendations(
            rep_id, trends, strengths, improvement_areas
        )

        response = self._format_performance_review(
            trends, strengths, improvement_areas, recommendations
        )

        return {
            "response": self.generate_response_with_personality(response, context),
            "coaching_type": "performance_review",
            "performance_trends": trends,
            "strengths": strengths,
            "improvement_areas": improvement_areas,
            "recommendations": recommendations,
        }

    async def _provide_motivation(self, user_input: str, context: dict[str, Any]) -> dict[str, Any]:
        """Provide motivational coaching"""
        motivation_type = context.get("motivation_type", "general")
        current_mood = context.get("mood", "neutral")

        # Retrieve successful motivation patterns
        self.retrieve_memories(f"motivation {motivation_type} {current_mood}", limit=3)

        # Generate personalized motivation
        motivation_message = self._generate_motivational_message(
            motivation_type, current_mood, user_input
        )

        # Add success story if appropriate
        if current_mood in ["discouraged", "frustrated"]:
            success_story = self._get_relevant_success_story(context)
            if success_story:
                motivation_message += f"\n\n{success_story}"

        response = motivation_message

        return {
            "response": self.generate_response_with_personality(
                response, {**context, "needs_motivation": True, "casual_context": True}
            ),
            "coaching_type": "motivation",
            "motivation_type": motivation_type,
            "follow_up_action": "Check in within 24 hours",
        }

    async def _general_coaching(self, user_input: str, context: dict[str, Any]) -> dict[str, Any]:
        """Provide general sales coaching"""
        # Extract coaching topic from input
        coaching_topic = self._extract_coaching_topic(user_input)

        # Get relevant coaching template
        template = self.coaching_templates.get(coaching_topic, self.coaching_templates["general"])

        # Personalize response based on user history
        personalized_response = await self._personalize_coaching_response(
            template, user_input, context
        )

        return {
            "response": self.generate_response_with_personality(personalized_response, context),
            "coaching_type": "general",
            "topic": coaching_topic,
        }

    async def _define_initial_goals(self) -> list[str]:
        """Define Marcus's initial coaching goals"""
        return [
            "Help every rep exceed their monthly quota",
            "Improve average deal size by 15%",
            "Reduce sales cycle length by 10%",
            "Increase win rate to 25%+",
            "Develop next generation of sales leaders",
            "Build a culture of continuous learning",
            "Maintain team morale above 8.5/10",
        ]

    def _initialize_methodologies(self) -> dict[str, dict[str, Any]]:
        """Initialize sales methodologies Marcus teaches"""
        return {
            "catalyst_method": {
                "name": "The Catalyst Method",
                "stages": ["Discovery", "Challenge", "Solution", "Value", "Close"],
                "key_principles": [
                    "Understand before being understood",
                    "Challenge assumptions respectfully",
                    "Quantify business impact",
                    "Create urgency through value",
                ],
            },
            "consultative_selling": {
                "name": "Consultative Selling",
                "focus": "Problem-solving partnership",
                "techniques": ["Active listening", "Diagnostic questioning", "Solution crafting"],
            },
            "challenger_sale": {
                "name": "Challenger Sale",
                "approach": "Teach, Tailor, Take Control",
                "when_to_use": "Complex B2B sales with multiple stakeholders",
            },
        }

    def _initialize_coaching_templates(self) -> dict[str, str]:
        """Initialize coaching response templates"""
        return {
            "objection_handling": """
            Great question about handling objections! Here's my Catalyst approach:

            1. **Listen Fully**: Let them express their concern completely
            2. **Acknowledge**: "I understand your concern about [specific objection]"
            3. **Question Deeper**: "Help me understand what's behind that concern"
            4. **Reframe**: Position the objection as a buying criteria
            5. **Provide Evidence**: Share relevant proof points or case studies

            Remember: Objections are buying signals in disguise!
            """,
            "prospecting": """
            Let's boost your prospecting game! Here's what top performers do differently:

            **The 3P Formula:**
            - **Personalize**: Reference something specific about their business
            - **Provoke**: Share an insight that challenges their thinking
            - **Propose**: Suggest a specific next step

            Quality over quantity always wins in prospecting!
            """,
            "closing": """
            Closing is just the natural conclusion of great discovery! Here's my approach:

            **The Assumption Close Framework:**
            1. Summarize the agreed-upon challenges
            2. Confirm the value of solving them
            3. Assume they want to move forward
            4. Ask about implementation timing, not if they want to buy

            "When would you like to start seeing these results?"
            """,
            "general": """
            I love that you're thinking strategically about this! Let me share some
            insights from my experience and what I'm seeing work in the field...
            """,
        }

    async def _analyze_crm_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Analyze CRM data for coaching insights"""
        # Placeholder for CRM data analysis
        insights = {
            "pipeline_health": "Strong",
            "activity_trends": "Increasing",
            "conversion_rates": "Above average",
            "coaching_priorities": [
                "Focus on larger deal sizes",
                "Improve follow-up consistency",
                "Strengthen discovery process",
            ],
        }
        return insights

    def _assess_deal_risk(self, deal_data: dict[str, Any]) -> str:
        """Assess risk level of a deal"""
        risk_factors = 0

        # Check various risk factors
        if deal_data.get("last_activity_days", 0) > 14:
            risk_factors += 1
        if not deal_data.get("champion_identified", False):
            risk_factors += 1
        if not deal_data.get("budget_confirmed", False):
            risk_factors += 1
        if not deal_data.get("timeline_defined", False):
            risk_factors += 1

        if risk_factors >= 3:
            return "HIGH"
        elif risk_factors >= 2:
            return "MEDIUM"
        else:
            return "LOW"

    async def _generate_deal_coaching_points(
        self, deal_data: dict[str, Any], question: str
    ) -> list[str]:
        """Generate specific coaching points for a deal"""
        points = []
        deal_data.get("stage", "")

        if "discovery" in question.lower():
            points.extend(
                [
                    "Ask about their current process and pain points",
                    "Quantify the cost of their current solution",
                    "Identify all decision makers and influencers",
                    "Understand their success criteria",
                ]
            )
        elif "closing" in question.lower():
            points.extend(
                [
                    "Review all agreed-upon value propositions",
                    "Address any remaining concerns directly",
                    "Create urgency through business impact",
                    "Ask for the business with confidence",
                ]
            )
        elif "objection" in question.lower():
            points.extend(
                [
                    "Listen completely before responding",
                    "Ask clarifying questions to understand the root concern",
                    "Provide specific evidence to address the objection",
                    "Confirm the objection is resolved before moving forward",
                ]
            )

        return points

    async def _recommend_next_actions(self, deal_data: dict[str, Any], context: str) -> list[str]:
        """Recommend specific next actions for a deal"""
        actions = []
        stage = deal_data.get("stage", "")

        if stage == "discovery":
            actions.extend(
                [
                    "Schedule stakeholder mapping session",
                    "Conduct economic buyer interview",
                    "Prepare custom ROI analysis",
                ]
            )
        elif stage == "proposal":
            actions.extend(
                [
                    "Schedule proposal presentation",
                    "Prepare for objection handling",
                    "Identify champions for internal selling",
                ]
            )

        return actions

    def _format_deal_coaching_response(
        self,
        coaching_points: list[str],
        risk_level: str,
        actions: list[str],
        deal_data: dict[str, Any],
    ) -> str:
        """Format deal coaching response"""
        response = f"""
        **Deal Analysis & Coaching:**

        **Risk Level: {risk_level}**

        **Key Coaching Points:**
        """

        for i, point in enumerate(coaching_points, 1):
            response += f"\n{i}. {point}"

        if actions:
            response += "\n\n**Recommended Next Actions:**"
            for action in actions:
                response += f"\n• {action}"

        response += "\n\nYou've got this! Every deal is an opportunity to create value and solve real problems."

        return response.strip()

    def _generate_motivational_message(self, motivation_type: str, mood: str, context: str) -> str:
        """Generate personalized motivational message"""
        if mood == "discouraged":
            return """
            Hey, I get it - sales can be tough sometimes. But here's what I know about you:
            you're here asking the right questions, which means you're committed to getting better.

            Every top performer I've coached has been exactly where you are right now. The difference?
            They used setbacks as setup for comebacks. Your next breakthrough is closer than you think.

            What's one small win we can focus on today?
            """
        elif mood == "frustrated":
            return """
            That frustration you're feeling? It's actually a good sign - it means you care and
            you have high standards. Channel that energy into focused action.

            Let's break this down into manageable pieces. What's the ONE thing that's causing
            the most friction right now? We'll tackle that first, then build momentum.

            Remember: every expert was once a beginner, and every pro was once an amateur.
            """
        else:
            return """
            I love the energy! Let's harness that momentum and turn it into results.
            What's your biggest opportunity right now? How can we 10x your impact this week?

            Keep that positive attitude - it's contagious and your prospects feel it too!
            """

    def _get_relevant_success_story(self, context: dict[str, Any]) -> Optional[str]:
        """Get relevant success story for motivation"""
        stories = [
            """
            **Success Story:** I once coached a rep who was at 40% of quota in Q3.
            We focused on just improving her discovery process - asking better questions
            and really listening. By Q4, she closed three deals in her pipeline that
            had been stalled for months. She finished the year at 115% of quota.

            The lesson? Sometimes small improvements in process create breakthrough results.
            """,
            """
            **Success Story:** One of my favorite coaching wins was with a rep who was
            terrified of calling C-level executives. We role-played until he felt
            confident, then he made one call to a CEO. That single call turned into
            the biggest deal of his career - $2.3M ARR.

            Courage + preparation = career-defining moments.
            """,
        ]

        import random

        return random.choice(stories)

    def _extract_coaching_topic(self, user_input: str) -> str:
        """Extract the main coaching topic from user input"""
        input_lower = user_input.lower()

        if any(word in input_lower for word in ["objection", "pushback", "concern"]):
            return "objection_handling"
        elif any(word in input_lower for word in ["prospect", "outreach", "cold"]):
            return "prospecting"
        elif any(word in input_lower for word in ["close", "closing", "ask"]):
            return "closing"
        elif any(word in input_lower for word in ["discovery", "question", "qualify"]):
            return "discovery"
        else:
            return "general"

    async def _personalize_coaching_response(
        self, template: str, user_input: str, context: dict[str, Any]
    ) -> str:
        """Personalize coaching response based on user history"""
        # Get relevant memories for personalization
        relevant_memories = self.retrieve_memories(user_input, limit=3)

        personalization = ""
        if relevant_memories:
            # Add context from previous interactions
            personalization = "\nBased on what we've discussed before, "

        return f"{personalization}{template}"

    # Additional helper methods for skill assessment, performance analysis, etc.
    async def _assess_rep_skills(
        self, rep_id: str, context: dict[str, Any]
    ) -> SalesSkillAssessment:
        """Create initial skill assessment for rep"""
        return SalesSkillAssessment(
            rep_id=rep_id,
            skill_category="general",
            current_level=5.0,  # Default starting level
            target_level=8.0,
            improvement_plan=[],
            practice_exercises=[],
            assessment_date=datetime.utcnow(),
        )

    async def _create_skill_development_plan(
        self, assessment: SalesSkillAssessment, skill_area: str, input_text: str
    ) -> list[str]:
        """Create personalized skill development plan"""
        return [
            f"Focus on {skill_area} fundamentals",
            "Practice with role-play scenarios",
            "Review top performer recordings",
            "Implement new techniques in next 3 calls",
        ]

    def _generate_practice_exercises(self, skill_area: str, current_level: float) -> list[str]:
        """Generate practice exercises based on skill area and level"""
        exercises = {
            "discovery": [
                "Practice the 'Tell me more about that' technique",
                "Role-play stakeholder mapping conversations",
                "Create industry-specific question banks",
            ],
            "closing": [
                "Practice assumption close scenarios",
                "Role-play objection handling flows",
                "Master the trial close technique",
            ],
        }

        return exercises.get(skill_area, ["General sales skills practice"])

    def _format_skill_coaching_response(
        self, plan: list[str], exercises: list[str], assessment: SalesSkillAssessment
    ) -> str:
        """Format skill coaching response"""
        response = f"""
        **Skill Development Plan:**

        **Current Level:** {assessment.current_level}/10
        **Target Level:** {assessment.target_level}/10

        **Development Actions:**
        """

        for i, action in enumerate(plan, 1):
            response += f"\n{i}. {action}"

        response += "\n\n**Practice Exercises:**"
        for exercise in exercises:
            response += f"\n• {exercise}"

        return response.strip()

    def _analyze_performance_trends(self, rep_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Analyze rep performance trends"""
        return {
            "trend": "improving",
            "key_metrics": {
                "quota_attainment": 0.85,
                "activity_level": "above_average",
                "win_rate": 0.22,
            },
        }

    def _identify_strengths(self, performance_data: dict[str, Any]) -> list[str]:
        """Identify rep strengths"""
        return [
            "Excellent relationship building",
            "Strong follow-up consistency",
            "Good at identifying decision makers",
        ]

    def _identify_improvement_areas(self, performance_data: dict[str, Any]) -> list[str]:
        """Identify areas for improvement"""
        return [
            "Discovery questioning depth",
            "Value proposition articulation",
            "Objection handling confidence",
        ]

    async def _generate_performance_recommendations(
        self, rep_id: str, trends: dict[str, Any], strengths: list[str], improvements: list[str]
    ) -> list[str]:
        """Generate specific performance recommendations"""
        return [
            "Focus next 30 days on improving discovery process",
            "Leverage relationship building strength for referrals",
            "Practice value-based selling techniques",
            "Schedule weekly coaching sessions for objection handling",
        ]

    def _format_performance_review(
        self,
        trends: dict[str, Any],
        strengths: list[str],
        improvements: list[str],
        recommendations: list[str],
    ) -> str:
        """Format performance review response"""
        response = f"""
        **Performance Review Summary:**

        **Overall Trend:** {trends['trend'].title()}

        **Your Strengths:**
        """

        for strength in strengths:
            response += f"\n✅ {strength}"

        response += "\n\n**Growth Opportunities:**"
        for improvement in improvements:
            response += f"\n🎯 {improvement}"

        response += "\n\n**Action Plan:**"
        for i, rec in enumerate(recommendations, 1):
            response += f"\n{i}. {rec}"

        return response.strip()

    async def coach_deal(self, deal_analysis) -> dict[str, Any]:
        """Provide coaching for a specific deal"""
        coaching_points = []
        recommended_actions = []

        # Analyze deal stage
        if deal_analysis.stage.lower() in ["discovery", "qualification"]:
            coaching_points.append("Focus on understanding the client's business impact")
            recommended_actions.append("Schedule a discovery call with key stakeholders")
        elif deal_analysis.stage.lower() in ["proposal", "negotiation"]:
            coaching_points.append("Emphasize value over price in your positioning")
            recommended_actions.append("Create a business case with clear ROI metrics")

        # Analyze probability
        if deal_analysis.probability < 0.3:
            coaching_points.append("This deal needs immediate attention or qualification out")
            recommended_actions.append("Identify and address the main blockers")
        elif deal_analysis.probability > 0.7:
            coaching_points.append("Strong position - focus on closing activities")
            recommended_actions.append("Secure executive sponsor commitment")

        # Analyze competitors
        if deal_analysis.competitors:
            coaching_points.append(
                f"Differentiate against {', '.join(deal_analysis.competitors[:2])}"
            )
            recommended_actions.append("Prepare competitive battle cards")

        return {
            "deal_id": deal_analysis.deal_id,
            "coaching_points": coaching_points,
            "recommended_actions": recommended_actions,
            "confidence_score": deal_analysis.probability,
            "risk_assessment": (
                "high"
                if deal_analysis.probability < 0.3
                else "medium" if deal_analysis.probability < 0.7 else "low"
            ),
            "next_best_action": (
                recommended_actions[0] if recommended_actions else "Schedule strategic review"
            ),
        }

    async def review_performance(self, review_data) -> dict[str, Any]:
        """Review sales performance and provide insights"""
        insights = []
        recommendations = []

        # Analyze metrics
        metrics = review_data.metrics or {}
        attainment = 1.0  # Default to 100% if not provided
        if "quota_attainment" in metrics:
            attainment = metrics["quota_attainment"]
            if attainment < 0.8:
                insights.append("Below quota - need immediate intervention")
                recommendations.append("Daily pipeline review for next 2 weeks")
            elif attainment > 1.2:
                insights.append("Exceeding quota - maintain momentum")
                recommendations.append("Share best practices with team")

        # Analyze deal flow
        deals_closed = len(review_data.deals_closed) if review_data.deals_closed else 0
        deals_lost = len(review_data.deals_lost) if review_data.deals_lost else 0

        if deals_closed + deals_lost > 0:
            win_rate = deals_closed / (deals_closed + deals_lost)
            insights.append(f"Win rate: {win_rate:.1%}")
            if win_rate < 0.3:
                recommendations.append("Focus on qualification criteria")
            elif win_rate > 0.5:
                recommendations.append("Increase pipeline velocity")

        return {
            "rep_id": review_data.rep_id,
            "period": review_data.period,
            "overall_assessment": (
                "needs improvement"
                if attainment < 0.8
                else "on track" if attainment < 1.0 else "exceeding"
            ),
            "insights": insights,
            "recommendations": recommendations,
            "strengths": ["Consistent activity levels", "Good customer relationships"],
            "areas_for_improvement": ["Discovery process", "Objection handling"],
            "action_items": recommendations[:3],
        }

    async def create_skill_development_plan(
        self, rep_id: str, skills: list[str], goals: list[str]
    ) -> dict[str, Any]:
        """Create personalized skill development plan"""
        plan_items = []
        timeline = []
        resources = []

        # Map skills to development activities
        skill_activities = {
            "prospecting": {
                "activities": ["Cold calling role-play", "LinkedIn outreach workshop"],
                "resources": ["Prospecting playbook", "Email templates"],
                "timeline": "Week 1-2",
            },
            "discovery": {
                "activities": ["Question framework training", "Active listening exercises"],
                "resources": ["Discovery call recordings", "SPIN selling guide"],
                "timeline": "Week 2-3",
            },
            "negotiation": {
                "activities": ["Negotiation simulation", "Pricing strategy session"],
                "resources": ["Negotiation tactics guide", "Deal desk collaboration"],
                "timeline": "Week 3-4",
            },
            "closing": {
                "activities": ["Closing techniques workshop", "Objection handling practice"],
                "resources": ["Closing framework", "Common objections guide"],
                "timeline": "Week 4-5",
            },
        }

        for skill in skills:
            skill_lower = skill.lower()
            for key, details in skill_activities.items():
                if key in skill_lower or skill_lower in key:
                    plan_items.extend(details["activities"])
                    resources.extend(details["resources"])
                    timeline.append(details["timeline"])
                    break

        # Add goal-specific elements
        for goal in goals[:3]:  # Focus on top 3 goals
            plan_items.append(f"Goal-focused activity: {goal}")

        return {
            "rep_id": rep_id,
            "plan_duration": "6 weeks",
            "focus_areas": skills[:3],
            "development_activities": plan_items[:5],
            "resources": list(set(resources))[:5],
            "milestones": [
                {"week": 2, "checkpoint": "Initial skill assessment"},
                {"week": 4, "checkpoint": "Mid-plan review"},
                {"week": 6, "checkpoint": "Final evaluation"},
            ],
            "success_metrics": [
                "Complete 80% of activities",
                "Improvement in skill assessments",
                "Apply learnings to active deals",
            ],
            "coaching_sessions": "Weekly 1:1 coaching calls",
        }
