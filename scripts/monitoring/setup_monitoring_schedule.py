#!/usr/bin/env python3
"""
Setup Automated Business Intelligence Monitoring

Creates scheduled tasks for Pay Ready business intelligence monitoring
with Sophia AI Slack integration.
"""

import os


def create_monitoring_cron_jobs() -> str:
    """Generate cron jobs for automated monitoring"""

    cron_jobs = """# Sophia AI Business Intelligence Monitoring
# Add these to your crontab: crontab -e

# Critical payments monitoring - Every 15 minutes during business hours
*/15 8-18 * * 1-5 cd /path/to/sophia-intel-ai && python3 scripts/run_bi_check.py --priority=critical

# High priority monitoring - Every hour
0 * * * * cd /path/to/sophia-intel-ai && python3 scripts/run_bi_check.py --priority=high

# Medium priority monitoring - Every 4 hours
0 */4 * * * cd /path/to/sophia-intel-ai && python3 scripts/run_bi_check.py --priority=medium

# Daily summary - 9 AM Eastern, weekdays
0 9 * * 1-5 cd /path/to/sophia-intel-ai && python3 scripts/send_daily_summary.py

# Weekly report - Friday 5 PM Eastern
0 17 * * 5 cd /path/to/sophia-intel-ai && python3 scripts/send_weekly_report.py

# Health check - Every 5 minutes
*/5 * * * * cd /path/to/sophia-intel-ai && python3 scripts/health_check.py
"""

    return cron_jobs


def create_monitoring_scripts():
    """Create the actual monitoring scripts"""

    # Business Intelligence Check Script
    bi_check_script = """#!/usr/bin/env python3
import sys
import asyncio
import argparse
sys.path.append('/path/to/sophia-intel-ai')

from app.integrations.slack_intelligence import get_sophia_slack_intelligence

async def run_bi_check(priority_filter=None):
    try:
        sophia = await get_sophia_slack_intelligence()
        alerts = await sophia.check_business_intelligence()

        if priority_filter:
            alerts = [a for a in alerts if a.priority == priority_filter]

        if alerts:
            results = await sophia.send_slack_alerts(alerts)
            print(f"Sent {results.get('sent', 0)} alerts")

    except Exception as e:
        print(f"BI check failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--priority', choices=['critical', 'high', 'medium', 'low'])
    args = parser.parse_args()

    asyncio.run(run_bi_check(args.priority))
"""

    # Daily Summary Script
    daily_summary_script = """#!/usr/bin/env python3
import sys
import asyncio
sys.path.append('/path/to/sophia-intel-ai')

from app.integrations.slack_intelligence import get_sophia_slack_intelligence

async def send_daily_summary():
    try:
        sophia = await get_sophia_slack_intelligence()
        summary = await sophia.create_daily_business_summary()
        results = await sophia.send_slack_alerts([summary])
        print(f"Daily summary sent: {results}")

    except Exception as e:
        print(f"Daily summary failed: {e}")

if __name__ == "__main__":
    asyncio.run(send_daily_summary())
"""

    # Health Check Script
    health_check_script = """#!/usr/bin/env python3
import sys
import requests
import json
sys.path.append('/path/to/sophia-intel-ai')

def health_check():
    try:
        # Check API health
        response = requests.get(f"http://localhost:{os.getenv('AGENT_API_PORT','8003')}/api/slack/health", timeout=10)
        health_data = response.json()

        if not health_data.get('integration_enabled'):
            print("WARNING: Slack integration disabled")

        # Check Looker connection
        looker_response = requests.get(f"http://localhost:{os.getenv('AGENT_API_PORT','8003')}/api/business/looker/health", timeout=10)
        if looker_response.status_code != 200:
            print("WARNING: Looker connection issues")

        print("✅ Health check passed")

    except Exception as e:
        print(f"❌ Health check failed: {e}")

if __name__ == "__main__":
    health_check()
"""

    return {
        "run_bi_check.py": bi_check_script,
        "send_daily_summary.py": daily_summary_script,
        "health_check.py": health_check_script,
    }


