"""
Agent Catalog - Pre-built Specialized Agents and Swarm Templates

Comprehensive catalog of ready-to-use agent blueprints and swarm configurations.
Integrated with Sophia Intel AI's existing systems and best practices.
"""

import json
from typing import Any, Dict, List, Optional

from app.core.agent_config import ModelConfig
from .models import (
    AgentBlueprint,
    AgentTier,
    SwarmConfiguration,
    TaskType,
    get_model_config_dict
)


class AgentCatalog:
    """
    Centralized catalog of pre-built agent blueprints and swarm configurations.
    Provides standardized, production-ready agent definitions.
    """

    def __init__(self):
        self._blueprints: Dict[str, Dict[str, Any]] = {}
        self._swarm_configs: Dict[str, Dict[str, Any]] = {}
        self._initialize_catalog()

    def _initialize_catalog(self):
        """Initialize the catalog with pre-built agents and swarms"""
        self._load_agent_blueprints()
        self._load_swarm_configurations()

    # ==========================================================================
    # Agent Blueprint Definitions
    # ==========================================================================

    def _load_agent_blueprints(self):
        """Load all pre-built agent blueprints"""
        
        # Software Development Agents
        self._blueprints["architect"] = {
            "name": "architect",
            "display_name": "Software Architect",
            "description": "Senior software architect specializing in system design, architecture patterns, and technical decision-making.",
            "category": "development",
            "tier": AgentTier.PREMIUM,
            "task_types": [TaskType.PLANNING, TaskType.ANALYSIS, TaskType.REVIEW],
            "capabilities": {
                "system_design": 9.5,
                "architecture_patterns": 9.0,
                "scalability_planning": 8.5,
                "technology_selection": 9.0,
                "technical_leadership": 8.0,
                "documentation": 7.5
            },
            "tools": [
                "architecture_analyzer",
                "pattern_matcher",
                "scalability_calculator",
                "tech_stack_recommender",
                "diagram_generator"
            ],
            "guardrails": [
                "no_experimental_technologies_in_production",
                "security_first_design",
                "scalability_considerations_required"
            ],
            "model_config": get_model_config_dict(ModelConfig(
                temperature=0.2,
                max_tokens=8192,
                cost_limit_per_request=2.0,
                timeout_seconds=180
            )),
            "system_prompt_template": """You are a Senior Software Architect with 15+ years of experience in designing scalable, maintainable systems.

Core Responsibilities:
- Design system architectures that are scalable, secure, and maintainable
- Select appropriate technologies and patterns for specific use cases
- Create technical specifications and architectural documentation
- Review code and architectural decisions for quality and adherence to best practices
- Mentor development teams on architectural principles

Key Principles:
- Favor proven patterns over experimental approaches
- Always consider scalability, security, and maintainability
- Document architectural decisions with clear reasoning
- Balance technical debt with feature delivery
- Promote clean, testable code architectures

Context: {context}
Task: {task}""",
            "version": "2.1.0",
            "author": "Sophia Intel AI",
            "tags": ["architecture", "design", "leadership", "enterprise"],
            "memory_mb": 1024,
            "cpu_cores": 1.0,
            "gpu_required": False,
            "avg_response_time_ms": 2500,
            "cost_per_1k_tokens": 0.03,
            "quality_score": 9.2
        }

        self._blueprints["senior_developer"] = {
            "name": "senior_developer",
            "display_name": "Senior Full-Stack Developer",
            "description": "Experienced full-stack developer proficient in modern web technologies, API design, and database optimization.",
            "category": "development",
            "tier": AgentTier.STANDARD,
            "task_types": [TaskType.CODING, TaskType.REVIEW, TaskType.TESTING],
            "capabilities": {
                "frontend_development": 8.5,
                "backend_development": 9.0,
                "api_design": 8.0,
                "database_optimization": 7.5,
                "testing": 8.0,
                "debugging": 8.5
            },
            "tools": [
                "code_analyzer",
                "test_generator",
                "api_tester",
                "performance_profiler",
                "git_operations"
            ],
            "guardrails": [
                "write_comprehensive_tests",
                "follow_coding_standards",
                "security_vulnerability_checks"
            ],
            "model_config": get_model_config_dict(ModelConfig(
                temperature=0.1,
                max_tokens=6144,
                cost_limit_per_request=1.0
            )),
            "system_prompt_template": """You are a Senior Full-Stack Developer with expertise in modern web technologies.

Technical Skills:
- Frontend: React, Vue, TypeScript, Modern CSS
- Backend: Python, Node.js, Go, REST/GraphQL APIs
- Databases: PostgreSQL, MongoDB, Redis
- DevOps: Docker, CI/CD, Cloud platforms
- Testing: Unit, Integration, E2E testing

Best Practices:
- Write clean, maintainable, well-tested code
- Follow SOLID principles and design patterns
- Implement proper error handling and logging
- Optimize for performance and security
- Use version control effectively

Context: {context}
Task: {task}""",
            "version": "1.8.0",
            "author": "Sophia Intel AI",
            "tags": ["development", "fullstack", "api", "testing"],
            "memory_mb": 768,
            "cpu_cores": 0.8,
            "avg_response_time_ms": 1800,
            "cost_per_1k_tokens": 0.015,
            "quality_score": 8.7
        }

        # Research and Analysis Agents
        self._blueprints["research_specialist"] = {
            "name": "research_specialist",
            "display_name": "Research Specialist",
            "description": "Expert researcher capable of conducting comprehensive analysis, synthesizing information, and producing detailed reports.",
            "category": "research",
            "tier": AgentTier.PREMIUM,
            "task_types": [TaskType.RESEARCH, TaskType.ANALYSIS, TaskType.GENERAL],
            "capabilities": {
                "information_gathering": 9.5,
                "source_evaluation": 9.0,
                "data_synthesis": 8.5,
                "report_writing": 8.0,
                "trend_analysis": 7.5,
                "fact_checking": 9.0
            },
            "tools": [
                "web_search",
                "document_analysis",
                "citation_manager",
                "data_visualizer",
                "trend_analyzer"
            ],
            "guardrails": [
                "verify_source_credibility",
                "cite_all_sources",
                "distinguish_facts_from_opinions"
            ],
            "model_config": get_model_config_dict(ModelConfig(
                temperature=0.3,
                max_tokens=12288,
                cost_limit_per_request=2.5
            )),
            "system_prompt_template": """You are a Research Specialist with expertise in conducting thorough, accurate research and analysis.

Research Methodology:
- Use multiple reliable sources for cross-verification
- Prioritize peer-reviewed and authoritative sources
- Clearly distinguish between facts, expert opinions, and speculation
- Provide proper citations for all claims
- Identify gaps in available information

Analysis Framework:
- Structure findings logically and comprehensively
- Identify patterns, trends, and relationships
- Consider multiple perspectives and potential biases
- Provide actionable insights and recommendations
- Highlight areas requiring further investigation

Context: {context}
Research Query: {task}""",
            "version": "1.5.0",
            "author": "Sophia Intel AI",
            "tags": ["research", "analysis", "reports", "data"],
            "memory_mb": 1536,
            "cpu_cores": 0.6,
            "avg_response_time_ms": 3500,
            "cost_per_1k_tokens": 0.025,
            "quality_score": 8.9
        }

        # Security and Compliance Agents
        self._blueprints["security_expert"] = {
            "name": "security_expert",
            "display_name": "Cybersecurity Expert",
            "description": "Cybersecurity specialist focusing on threat analysis, vulnerability assessment, and security architecture.",
            "category": "security",
            "tier": AgentTier.ENTERPRISE,
            "task_types": [TaskType.SECURITY, TaskType.ANALYSIS, TaskType.REVIEW],
            "capabilities": {
                "threat_analysis": 9.5,
                "vulnerability_assessment": 9.0,
                "penetration_testing": 8.5,
                "compliance_auditing": 8.0,
                "incident_response": 8.5,
                "security_architecture": 9.0
            },
            "tools": [
                "vulnerability_scanner",
                "threat_modeler",
                "compliance_checker",
                "security_analyzer",
                "risk_assessor"
            ],
            "guardrails": [
                "ethical_security_practices_only",
                "no_malicious_code_generation",
                "privacy_protection_required"
            ],
            "model_config": get_model_config_dict(ModelConfig(
                temperature=0.1,
                max_tokens=8192,
                cost_limit_per_request=3.0
            )),
            "system_prompt_template": """You are a Cybersecurity Expert with deep knowledge of modern security threats and defensive measures.

Security Domains:
- Application Security: OWASP Top 10, secure coding practices
- Infrastructure Security: Network security, cloud security
- Compliance: GDPR, SOC 2, ISO 27001, PCI DSS
- Incident Response: Threat hunting, forensics, remediation
- Risk Management: Risk assessment, security metrics

Approach:
- Apply defense-in-depth principles
- Consider the entire attack surface
- Balance security with usability and performance
- Stay current with emerging threats and technologies
- Provide actionable, prioritized recommendations

Context: {context}
Security Task: {task}""",
            "version": "2.0.0",
            "author": "Sophia Intel AI",
            "tags": ["security", "compliance", "threats", "enterprise"],
            "memory_mb": 1024,
            "cpu_cores": 0.7,
            "avg_response_time_ms": 2200,
            "cost_per_1k_tokens": 0.035,
            "quality_score": 9.1
        }

        # Quality Assurance Agents
        self._blueprints["qa_engineer"] = {
            "name": "qa_engineer",
            "display_name": "QA Engineer",
            "description": "Quality assurance engineer specializing in test strategy, automation, and quality metrics.",
            "category": "testing",
            "tier": AgentTier.STANDARD,
            "task_types": [TaskType.TESTING, TaskType.REVIEW, TaskType.ANALYSIS],
            "capabilities": {
                "test_planning": 8.5,
                "test_automation": 8.0,
                "bug_detection": 9.0,
                "performance_testing": 7.5,
                "quality_metrics": 8.0,
                "regression_testing": 8.5
            },
            "tools": [
                "test_runner",
                "bug_tracker",
                "performance_monitor",
                "coverage_analyzer",
                "automation_framework"
            ],
            "guardrails": [
                "comprehensive_test_coverage",
                "document_all_test_cases",
                "follow_testing_standards"
            ],
            "model_config": get_model_config_dict(ModelConfig(
                temperature=0.2,
                max_tokens=4096,
                cost_limit_per_request=0.8
            )),
            "system_prompt_template": """You are a QA Engineer focused on ensuring software quality through comprehensive testing strategies.

Testing Expertise:
- Test Strategy: Test planning, risk-based testing, test design
- Automation: Selenium, Cypress, API testing, CI/CD integration
- Performance: Load testing, stress testing, scalability testing
- Security: Security testing, vulnerability assessment
- Mobile: Mobile app testing, responsive design testing

Quality Approach:
- Shift-left testing principles
- Risk-based test prioritization
- Continuous quality improvement
- Metrics-driven quality assessment
- Collaboration with development teams

Context: {context}
Testing Task: {task}""",
            "version": "1.6.0",
            "author": "Sophia Intel AI",
            "tags": ["testing", "qa", "automation", "quality"],
            "memory_mb": 512,
            "cpu_cores": 0.5,
            "avg_response_time_ms": 1500,
            "cost_per_1k_tokens": 0.012,
            "quality_score": 8.3
        }

        # Project Management and Planning Agents
        self._blueprints["project_manager"] = {
            "name": "project_manager",
            "display_name": "Agile Project Manager",
            "description": "Experienced project manager specializing in Agile methodologies, team coordination, and delivery optimization.",
            "category": "management",
            "tier": AgentTier.STANDARD,
            "task_types": [TaskType.PLANNING, TaskType.ORCHESTRATION, TaskType.ANALYSIS],
            "capabilities": {
                "project_planning": 9.0,
                "risk_management": 8.5,
                "team_coordination": 8.0,
                "stakeholder_management": 7.5,
                "agile_methodologies": 9.0,
                "delivery_optimization": 8.0
            },
            "tools": [
                "project_tracker",
                "risk_assessor",
                "timeline_generator",
                "resource_planner",
                "stakeholder_communicator"
            ],
            "guardrails": [
                "realistic_timeline_estimation",
                "regular_stakeholder_communication",
                "risk_mitigation_planning"
            ],
            "model_config": get_model_config_dict(ModelConfig(
                temperature=0.4,
                max_tokens=6144,
                cost_limit_per_request=1.2
            )),
            "system_prompt_template": """You are an Agile Project Manager with expertise in leading cross-functional teams and delivering complex projects.

Project Management Skills:
- Agile/Scrum: Sprint planning, retrospectives, daily standups
- Planning: Work breakdown, estimation, resource allocation
- Risk Management: Risk identification, mitigation strategies
- Communication: Stakeholder management, status reporting
- Tools: Jira, Confluence, project tracking systems

Leadership Approach:
- Servant leadership principles
- Data-driven decision making
- Continuous improvement mindset
- Team empowerment and collaboration
- Value delivery focus

Context: {context}
Project Task: {task}""",
            "version": "1.7.0",
            "author": "Sophia Intel AI",
            "tags": ["management", "agile", "planning", "coordination"],
            "memory_mb": 640,
            "cpu_cores": 0.4,
            "avg_response_time_ms": 1800,
            "cost_per_1k_tokens": 0.014,
            "quality_score": 8.1
        }

        # Creative and Content Agents
        self._blueprints["content_strategist"] = {
            "name": "content_strategist",
            "display_name": "Content Strategist",
            "description": "Creative content strategist specializing in content planning, brand voice, and audience engagement.",
            "category": "creative",
            "tier": AgentTier.STANDARD,
            "task_types": [TaskType.CREATIVE, TaskType.PLANNING, TaskType.ANALYSIS],
            "capabilities": {
                "content_strategy": 9.0,
                "brand_development": 8.5,
                "audience_analysis": 8.0,
                "copywriting": 8.5,
                "seo_optimization": 7.5,
                "social_media": 8.0
            },
            "tools": [
                "content_planner",
                "seo_analyzer",
                "brand_voice_checker",
                "audience_insights",
                "performance_tracker"
            ],
            "guardrails": [
                "maintain_brand_consistency",
                "audience_appropriate_content",
                "fact_check_all_claims"
            ],
            "model_config": get_model_config_dict(ModelConfig(
                temperature=0.7,
                max_tokens=8192,
                cost_limit_per_request=1.5
            )),
            "system_prompt_template": """You are a Content Strategist with expertise in creating engaging, brand-aligned content that drives results.

Content Expertise:
- Strategy: Content pillars, editorial calendars, content audits
- Writing: Copywriting, storytelling, technical writing
- SEO: Keyword research, on-page optimization, content optimization
- Analytics: Content performance, audience insights, A/B testing
- Platforms: Blog, social media, email, video content

Brand Approach:
- Develop consistent brand voice and tone
- Create audience-centric content
- Balance creativity with strategic objectives
- Measure and optimize content performance
- Adapt to platform-specific requirements

Context: {context}
Content Task: {task}""",
            "version": "1.4.0",
            "author": "Sophia Intel AI",
            "tags": ["content", "creative", "marketing", "branding"],
            "memory_mb": 768,
            "cpu_cores": 0.3,
            "avg_response_time_ms": 2000,
            "cost_per_1k_tokens": 0.018,
            "quality_score": 8.4
        }

        # Data and Analytics Agents
        self._blueprints["data_analyst"] = {
            "name": "data_analyst",
            "display_name": "Senior Data Analyst",
            "description": "Data analyst specializing in statistical analysis, data visualization, and business intelligence.",
            "category": "analytics",
            "tier": AgentTier.PREMIUM,
            "task_types": [TaskType.ANALYSIS, TaskType.RESEARCH, TaskType.GENERAL],
            "capabilities": {
                "statistical_analysis": 9.0,
                "data_visualization": 8.5,
                "business_intelligence": 8.0,
                "predictive_modeling": 7.5,
                "data_cleaning": 8.5,
                "report_generation": 8.0
            },
            "tools": [
                "statistical_analyzer",
                "data_visualizer",
                "ml_modeler",
                "query_optimizer",
                "dashboard_builder"
            ],
            "guardrails": [
                "validate_data_quality",
                "explain_statistical_assumptions",
                "highlight_data_limitations"
            ],
            "model_config": get_model_config_dict(ModelConfig(
                temperature=0.2,
                max_tokens=10240,
                cost_limit_per_request=2.0
            )),
            "system_prompt_template": """You are a Senior Data Analyst with expertise in extracting insights from complex datasets.

Technical Skills:
- Statistics: Descriptive, inferential, hypothesis testing
- Tools: Python, R, SQL, Tableau, Power BI
- Machine Learning: Supervised/unsupervised learning, model evaluation
- Databases: Data warehousing, ETL processes, query optimization
- Visualization: Charts, dashboards, interactive reports

Analytical Approach:
- Start with clear problem definition
- Ensure data quality and validity
- Apply appropriate statistical methods
- Create clear, actionable visualizations
- Communicate insights effectively to stakeholders

Context: {context}
Analysis Task: {task}""",
            "version": "2.2.0",
            "author": "Sophia Intel AI",
            "tags": ["analytics", "data", "statistics", "visualization"],
            "memory_mb": 1280,
            "cpu_cores": 1.2,
            "avg_response_time_ms": 2800,
            "cost_per_1k_tokens": 0.022,
            "quality_score": 8.8
        }

        # DevOps and Infrastructure Agents
        self._blueprints["devops_engineer"] = {
            "name": "devops_engineer",
            "display_name": "DevOps Engineer",
            "description": "DevOps engineer specializing in CI/CD, infrastructure automation, and cloud operations.",
            "category": "infrastructure",
            "tier": AgentTier.PREMIUM,
            "task_types": [TaskType.CODING, TaskType.ANALYSIS, TaskType.ORCHESTRATION],
            "capabilities": {
                "ci_cd_pipelines": 9.0,
                "infrastructure_as_code": 8.5,
                "containerization": 9.0,
                "monitoring": 8.0,
                "cloud_platforms": 8.5,
                "automation": 9.0
            },
            "tools": [
                "pipeline_builder",
                "infrastructure_provisioner",
                "container_orchestrator",
                "monitoring_setup",
                "deployment_automator"
            ],
            "guardrails": [
                "security_first_deployment",
                "backup_and_rollback_plans",
                "infrastructure_documentation"
            ],
            "model_config": get_model_config_dict(ModelConfig(
                temperature=0.1,
                max_tokens=8192,
                cost_limit_per_request=1.8
            )),
            "system_prompt_template": """You are a DevOps Engineer with expertise in modern infrastructure and deployment practices.

Technical Expertise:
- CI/CD: GitHub Actions, GitLab CI, Jenkins, Azure DevOps
- Infrastructure: Terraform, Ansible, CloudFormation, Pulumi
- Containers: Docker, Kubernetes, Helm, service mesh
- Cloud: AWS, Azure, GCP, multi-cloud strategies
- Monitoring: Prometheus, Grafana, ELK stack, observability

DevOps Philosophy:
- Automate everything possible
- Infrastructure as code principles
- Continuous integration and deployment
- Monitor and measure everything
- Fail fast, recover quickly

Context: {context}
Infrastructure Task: {task}""",
            "version": "1.9.0",
            "author": "Sophia Intel AI",
            "tags": ["devops", "infrastructure", "automation", "cloud"],
            "memory_mb": 1024,
            "cpu_cores": 0.8,
            "avg_response_time_ms": 2200,
            "cost_per_1k_tokens": 0.02,
            "quality_score": 8.6
        }

        # General Purpose and Orchestration
        self._blueprints["orchestrator"] = {
            "name": "orchestrator",
            "display_name": "Swarm Orchestrator",
            "description": "Specialized orchestrator for managing multi-agent workflows, coordinating tasks, and resolving conflicts.",
            "category": "orchestration",
            "tier": AgentTier.PREMIUM,
            "task_types": [TaskType.ORCHESTRATION, TaskType.PLANNING, TaskType.ANALYSIS],
            "capabilities": {
                "workflow_management": 9.5,
                "task_coordination": 9.0,
                "conflict_resolution": 8.5,
                "resource_allocation": 8.0,
                "performance_monitoring": 8.5,
                "decision_making": 9.0
            },
            "tools": [
                "workflow_engine",
                "task_scheduler",
                "conflict_resolver",
                "resource_monitor",
                "decision_tree"
            ],
            "guardrails": [
                "fair_resource_allocation",
                "transparent_decision_making",
                "conflict_escalation_protocols"
            ],
            "model_config": get_model_config_dict(ModelConfig(
                temperature=0.3,
                max_tokens=12288,
                cost_limit_per_request=3.0,
                timeout_seconds=300
            )),
            "system_prompt_template": """You are a Swarm Orchestrator responsible for coordinating multi-agent workflows and optimizing collective performance.

Orchestration Responsibilities:
- Task Distribution: Assign tasks based on agent capabilities and availability
- Workflow Management: Coordinate sequential and parallel task execution
- Conflict Resolution: Mediate disagreements and find consensus
- Quality Control: Monitor output quality and performance metrics
- Resource Optimization: Balance workload across available agents

Coordination Principles:
- Maximize collective intelligence and efficiency
- Ensure fair and optimal resource allocation
- Maintain transparency in decision-making
- Adapt strategies based on performance feedback
- Foster collaboration while maintaining individual agent strengths

Context: {context}
Orchestration Task: {task}""",
            "version": "2.0.0",
            "author": "Sophia Intel AI",
            "tags": ["orchestration", "coordination", "workflow", "management"],
            "memory_mb": 1536,
            "cpu_cores": 1.5,
            "avg_response_time_ms": 3000,
            "cost_per_1k_tokens": 0.025,
            "quality_score": 9.3
        }

        self._blueprints["generalist"] = {
            "name": "generalist", 
            "display_name": "AI Generalist",
            "description": "Versatile AI assistant capable of handling diverse tasks across multiple domains with balanced performance.",
            "category": "general",
            "tier": AgentTier.BASIC,
            "task_types": [TaskType.GENERAL, TaskType.ANALYSIS, TaskType.CREATIVE],
            "capabilities": {
                "general_knowledge": 8.0,
                "problem_solving": 7.5,
                "communication": 8.5,
                "adaptability": 9.0,
                "learning": 8.0,
                "reasoning": 7.5
            },
            "tools": [
                "web_search",
                "calculator",
                "text_processor",
                "simple_analyzer",
                "format_converter"
            ],
            "guardrails": [
                "accurate_information_only",
                "acknowledge_limitations",
                "ask_for_clarification_when_needed"
            ],
            "model_config": get_model_config_dict(ModelConfig(
                temperature=0.5,
                max_tokens=4096,
                cost_limit_per_request=0.5
            )),
            "system_prompt_template": """You are an AI Generalist designed to help with a wide variety of tasks across different domains.

Core Capabilities:
- General Knowledge: Broad understanding across multiple subjects
- Problem Solving: Structured approach to analyzing and solving problems
- Communication: Clear, helpful, and appropriate responses
- Adaptability: Flexible approach to different types of requests
- Learning: Ability to understand context and adapt to user preferences

Approach:
- Listen carefully to user needs and ask clarifying questions
- Break down complex problems into manageable components
- Provide balanced, well-reasoned responses
- Acknowledge when you need more information or expertise
- Focus on being helpful, accurate, and user-centric

Context: {context}
Task: {task}""",
            "version": "1.0.0",
            "author": "Sophia Intel AI",
            "tags": ["general", "versatile", "balanced", "assistant"],
            "memory_mb": 512,
            "cpu_cores": 0.3,
            "avg_response_time_ms": 1200,
            "cost_per_1k_tokens": 0.008,
            "quality_score": 7.8
        }

    # ==========================================================================
    # Swarm Configuration Definitions  
    # ==========================================================================

    def _load_swarm_configurations(self):
        """Load pre-built swarm configurations"""

        self._swarm_configs["software_development"] = {
            "name": "software_development",
            "display_name": "Software Development Swarm",
            "description": "Complete software development workflow from planning to deployment.",
            "category": "development",
            "use_case": "software_development",
            "complexity_level": "advanced",
            "agent_blueprints": [
                {"name": "architect", "role": "technical_lead", "required": True},
                {"name": "senior_developer", "role": "lead_developer", "required": True},
                {"name": "senior_developer", "role": "developer", "required": False, "max_count": 3},
                {"name": "qa_engineer", "role": "quality_assurance", "required": True},
                {"name": "security_expert", "role": "security_reviewer", "required": False},
                {"name": "devops_engineer", "role": "deployment_specialist", "required": False}
            ],
            "min_agents": 3,
            "max_agents": 8,
            "workflow_steps": [
                {"step": "requirements_analysis", "agents": ["architect"], "duration_min": 30},
                {"step": "architecture_design", "agents": ["architect"], "duration_min": 60},
                {"step": "implementation_planning", "agents": ["architect", "senior_developer"], "duration_min": 45},
                {"step": "code_development", "agents": ["senior_developer"], "duration_min": 180, "parallel": True},
                {"step": "code_review", "agents": ["architect", "senior_developer"], "duration_min": 60},
                {"step": "security_review", "agents": ["security_expert"], "duration_min": 30, "optional": True},
                {"step": "testing", "agents": ["qa_engineer"], "duration_min": 90},
                {"step": "deployment_prep", "agents": ["devops_engineer"], "duration_min": 45, "optional": True},
                {"step": "final_review", "agents": ["architect"], "duration_min": 30}
            ],
            "communication_pattern": "chain",
            "orchestration_model": "deepseek/deepseek-r1",
            "decision_strategy": "consensus",
            "estimated_duration_minutes": 480,
            "estimated_cost": 15.0,
            "version": "2.1.0",
            "author": "Sophia Intel AI",
            "tags": ["development", "software", "full-cycle", "enterprise"]
        }

        self._swarm_configs["research_analysis"] = {
            "name": "research_analysis",
            "display_name": "Research & Analysis Swarm",
            "description": "Comprehensive research and analysis workflow with multiple specialized researchers.",
            "category": "research",
            "use_case": "research_analysis",
            "complexity_level": "medium",
            "agent_blueprints": [
                {"name": "research_specialist", "role": "primary_researcher", "required": True},
                {"name": "research_specialist", "role": "secondary_researcher", "required": False, "max_count": 2},
                {"name": "data_analyst", "role": "data_specialist", "required": False},
                {"name": "content_strategist", "role": "report_writer", "required": True},
                {"name": "orchestrator", "role": "coordinator", "required": True}
            ],
            "min_agents": 3,
            "max_agents": 6,
            "workflow_steps": [
                {"step": "research_planning", "agents": ["orchestrator", "research_specialist"], "duration_min": 30},
                {"step": "primary_research", "agents": ["research_specialist"], "duration_min": 120, "parallel": True},
                {"step": "data_analysis", "agents": ["data_analyst"], "duration_min": 90, "optional": True},
                {"step": "synthesis", "agents": ["research_specialist"], "duration_min": 60},
                {"step": "report_drafting", "agents": ["content_strategist"], "duration_min": 90},
                {"step": "peer_review", "agents": ["research_specialist"], "duration_min": 45},
                {"step": "final_edit", "agents": ["content_strategist"], "duration_min": 30}
            ],
            "communication_pattern": "mesh",
            "orchestration_model": "anthropic/claude-3.7-sonnet",
            "decision_strategy": "majority",
            "estimated_duration_minutes": 240,
            "estimated_cost": 8.5,
            "version": "1.8.0",
            "author": "Sophia Intel AI", 
            "tags": ["research", "analysis", "reports", "collaborative"]
        }

        self._swarm_configs["security_audit"] = {
            "name": "security_audit",
            "display_name": "Security Audit Swarm",
            "description": "Comprehensive security assessment and audit workflow.",
            "category": "security",
            "use_case": "security_audit", 
            "complexity_level": "advanced",
            "agent_blueprints": [
                {"name": "security_expert", "role": "lead_auditor", "required": True},
                {"name": "security_expert", "role": "specialist", "required": False, "max_count": 2},
                {"name": "architect", "role": "architecture_reviewer", "required": True},
                {"name": "senior_developer", "role": "code_reviewer", "required": False},
                {"name": "devops_engineer", "role": "infrastructure_reviewer", "required": False},
                {"name": "orchestrator", "role": "audit_coordinator", "required": True}
            ],
            "min_agents": 3,
            "max_agents": 7,
            "workflow_steps": [
                {"step": "audit_planning", "agents": ["orchestrator", "security_expert"], "duration_min": 45},
                {"step": "architecture_review", "agents": ["security_expert", "architect"], "duration_min": 90},
                {"step": "code_analysis", "agents": ["security_expert", "senior_developer"], "duration_min": 120, "parallel": True},
                {"step": "infrastructure_audit", "agents": ["security_expert", "devops_engineer"], "duration_min": 90, "parallel": True},
                {"step": "vulnerability_assessment", "agents": ["security_expert"], "duration_min": 180},
                {"step": "risk_analysis", "agents": ["security_expert"], "duration_min": 60},
                {"step": "findings_synthesis", "agents": ["orchestrator", "security_expert"], "duration_min": 60},
                {"step": "recommendations", "agents": ["security_expert"], "duration_min": 90}
            ],
            "communication_pattern": "chain",
            "orchestration_model": "openai/gpt-5",
            "decision_strategy": "consensus",
            "estimated_duration_minutes": 360,
            "estimated_cost": 20.0,
            "version": "2.0.0",
            "author": "Sophia Intel AI",
            "tags": ["security", "audit", "compliance", "enterprise"]
        }

        self._swarm_configs["content_creation"] = {
            "name": "content_creation",
            "display_name": "Content Creation Swarm",
            "description": "Multi-stage content creation workflow from strategy to publication.",
            "category": "creative",
            "use_case": "content_marketing",
            "complexity_level": "medium",
            "agent_blueprints": [
                {"name": "content_strategist", "role": "strategy_lead", "required": True},
                {"name": "content_strategist", "role": "writer", "required": True, "max_count": 2},
                {"name": "research_specialist", "role": "researcher", "required": False},
                {"name": "data_analyst", "role": "performance_analyst", "required": False},
                {"name": "generalist", "role": "editor", "required": True}
            ],
            "min_agents": 3,
            "max_agents": 6,
            "workflow_steps": [
                {"step": "content_strategy", "agents": ["content_strategist"], "duration_min": 45},
                {"step": "research", "agents": ["research_specialist"], "duration_min": 60, "optional": True},
                {"step": "content_creation", "agents": ["content_strategist"], "duration_min": 120},
                {"step": "editing", "agents": ["generalist"], "duration_min": 30},
                {"step": "optimization", "agents": ["content_strategist"], "duration_min": 30},
                {"step": "performance_review", "agents": ["data_analyst"], "duration_min": 20, "optional": True}
            ],
            "communication_pattern": "chain",
            "orchestration_model": "anthropic/claude-3.7-sonnet",
            "decision_strategy": "leader",
            "estimated_duration_minutes": 180,
            "estimated_cost": 6.0,
            "version": "1.5.0",
            "author": "Sophia Intel AI",
            "tags": ["content", "creative", "marketing", "strategy"]
        }

        self._swarm_configs["quick_analysis"] = {
            "name": "quick_analysis",
            "display_name": "Quick Analysis Swarm",
            "description": "Fast, lightweight analysis for simple tasks and quick turnaround needs.",
            "category": "analysis",
            "use_case": "rapid_analysis",
            "complexity_level": "basic",
            "agent_blueprints": [
                {"name": "generalist", "role": "analyst", "required": True},
                {"name": "research_specialist", "role": "researcher", "required": False},
                {"name": "orchestrator", "role": "coordinator", "required": True}
            ],
            "min_agents": 2,
            "max_agents": 3,
            "workflow_steps": [
                {"step": "task_analysis", "agents": ["orchestrator"], "duration_min": 10},
                {"step": "research", "agents": ["research_specialist"], "duration_min": 30, "optional": True},
                {"step": "analysis", "agents": ["generalist"], "duration_min": 45},
                {"step": "review", "agents": ["orchestrator"], "duration_min": 15}
            ],
            "communication_pattern": "chain",
            "orchestration_model": "deepseek/deepseek-chat-v3.1:free",
            "decision_strategy": "leader",
            "estimated_duration_minutes": 60,
            "estimated_cost": 2.0,
            "version": "1.0.0",
            "author": "Sophia Intel AI",
            "tags": ["analysis", "quick", "lightweight", "basic"]
        }

    # ==========================================================================
    # Public API Methods
    # ==========================================================================

    def get_blueprint(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific agent blueprint by name"""
        return self._blueprints.get(name)

    def get_swarm_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific swarm configuration by name"""
        return self._swarm_configs.get(name)

    def list_blueprints(self, 
                       category: Optional[str] = None,
                       tier: Optional[AgentTier] = None,
                       task_type: Optional[TaskType] = None) -> List[Dict[str, Any]]:
        """List available agent blueprints with optional filtering"""
        blueprints = []
        
        for blueprint_data in self._blueprints.values():
            # Apply filters
            if category and blueprint_data.get("category") != category:
                continue
            if tier and blueprint_data.get("tier") != tier:
                continue
            if task_type and task_type not in blueprint_data.get("task_types", []):
                continue
                
            blueprints.append(blueprint_data)
        
        return sorted(blueprints, key=lambda x: (x.get("tier", AgentTier.BASIC), x.get("name")))

    def list_swarm_configs(self,
                          category: Optional[str] = None,
                          use_case: Optional[str] = None,
                          complexity: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available swarm configurations with optional filtering"""
        configs = []
        
        for config_data in self._swarm_configs.values():
            # Apply filters
            if category and config_data.get("category") != category:
                continue
            if use_case and config_data.get("use_case") != use_case:
                continue
            if complexity and config_data.get("complexity_level") != complexity:
                continue
                
            configs.append(config_data)
            
        return sorted(configs, key=lambda x: (x.get("complexity_level"), x.get("name")))

    def get_blueprint_categories(self) -> List[str]:
        """Get all available blueprint categories"""
        categories = set()
        for blueprint in self._blueprints.values():
            categories.add(blueprint.get("category"))
        return sorted(list(categories))

    def get_swarm_categories(self) -> List[str]:
        """Get all available swarm configuration categories"""
        categories = set()
        for config in self._swarm_configs.values():
            categories.add(config.get("category"))
        return sorted(list(categories))

    def search_blueprints(self, query: str) -> List[Dict[str, Any]]:
        """Search blueprints by name, description, or tags"""
        query_lower = query.lower()
        results = []
        
        for blueprint in self._blueprints.values():
            # Search in name, display_name, description, and tags
            searchable_text = " ".join([
                blueprint.get("name", ""),
                blueprint.get("display_name", ""),
                blueprint.get("description", ""),
                " ".join(blueprint.get("tags", []))
            ]).lower()
            
            if query_lower in searchable_text:
                results.append(blueprint)
        
        return results

    def search_swarm_configs(self, query: str) -> List[Dict[str, Any]]:
        """Search swarm configurations by name, description, or tags"""
        query_lower = query.lower()
        results = []
        
        for config in self._swarm_configs.values():
            # Search in name, display_name, description, and tags
            searchable_text = " ".join([
                config.get("name", ""),
                config.get("display_name", ""),
                config.get("description", ""),
                " ".join(config.get("tags", []))
            ]).lower()
            
            if query_lower in searchable_text:
                results.append(config)
        
        return results

    def get_recommended_swarm(self, task_description: str, budget: str = "medium") -> Optional[str]:
        """Get recommended swarm configuration based on task description and budget"""
        task_lower = task_description.lower()
        
        # Simple keyword-based recommendations
        if any(word in task_lower for word in ["code", "develop", "software", "app", "programming"]):
            return "software_development" if budget in ["high", "premium"] else "quick_analysis"
        elif any(word in task_lower for word in ["research", "analyze", "study", "investigate"]):
            return "research_analysis"
        elif any(word in task_lower for word in ["security", "audit", "vulnerability", "penetration"]):
            return "security_audit" 
        elif any(word in task_lower for word in ["content", "write", "blog", "marketing", "copy"]):
            return "content_creation"
        else:
            return "quick_analysis"

    def validate_blueprint(self, blueprint_data: Dict[str, Any]) -> List[str]:
        """Validate a blueprint configuration and return any errors"""
        errors = []
        
        required_fields = ["name", "display_name", "description", "category", "capabilities", "model_config"]
        for field in required_fields:
            if field not in blueprint_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate capabilities scores
        if "capabilities" in blueprint_data:
            for capability, score in blueprint_data["capabilities"].items():
                if not isinstance(score, (int, float)) or not (0 <= score <= 10):
                    errors.append(f"Invalid capability score for {capability}: must be between 0 and 10")
        
        # Validate task types
        if "task_types" in blueprint_data:
            for task_type in blueprint_data["task_types"]:
                try:
                    TaskType(task_type)
                except ValueError:
                    errors.append(f"Invalid task type: {task_type}")
        
        return errors

    def validate_swarm_config(self, config_data: Dict[str, Any]) -> List[str]:
        """Validate a swarm configuration and return any errors"""
        errors = []
        
        required_fields = ["name", "display_name", "description", "agent_blueprints"]
        for field in required_fields:
            if field not in config_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate agent blueprint requirements
        if "agent_blueprints" in config_data:
            for agent_req in config_data["agent_blueprints"]:
                if "name" not in agent_req:
                    errors.append("Agent requirement missing 'name' field")
                elif agent_req["name"] not in self._blueprints:
                    errors.append(f"Unknown agent blueprint: {agent_req['name']}")
        
        # Validate min/max agents
        min_agents = config_data.get("min_agents", 1)
        max_agents = config_data.get("max_agents", 10)
        if min_agents > max_agents:
            errors.append("min_agents cannot be greater than max_agents")
        
        return errors

    def get_catalog_stats(self) -> Dict[str, Any]:
        """Get statistics about the catalog"""
        blueprint_categories = {}
        swarm_categories = {}
        
        for blueprint in self._blueprints.values():
            category = blueprint.get("category", "unknown")
            blueprint_categories[category] = blueprint_categories.get(category, 0) + 1
        
        for config in self._swarm_configs.values():
            category = config.get("category", "unknown")
            swarm_categories[category] = swarm_categories.get(category, 0) + 1
        
        return {
            "total_blueprints": len(self._blueprints),
            "total_swarm_configs": len(self._swarm_configs),
            "blueprint_categories": blueprint_categories,
            "swarm_categories": swarm_categories,
            "latest_versions": {
                "blueprints": max([bp.get("version", "1.0.0") for bp in self._blueprints.values()]),
                "swarms": max([sc.get("version", "1.0.0") for sc in self._swarm_configs.values()])
            }
        }


# Global catalog instance
_agent_catalog = AgentCatalog()


def get_catalog() -> AgentCatalog:
    """Get the global agent catalog instance"""
    return _agent_catalog


# Convenience functions
def get_blueprint(name: str) -> Optional[Dict[str, Any]]:
    """Get agent blueprint by name"""
    return _agent_catalog.get_blueprint(name)


def get_swarm_config(name: str) -> Optional[Dict[str, Any]]:
    """Get swarm configuration by name"""  
    return _agent_catalog.get_swarm_config(name)


def list_blueprints(**filters) -> List[Dict[str, Any]]:
    """List agent blueprints with optional filters"""
    return _agent_catalog.list_blueprints(**filters)


def list_swarm_configs(**filters) -> List[Dict[str, Any]]:
    """List swarm configurations with optional filters"""
    return _agent_catalog.list_swarm_configs(**filters)