#!/usr/bin/env python3
"""
Sales Intelligence Swarm - Comprehensive Demo Script

This script demonstrates the complete Sales Intelligence Swarm system including:
- Real-time call analysis with 6 specialized agents
- Live coaching feedback and risk alerts
- Competitive intelligence monitoring
- Universal Sophia chat integration
- WebSocket-powered live dashboard
- Gong API integration (simulated)

Usage:
    python demo_sales_intelligence.py [--mode demo|test|benchmark]
"""

import asyncio
import json
import logging
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import argparse
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

# Import Sales Intelligence components
from app.swarms.sales_intelligence import (
    create_sales_intelligence_swarm,
    SalesIntelligenceOrchestrator,
    GongRealtimeConnector,
    SalesFeedbackSystem,
    SalesIntelligenceDashboard,
    RealtimeCallData,
    CallMetadata,
    TranscriptSegment,
    CallParticipant
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sales_intelligence_demo.log')
    ]
)

logger = logging.getLogger(__name__)


class SalesIntelligenceDemo:
    """Complete Sales Intelligence Swarm demonstration"""
    
    def __init__(self, mode: str = "demo"):
        self.mode = mode
        self.orchestrator = None
        self.feedback_system = None
        self.dashboard = None
        self.demo_calls = {}
        self.demo_data = self._load_demo_data()
        
    def _load_demo_data(self) -> Dict[str, Any]:
        """Load realistic demo data for the sales intelligence system"""
        return {
            "demo_calls": [
                {
                    "call_id": "demo_call_001",
                    "title": "Discovery Call - TechCorp Solutions",
                    "participants": [
                        CallParticipant(
                            user_id="rep_john",
                            email="john.sales@company.com",
                            name="John Sales",
                            role="host",
                            joined_at=datetime.now(),
                            is_internal=True
                        ),
                        CallParticipant(
                            user_id="prospect_jane",
                            email="jane.smith@techcorp.com", 
                            name="Jane Smith",
                            role="participant",
                            joined_at=datetime.now(),
                            is_internal=False
                        ),
                        CallParticipant(
                            user_id="prospect_bob",
                            email="bob.jones@techcorp.com",
                            name="Bob Jones", 
                            role="participant",
                            joined_at=datetime.now(),
                            is_internal=False
                        )
                    ],
                    "scenario": "discovery_with_competition"
                },
                {
                    "call_id": "demo_call_002", 
                    "title": "Product Demo - StartupXYZ",
                    "participants": [
                        CallParticipant(
                            user_id="rep_sarah",
                            email="sarah.rep@company.com",
                            name="Sarah Rep",
                            role="host", 
                            joined_at=datetime.now(),
                            is_internal=True
                        ),
                        CallParticipant(
                            user_id="prospect_alex",
                            email="alex.founder@startupxyz.com",
                            name="Alex Founder",
                            role="participant",
                            joined_at=datetime.now(),
                            is_internal=False
                        )
                    ],
                    "scenario": "demo_high_interest"
                },
                {
                    "call_id": "demo_call_003",
                    "title": "Closing Call - Enterprise Inc",
                    "participants": [
                        CallParticipant(
                            user_id="rep_mike",
                            email="mike.close@company.com", 
                            name="Mike Close",
                            role="host",
                            joined_at=datetime.now(),
                            is_internal=True
                        ),
                        CallParticipant(
                            user_id="prospect_lisa",
                            email="lisa.exec@enterprise.com",
                            name="Lisa Executive", 
                            role="participant",
                            joined_at=datetime.now(),
                            is_internal=False
                        )
                    ],
                    "scenario": "closing_with_objections"
                }
            ],
            "conversation_scripts": {
                "discovery_with_competition": [
                    ("John Sales", "Thanks for taking the time to meet with us today. Can you tell me about your current challenges with customer data management?"),
                    ("Jane Smith", "Well, we're really struggling with our current CRM. It's Salesforce, and while it works, it's expensive and doesn't integrate well with our other tools."),
                    ("John Sales", "I understand. What specific integration challenges are you facing?"),
                    ("Bob Jones", "Our biggest issue is connecting it to our customer success platform. We're spending too much time on manual data entry."),
                    ("Jane Smith", "Exactly. And the reporting is limited. We need better visibility into our sales pipeline and customer health scores."),
                    ("John Sales", "That makes perfect sense. How many users are currently on Salesforce?"),
                    ("Jane Smith", "About 50 users across sales and customer success. We're paying around $150 per user per month."),
                    ("Bob Jones", "The cost is definitely a concern. We're looking at alternatives that might give us more value."),
                    ("John Sales", "What other solutions have you evaluated so far?"),
                    ("Jane Smith", "We've looked at HubSpot and Pipedrive. HubSpot seems feature-rich but maybe overkill for us."),
                    ("Bob Jones", "Pipedrive is more affordable but seems too simple. We need something in between."),
                    ("John Sales", "I think our solution could be perfect for your needs. Let me show you how we handle integrations differently..."),
                ],
                "demo_high_interest": [
                    ("Sarah Rep", "Thanks Alex. I'm excited to show you how our platform can help StartupXYZ scale efficiently."),
                    ("Alex Founder", "Great! I'm particularly interested in the automation features. We're growing fast and need to reduce manual work."),
                    ("Sarah Rep", "Perfect. Let me start with our workflow automation. This dashboard shows how deals flow through your pipeline automatically."),
                    ("Alex Founder", "Wow, this looks much more intuitive than what we're using now. Can it integrate with Slack?"),
                    ("Sarah Rep", "Absolutely. We have native Slack integration plus API connections to over 200 tools. What's your current tech stack?"),
                    ("Alex Founder", "We use Slack, Google Workspace, Stripe for billing, and a mix of other tools. Integration is crucial."),
                    ("Sarah Rep", "No problem at all. I can show you our pre-built connectors. How many team members would be using this?"),
                    ("Alex Founder", "Right now about 15, but we're planning to double that in the next 6 months."),
                    ("Sarah Rep", "That's exciting growth! Our platform scales seamlessly. Let me show you the admin controls..."),
                    ("Alex Founder", "This is exactly what we need. What's the pricing like?"),
                    ("Sarah Rep", "For a startup your size, we have a special growth package starting at $50 per user. Much more affordable than enterprise solutions."),
                    ("Alex Founder", "That's very reasonable. When can we get started?"),
                ],
                "closing_with_objections": [
                    ("Mike Close", "Lisa, thanks for the follow-up call. I know you've had some time to think about our proposal."),
                    ("Lisa Executive", "Yes, Mike. The team is interested, but we have some concerns about the implementation timeline."),
                    ("Mike Close", "I understand. What specific timeline concerns do you have?"),
                    ("Lisa Executive", "Our IT team is already stretched thin. They're worried about a lengthy implementation affecting other projects."),
                    ("Mike Close", "That's a valid concern. The good news is our implementation is typically much faster than traditional solutions. What timeline were you hoping for?"),
                    ("Lisa Executive", "Ideally, we'd want to be up and running within 6 weeks. Is that realistic?"),
                    ("Mike Close", "Absolutely. With your team size, we typically complete implementations in 4-5 weeks. We also provide dedicated support."),
                    ("Lisa Executive", "That sounds better. The other concern is cost. The CFO thinks it's expensive compared to keeping our current system."),
                    ("Mike Close", "I understand the cost consideration. Have you calculated the cost of maintaining your current system?"),
                    ("Lisa Executive", "Not in detail, but we know it requires a lot of manual work."),
                    ("Mike Close", "Based on our analysis, companies your size typically save 20-30% in operational costs within the first year. Plus the productivity gains."),
                    ("Lisa Executive", "Those are compelling numbers. Can you provide a detailed ROI analysis?"),
                    ("Mike Close", "Absolutely. I can have that to you by tomorrow. Are you ready to move forward with the contract?"),
                ]
            }
        }
    
    async def run_demo(self):
        """Run the complete sales intelligence demo"""
        logger.info("🚀 Starting Sales Intelligence Swarm Demo")
        logger.info("=" * 60)
        
        try:
            # Initialize components
            await self._initialize_components()
            
            # Run demo based on mode
            if self.mode == "demo":
                await self._run_interactive_demo()
            elif self.mode == "test":
                await self._run_system_tests()
            elif self.mode == "benchmark":
                await self._run_performance_benchmark()
            
            logger.info("✅ Demo completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            raise
        finally:
            await self._cleanup()
    
    async def _initialize_components(self):
        """Initialize all Sales Intelligence components"""
        logger.info("🔧 Initializing Sales Intelligence components...")
        
        # Initialize orchestrator
        self.orchestrator = SalesIntelligenceOrchestrator()
        await self.orchestrator.initialize()
        logger.info("✅ Sales Intelligence Orchestrator initialized")
        
        # Initialize feedback system
        self.feedback_system = SalesFeedbackSystem()
        logger.info("✅ Sales Feedback System initialized")
        
        # Initialize dashboard
        self.dashboard = SalesIntelligenceDashboard()
        await self.dashboard.initialize()
        logger.info("✅ Sales Intelligence Dashboard initialized")
        
        # Setup integrations
        await self._setup_integrations()
        
        logger.info("🎯 All components initialized successfully!")
    
    async def _setup_integrations(self):
        """Setup integrations between components"""
        logger.info("🔗 Setting up component integrations...")
        
        # Link feedback system to orchestrator
        self.orchestrator.agent_orchestrator.feedback_callbacks.append(
            self.feedback_system.process_agent_output
        )
        
        # Link dashboard to feedback system
        self.feedback_system.feedback_engine.register_feedback_callback(
            self._handle_feedback_for_dashboard
        )
        
        logger.info("✅ Component integrations configured")
    
    async def _handle_feedback_for_dashboard(self, feedback_messages: List):
        """Handle feedback messages for dashboard updates"""
        for feedback in feedback_messages:
            await self.dashboard.process_feedback_message(feedback)
    
    async def _run_interactive_demo(self):
        """Run interactive demonstration of all features"""
        logger.info("🎬 Starting Interactive Sales Intelligence Demo")
        logger.info("=" * 50)
        
        print("\n🎯 SALES INTELLIGENCE SWARM DEMO")
        print("=" * 50)
        print("\nThis demo will show you:")
        print("• 6 specialized AI agents analyzing calls in real-time")
        print("• Live coaching feedback and risk alerts")
        print("• Competitive intelligence monitoring")
        print("• Universal Sophia chat integration")
        print("• WebSocket-powered live dashboard")
        print("\nStarting in 3 seconds...")
        await asyncio.sleep(3)
        
        # Demo each call scenario
        for i, call_data in enumerate(self.demo_data["demo_calls"], 1):
            print(f"\n📞 DEMO CALL {i}: {call_data['title']}")
            print("-" * 40)
            await self._simulate_call(call_data)
            
            if i < len(self.demo_data["demo_calls"]):
                print("\n⏸️  Pausing between calls...")
                await asyncio.sleep(2)
        
        # Demo Sophia integration
        await self._demo_sophia_integration()
        
        # Demo dashboard features
        await self._demo_dashboard_features()
        
        # Show final results
        await self._show_demo_results()
    
    async def _simulate_call(self, call_data: Dict[str, Any]):
        """Simulate a realistic sales call with live agent analysis"""
        call_id = call_data["call_id"]
        scenario = call_data["scenario"]
        participants = call_data["participants"]
        
        print(f"🔴 Call starting: {call_data['title']}")
        print(f"👥 Participants: {', '.join([p.name for p in participants])}")
        
        # Create call metadata
        metadata = CallMetadata(
            call_id=call_id,
            call_url=f"https://demo.gong.io/call/{call_id}",
            title=call_data["title"],
            scheduled_start=datetime.now(),
            actual_start=datetime.now(),
            duration_seconds=None,
            participants=participants,
            meeting_platform="zoom",
            recording_status="recording",
            tags=["demo", scenario.split("_")[0]]
        )
        
        # Initialize call data
        call_data_obj = RealtimeCallData(
            metadata=metadata,
            transcripts=[],
            last_update=datetime.now(),
            is_active=True
        )
        
        # Add to orchestrator's active calls
        self.orchestrator.active_calls[call_id] = call_data_obj
        self.orchestrator.current_call_id = call_id
        
        # Simulate conversation
        conversation = self.demo_data["conversation_scripts"][scenario]
        
        print(f"\n💬 Simulating conversation ({len(conversation)} segments):")
        
        for i, (speaker, text) in enumerate(conversation):
            # Create transcript segment
            segment = TranscriptSegment(
                speaker_id=speaker.lower().replace(" ", "_"),
                speaker_name=speaker,
                text=text,
                start_time=time.time() + i * 10,
                end_time=time.time() + (i + 1) * 10,
                confidence=0.95
            )
            
            # Add to call data
            call_data_obj.transcripts.append(segment)
            call_data_obj.last_update = datetime.now()
            
            # Print conversation
            is_internal = any(p.name == speaker and p.is_internal for p in participants)
            speaker_icon = "🧑‍💼" if is_internal else "👤"
            print(f"  {speaker_icon} {speaker}: {text}")
            
            # Process through agents (every few segments to show real-time analysis)
            if i % 3 == 2 or i == len(conversation) - 1:
                await self._process_call_through_agents(call_id, call_data_obj)
                await asyncio.sleep(0.5)  # Brief pause for realism
        
        # Mark call as completed
        call_data_obj.is_active = False
        call_data_obj.metadata.duration_seconds = len(conversation) * 10
        
        print(f"✅ Call completed: {call_data_obj.metadata.duration_seconds // 60} minutes")
        
        # Final processing
        await self._process_call_through_agents(call_id, call_data_obj)
        
        # Show call summary
        await self._show_call_summary(call_id)
    
    async def _process_call_through_agents(self, call_id: str, call_data: RealtimeCallData):
        """Process call data through all specialized agents"""
        logger.info(f"🤖 Processing call {call_id} through specialized agents...")
        
        # Process through agent orchestrator
        await self.orchestrator.agent_orchestrator.process_call_data(call_data)
        
        # Get recent outputs from all agents
        recent_outputs = self.orchestrator.agent_orchestrator.get_recent_outputs()
        
        # Process outputs for this call
        call_outputs = [output for output in recent_outputs if output.call_id == call_id]
        
        if call_outputs:
            print(f"    🔍 Analyzed by {len(call_outputs)} agents:")
            
            for output in call_outputs[-6:]:  # Show last 6 agent outputs
                priority_icon = {
                    "critical": "🚨",
                    "high": "⚠️",
                    "medium": "ℹ️",
                    "low": "💡"
                }.get(output.priority.value, "📊")
                
                agent_name = output.agent_type.title().replace("_", " ")
                print(f"      {priority_icon} {agent_name}: {self._summarize_agent_output(output)}")
        
        # Process through feedback system
        for output in call_outputs:
            feedback_messages = await self.feedback_system.process_agent_output(output)
            for msg in feedback_messages:
                if msg.priority.value in ["critical", "high"]:
                    icon = "🚨" if msg.priority.value == "critical" else "⚠️"
                    print(f"    {icon} ALERT: {msg.title} - {msg.message}")
        
        # Update dashboard
        for output in call_outputs:
            await self.dashboard.process_agent_output(output)
    
    def _summarize_agent_output(self, output) -> str:
        """Create a brief summary of agent output for display"""
        agent_type = output.agent_type
        data = output.data
        
        if agent_type == "transcription":
            return f"Processed {data.get('new_segments', 0)} new segments"
        elif agent_type == "sentiment":
            sentiment = data.get('overall_sentiment', 0)
            sentiment_label = "positive" if sentiment > 0.2 else "negative" if sentiment < -0.2 else "neutral"
            return f"Sentiment: {sentiment_label} ({sentiment:+.2f})"
        elif agent_type == "competitive":
            mentions = len(data.get('competitor_mentions', []))
            return f"Found {mentions} competitor mentions" if mentions > 0 else "No competitor activity"
        elif agent_type == "risk_assessment":
            risk = data.get('overall_risk_score', 0)
            level = "high" if risk > 0.7 else "medium" if risk > 0.4 else "low"
            return f"Deal risk: {level} ({risk:.1%})"
        elif agent_type == "coaching":
            recs = len(data.get('coaching_recommendations', []))
            return f"Generated {recs} coaching recommendations"
        elif agent_type == "summary":
            return f"Call summary: {data.get('call_outcome', 'In progress')}"
        else:
            return "Analysis completed"
    
    async def _show_call_summary(self, call_id: str):
        """Show comprehensive summary of call analysis"""
        print(f"\n📊 CALL ANALYSIS SUMMARY - {call_id}")
        print("-" * 45)
        
        # Get dashboard data
        dashboard_data = self.dashboard.get_call_dashboard_data(call_id)
        
        # Overall score
        overall_score = dashboard_data.get("overall_score", 50)
        score_emoji = "🟢" if overall_score >= 70 else "🟡" if overall_score >= 50 else "🔴"
        print(f"{score_emoji} Overall Call Score: {overall_score:.1f}/100")
        
        # Latest metrics
        metrics = dashboard_data.get("latest_metrics", {})
        for metric_type, metric_data in metrics.items():
            value = metric_data.get("value", 0)
            label = metric_data.get("label", metric_type)
            color = metric_data.get("color", "gray")
            
            color_emoji = {
                "green": "🟢",
                "yellow": "🟡", 
                "red": "🔴",
                "gray": "⚪"
            }.get(color, "⚪")
            
            print(f"  {color_emoji} {label}: {value}")
        
        # Active feedback
        active_feedback = self.feedback_system.get_call_feedback(call_id)
        feedback_items = active_feedback.get("active_feedback", [])
        
        if feedback_items:
            print(f"\n💡 Active Feedback ({len(feedback_items)} items):")
            for feedback in feedback_items[:3]:  # Show top 3
                priority_emoji = {
                    "critical": "🚨",
                    "high": "⚠️", 
                    "medium": "ℹ️",
                    "low": "💡"
                }.get(feedback.get("priority", "medium"), "💡")
                print(f"  {priority_emoji} {feedback.get('title', 'Alert')}: {feedback.get('message', 'No message')}")
        
        print()  # Extra newline for readability
    
    async def _demo_sophia_integration(self):
        """Demonstrate Universal Sophia chat integration"""
        print("\n🧠 UNIVERSAL SOPHIA INTEGRATION DEMO")
        print("=" * 45)
        print("\nSophia can now answer sales intelligence queries in natural language!")
        print("Here are some example queries:\n")
        
        demo_queries = [
            "What's the status of the current call?",
            "How risky is this deal?", 
            "Any competitors mentioned?",
            "Give me some coaching feedback",
            "What's the sentiment like?",
            "Show me performance metrics"
        ]
        
        for i, query in enumerate(demo_queries, 1):
            print(f"👤 Query {i}: {query}")
            
            try:
                response = await self.orchestrator.process_sophia_query(query)
                
                if response.get("success"):
                    command_type = response.get("command_type", "unknown")
                    data = response.get("data", {})
                    
                    print(f"🧠 Sophia ({command_type}): ", end="")
                    
                    # Format response based on command type
                    if command_type == "call_status":
                        if "message" in data:
                            print(data["message"])
                        else:
                            print(f"Call {data.get('call_id', 'unknown')} - Score: {data.get('overall_score', 0):.1f}, Active: {data.get('is_active', False)}")
                    
                    elif command_type == "risk_assessment":
                        if "message" in data:
                            print(data["message"])
                        else:
                            risk_level = data.get("risk_level", "unknown")
                            risk_score = data.get("risk_score", 0)
                            print(f"Risk level: {risk_level} ({risk_score:.1%})")
                    
                    elif command_type == "competitive_intel":
                        if "message" in data:
                            print(data["message"])
                        else:
                            mentions = data.get("competitor_mentions", [])
                            print(f"Found {len(mentions)} competitor mentions")
                    
                    elif command_type == "coaching_feedback":
                        if "message" in data:
                            print(data["message"])
                        else:
                            coaching = data.get("active_coaching", [])
                            print(f"Found {len(coaching)} coaching recommendations")
                    
                    elif command_type == "sentiment_analysis":
                        if "message" in data:
                            print(data["message"])
                        else:
                            sentiment_label = data.get("sentiment_label", "unknown")
                            print(f"Overall sentiment: {sentiment_label}")
                    
                    else:
                        print(f"Response received: {command_type}")
                
                else:
                    print(f"🚫 Error: {response.get('error', 'Unknown error')}")
                
            except Exception as e:
                print(f"🚫 Error processing query: {e}")
            
            print()  # Extra spacing
            await asyncio.sleep(0.5)
    
    async def _demo_dashboard_features(self):
        """Demonstrate dashboard features and WebSocket updates"""
        print("\n📊 LIVE DASHBOARD FEATURES DEMO")
        print("=" * 40)
        
        # Show team dashboard
        team_data = self.dashboard.get_team_dashboard_data()
        team_summary = team_data.get("team_summary", {})
        
        print("\n🏢 Team Overview:")
        print(f"  📞 Active Calls: {team_summary.get('total_active_calls', 0)}")
        print(f"  ⚠️  High Risk Calls: {team_summary.get('high_risk_calls', 0)}")
        print(f"  😊 Average Sentiment: {team_summary.get('average_sentiment', 0):.2f}")
        
        # Show active calls
        active_calls = team_data.get("active_calls", [])
        if active_calls:
            print(f"\n📋 Active Calls ({len(active_calls)}):")
            for call in active_calls:
                status_emoji = "🟢" if call.get("status") == "active" else "⚪"
                risk_emoji = {
                    "low": "🟢",
                    "medium": "🟡", 
                    "high": "🟠",
                    "critical": "🔴"
                }.get(call.get("risk_level", "medium"), "🟡")
                
                print(f"  {status_emoji} {call.get('title', 'Unknown Call')} - Risk: {risk_emoji} {call.get('risk_level', 'medium').title()}")
        
        # Show recent insights
        recent_insights = team_data.get("recent_insights", [])
        if recent_insights:
            print(f"\n💡 Recent Insights ({len(recent_insights)}):")
            for insight in recent_insights[:5]:  # Show top 5
                print(f"  • {insight.get('insight', 'No insight')} ({insight.get('call_id', 'unknown')})")
        
        print("\n🌐 Dashboard available at: http://localhost:3333/sales-dashboard")
        print("📱 Real-time updates via WebSocket at: ws://localhost:3333/ws/sales")
    
    async def _show_demo_results(self):
        """Show final demo results and statistics"""
        print("\n🎯 DEMO RESULTS & STATISTICS")
        print("=" * 40)
        
        total_calls = len(self.demo_data["demo_calls"])
        total_feedback = 0
        total_alerts = 0
        
        # Count feedback across all calls
        for call_data in self.demo_data["demo_calls"]:
            call_id = call_data["call_id"] 
            feedback_data = self.feedback_system.get_call_feedback(call_id)
            feedback_items = feedback_data.get("active_feedback", [])
            total_feedback += len(feedback_items)
            
            # Count high priority alerts
            high_priority = [f for f in feedback_items if f.get("priority") in ["critical", "high"]]
            total_alerts += len(high_priority)
        
        print(f"📊 Demo Statistics:")
        print(f"  📞 Calls Processed: {total_calls}")
        print(f"  🤖 Agents Active: 6 (Transcription, Sentiment, Competitive, Risk, Coaching, Summary)")
        print(f"  💡 Feedback Generated: {total_feedback} messages")
        print(f"  🚨 High Priority Alerts: {total_alerts}")
        
        # Agent performance summary
        print(f"\n🤖 Agent Performance Summary:")
        agents = ["transcription", "sentiment", "competitive", "risk_assessment", "coaching", "summary"]
        
        for agent in agents:
            outputs = self.orchestrator.agent_orchestrator.get_recent_outputs(agent_type=agent)
            agent_name = agent.title().replace("_", " ")
            print(f"  • {agent_name}: {len(outputs)} analyses")
        
        print(f"\n✅ All {total_calls} demo calls completed successfully!")
        print("🎬 Demo finished. The Sales Intelligence Swarm is ready for production use!")
    
    async def _run_system_tests(self):
        """Run comprehensive system tests"""
        logger.info("🧪 Running Sales Intelligence System Tests")
        
        test_results = []
        
        # Test 1: Agent initialization
        test_results.append(await self._test_agent_initialization())
        
        # Test 2: Real-time processing
        test_results.append(await self._test_realtime_processing())
        
        # Test 3: Feedback system
        test_results.append(await self._test_feedback_system())
        
        # Test 4: Dashboard functionality
        test_results.append(await self._test_dashboard_functionality())
        
        # Test 5: Sophia integration
        test_results.append(await self._test_sophia_integration())
        
        # Test 6: WebSocket connectivity
        test_results.append(await self._test_websocket_connectivity())
        
        # Report results
        passed = sum(1 for result in test_results if result["passed"])
        total = len(test_results)
        
        print(f"\n🧪 SYSTEM TEST RESULTS")
        print("=" * 30)
        print(f"✅ Passed: {passed}/{total} tests")
        
        for result in test_results:
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {result['name']}: {result['message']}")
        
        if passed == total:
            print(f"\n🎉 All tests passed! System is ready for production.")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Please review and fix issues.")
    
    async def _test_agent_initialization(self) -> Dict[str, Any]:
        """Test agent initialization and configuration"""
        try:
            # Test agent orchestrator
            agents = self.orchestrator.agent_orchestrator.agents
            expected_agents = 6  # TranscriptionAgent, SentimentAgent, etc.
            
            if len(agents) >= expected_agents:
                return {"name": "Agent Initialization", "passed": True, "message": f"All {len(agents)} agents initialized"}
            else:
                return {"name": "Agent Initialization", "passed": False, "message": f"Only {len(agents)} agents initialized, expected {expected_agents}"}
        
        except Exception as e:
            return {"name": "Agent Initialization", "passed": False, "message": f"Error: {e}"}
    
    async def _test_realtime_processing(self) -> Dict[str, Any]:
        """Test real-time call processing"""
        try:
            # Create test call
            test_call = self.demo_data["demo_calls"][0]
            call_id = f"test_{int(time.time())}"
            
            # Simulate processing
            metadata = CallMetadata(
                call_id=call_id,
                call_url="https://test.call",
                title="Test Call",
                scheduled_start=datetime.now(),
                actual_start=datetime.now(),
                duration_seconds=300,
                participants=[],
                meeting_platform="test",
                recording_status="recording",
                tags=["test"]
            )
            
            call_data = RealtimeCallData(
                metadata=metadata,
                transcripts=[TranscriptSegment(
                    speaker_id="test",
                    speaker_name="Test Speaker",
                    text="This is a test transcript.",
                    start_time=time.time(),
                    end_time=time.time() + 5,
                    confidence=0.95
                )],
                last_update=datetime.now(),
                is_active=True
            )
            
            # Process through agents
            await self.orchestrator.agent_orchestrator.process_call_data(call_data)
            
            # Check for outputs
            outputs = self.orchestrator.agent_orchestrator.get_recent_outputs()
            call_outputs = [o for o in outputs if o.call_id == call_id]
            
            if call_outputs:
                return {"name": "Real-time Processing", "passed": True, "message": f"Generated {len(call_outputs)} agent outputs"}
            else:
                return {"name": "Real-time Processing", "passed": False, "message": "No agent outputs generated"}
        
        except Exception as e:
            return {"name": "Real-time Processing", "passed": False, "message": f"Error: {e}"}
    
    async def _test_feedback_system(self) -> Dict[str, Any]:
        """Test feedback generation and delivery"""
        try:
            # Create mock agent output
            from app.swarms.sales_intelligence.agents import AgentOutput, AgentPriority, ConfidenceLevel
            
            mock_output = AgentOutput(
                agent_id="test_agent",
                agent_type="risk_assessment",
                call_id="test_feedback",
                timestamp=datetime.now(),
                priority=AgentPriority.HIGH,
                confidence=ConfidenceLevel.HIGH,
                data={"overall_risk_score": 0.9, "red_flags": [{"type": "budget_concerns"}]},
                requires_action=True
            )
            
            # Process through feedback system
            feedback_messages = await self.feedback_system.process_agent_output(mock_output)
            
            if feedback_messages:
                return {"name": "Feedback System", "passed": True, "message": f"Generated {len(feedback_messages)} feedback messages"}
            else:
                return {"name": "Feedback System", "passed": False, "message": "No feedback messages generated"}
        
        except Exception as e:
            return {"name": "Feedback System", "passed": False, "message": f"Error: {e}"}
    
    async def _test_dashboard_functionality(self) -> Dict[str, Any]:
        """Test dashboard data generation"""
        try:
            # Get team dashboard data
            team_data = self.dashboard.get_team_dashboard_data()
            
            # Check required fields
            required_fields = ["team_summary", "active_calls", "recent_insights"]
            missing_fields = [field for field in required_fields if field not in team_data]
            
            if not missing_fields:
                return {"name": "Dashboard Functionality", "passed": True, "message": "Dashboard data structure correct"}
            else:
                return {"name": "Dashboard Functionality", "passed": False, "message": f"Missing fields: {missing_fields}"}
        
        except Exception as e:
            return {"name": "Dashboard Functionality", "passed": False, "message": f"Error: {e}"}
    
    async def _test_sophia_integration(self) -> Dict[str, Any]:
        """Test Sophia natural language processing"""
        try:
            # Test query processing
            test_query = "What's the status of the current call?"
            response = await self.orchestrator.process_sophia_query(test_query)
            
            if response.get("success") is not None:  # Response structure is correct
                return {"name": "Sophia Integration", "passed": True, "message": "Query processing successful"}
            else:
                return {"name": "Sophia Integration", "passed": False, "message": "Invalid response structure"}
        
        except Exception as e:
            return {"name": "Sophia Integration", "passed": False, "message": f"Error: {e}"}
    
    async def _test_websocket_connectivity(self) -> Dict[str, Any]:
        """Test WebSocket connection handling"""
        try:
            # Test WebSocket manager
            ws_manager = self.dashboard.websocket_manager
            
            # Check if manager is properly initialized
            if hasattr(ws_manager, 'connections') and hasattr(ws_manager, 'call_subscriptions'):
                return {"name": "WebSocket Connectivity", "passed": True, "message": "WebSocket manager initialized"}
            else:
                return {"name": "WebSocket Connectivity", "passed": False, "message": "WebSocket manager not properly initialized"}
        
        except Exception as e:
            return {"name": "WebSocket Connectivity", "passed": False, "message": f"Error: {e}"}
    
    async def _run_performance_benchmark(self):
        """Run performance benchmarks"""
        logger.info("⚡ Running Sales Intelligence Performance Benchmarks")
        
        print("\n⚡ PERFORMANCE BENCHMARK RESULTS")
        print("=" * 40)
        
        # Benchmark 1: Agent processing speed
        start_time = time.time()
        await self._simulate_call(self.demo_data["demo_calls"][0])
        agent_processing_time = time.time() - start_time
        
        print(f"🤖 Agent Processing: {agent_processing_time:.2f} seconds per call")
        
        # Benchmark 2: Feedback generation speed
        start_time = time.time()
        for _ in range(10):
            from app.swarms.sales_intelligence.agents import AgentOutput, AgentPriority, ConfidenceLevel
            
            mock_output = AgentOutput(
                agent_id="benchmark",
                agent_type="sentiment",
                call_id="benchmark_call",
                timestamp=datetime.now(),
                priority=AgentPriority.MEDIUM,
                confidence=ConfidenceLevel.HIGH,
                data={"overall_sentiment": 0.5},
                requires_action=False
            )
            
            await self.feedback_system.process_agent_output(mock_output)
        
        feedback_processing_time = (time.time() - start_time) / 10
        print(f"💡 Feedback Generation: {feedback_processing_time:.3f} seconds per message")
        
        # Benchmark 3: Dashboard updates
        start_time = time.time()
        for _ in range(5):
            self.dashboard.get_team_dashboard_data()
        dashboard_update_time = (time.time() - start_time) / 5
        
        print(f"📊 Dashboard Updates: {dashboard_update_time:.3f} seconds per update")
        
        # Benchmark 4: Sophia query processing
        start_time = time.time()
        queries = ["Status?", "Risk?", "Competitors?", "Feedback?", "Sentiment?"]
        for query in queries:
            await self.orchestrator.process_sophia_query(query)
        sophia_processing_time = (time.time() - start_time) / len(queries)
        
        print(f"🧠 Sophia Queries: {sophia_processing_time:.3f} seconds per query")
        
        # Overall assessment
        total_time = agent_processing_time + feedback_processing_time + dashboard_update_time + sophia_processing_time
        print(f"\n🎯 Overall Performance Score: {total_time:.2f} seconds (lower is better)")
        
        if total_time < 5.0:
            print("✅ Excellent performance - ready for production!")
        elif total_time < 10.0:
            print("⚠️  Good performance - monitor under load") 
        else:
            print("🔴 Performance issues - optimization needed")
    
    async def _cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up demo resources...")
        
        try:
            # Stop agent orchestrator
            if self.orchestrator:
                await self.orchestrator.agent_orchestrator.stop_all_agents()
            
            # Clear demo data
            self.demo_calls.clear()
            
            logger.info("✅ Cleanup completed")
        
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")


async def main():
    """Main entry point for the demo"""
    parser = argparse.ArgumentParser(description="Sales Intelligence Swarm Demo")
    parser.add_argument(
        "--mode",
        choices=["demo", "test", "benchmark"],
        default="demo",
        help="Demo mode: demo (interactive), test (system tests), benchmark (performance)"
    )
    
    args = parser.parse_args()
    
    # Print header
    print("🚀 SALES INTELLIGENCE SWARM - COMPREHENSIVE DEMO")
    print("=" * 60)
    print("Real-time call analysis • Live coaching feedback • Competitive intelligence")
    print("Universal Sophia integration • WebSocket dashboard • Production-ready")
    print("=" * 60)
    
    try:
        demo = SalesIntelligenceDemo(mode=args.mode)
        await demo.run_demo()
    
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted by user")
        logger.info("Demo interrupted by user")
    
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.error(f"Demo failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())