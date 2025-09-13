#!/usr/bin/env python3
"""
List the most active Slack channels by message count in the last 24 hours.
Requires SLACK_BOT_TOKEN with scopes: conversations.list, conversations.history.
Writes results to slack_top_channels.json and prints a ranked summary.
"""
import asyncio
import json
import os
import time
from datetime import datetime, timedelta, timezone

import aiohttp


def now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


async def slack_api_get(session: aiohttp.ClientSession, endpoint: str, params: dict) -> dict:
    base = "https://slack.com/api"
    async with session.get(f"{base}/{endpoint}", params=params, timeout=30) as r:
        return await r.json()


async def list_all_channels(session: aiohttp.ClientSession, limit: int = 200) -> list:
    channels = []
    cursor = None
    tries = 0
    while True:
        params = {
            "exclude_archived": "true",
            "types": "public_channel,private_channel",
            "limit": str(limit),
        }
        if cursor:
            params["cursor"] = cursor
        data = await slack_api_get(session, "conversations.list", params)
        if not data.get("ok"):
            # Stop on error
            break
        channels.extend(data.get("channels", []))
        cursor = (data.get("response_metadata") or {}).get("next_cursor")
        if not cursor:
            break
        tries += 1
        if tries > 20:  # safety cap
            break
    return channels


async def channel_message_count(session: aiohttp.ClientSession, channel_id: str, oldest: float) -> int:
    count = 0
    cursor = None
    tries = 0
    while True:
        params = {
            "channel": channel_id,
            "oldest": str(oldest),
            "limit": "200",
        }
        if cursor:
            params["cursor"] = cursor
        data = await slack_api_get(session, "conversations.history", params)
        if not data.get("ok"):
            # Likely not a member or missing scope
            break
        msgs = data.get("messages", [])
        count += len(msgs)
        cursor = (data.get("response_metadata") or {}).get("next_cursor")
        if not cursor:
            break
        tries += 1
        if tries > 50:
            break
    return count


async def main():
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        print("SLACK_BOT_TOKEN not set")
        return 1
    headers = {"Authorization": f"Bearer {token}"}
    oldest = now_ts() - 24 * 3600
    async with aiohttp.ClientSession(headers=headers) as session:
        chans = await list_all_channels(session)
        # Compute message counts concurrently but with a cap to avoid rate limits
        results = []
        sem = asyncio.Semaphore(8)

        async def worker(ch):
            async with sem:
                cid = ch.get("id")
                name = ch.get("name")
                cnt = await channel_message_count(session, cid, oldest)
                return {"id": cid, "name": name, "count_24h": cnt, "is_member": ch.get("is_member", False), "is_private": ch.get("is_private", False)}

        tasks = [asyncio.create_task(worker(c)) for c in chans]
        for t in asyncio.as_completed(tasks):
            res = await t
            results.append(res)

        # Rank
        results.sort(key=lambda x: x["count_24h"], reverse=True)
        # Save
        with open("slack_top_channels.json", "w") as f:
            json.dump({"generated_at": datetime.utcnow().isoformat()+"Z", "channels": results}, f, indent=2)
        # Print summary top 20
        top = results[:20]
        for i, ch in enumerate(top, 1):
            print(f"{i:2d}. #{ch['name']}  | msgs(24h)={ch['count_24h']}  | private={ch['is_private']}  member={ch['is_member']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

