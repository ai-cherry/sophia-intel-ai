"""
Military-Themed Swarm Configurations for Artemis Code Excellence Platform
Professional command structure with military-inspired organization
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MissionStatus(Enum):
    """Mission execution status codes"""

    PENDING = "AWAITING_DEPLOYMENT"
    ACTIVE = "MISSION_ACTIVE"
    COMPLETE = "MISSION_COMPLETE"
    CRITICAL = "PRIORITY_OVERRIDE"
    ABORT = "MISSION_ABORT"


class UnitType(Enum):
    """Military unit classifications"""

    RECON = "reconnaissance"  # Scouting and intelligence gathering
    TACTICAL = "tactical_operations"  # Planning and strategy
    STRIKE = "strike_force"  # Direct action and execution
    SUPPORT = "support_operations"  # Quality control and validation
    COMMAND = "command_control"  # Leadership and coordination


@dataclass
class AgentProfile:
    """Individual agent combat profile"""

    callsign: str
    rank: str
    model: str
    specialty: str
    clearance_level: int  # 1-5 security clearance
    deployment_ready: bool = True
    mission_count: int = 0
    success_rate: float = 1.0
    commendations: List[str] = field(default_factory=list)


@dataclass
class SquadFormation:
    """Squad tactical formation configuration"""

    designation: str
    unit_type: UnitType
    motto: str
    minimum_agents: int
    maximum_agents: int
    required_specialists: List[str]
    communication_protocol: str
    chain_of_command: List[str]  # Ranks in order of authority


# ============================================
# TACTICAL UNIT CONFIGURATIONS
# ============================================

ARTEMIS_MILITARY_UNITS = {
    # 1. RECONNAISSANCE BATTALION - "Eyes of Artemis"
    "recon_battalion": {
        "designation": "1st Reconnaissance Battalion 'Pathfinders'",
        "unit_type": UnitType.RECON,
        "motto": "First to Know, First to Strike",
        "mission_brief": "Repository scanning and intelligence gathering operations",
        "squad_composition": {
            "scout_alpha": AgentProfile(
                callsign="SCOUT-1",
                rank="Reconnaissance Lead",
                model="google/gemini-2.0-flash-exp",
                specialty="Rapid codebase scanning and conflict detection",
                clearance_level=4,
            ),
            "scout_bravo": AgentProfile(
                callsign="SCOUT-2",
                rank="Architecture Analyst",
                model="google/gemini-2.0-flash-thinking-exp",
                specialty="Structural pattern recognition and dependency mapping",
                clearance_level=3,
            ),
            "scout_charlie": AgentProfile(
                callsign="SCOUT-3",
                rank="Documentation Specialist",
                model="google/gemini-flash-1.5",
                specialty="Documentation alignment and IaC verification",
                clearance_level=3,
            ),
        },
        "operational_parameters": {
            "scan_speed": "maximum",
            "coverage_requirement": 0.95,  # 95% repository coverage
            "reporting_interval": 30,  # seconds
            "parallel_operations": True,
            "stealth_mode": False,  # Visible progress indicators
        },
        "communication_protocol": "RECON-NET-SECURE",
        "chain_of_command": [
            "Reconnaissance Lead",
            "Architecture Analyst",
            "Documentation Specialist",
        ],
        "equipment": {
            "primary_tools": ["AST Parser", "Dependency Analyzer", "Conflict Detector"],
            "secondary_tools": ["Pattern Matcher", "Code Metrics Engine"],
            "intelligence_systems": ["Repository Knowledge Base", "Historical Analysis DB"],
        },
        "success_metrics": {
            "issues_detected": "integer",
            "scan_completion_time": "seconds",
            "false_positive_rate": "percentage",
        },
    },
    # 2. QUALITY CONTROL DIVISION - "Artemis Guard"
    "qc_division": {
        "designation": "Quality Control Division 'Sentinels'",
        "unit_type": UnitType.SUPPORT,
        "motto": "Excellence Through Vigilance",
        "mission_brief": "Detailed review and validation of reconnaissance findings",
        "squad_composition": {
            "qc_commander": AgentProfile(
                callsign="SENTINEL-LEAD",
                rank="QC Commander",
                model="anthropic/claude-3.5-sonnet-20241022",
                specialty="Strategic quality assessment and validation",
                clearance_level=5,
            ),
            "validator_alpha": AgentProfile(
                callsign="VALIDATOR-1",
                rank="Senior Validator",
                model="openai/gpt-4o-2024-11-20",
                specialty="Code quality metrics and best practices validation",
                clearance_level=4,
            ),
            "validator_bravo": AgentProfile(
                callsign="VALIDATOR-2",
                rank="Security Auditor",
                model="mistral/mistral-large-latest",
                specialty="Security vulnerability assessment",
                clearance_level=4,
            ),
            "validator_charlie": AgentProfile(
                callsign="VALIDATOR-3",
                rank="Performance Analyst",
                model="deepseek/deepseek-chat",
                specialty="Performance bottleneck identification",
                clearance_level=3,
            ),
        },
        "operational_parameters": {
            "review_depth": "comprehensive",
            "validation_rounds": 2,
            "consensus_requirement": 0.8,  # 80% agreement for approval
            "escalation_threshold": 0.6,  # Escalate if consensus below 60%
        },
        "communication_protocol": "QC-SECURE-CHANNEL",
        "chain_of_command": [
            "QC Commander",
            "Senior Validator",
            "Security Auditor",
            "Performance Analyst",
        ],
        "validation_criteria": {
            "code_quality": ["maintainability", "readability", "efficiency"],
            "security": ["vulnerability_scan", "dependency_audit", "access_control"],
            "performance": ["complexity_analysis", "resource_usage", "bottlenecks"],
            "compliance": ["coding_standards", "documentation", "test_coverage"],
        },
    },
    # 3. STRATEGIC PLANNING COMMAND - "Artemis Command"
    "planning_command": {
        "designation": "Strategic Planning Command 'Architects'",
        "unit_type": UnitType.COMMAND,
        "motto": "Vision, Strategy, Victory",
        "mission_brief": "High-level remediation planning and strategic decision making",
        "squad_composition": {
            "strategic_commander": AgentProfile(
                callsign="COMMAND-1",
                rank="Strategic Commander",
                model="openai/gpt-5",
                specialty="Master strategic planning and decision orchestration",
                clearance_level=5,
            ),
            "tactical_advisor": AgentProfile(
                callsign="COMMAND-2",
                rank="Tactical Advisor",
                model="x-ai/grok-5",
                specialty="Tactical implementation strategies",
                clearance_level=5,
            ),
            "intelligence_chief": AgentProfile(
                callsign="COMMAND-3",
                rank="Intelligence Chief",
                model="anthropic/claude-opus-4.1",
                specialty="Intelligence synthesis and risk assessment",
                clearance_level=5,
            ),
        },
        "operational_parameters": {
            "planning_depth": "strategic",
            "risk_tolerance": "minimal",
            "decision_consensus": "required",
            "authorization_level": "maximum",
        },
        "communication_protocol": "COMMAND-PRIORITY-ALPHA",
        "chain_of_command": ["Strategic Commander", "Tactical Advisor", "Intelligence Chief"],
        "planning_phases": [
            "intelligence_briefing",
            "threat_assessment",
            "resource_allocation",
            "strategy_formulation",
            "risk_mitigation",
            "execution_authorization",
        ],
        "decision_matrix": {
            "critical_issues": "immediate_action",
            "high_priority": "rapid_response",
            "standard_issues": "scheduled_remediation",
            "low_priority": "batch_processing",
        },
    },
    # 4. CODING STRIKE FORCE - "Artemis Operators"
    "strike_force": {
        "designation": "1st Coding Strike Force 'Operators'",
        "unit_type": UnitType.STRIKE,
        "motto": "Swift, Silent, Effective",
        "mission_brief": "Direct action code remediation and implementation",
        "squad_composition": {
            "strike_leader": AgentProfile(
                callsign="OPERATOR-LEAD",
                rank="Strike Team Leader",
                model="owen/owen-coder",
                specialty="Advanced code generation and refactoring",
                clearance_level=5,
            ),
            "operator_alpha": AgentProfile(
                callsign="OPERATOR-1",
                rank="Senior Developer",
                model="deepseek/deepseek-coder-v3",
                specialty="Complex algorithm implementation",
                clearance_level=4,
            ),
            "operator_bravo": AgentProfile(
                callsign="OPERATOR-2",
                rank="Systems Engineer",
                model="openai/gpt-4.1-preview",
                specialty="System integration and optimization",
                clearance_level=4,
            ),
            "operator_charlie": AgentProfile(
                callsign="OPERATOR-3",
                rank="Debug Specialist",
                model="qwen/qwen-3-coder",
                specialty="Bug fixing and error resolution",
                clearance_level=3,
            ),
        },
        "operational_parameters": {
            "execution_mode": "parallel_strike",
            "code_quality_threshold": 0.9,
            "test_coverage_minimum": 0.85,
            "rollback_capability": True,
            "hot_reload_enabled": True,
        },
        "communication_protocol": "STRIKE-SECURE-OPS",
        "chain_of_command": [
            "Strike Team Leader",
            "Senior Developer",
            "Systems Engineer",
            "Debug Specialist",
        ],
        "engagement_rules": {
            "breaking_changes": "commander_approval_required",
            "critical_systems": "dual_operator_verification",
            "production_code": "staged_deployment",
            "test_environment": "rapid_deployment",
        },
        "equipment": {
            "primary_tools": ["Advanced IDE", "Code Generator", "Refactoring Engine"],
            "testing_tools": ["Unit Test Framework", "Integration Tester", "Performance Profiler"],
            "deployment_tools": ["CI/CD Pipeline", "Version Control", "Rollback System"],
        },
    },
    # 5. FINAL REVIEW BATTALION - "Artemis Shield"
    "review_battalion": {
        "designation": "Final Review Battalion 'Guardians'",
        "unit_type": UnitType.SUPPORT,
        "motto": "Last Line of Excellence",
        "mission_brief": "Final quality assurance and deployment authorization",
        "squad_composition": {
            "review_commander": AgentProfile(
                callsign="GUARDIAN-LEAD",
                rank="Review Commander",
                model="anthropic/claude-3.5-sonnet-latest",
                specialty="Final approval and quality certification",
                clearance_level=5,
            ),
            "guardian_alpha": AgentProfile(
                callsign="GUARDIAN-1",
                rank="Code Inspector",
                model="openai/gpt-4o",
                specialty="Code compliance and standards verification",
                clearance_level=4,
            ),
            "guardian_bravo": AgentProfile(
                callsign="GUARDIAN-2",
                rank="Test Marshal",
                model="google/gemini-2.0-pro",
                specialty="Test coverage and quality validation",
                clearance_level=4,
            ),
            "guardian_charlie": AgentProfile(
                callsign="GUARDIAN-3",
                rank="Deployment Officer",
                model="mistral/mistral-large",
                specialty="Deployment readiness assessment",
                clearance_level=4,
            ),
        },
        "operational_parameters": {
            "review_thoroughness": "exhaustive",
            "approval_threshold": 0.95,
            "veto_power": True,
            "deployment_gate": True,
        },
        "communication_protocol": "GUARDIAN-FINAL-NET",
        "chain_of_command": [
            "Review Commander",
            "Code Inspector",
            "Test Marshal",
            "Deployment Officer",
        ],
        "checklist": {
            "code_quality": ["syntax", "style", "complexity", "documentation"],
            "testing": ["unit_tests", "integration_tests", "coverage", "performance"],
            "security": ["vulnerabilities", "dependencies", "secrets", "permissions"],
            "deployment": ["configuration", "environment", "rollback_plan", "monitoring"],
        },
        "sign_off_requirements": {
            "all_tests_passing": True,
            "coverage_threshold_met": True,
            "no_critical_issues": True,
            "documentation_complete": True,
            "approval_signatures": ["Review Commander", "Code Inspector"],
        },
    },
}


# ============================================
# MISSION CONFIGURATIONS
# ============================================

ARTEMIS_MISSION_TEMPLATES = {
    "operation_clean_sweep": {
        "name": "Operation Clean Sweep",
        "objective": "Full repository scan and comprehensive remediation",
        "units_deployed": [
            "recon_battalion",
            "qc_division",
            "planning_command",
            "strike_force",
            "review_battalion",
        ],
        "phases": [
            {
                "phase": 1,
                "name": "Reconnaissance",
                "units": ["recon_battalion"],
                "duration": "5-10 minutes",
                "deliverables": ["Initial scan report", "Issue inventory"],
            },
            {
                "phase": 2,
                "name": "Analysis",
                "units": ["qc_division"],
                "duration": "10-15 minutes",
                "deliverables": ["Detailed findings", "Priority matrix"],
            },
            {
                "phase": 3,
                "name": "Planning",
                "units": ["planning_command"],
                "duration": "5-10 minutes",
                "deliverables": ["Remediation plan", "Resource allocation"],
            },
            {
                "phase": 4,
                "name": "Execution",
                "units": ["strike_force"],
                "duration": "15-30 minutes",
                "deliverables": ["Code fixes", "Improvements"],
            },
            {
                "phase": 5,
                "name": "Verification",
                "units": ["review_battalion"],
                "duration": "5-10 minutes",
                "deliverables": ["Final report", "Deployment approval"],
            },
        ],
        "total_duration": "40-75 minutes",
        "success_criteria": {
            "issues_resolved": ">90%",
            "test_coverage": ">85%",
            "quality_score": ">95%",
        },
    },
    "rapid_response": {
        "name": "Rapid Response Protocol",
        "objective": "Quick critical issue resolution",
        "units_deployed": ["recon_battalion", "strike_force", "review_battalion"],
        "phases": [
            {
                "phase": 1,
                "name": "Quick Scan",
                "units": ["recon_battalion"],
                "duration": "2-5 minutes",
                "deliverables": ["Critical issues list"],
            },
            {
                "phase": 2,
                "name": "Strike",
                "units": ["strike_force"],
                "duration": "5-10 minutes",
                "deliverables": ["Critical fixes"],
            },
            {
                "phase": 3,
                "name": "Verify",
                "units": ["review_battalion"],
                "duration": "2-3 minutes",
                "deliverables": ["Deployment clearance"],
            },
        ],
        "total_duration": "9-18 minutes",
        "success_criteria": {
            "critical_issues_fixed": "100%",
            "deployment_ready": True,
        },
    },
    "deep_reconnaissance": {
        "name": "Deep Reconnaissance Mission",
        "objective": "Comprehensive codebase intelligence gathering",
        "units_deployed": ["recon_battalion", "qc_division", "planning_command"],
        "phases": [
            {
                "phase": 1,
                "name": "Deep Scan",
                "units": ["recon_battalion"],
                "duration": "10-15 minutes",
                "deliverables": ["Comprehensive scan", "Dependency map"],
            },
            {
                "phase": 2,
                "name": "Intelligence Analysis",
                "units": ["qc_division"],
                "duration": "15-20 minutes",
                "deliverables": ["Detailed analysis", "Risk assessment"],
            },
            {
                "phase": 3,
                "name": "Strategic Planning",
                "units": ["planning_command"],
                "duration": "10-15 minutes",
                "deliverables": ["Long-term strategy", "Improvement roadmap"],
            },
        ],
        "total_duration": "35-50 minutes",
        "success_criteria": {
            "coverage": "100%",
            "insights_generated": ">20",
            "actionable_recommendations": ">10",
        },
    },
}


# ============================================
# COMMUNICATION PROTOCOLS
# ============================================

COMMUNICATION_PROTOCOLS = {
    "RECON-NET-SECURE": {
        "encryption": "AES-256",
        "frequency": "High-bandwidth parallel",
        "format": "Structured intelligence reports",
        "priority_levels": ["FLASH", "IMMEDIATE", "PRIORITY", "ROUTINE"],
    },
    "QC-SECURE-CHANNEL": {
        "encryption": "RSA-4096",
        "frequency": "Dedicated validation channel",
        "format": "Detailed assessment matrices",
        "priority_levels": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
    },
    "COMMAND-PRIORITY-ALPHA": {
        "encryption": "Quantum-resistant",
        "frequency": "Command priority override",
        "format": "Strategic directives",
        "priority_levels": ["COMMAND", "STRATEGIC", "TACTICAL", "OPERATIONAL"],
    },
    "STRIKE-SECURE-OPS": {
        "encryption": "End-to-end encrypted",
        "frequency": "Real-time operational",
        "format": "Execution commands",
        "priority_levels": ["EXECUTE", "STANDBY", "ABORT"],
    },
    "GUARDIAN-FINAL-NET": {
        "encryption": "Multi-signature required",
        "frequency": "Final approval channel",
        "format": "Sign-off documentation",
        "priority_levels": ["APPROVED", "CONDITIONAL", "DENIED"],
    },
}


# ============================================
# STATUS INDICATORS
# ============================================

MISSION_STATUS_INDICATORS = {
    "STANDBY": {
        "color": "#808080",
        "icon": "⚪",
        "message": "Unit on standby",
    },
    "DEPLOYING": {
        "color": "#FFD700",
        "icon": "🟡",
        "message": "Deployment in progress",
    },
    "ACTIVE": {
        "color": "#00FF00",
        "icon": "🟢",
        "message": "Mission active",
    },
    "ENGAGED": {
        "color": "#FFA500",
        "icon": "🟠",
        "message": "Engaged with target",
    },
    "CRITICAL": {
        "color": "#FF0000",
        "icon": "🔴",
        "message": "Critical situation",
    },
    "COMPLETE": {
        "color": "#0000FF",
        "icon": "🔵",
        "message": "Mission complete",
    },
    "ABORT": {
        "color": "#800080",
        "icon": "🟣",
        "message": "Mission aborted",
    },
}


# ============================================
# COMMAND CENTER CONFIGURATION
# ============================================

COMMAND_CENTER_CONFIG = {
    "display_name": "Artemis Command Center",
    "theme": {
        "primary_color": "#1a1a2e",  # Dark navy
        "secondary_color": "#16213e",  # Darker navy
        "accent_color": "#e94560",  # Strategic red
        "success_color": "#0f9d58",  # Mission green
        "warning_color": "#f4b400",  # Alert yellow
        "info_color": "#4285f4",  # Intel blue
        "text_primary": "#ffffff",
        "text_secondary": "#a0a0a0",
        "border_color": "#2d2d44",
    },
    "layout": {
        "header": "mission_briefing",
        "main_display": "tactical_map",
        "sidebar_left": "unit_status",
        "sidebar_right": "intelligence_feed",
        "footer": "command_controls",
    },
    "displays": {
        "mission_briefing": {
            "title": "Mission Briefing",
            "components": ["objective", "timeline", "success_criteria"],
        },
        "tactical_map": {
            "title": "Tactical Overview",
            "components": ["repository_map", "issue_markers", "unit_positions"],
        },
        "unit_status": {
            "title": "Unit Status",
            "components": ["squad_health", "agent_readiness", "resource_usage"],
        },
        "intelligence_feed": {
            "title": "Intelligence Feed",
            "components": ["real_time_updates", "issue_discoveries", "progress_metrics"],
        },
        "command_controls": {
            "title": "Command Controls",
            "components": ["deploy_button", "abort_button", "status_indicators"],
        },
    },
    "sound_effects": {
        "enabled": False,  # Professional mode - no sounds
        "mission_start": None,
        "mission_complete": None,
        "alert": None,
    },
    "animations": {
        "subtle": True,
        "duration": "200ms",
        "easing": "ease-in-out",
    },
}


# ============================================
# OPERATIONAL FUNCTIONS
# ============================================


def get_unit_by_designation(designation: str) -> Dict[str, Any]:
    """Get military unit configuration by designation"""
    return ARTEMIS_MILITARY_UNITS.get(designation, {})


def get_mission_template(mission_type: str) -> Dict[str, Any]:
    """Get mission template configuration"""
    return ARTEMIS_MISSION_TEMPLATES.get(mission_type, {})


def calculate_mission_resources(units: List[str]) -> Dict[str, Any]:
    """Calculate total resources needed for mission"""
    total_agents = 0
    models_required = set()
    max_clearance_required = 0

    for unit_name in units:
        unit = get_unit_by_designation(unit_name)
        if unit:
            squad = unit.get("squad_composition", {})
            total_agents += len(squad)

            for agent in squad.values():
                if isinstance(agent, AgentProfile):
                    models_required.add(agent.model)
                    max_clearance_required = max(max_clearance_required, agent.clearance_level)

    return {
        "total_agents": total_agents,
        "unique_models": len(models_required),
        "models": list(models_required),
        "clearance_level_required": max_clearance_required,
        "estimated_tokens": total_agents * 4000,  # Rough estimate
    }


def generate_mission_briefing(mission_type: str, target: str = None) -> str:
    """Generate formatted mission briefing"""
    mission = get_mission_template(mission_type)
    if not mission:
        return "Mission template not found"

    briefing = f"""
