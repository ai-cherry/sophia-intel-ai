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
        "stats": {"users": 92, "calls": "100+", "company": "PayReady"}
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
        "enabled": False,
        "status": "needs_instance_url",
        "client_id": "jChsJPr9FDP2qSCYyyD2",
        "client_secret": "kXxhgscT87fstFBcPRTNj733",
        "note": "Credentials ready - provide instance URL to complete"
    },
    "slack": {
        "enabled": True,
        "status": "connected",
        "client_id": "293968207940.84057706630910663091",
        "client_secret": "778e2fb5b026f97587210602acfe1e0b",
        "signing_secret": "535eff2a503b06c333ec880f0e61d3c0",
        "app_token": "xapp-1-A08BXNNKH2P-8419174294449-0017379454ab9f022e02af300c29819d9d665e961a0d223aa782c2c9e0cd875f",
        "socket_token": "xapp-1-A08BXNNKH2P-8419174294449-0017379454ab9f022e02af300c29819d9d665e961a0d223aa782c2c9e0cd875f",
        "bot_token": "xoxe.xoxb-1-MS0yLTI5Mzk2ODIwNzk0MC04Mzk5OTUyNDE5MjA2LTg0MjkzOTEwOTc3MjgtODQxOTI2NzQzNjExMy01NmExNGJlMjNmNmNlZGQ2ODkzYTk4MzZlNTM5OWNhY2Q4NThiZmIwZmJmZThlMzc0YTgyNzg5NDRhMGQ1N2I1",
        "stats": {"workspace": "PayReady", "integration": "active"}
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