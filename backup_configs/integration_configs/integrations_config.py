"""
Platform Integration Configuration
Status: 10/13 platforms configured
Last Updated: 2025-01-04 - Security Update: Moved all credentials to environment variables
"""
import os

# INTEGRATION CONFIGURATION - ALL CREDENTIALS FROM ENVIRONMENT VARIABLES
INTEGRATIONS = {
    "gong": {
        "enabled": True,
        "status": "configured",
        "api_url": "https://us-70092.api.gong.io",
        "access_key": os.getenv("GONG_ACCESS_KEY"),
        "client_secret": os.getenv("GONG_CLIENT_SECRET"),
        "stats": {"users": 92, "calls": "100+", "company": "Pay Ready"},
    },
    "asana": {
        "enabled": True,
        "status": "configured",
        "pat_token": os.getenv("ASANA_PAT_TOKEN"),
        "stats": {"workspaces": 2, "primary": "payready.com"},
    },
    "linear": {
        "enabled": True,
        "status": "configured",
        "api_key": os.getenv("LINEAR_API_KEY"),
        "stats": {"teams": 9, "user": "Lynn Musil"},
    },
    "ceo_knowledge_base": {
        "enabled": True,
        "status": "configured",
        "platform": "airtable",
        "purpose": "CEO proprietary and foundational knowledge only - NOT operational data",
        "api_key": os.getenv("AIRTABLE_API_KEY"),
        "base_id": "appBOVJqGE166onrD",  # CEO Knowledge Base
        "tables": {
            "employee_roster": "Employee Roster",  # 100+ employees with cross-platform IDs
            "strategic_initiatives": "Strategic Initiatives",  # CEO-level initiatives
            "executive_decisions": "Executive Decisions",  # Critical decisions & rationale
        },
        "data_classification": "Proprietary/Confidential",
        "sync_direction": "Airtable → Sophia (one-way)",
        "webhook_url": None,
        "stats": {"type": "strategic", "sensitivity": "high", "integration": "active"},
        "note": "Business service data (Gong, Slack, etc.) stays in native platforms",
        "pay_ready_foundational_knowledge": {
            "company_overview": {
                "name": "Pay Ready",
                "mission": "AI-first resident engagement, payments, and recovery platform for U.S. multifamily housing industry",
                "evolution": "Evolved from specialized collections vendor to comprehensive financial operating system for PMCs",
                "stage": "High-growth, bootstrapped and profitable",
                "team": "~100 talented humans",
                "reach": "$20B+ in annual rent processed",
            },
            "critical_connections": {
                "gong": "Sales data, customer interactions, pipeline metrics",
                "linear": "Product development, engineering roadmap, sprint tracking",
                "asana": "Company-wide project management, OKRs, cross-functional initiatives",
                "slack": "Real-time team communication, decisions, updates",
                "intercom": "Customer support, feedback, product adoption metrics",
                "notion": "Company knowledge base, documentation, policies",
            },
            "integration_purpose": "Unified context for AI agents to understand business operations holistically",
        },
    },
    "operational_data": {
        "enabled": True,
        "status": "configured",
        "platform": "airtable",
        "purpose": "Operational metrics, performance data, and analytics",
        "api_key": os.getenv("AIRTABLE_API_KEY"),  # Same API key as CEO Knowledge Base
        "base_id": "appZXYABCDEF12345",  # Operational Data Base (placeholder - update with actual)
        "tables": {
            "metrics": "Metrics",
            "performance": "Performance",
            "analytics": "Analytics",
        },
        "data_classification": "Internal/Operational",
        "sync_direction": "bidirectional",
        "webhook_url": "https://sophia-webhooks.payready.com/airtable",
        "stats": {"type": "operational", "sensitivity": "medium", "integration": "active"},
    },
    "hubspot": {
        "enabled": True,
        "status": "configured",
        "app_id": "1688965",
        "client_id": "f690cabd-1234-5678-90ab-cdef12345678",
        "client_secret": os.getenv("HUBSPOT_CLIENT_SECRET"),
        "redirect_uri": "http://localhost:3000/oauth/hubspot/callback",
        "stats": {"type": "CRM", "connection": "OAuth 2.0"},
    },
    "intercom": {
        "enabled": True,
        "status": "configured",
        "client_id": "5678abcd-ef01-2345-6789-abcdef012345",
        "client_secret": os.getenv("INTERCOM_CLIENT_SECRET"),
        "redirect_uri": "http://localhost:3000/auth/intercom/callback",
        "stats": {"type": "Customer Support", "connection": "OAuth 2.0"},
    },
    "salesforce": {
        "enabled": False,
        "status": "planned",
        "note": "Enterprise CRM - integration planned for Q1 2025",
    },
    "airtable": {
        "enabled": True,
        "status": "connected via CEO Knowledge Base and Operational Data",
        "note": "Primary data platform for strategic and operational intelligence",
    },
    "looker": {
        "enabled": False,
        "status": "planned",
        "note": "BI Platform - integration planned for advanced analytics",
    },
    "elevenlabs": {
        "enabled": True,
        "status": "configured",
        "api_key": os.getenv("ELEVENLABS_API_KEY"),
        "voice_models": {
            "sophia": "21m00Tcm4TlvDq8ikWAM",  # Professional female voice
            "artemis": "ErXwobaYiN019PkySvjV",  # Clear male voice
        },
        "stats": {"type": "Text-to-Speech", "quality": "Ultra-realistic"},
    },
    "discord": {
        "enabled": False,
        "status": "evaluating",
        "note": "Team collaboration - evaluating vs Slack for engineering teams",
    },
    "zoho": {
        "enabled": False,
        "status": "evaluating",
        "note": "CRM Suite - alternative to Salesforce for SMB segment",
    },
    "github": {
        "enabled": True,
        "status": "native",
        "note": "Version control - integrated via git operations",
    },
    "lattice": {
        "enabled": True,
        "status": "configured",
        "api_key": os.getenv("LATTICE_API_KEY"),
        "base_url": "https://api.lattice.com/v1",
        "stats": {"type": "HR/Performance", "employees": "100+"},
    },
    "datadog": {
        "enabled": False,
        "status": "planned",
        "note": "Monitoring & APM - integration planned for production",
    },
    "segment": {
        "enabled": False,
        "status": "evaluating",
        "note": "Customer data platform - evaluating for event tracking",
    },
}


