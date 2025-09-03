"""
Mock Data Generator for Business Intelligence Integration Testing

This module provides realistic mock data for testing BI integrations without
depending on live external services. Supports all major BI platforms.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from faker import Faker
import uuid

fake = Faker()

@dataclass 
class MockDataConfig:
    """Configuration for mock data generation"""
    platform: str
    scenario: str  # 'success', 'partial_failure', 'timeout', 'auth_error', 'rate_limit'
    record_count: int = 50
    response_delay_ms: int = 100
    data_quality: float = 1.0  # 0.0 to 1.0, affects missing/corrupt data

class BIMockDataGenerator:
    """Generates realistic mock data for BI platform testing"""
    
    def __init__(self):
        self.fake = Faker()
        # Pre-generate some consistent data for relationships
        self.companies = [
            "TechCorp Inc", "DataFlow Systems", "CloudVision", "NextGen Analytics",
            "Smart Solutions", "Digital Dynamics", "Innovation Labs", "Future Tech",
            "Alpha Systems", "Beta Corporation", "Gamma Industries", "Delta Enterprises"
        ]
        
        self.contact_titles = [
            "CEO", "CTO", "VP Engineering", "Director of Sales", "VP Marketing", 
            "Head of Operations", "Senior Manager", "Principal Engineer", "Data Scientist",
            "Product Manager", "Business Analyst", "Sales Director"
        ]
        
        self.deal_stages = [
            "Qualified Lead", "Discovery", "Demo Scheduled", "Proposal Sent", 
            "Negotiation", "Closed Won", "Closed Lost"
        ]

    # ==============================================================================
    # GONG INTEGRATION MOCKS
    # ==============================================================================
    
    def generate_gong_calls(self, config: MockDataConfig) -> Dict[str, Any]:
        """Generate mock Gong call data"""
        
        if config.scenario == "auth_error":
            return {"error": "Unauthorized - Invalid Gong credentials"}
        
        if config.scenario == "rate_limit":
            return {"error": "Rate limit exceeded - Try again in 60 seconds"}
        
        calls = []
        for _ in range(config.record_count):
            call_id = str(random.randint(1000000000000000000, 9999999999999999999))
            
            # Inject some data quality issues based on config
            missing_data = random.random() > config.data_quality
            
            call_data = {
                "callId": call_id,
                "date": None if missing_data else self.fake.date_time_between(
                    start_date='-7d', end_date='now'
                ).isoformat(),
                "topic": self._generate_call_topic(),
                "durationSec": random.randint(300, 3600),
                "participants": None if missing_data else [
                    self.fake.name() for _ in range(random.randint(2, 5))
                ]
            }
            
            # Add AI analysis data for some calls
            if random.random() < 0.7:  # 70% of calls have analysis
                call_data["ai_analysis"] = {
                    "sentiment": random.choice(["positive", "neutral", "negative"]),
                    "engagement_score": round(random.uniform(1, 10), 1),
                    "key_topics": random.sample([
                        "pricing", "technical_requirements", "timeline", "integration",
                        "security", "compliance", "scalability", "support"
                    ], random.randint(2, 4)),
                    "concerns_raised": random.sample([
                        "budget_constraints", "timeline_pressure", "technical_complexity", 
                        "security_requirements", "integration_challenges"
                    ], random.randint(0, 2)),
                    "next_steps": random.sample([
                        "Technical demo", "Proposal preparation", "Security review",
                        "Stakeholder alignment", "Contract negotiation"
                    ], random.randint(1, 3))
                }
            
            calls.append(call_data)
        
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        return {
            "fromDate": start_date,
            "count": len(calls),
            "calls": calls
        }
    
    def _generate_call_topic(self) -> str:
        """Generate realistic call topics"""
        templates = [
            "{company} - {service} Discovery Call",
            "{company} x Pay Ready Integration Meeting", 
            "{service} Implementation - {company}",
            "{company} Weekly Sync",
            "{company} Technical Deep Dive",
            "{service} Demo - {company}",
            "{company} Contract Review",
            "{company} Executive Update"
        ]
        
        template = random.choice(templates)
        return template.format(
            company=random.choice(self.companies),
            service=random.choice(["Pay Ready", "Data Analytics", "AI Platform"])
        )

    # ==============================================================================
    # CRM INTEGRATION MOCKS (HubSpot, Salesforce)
    # ==============================================================================
    
    def generate_crm_contacts(self, config: MockDataConfig) -> Dict[str, Any]:
        """Generate mock CRM contact data"""
        
        if config.scenario == "auth_error":
            return {"error": "Invalid API key or expired token"}
        
        contacts = []
        for _ in range(config.record_count):
            contact_id = f"contact_{random.randint(1000, 9999)}"
            
            # Data quality issues
            missing_company = random.random() > config.data_quality
            missing_contact_info = random.random() > config.data_quality
            
            contact = {
                "id": contact_id,
                "name": self.fake.name(),
                "company": None if missing_company else random.choice(self.companies),
                "title": random.choice(self.contact_titles),
                "email": None if missing_contact_info else self.fake.email(),
                "phone": None if missing_contact_info else self.fake.phone_number(),
                "status": random.choice([
                    "new_lead", "qualified_lead", "demo_scheduled", 
                    "proposal_sent", "customer", "churned"
                ]),
                "last_activity": self.fake.date_time_between(
                    start_date='-30d', end_date='now'
                ).isoformat(),
                "lead_score": random.randint(1, 100),
                "source": random.choice([
                    "website", "referral", "cold_outreach", "conference", 
                    "social_media", "advertisement"
                ]),
                "ai_insights": {
                    "engagement_score": round(random.uniform(1, 10), 1),
                    "likelihood_to_close": round(random.uniform(0, 1), 2),
                    "recommended_action": random.choice([
                        "Schedule demo meeting", "Send follow-up email",
                        "Prepare technical presentation", "Schedule stakeholder call",
                        "Send pricing proposal", "Assign to account executive"
                    ]),
                    "suggested_agents": random.sample([
                        "backend_specialist", "frontend_creative", "security_auditor"
                    ], random.randint(1, 2)),
                    "risk_factors": random.sample([
                        "budget_uncertainty", "long_decision_cycle", "multiple_stakeholders",
                        "competitive_evaluation", "technical_complexity"
                    ], random.randint(0, 2))
                }
            }
            
            contacts.append(contact)
        
        return {
            "contacts": contacts,
            "count": len(contacts),
            "ai_summary": {
                "total_qualified_leads": random.randint(10, 30),
                "conversion_trend": f"+{random.randint(5, 25)}%",
                "recommended_focus": random.choice([
                    "technical_demos", "pricing_discussions", "stakeholder_alignment"
                ])
            }
        }
    
    def generate_crm_pipeline(self, config: MockDataConfig) -> Dict[str, Any]:
        """Generate mock CRM pipeline data"""
        
        pipeline_stages = []
        total_value = 0
        
        for stage in self.deal_stages:
            count = random.randint(1, 15)
            stage_value = random.randint(10000, 100000)
            total_value += stage_value
            
            pipeline_stages.append({
                "stage": stage,
                "count": count,
                "value": stage_value,
                "deals": self._generate_deals(count, stage),
                "ai_recommendation": self._get_stage_recommendation(stage),
                "conversion_rate": round(random.uniform(0.1, 0.8), 2),
                "avg_days_in_stage": random.randint(5, 45)
            })
        
        return {
            "pipeline": pipeline_stages,
            "total_pipeline_value": total_value,
            "ai_insights": {
                "bottleneck_stage": random.choice(self.deal_stages[2:5]),
                "recommended_action": "Deploy proposal optimization agent",
                "success_probability": round(random.uniform(0.5, 0.9), 2),
                "forecasted_revenue": int(total_value * random.uniform(0.3, 0.7)),
                "at_risk_deals": random.randint(2, 8)
            }
        }
    
    def _generate_deals(self, count: int, stage: str) -> List[Dict[str, Any]]:
        """Generate individual deal records"""
        deals = []
        for _ in range(min(count, 5)):  # Limit to 5 deals per stage for brevity
            deals.append({
                "deal_id": f"deal_{random.randint(10000, 99999)}",
                "company": random.choice(self.companies),
                "value": random.randint(5000, 50000),
                "owner": self.fake.name(),
                "created_date": self.fake.date_between(start_date='-90d', end_date='now').isoformat(),
                "expected_close_date": self.fake.date_between(start_date='now', end_date='+60d').isoformat()
            })
        return deals
    
    def _get_stage_recommendation(self, stage: str) -> str:
        """Get AI recommendation for pipeline stage"""
        recommendations = {
            "Qualified Lead": "Deploy lead nurturing agents",
            "Discovery": "Schedule technical deep-dive sessions",
            "Demo Scheduled": "Create technical presentation materials",
            "Proposal Sent": "Follow-up with personalized content",
            "Negotiation": "Deploy pricing optimization agent",
            "Closed Won": "Activate customer success workflows",
            "Closed Lost": "Analyze loss reasons and improve process"
        }
        return recommendations.get(stage, "Monitor progress closely")

    # ==============================================================================  
    # PROJECT MANAGEMENT MOCKS (Asana, Linear, Notion)
    # ==============================================================================
    
    def generate_project_data(self, config: MockDataConfig) -> Dict[str, Any]:
        """Generate mock project management data"""
        
        platforms = ["asana", "linear", "notion"] 
        project_types = [
            "API Development", "UI/UX Redesign", "Security Audit", 
            "Database Migration", "Integration Testing", "Documentation Update",
            "Performance Optimization", "Mobile App", "DevOps Pipeline"
        ]
        
        projects = []
        for _ in range(config.record_count):
            project_id = f"proj_{random.randint(100, 999)}"
            completion = round(random.uniform(0, 1), 2)
            
            # Determine project health based on completion and timeline
            deadline = self.fake.date_between(start_date='-30d', end_date='+90d')
            days_until_deadline = (deadline - datetime.now().date()).days
            
            if completion > 0.8 and days_until_deadline > 0:
                risk_level = "low"
                on_track = True
            elif completion < 0.3 and days_until_deadline < 7:
                risk_level = "high"
                on_track = False
            else:
                risk_level = "medium"
                on_track = random.choice([True, False])
            
            project = {
                "id": project_id,
                "name": random.choice(project_types),
                "platform": random.choice(platforms),
                "status": random.choice(["planning", "in_progress", "review", "completed", "on_hold"]),
                "completion": completion,
                "team_size": random.randint(1, 8),
                "deadline": deadline.isoformat(),
                "created_date": self.fake.date_between(start_date='-180d', end_date='-30d').isoformat(),
                "priority": random.choice(["low", "medium", "high", "critical"]),
                "budget": random.randint(10000, 200000),
                "ai_insights": {
                    "on_track": on_track,
                    "risk_level": risk_level,
                    "suggested_optimization": self._get_project_optimization(project_id),
                    "blockers": self._generate_project_blockers(),
                    "estimated_completion": self.fake.date_between(
                        start_date='now', end_date='+60d'
                    ).isoformat(),
                    "resource_utilization": round(random.uniform(0.4, 1.2), 2),
                    "quality_score": round(random.uniform(0.6, 1.0), 2)
                },
                "tasks": {
                    "total": random.randint(10, 50),
                    "completed": int(completion * random.randint(10, 50)),
                    "in_progress": random.randint(1, 5),
                    "blocked": random.randint(0, 3)
                }
            }
            
            projects.append(project)
        
        # Calculate summary statistics
        on_track_count = sum(1 for p in projects if p["ai_insights"]["on_track"])
        at_risk_count = len(projects) - on_track_count
        
        return {
            "projects": projects,
            "count": len(projects),
            "ai_summary": {
                "total_projects": len(projects),
                "on_track": on_track_count,
                "at_risk": at_risk_count,
                "average_completion": round(sum(p["completion"] for p in projects) / len(projects), 2),
                "recommended_agent_deployments": [
                    "Deploy documentation agent for automated updates",
                    "Use security auditor for compliance review",
                    "Activate performance optimization agents"
                ],
                "resource_bottlenecks": ["Frontend development", "Security testing", "DevOps"]
            }
        }
    
    def _get_project_optimization(self, project_id: str) -> str:
        """Generate project-specific optimization recommendations"""
        optimizations = [
            "Deploy frontend creative agent for UI review",
            "Deploy security auditor agent for final review", 
            "Deploy backend specialist agent for automated documentation",
            "Use AI pair programming for code completion",
            "Activate automated testing agents",
            "Deploy performance monitoring agents"
        ]
        return random.choice(optimizations)
    
    def _generate_project_blockers(self) -> List[str]:
        """Generate realistic project blockers"""
        all_blockers = [
            "Pending stakeholder approval", "Resource allocation constraints",
            "External dependency delays", "Technical complexity issues",
            "Budget approval pending", "Third-party integration delays",
            "Security review requirements", "Performance testing bottlenecks"
        ]
        return random.sample(all_blockers, random.randint(0, 2))

    # ==============================================================================
    # BUSINESS DASHBOARD MOCKS  
    # ==============================================================================
    
    def generate_business_dashboard(self, config: MockDataConfig) -> Dict[str, Any]:
        """Generate mock business dashboard data"""
        
        return {
            "overview": {
                "leads_this_week": random.randint(15, 35),
                "deals_in_pipeline": random.randint(100000, 300000),
                "active_projects": random.randint(8, 20),
                "ai_optimizations": random.randint(5, 15),
                "revenue_this_month": random.randint(50000, 150000),
                "team_utilization": round(random.uniform(0.7, 0.95), 2)
            },
            "ai_insights": {
                "revenue_forecast": random.randint(150000, 400000),
                "conversion_probability": round(random.uniform(0.6, 0.9), 2),
                "bottlenecks": random.sample([
                    "proposal_approval", "technical_demo", "contract_negotiation",
                    "stakeholder_alignment", "resource_allocation"
                ], random.randint(1, 3)),
                "opportunities": random.sample([
                    "upsell_existing", "referral_program", "market_expansion", 
                    "product_diversification", "automation_opportunities"
                ], random.randint(2, 3)),
                "risk_factors": random.sample([
                    "market_volatility", "competitive_pressure", "resource_constraints",
                    "technical_debt", "customer_churn_risk"
                ], random.randint(1, 2))
            },
            "recommended_actions": [
                {
                    "action": "Deploy lead qualification agents",
                    "impact": random.choice(["high", "medium", "low"]),
                    "effort": random.choice(["high", "medium", "low"]), 
                    "estimated_value": random.randint(10000, 50000),
                    "timeline": f"{random.randint(1, 4)} weeks"
                },
                {
                    "action": "Automate proposal generation",
                    "impact": random.choice(["high", "medium", "low"]),
                    "effort": random.choice(["high", "medium", "low"]),
                    "estimated_value": random.randint(5000, 30000),
                    "timeline": f"{random.randint(2, 8)} weeks"
                },
                {
                    "action": "Optimize customer onboarding",
                    "impact": random.choice(["high", "medium", "low"]),
                    "effort": random.choice(["high", "medium", "low"]),
                    "estimated_value": random.randint(15000, 40000),
                    "timeline": f"{random.randint(3, 6)} weeks"
                }
            ],
            "agent_performance": {
                "total_deployments": random.randint(30, 100),
                "success_rate": round(random.uniform(0.8, 0.98), 2),
                "average_task_time": f"{round(random.uniform(1.5, 4.0), 1)} hours",
                "business_value_generated": random.randint(50000, 200000),
                "cost_savings": random.randint(20000, 80000),
                "top_performing_agents": random.sample([
                    "backend_specialist", "frontend_creative", "security_auditor",
                    "data_analyst", "project_manager", "sales_optimizer"
                ], 3)
            },
            "trends": {
                "lead_generation": {
                    "trend": random.choice(["up", "down", "stable"]),
                    "change_percent": random.randint(-20, 30)
                },
                "conversion_rate": {
                    "trend": random.choice(["up", "down", "stable"]),
                    "change_percent": random.randint(-15, 25)
                },
                "project_velocity": {
                    "trend": random.choice(["up", "down", "stable"]),
                    "change_percent": random.randint(-10, 40)
                }
            }
        }

    # ==============================================================================
    # WORKFLOW AUTOMATION MOCKS
    # ==============================================================================
    
    def generate_workflow_response(self, workflow_type: str, config: MockDataConfig) -> Dict[str, Any]:
        """Generate mock workflow automation responses"""
        
        workflow_id = f"wf_{random.randint(1000, 9999)}"
        
        workflows = {
            "lead_qualification": {
                "workflow_id": workflow_id,
                "type": "lead_qualification", 
                "agents_deployed": random.sample([
                    "backend_specialist", "frontend_creative", "sales_optimizer"
                ], random.randint(1, 3)),
                "status": "running",
                "expected_completion": f"{random.randint(15, 60)} minutes",
                "steps": [
                    "Analyze lead requirements",
                    "Generate custom proposal", 
                    "Create technical demo materials",
                    "Schedule follow-up actions"
                ],
                "progress": round(random.uniform(0.1, 0.8), 2)
            },
            "project_optimization": {
                "workflow_id": workflow_id,
                "type": "project_optimization",
                "agents_deployed": random.sample([
                    "security_auditor", "performance_optimizer", "code_reviewer"
                ], random.randint(1, 2)),
                "status": "running",
                "expected_completion": f"{random.randint(1, 4)} hours", 
                "steps": [
                    "Audit project security",
                    "Generate compliance report",
                    "Recommend optimizations",
                    "Create action plan"
                ],
                "progress": round(random.uniform(0.2, 0.9), 2)
            },
            "call_analysis": {
                "workflow_id": workflow_id,
                "type": "call_analysis",
                "agents_deployed": ["conversation_analyst", "sentiment_analyzer"],
                "status": "running", 
                "expected_completion": f"{random.randint(10, 30)} minutes",
                "steps": [
                    "Extract call transcript",
                    "Analyze sentiment and engagement",
                    "Identify key topics and concerns", 
                    "Generate follow-up recommendations"
                ],
                "progress": round(random.uniform(0.3, 0.95), 2)
            }
        }
        
        if workflow_type not in workflows:
            return {
                "error": "Unknown workflow type",
                "supported_types": list(workflows.keys())
            }
        
        return workflows[workflow_type]

    # ==============================================================================
    # ERROR SCENARIOS 
    # ==============================================================================
    
    def generate_error_response(self, platform: str, scenario: str) -> Dict[str, Any]:
        """Generate realistic error responses for testing"""
        
        error_responses = {
            "auth_error": {
                "gong": {"error": "Invalid credentials", "code": 401},
                "hubspot": {"error": "API key invalid or expired", "code": 401}, 
                "salesforce": {"error": "Authentication failed", "code": 401},
                "asana": {"error": "Unauthorized access", "code": 401},
                "linear": {"error": "Invalid API token", "code": 401}
            },
            "rate_limit": {
                "gong": {"error": "Rate limit exceeded", "retry_after": 3600, "code": 429},
                "hubspot": {"error": "API rate limit reached", "retry_after": 1800, "code": 429},
                "salesforce": {"error": "Request limit exceeded", "retry_after": 86400, "code": 429}
            },
            "service_unavailable": {
                "gong": {"error": "Service temporarily unavailable", "code": 503},
                "hubspot": {"error": "Service maintenance in progress", "code": 503},
                "salesforce": {"error": "Service unavailable", "code": 503}
            },
            "timeout": {
                "error": "Request timeout", 
                "message": "The request took too long to complete",
                "timeout_seconds": 30
            }
        }
        
        return error_responses.get(scenario, {}).get(platform, {
            "error": f"Unknown error scenario: {scenario}",
            "platform": platform
        })

    # ==============================================================================
    # MAIN GENERATOR METHODS
    # ==============================================================================
    
    def generate_mock_data(self, platform: str, data_type: str, config: MockDataConfig) -> Dict[str, Any]:
        """Main method to generate mock data for any platform/type combination"""
        
        generators = {
            ("gong", "calls"): self.generate_gong_calls,
            ("hubspot", "contacts"): self.generate_crm_contacts,
            ("hubspot", "pipeline"): self.generate_crm_pipeline,
            ("salesforce", "contacts"): self.generate_crm_contacts,
            ("salesforce", "pipeline"): self.generate_crm_pipeline,
            ("asana", "projects"): self.generate_project_data,
            ("linear", "projects"): self.generate_project_data,
            ("notion", "projects"): self.generate_project_data,
            ("dashboard", "overview"): self.generate_business_dashboard,
            ("workflow", "automation"): lambda cfg: self.generate_workflow_response(cfg.scenario, cfg)
        }
        
        key = (platform, data_type)
        generator = generators.get(key)
        
        if not generator:
            return {"error": f"No generator found for {platform}/{data_type}"}
        
        # Handle error scenarios first
        if config.scenario in ["auth_error", "rate_limit", "service_unavailable", "timeout"]:
            return self.generate_error_response(platform, config.scenario)
        
        return generator(config)

# ==============================================================================
# USAGE EXAMPLES AND TESTING
# ==============================================================================

def main():
    """Example usage of the mock data generator"""
    generator = BIMockDataGenerator()
    
    print("🎭 BI Mock Data Generator Examples")
    print("=" * 50)
    
    # Example 1: Generate successful Gong calls
    config = MockDataConfig(platform="gong", scenario="success", record_count=5)
    gong_data = generator.generate_gong_calls(config)
    print("\n📞 Gong Calls (Success):")
    print(json.dumps(gong_data, indent=2)[:500] + "...")
    
    # Example 2: Generate CRM contacts with data quality issues
    config = MockDataConfig(platform="hubspot", scenario="success", 
                          record_count=3, data_quality=0.7)
    crm_data = generator.generate_crm_contacts(config)
    print("\n👥 CRM Contacts (Partial Quality):")
    print(json.dumps(crm_data, indent=2)[:500] + "...")
    
    # Example 3: Generate auth error
    config = MockDataConfig(platform="gong", scenario="auth_error")
    error_data = generator.generate_gong_calls(config)
    print("\n🚫 Auth Error Example:")
    print(json.dumps(error_data, indent=2))
    
    # Example 4: Business dashboard
    config = MockDataConfig(platform="dashboard", scenario="success")
    dashboard_data = generator.generate_business_dashboard(config)
    print("\n📊 Business Dashboard:")
    print(json.dumps(dashboard_data, indent=2)[:400] + "...")

if __name__ == "__main__":
    main()