#!/usr/bin/env python3
"""
Configure Slack Channel Permissions for Sophia AI
Sets up channel-specific permissions and posting rules
for Pay Ready business intelligence alerts.
"""
import json
def generate_channel_configuration() -> dict[str, any]:
    """Generate comprehensive channel configuration"""
    channel_config = {
        "channels": {
            "#payments": {
                "purpose": "Master payment processing alerts (270 views report)",
                "alert_types": ["critical", "high"],
                "reports": ["master_payments"],
                "frequency": "real-time",
                "permissions": {
                    "sophia_can_post": True,
                    "alert_mentions": ["@finance-team", "@payments-lead"],
                    "escalation_channels": ["#finance-alerts"],
                },
                "business_hours": {
                    "enabled": True,
                    "timezone": "America/New_York",
                    "hours": "08:00-18:00",
                    "after_hours_channel": "#finance-alerts",
                },
            },
            "#finance": {
                "purpose": "ABS history and balance monitoring (252 views)",
                "alert_types": ["high", "medium"],
                "reports": ["abs_history"],
                "frequency": "hourly",
                "permissions": {
                    "sophia_can_post": True,
                    "alert_mentions": ["@finance-team"],
                    "escalation_channels": ["#finance-alerts"],
                },
            },
            "#operations": {
                "purpose": "Batch processing and operational alerts (235 views)",
                "alert_types": ["high", "medium"],
                "reports": ["batch_processing"],
                "frequency": "every_4_hours",
                "permissions": {
                    "sophia_can_post": True,
                    "alert_mentions": ["@ops-team"],
                    "escalation_channels": ["#tech-alerts"],
                },
            },
            "#finance-alerts": {
                "purpose": "Critical financial alerts and escalations",
                "alert_types": ["critical"],
                "reports": ["all"],
                "frequency": "immediate",
                "permissions": {
                    "sophia_can_post": True,
                    "alert_mentions": ["@finance-leadership", "@on-call"],
                    "escalation_channels": ["#executive"],
                },
            },
            "#tech-alerts": {
                "purpose": "System issues and data quality problems",
                "alert_types": ["medium", "high"],
                "reports": ["system_health", "data_quality"],
                "frequency": "immediate",
                "permissions": {
                    "sophia_can_post": True,
                    "alert_mentions": ["@tech-team", "@on-call-engineer"],
                },
            },
            "#general": {
                "purpose": "Daily summaries and general updates",
                "alert_types": ["low"],
                "reports": ["daily_summary"],
                "frequency": "daily",
                "permissions": {
                    "sophia_can_post": True,
                    "alert_mentions": [],
                    "business_hours_only": True,
                },
            },
        },
        "global_settings": {
            "rate_limits": {
                "max_alerts_per_hour": 10,
                "max_alerts_per_day": 50,
                "cooldown_between_similar_alerts": "15_minutes",
            },
            "emergency_contacts": {
                "critical_alerts": ["@finance-director", "@cto"],
                "system_down": ["@on-call-engineer", "@devops"],
            },
            "business_hours": {
                "timezone": "America/New_York",
                "weekdays": "Monday-Friday",
                "hours": "08:00-18:00",
            },
        },
    }
    return channel_config
def generate_slack_app_manifest() -> dict[str, any]:
    """Generate Slack app manifest with required permissions"""
    manifest = {
        "display_information": {
            "name": "Sophia AI Assistant",
            "description": "AI-powered business intelligence assistant for Pay Ready",
            "background_color": "#2c3e50",
        },
        "features": {
            "bot_user": {"display_name": "Sophia AI Assistant", "always_online": True},
            "slash_commands": [
                {
                    "command": "/sophia",
                    "description": "Get Pay Ready business intelligence insights",
                    "usage_hint": "help | reports | alerts | status",
                    "should_escape": False,
                }
            ],
        },
        "oauth_config": {
            "scopes": {
                "bot": [
                    "chat:write",  # Send messages
                    "chat:write.public",  # Send to channels without invitation
                    "channels:read",  # List channels
                    "groups:read",  # Access private channels
                    "im:read",  # Read direct messages
                    "im:write",  # Send direct messages
                    "commands",  # Handle slash commands
                    "users:read",  # Read user information
                    "reactions:write",  # Add reactions to messages
                ]
            }
        },
        "settings": {
            "event_subscriptions": {
                "request_url": "https://your-domain.com/api/slack/webhook",
                "bot_events": [
                    "app_mention",
                    "message.im",
                ],  # @sophia mentions  # Direct messages
            },
            "interactivity": {
                "is_enabled": True,
                "request_url": "https://your-domain.com/api/slack/webhook",
            },
            "org_deploy_enabled": False,
            "socket_mode_enabled": False,
            "token_rotation_enabled": False,
        },
    }
    return manifest
def save_configurations():
    """Save configuration files"""
    # Save channel configuration
    channel_config = generate_channel_configuration()
    with open("slack_channel_config.json", "w") as f:
        json.dump(channel_config, f, indent=2)
    # Save Slack app manifest
    app_manifest = generate_slack_app_manifest()
    with open("slack_app_manifest.json", "w") as f:
        json.dump(app_manifest, f, indent=2)
    print("✅ Configuration files generated:")
    print("   📋 slack_channel_config.json - Channel permissions and rules")
    print("   🔧 slack_app_manifest.json - Slack app configuration")
def print_setup_instructions():
    """Print setup instructions"""
    print("\n🚀 SLACK CHANNEL PERMISSIONS SETUP")
    print("=" * 50)
    instructions = [
        "1. **Add Sophia to Required Channels:**",
        "   /invite @sophia-ai-assistant",
        "",
        "2. **Set Channel Topics (to indicate Sophia monitoring):**",
        "   #payments: 🤖 Monitored by Sophia AI - Master payments (270 views)",
        "   #finance: 🤖 Monitored by Sophia AI - ABS history (252 views)",
        "   #operations: 🤖 Monitored by Sophia AI - Batch processing (235 views)",
        "",
        "3. **Configure User Groups:**",
        "   @finance-team - Finance department alerts",
        "   @ops-team - Operations team alerts",
        "   @tech-team - Technical issue alerts",
        "   @finance-leadership - Critical escalations",
        "",
        "4. **Set Channel Notification Preferences:**",
        "   #finance-alerts: All activity (critical alerts)",
        "   #payments: Mentions only (reduce noise)",
        "   #operations: Mentions only (operational focus)",
        "",
        "5. **Test Sophia Access:**",
        "   @sophia-ai-assistant help",
        "   /sophia status",
        "",
    ]
    for instruction in instructions:
        print(instruction)
if __name__ == "__main__":
    save_configurations()
    print_setup_instructions()
