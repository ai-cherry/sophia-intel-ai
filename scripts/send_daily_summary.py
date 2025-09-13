#!/usr/bin/env python3
import asyncio
import sys
sys.path.append("/path/to/sophia-intel-ai")
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