╔════════════════════════════════════════════════════════════════╗
║                    MISSION BRIEFING                           ║
║                    Classification: UNCLASSIFIED               ║
╠════════════════════════════════════════════════════════════════╣
║ OPERATION: {mission['name']:<48}║
║ OBJECTIVE: {mission['objective']:<48}║
║ DURATION:  {mission['total_duration']:<48}║
╠════════════════════════════════════════════════════════════════╣
║ UNITS DEPLOYED:                                               ║
"""

    for unit in mission["units_deployed"]:
        unit_config = get_unit_by_designation(unit)
        if unit_config:
            briefing += f"║  • {unit_config['designation']:<57}║\n"
            briefing += f"║    {unit_config['motto']:<57}║\n"

    briefing += """╠════════════════════════════════════════════════════════════════╣
║ PHASES:                                                        ║
"""

    for phase in mission["phases"]:
        briefing += f"║  Phase {phase['phase']}: {phase['name']:<50}║\n"
        briefing += f"║    Duration: {phase['duration']:<46}║\n"

    briefing += """╠════════════════════════════════════════════════════════════════╣
║ AUTHORIZATION: Artemis Command                                ║
║ STATUS: READY FOR DEPLOYMENT                                  ║
╚════════════════════════════════════════════════════════════════╝
"""

    return briefing


# ============================================
# AGENT FACTORY INTEGRATION
# ============================================


class MilitaryAgentFactory:
    """Factory for creating military-themed agent configurations"""

    @staticmethod
    def create_squad(unit_designation: str) -> List[Dict[str, Any]]:
        """Create a squad of agents from unit configuration"""
        unit = get_unit_by_designation(unit_designation)
        if not unit:
            return []

        agents = []
        squad = unit.get("squad_composition", {})

        for role, profile in squad.items():
            if isinstance(profile, AgentProfile):
                agent_config = {
                    "name": profile.callsign,
                    "role": profile.rank,
                    "model": profile.model,
                    "system_prompt": f"""You are {profile.callsign}, {profile.rank} in {unit['designation']}.

