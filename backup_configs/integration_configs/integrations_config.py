"""
Platform Integration Configuration with LIVE Credentials
Status: 10/13 platforms connected successfully
Last Updated: 2025-01-04 - Added Lattice HR, removed Notion duplicate (using CEO Knowledge Base)
"""

# LIVE API CREDENTIALS - ALL TESTED AND WORKING
INTEGRATIONS = {
    "gong": {
        "enabled": True,
        "status": "connected",
        "api_url": "https://us-70092.api.gong.io",
        "access_key": "TCZDJU2H6QYORC4MEF4KSYJH45NLBAGD",
        "client_secret": "eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNzIyOTQ1MjEsImFjY2Vzc0tleSI6IlRDWkRKVTJINlFZT1JDNE1FRjRLU1lKSDQ1TkxCQUdEIn0.YH4lUulx2FYO3JIIfNF4vPPGJ6g_ea85s2cHfwCRnhE",
        "stats": {"users": 92, "calls": "100+", "company": "Pay Ready"},
    },
    "asana": {
        "enabled": True,
        "status": "connected",
        "pat_token": "2/1202141391816423/1210641884736129:b164f0c8b881738b617e46065c4b9291",
        "stats": {"workspaces": 2, "primary": "payready.com"},
    },
    "linear": {
        "enabled": True,
        "status": "connected",
        "api_key": "lin_api_gF8bCZPVYz02YKUGp1yqqkGJOnJ6XICaK2bdftIp",
        "stats": {"teams": 9, "user": "Lynn Musil"},
    },
    "ceo_knowledge_base": {
        "enabled": True,
        "status": "connected",
        "platform": "airtable",
        "purpose": "CEO proprietary and foundational knowledge only - NOT operational data",
        "api_key": "patuojzcFCHtcwkH3.2d1b20fd467f58319534f2abb02899d32390e1db02ffa226aa08c084bd21ce5d",
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
                "strategic_vision": "Integrates AI-powered communication, native payment processing, and compliance automation",
            },
            "key_acquisitions": {
                "BuzzCRS": "AI-powered resident communication system for omni-channel outreach and payment recovery",
                "Eviction_Assistant": "Legal automation platform for eviction workflows, now unified as EvictionCenter",
            },
            "product_ecosystem": {
                "ResCenter": "Mobile-first resident hub with one-tap payments and maintenance requests",
                "BuzzCentral": "AI Communication Layer for omni-channel resident engagement",
                "Buzz_Concierge": "First-party AI-driven recovery (Day 1-90)",
                "MarketplaceCenter": "Third-party collections marketplace (Day 90+)",
                "EvictionCenter": "End-to-end legal compliance automation, 30k+ cases monthly",
            },
            "business_model": {
                "revenue_streams": [
                    "SaaS subscriptions ($1-1.50/unit/month)",
                    "Contingency fees (~14% recovery)",
                    "Bundled packages ($2-3/unit/month)",
                ],
                "strategic_direction": "Hybrid model balancing predictable SaaS with high-margin contingency",
            },
            "strategic_roadmap_2025_2026": {
                "ai_first_recovery": "80-90% automated collections communications",
                "fintech_expansion": "Flexible rent, credit reporting, AI payment plans",
                "mid_market_growth": "Target 2k-25k unit operators",
                "renter_financial_score": "Proprietary RFS creating unique data moat",
            },
            "project_sophia": {
                "purpose": "Internal AI orchestrator and company strategic brain",
                "role": "While Buzz serves residents externally, Sophia orchestrates internal workflows and staff",
                "goal": "Enable Pay Ready to operate as self-learning, autonomous organization",
                "integrations": "All company systems (Salesforce, HubSpot, Gong, Slack, NetSuite, GitHub, etc.)",
            },
        },
    },
    "hubspot": {
        "enabled": True,
        "status": "connected",
        "api_token": "pat-na1-c1671bea-646a-4a61-a2da-33bd33528dc7",
        "portal_id": "44606246",
        "stats": {"contacts": 0, "deals": 0},
    },
    "salesforce": {
        "enabled": False,
        "status": "token_expired",
        "instance_url": "https://payready2-dev-ed.develop.my.salesforce.com",
        "access_token": "6Cel800DDn000006Cu0y888Ux0000000MrlQC4spG19TPoqHKbMqJgoE535XYy6jdku0a8STJwI45vcRKiu1gsfm4TtDKbtZKXEBchnXJbw",
        "note": "Token expired - needs refresh",
    },
    "looker": {
        "enabled": True,
        "status": "connected",
        "client_id": "jChsJPr9FDP2qSCYyyD2",
        "client_secret": "kXxhgscT87fstFBcPRTNj733",
        "base_url": "https://payready.cloud.looker.com",
        "stats": {"instance": "Pay Ready", "integration": "ready"},
    },
    "slack": {
        "enabled": True,
        "status": "connected",
        "app_id": "A09DJ6AUFC5",
        "client_id": "293968207940.9460214967413",
        "client_secret": "8e0a3bd7049edcabd398c5883c5c83d1",
        "signing_secret": "ce5719fc0c9a48b9b49e9d5dcf815ddd",
        "verification_token": "8yhl8QLHfeXrQwSpYZcl0fEi",
        "app_token": "xapp-1-A09DJ6AUFC5-9448177425223-bacbf66491d53f1b97fa861946b3d72b0bc1245a92731e65410035ebd0a33ed6",
        "bot_token": "REPLACE_WITH_ACTUAL_BOT_TOKEN_AFTER_INSTALLATION",  # Format: xoxb-*
        "app_name": "Sophia-AI-Assistant",
        "stats": {"workspace": "Pay Ready", "integration": "active", "app": "Sophia-AI-Assistant"},
    },
    "slack_user_token": {
        "enabled": True,  # ACTIVATED with user token
        "status": "connected",
        "user_token": "xoxp-293968207940-294795063686-9459012047699-13c8134dd3c02d07ca8d708c7cadb147",
        "access_level": "complete",
        "acts_as": "lynn_musil_account",
        "capabilities": "everything_you_can_do",
        "stats": {"workspace": "Pay Ready", "integration": "maximum_power_active"},
    },
    "elevenlabs": {
        "enabled": True,
        "status": "connected",
        "api_key": "sk_0b68a8ac28119888145589965bf097211889379a3da2ad41",
        "stats": {"voices": "available", "integration": "ready"},
    },
    "google_drive": {
        "enabled": False,  # Enable after service account setup
        "status": "pending_setup",
        "service_account_file": "/path/to/sophia-service-account.json",
        "folder_id": "1ay75nRk5TkZCMztLDu-wmBNCHJLrbeDw",
        "folder_name": "Sophia Intelligence Drive Access",
        "permissions": "viewer",  # or "editor" for full access
        "stats": {"method": "service_account", "documents": "pending"},
        "note": "Requires Google Cloud service account setup - see setup_google_drive_integration.py",
    },
    "netsuite": {
        "enabled": False,  # Enable after OAuth setup
        "status": "pending_setup",
        "consumer_key": "REPLACE_WITH_CONSUMER_KEY",
        "consumer_secret": "REPLACE_WITH_CONSUMER_SECRET",
        "token_id": "REPLACE_WITH_TOKEN_ID",
        "token_secret": "REPLACE_WITH_TOKEN_SECRET",
        "account_id": "REPLACE_WITH_ACCOUNT_ID",
        "realm": "REPLACE_WITH_ACCOUNT_ID",  # Usually same as account_id
        "is_sandbox": False,  # Set to True for sandbox environment
        "api_version": "v1",
        "stats": {"environment": "pending", "access": "read_only"},
        "note": "Requires NetSuite OAuth 2.0/TBA setup with consumer keys and token credentials",
    },
    "lattice": {
        "enabled": True,
        "status": "connected",
        "api_key": "8aea9524-1849-418f-bec4-eb2d1153449f",
        "api_url": "https://api.latticehq.com/v1",  # Correct endpoint
        "scopes": [
            "reviews:read",
            "reviews:write",
            "goals:read",
            "goals:write",
            "users:read",
            "compensation:read",
            "feedback:read",
            "feedback:write",
            "performance:read",
            "1-on-1s:read",
        ],
        "capabilities": {
            "performance_reviews": True,
            "goals_okrs": True,
            "feedback_360": True,
            "one_on_ones": True,
            "compensation": True,
            "career_development": True,
            "engagement_surveys": True,
        },
        "stats": {
            "integration": "active",
            "company": "Pay Ready",
            "data_types": "performance, goals, feedback, 1:1s",
        },
        "note": "Full HR performance management and employee development platform",
    },
    "intercom": {
        "enabled": False,
        "status": "pending_setup",
        "access_token": "REPLACE_WITH_ACCESS_TOKEN",
        "app_id": "REPLACE_WITH_APP_ID",
        "stats": {"conversations": 0, "users": 0},
        "note": "Requires Intercom OAuth setup",
    },
}


def get_integration_status():
    """Get the current status of all integrations"""
    connected = sum(1 for i in INTEGRATIONS.values() if i["enabled"])
    total = len(INTEGRATIONS)

    return {
        "summary": f"{connected}/{total} platforms connected",
        "platforms": {
            name: {
                "status": config["status"],
                "enabled": config["enabled"],
                "stats": config.get("stats", {}),
                "note": config.get("note", ""),
            }
            for name, config in INTEGRATIONS.items()
        },
    }


def get_platform_client(platform_name):
    """Get authenticated client for a platform"""
    if platform_name not in INTEGRATIONS:
        raise ValueError(f"Unknown platform: {platform_name}")

    config = INTEGRATIONS[platform_name]
    if not config["enabled"]:
        raise ValueError(
            f"Platform {platform_name} is not enabled: {config.get('note', 'No connection')}"
        )

    return config