# Summary Statistics
def get_integration_summary():
    """Generate integration summary statistics"""
    total = len(INTEGRATIONS)
    connected = sum(
        1 for i in INTEGRATIONS.values() if i.get("status") in ["connected", "configured", "native"]
    )
    planned = sum(1 for i in INTEGRATIONS.values() if i.get("status") == "planned")
    evaluating = sum(1 for i in INTEGRATIONS.values() if i.get("status") == "evaluating")

    return {
        "total_platforms": total,
        "connected": connected,
        "planned": planned,
        "evaluating": evaluating,
        "completion_rate": f"{(connected/total)*100:.1f}%",
    }


# Required Environment Variables
REQUIRED_ENV_VARS = [
    "GONG_ACCESS_KEY",
    "GONG_CLIENT_SECRET",
    "ASANA_PAT_TOKEN",
    "LINEAR_API_KEY",
    "AIRTABLE_API_KEY",
    "HUBSPOT_CLIENT_SECRET",
    "INTERCOM_CLIENT_SECRET",
    "ELEVENLABS_API_KEY",
    "LATTICE_API_KEY",
]


def validate_credentials():
    """Validate that all required environment variables are set"""
    missing = []
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print(f"⚠️  Missing environment variables: {', '.join(missing)}")
        print("Please set these in your .env file")
        return False

    print("✅ All integration credentials are configured")
    return True


if __name__ == "__main__":
    summary = get_integration_summary()
    print("\n📊 Integration Summary:")
    print(f"  • Total Platforms: {summary['total_platforms']}")
    print(f"  • Connected: {summary['connected']}")
    print(f"  • Planned: {summary['planned']}")
    print(f"  • Evaluating: {summary['evaluating']}")
    print(f"  • Completion Rate: {summary['completion_rate']}")

    validate_credentials()