Specialty: {profile.specialty}
Motto: {unit['motto']}
Security Clearance: Level {profile.clearance_level}

Your mission parameters:
- Maintain professional military bearing at all times
- Report findings in clear, concise tactical format
- Follow chain of command protocols
- Execute missions with precision and efficiency

Current Mission Brief: {unit['mission_brief']}

Operational Guidelines:
1. Acknowledge orders with "Roger" or "Copy"
2. Use NATO phonetic alphabet when necessary
3. Report status at regular intervals
4. Maintain operational security at all times
5. Complete objectives with maximum efficiency

Remember: {unit['motto']}""",
                    "metadata": {
                        "unit": unit_designation,
                        "clearance_level": profile.clearance_level,
                        "specialty": profile.specialty,
                        "communication_protocol": unit.get("communication_protocol", "STANDARD"),
                    },
                }
                agents.append(agent_config)

        return agents

    @staticmethod
    def create_mission_team(mission_type: str) -> Dict[str, List[Dict[str, Any]]]:
        """Create complete team for a mission"""
        mission = get_mission_template(mission_type)
        if not mission:
            return {}

        mission_team = {}
        for unit_name in mission["units_deployed"]:
            mission_team[unit_name] = MilitaryAgentFactory.create_squad(unit_name)

        return mission_team


# Export main components
__all__ = [
    "ARTEMIS_MILITARY_UNITS",
    "ARTEMIS_MISSION_TEMPLATES",
    "COMMAND_CENTER_CONFIG",
    "MilitaryAgentFactory",
    "get_unit_by_designation",
    "get_mission_template",
    "calculate_mission_resources",
    "generate_mission_briefing",
    "MissionStatus",
    "UnitType",
    "AgentProfile",
]