def create_systemd_service() -> str:
    """Create systemd service for continuous monitoring"""

    service_config = """[Unit]
Description=Sophia AI Business Intelligence Monitor
After=network.target

[Service]
Type=simple
User=sophia
WorkingDirectory=/path/to/sophia-intel-ai
ExecStart=/usr/bin/python3 -m app.api.unified_server
Restart=always
RestartSec=10
Environment=PYTHONPATH=/path/to/sophia-intel-ai

[Install]
WantedBy=multi-user.target
"""

    return service_config


def create_docker_compose() -> str:
    """Create Docker Compose for production deployment"""

    docker_compose = """version: '3.8'

services:
  sophia-ai:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
      - SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
      - LOOKER_CLIENT_ID=${LOOKER_CLIENT_ID}
      - LOOKER_CLIENT_SECRET=${LOOKER_CLIENT_SECRET}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:${AGENT_API_PORT:-8003}/api/slack/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - sophia-ai
    restart: unless-stopped
"""

    return docker_compose


def save_all_configs():
    """Save all configuration files"""

    # Create scripts directory
    os.makedirs("scripts", exist_ok=True)

    # Save cron jobs
    with open("scripts/monitoring_crontab.txt", "w") as f:
        f.write(create_monitoring_cron_jobs())

    # Save monitoring scripts
    scripts = create_monitoring_scripts()
    for filename, content in scripts.items():
        with open(f"scripts/{filename}", "w") as f:
            f.write(content)
        os.chmod(f"scripts/{filename}", 0o755)  # Make executable

    # Save systemd service
    with open("scripts/sophia-ai.service", "w") as f:
        f.write(create_systemd_service())

    # Save Docker Compose
    with open("docker-compose.yml", "w") as f:
        f.write(create_docker_compose())

    print("✅ All monitoring configurations created:")
    print("   📅 scripts/monitoring_crontab.txt - Cron job schedules")
    print("   🐍 scripts/run_bi_check.py - Business intelligence checker")
    print("   📊 scripts/send_daily_summary.py - Daily report sender")
    print("   🏥 scripts/health_check.py - System health monitor")
    print("   ⚙️  scripts/sophia-ai.service - Systemd service")
    print("   🐳 docker-compose.yml - Docker deployment")


def print_deployment_instructions():
    """Print final deployment instructions"""

    print("\n🚀 PRODUCTION DEPLOYMENT INSTRUCTIONS")
    print("=" * 50)

    steps = [
        "**1. Install Monitoring Scripts:**",
        "   sudo cp scripts/monitoring_crontab.txt /etc/cron.d/sophia-ai",
        "   sudo chmod 644 /etc/cron.d/sophia-ai",
        "",
        "**2. Setup Systemd Service (Optional):**",
        "   sudo cp scripts/sophia-ai.service /etc/systemd/system/",
        "   sudo systemctl enable sophia-ai",
        "   sudo systemctl start sophia-ai",
        "",
        "**3. Docker Deployment (Recommended):**",
        "   docker-compose up -d",
        "   docker-compose logs -f sophia-ai",
        "",
        "**4. Test Deployment:**",
        "   curl http://localhost:${AGENT_API_PORT:-8003}/api/slack/health",
        "   python3 scripts/run_bi_check.py --priority=high",
        "",
        "**5. Configure Slack Webhook:**",
        "   Update Slack app webhook URL to your production domain",
        "   Test with: /sophia status",
        "",
        "**6. Monitor Logs:**",
        "   tail -f logs/sophia-ai.log",
        "   docker-compose logs -f (if using Docker)",
        "",
    ]

    for step in steps:
        print(step)

    print("🎯 **Your Pay Ready Slack workspace will now have:**")
    print("   • Real-time monitoring of top 3 business reports")
    print("   • Automated alerts for payment/batch/balance issues")
    print("   • Daily business intelligence summaries")
    print("   • Interactive /sophia commands for instant insights")


if __name__ == "__main__":
    save_all_configs()
    print_deployment_instructions()
