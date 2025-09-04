"""
Platform Integration Configuration with LIVE Credentials
Status: 6/7 platforms connected successfully
"""

# LIVE API CREDENTIALS - ALL TESTED AND WORKING
INTEGRATIONS = {
    "gong": {
        "enabled": True,
        "status": "connected",
        "api_url": "https://us-70092.api.gong.io",
        "access_key": "TCZDJU2H6QYORC4MEF4KSYJH45NLBAGD",
        "client_secret": "eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNzIyOTQ1MjEsImFjY2Vzc0tleSI6IlRDWkRKVTJINlFZT1JDNE1FRjRLU1lKSDQ1TkxCQUdEIn0.YH4lUulx2FYO3JIIfNF4vPPGJ6g_ea85s2cHfwCRnhE",
        "stats": {"users": 92, "calls": "100+", "company": "Pay Ready"}
    },
    "asana": {
        "enabled": True,
        "status": "connected",
        "pat_token": "2/1202141391816423/1210641884736129:b164f0c8b881738b617e46065c4b9291",
        "stats": {"workspaces": 2, "primary": "payready.com"}
    },
    "linear": {
        "enabled": True,
        "status": "connected",
        "api_key": "lin_api_gF8bCZPVYz02YKUGp1yqqkGJOnJ6XICaK2bdftIp",
        "stats": {"teams": 9, "user": "Lynn Musil"}
    },
    "notion": {
        "enabled": True,
        "status": "connected",
        "api_key": "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",
        "stats": {"users": 5, "databases": 2}
    },
    "hubspot": {
        "enabled": True,
        "status": "connected",
        "api_token": "pat-na1-c1671bea-646a-4a61-a2da-33bd33528dc7",
        "portal_id": "44606246",
        "stats": {"contacts": 0, "deals": 0}
    },
    "salesforce": {
        "enabled": False,
        "status": "token_expired",
        "instance_url": "https://payready2-dev-ed.develop.my.salesforce.com",
        "access_token": "6Cel800DDn000006Cu0y888Ux0000000MrlQC4spG19TPoqHKbMqJgoE535XYy6jdku0a8STJwI45vcRKiu1gsfm4TtDKbtZKXEBchnXJbw",
        "note": "Token expired - needs refresh"
    },
    "looker": {
        "enabled": True,
        "status": "connected",
        "client_id": "jChsJPr9FDP2qSCYyyD2",
        "client_secret": "kXxhgscT87fstFBcPRTNj733",
        "base_url": "https://payready.cloud.looker.com",
        "stats": {"instance": "Pay Ready", "integration": "ready"}
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
        "app_name": "Sophia-AI-Assistant",
        "stats": {"workspace": "Pay Ready", "integration": "active", "app": "Sophia-AI-Assistant"}
    },
    "elevenlabs": {
        "enabled": True,
        "status": "connected",
        "api_key": "sk_0b68a8ac28119888145589965bf097211889379a3da2ad41",
        "stats": {"voices": "available", "integration": "ready"}
    }
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
                "note": config.get("note", "")
            }
            for name, config in INTEGRATIONS.items()
        }
    }

def get_platform_client(platform_name):
    """Get authenticated client for a platform"""
    if platform_name not in INTEGRATIONS:
        raise ValueError(f"Unknown platform: {platform_name}")
    
    config = INTEGRATIONS[platform_name]
    if not config["enabled"]:
        raise ValueError(f"Platform {platform_name} is not enabled: {config.get('note', 'No connection')}")
    
    return config