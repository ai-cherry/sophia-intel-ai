#!/usr/bin/env python3
import argparse
import asyncio
import sys
sys.path.append("/path/to/sophia-intel-ai")
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
    parser.add_argument("--priority", choices=["critical", "high", "medium", "low"])
    args = parser.parse_args()
    asyncio.run(run_bi_check(args.priority))
