#!/usr/bin/env python3
"""
Fetch 24h activity across Asana, Linear, and Slack to infer the top project getting attention.
Outputs a simple JSON summary with per-system counts and a combined score.
"""
import asyncio
import os
import json
from datetime import datetime, timedelta, timezone

import aiohttp


def now_utc():
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


async def fetch_asana_activity(session: aiohttp.ClientSession) -> dict:
    token = os.getenv("ASANA_API_TOKEN")
    if not token:
        return {"enabled": False, "error": "missing token"}
    headers = {"Authorization": f"Bearer {token}"}
    base = "https://app.asana.com/api/1.0"
    since = now_utc() - timedelta(hours=24)
    # Discover first workspace
    try:
        async with session.get(f"{base}/workspaces", headers=headers, timeout=30) as wr:
            wdata = await wr.json()
        workspaces = wdata.get("data", [])
        if not workspaces:
            return {"enabled": True, "per_project": {}}
        ws_gid = workspaces[0].get("gid")
    except Exception as e:
        return {"enabled": True, "error": f"workspace: {e}", "per_project": {}}
    # Search tasks modified after across workspace; group by project
    # https://developers.asana.com/reference/searchtasksforworkspace
    params = {
        "modified_at.after": iso(since),
        "opt_fields": "projects.name",
        "limit": "100"
    }
    activity: dict = {}
    next_page = None
    pages = 0
    try:
        while pages < 5:  # cap 5 pages (500 tasks)
            url = f"{base}/workspaces/{ws_gid}/tasks/search"
            if next_page:
                url = next_page
            async with session.get(url, headers=headers, params=None if next_page else params, timeout=45) as sr:
                sdata = await sr.json()
            for t in sdata.get("data", []):
                projects = t.get("projects") or []
                if not projects:
                    pname = "(no project)"
                    activity[pname] = activity.get(pname, 0) + 1
                else:
                    for pr in projects:
                        pname = pr.get("name") or "(no project)"
                        activity[pname] = activity.get(pname, 0) + 1
            next_page = (sdata.get("next_page") or {}).get("uri")
            pages += 1
            if not next_page:
                break
    except Exception:
        pass
    return {"enabled": True, "per_project": activity}


async def fetch_linear_activity(session: aiohttp.ClientSession) -> dict:
    token = os.getenv("LINEAR_API_KEY") or os.getenv("LINEAR_API_TOKEN")
    if not token:
        return {"enabled": False, "error": "missing token"}
    url = "https://api.linear.app/graphql"
    since = now_utc() - timedelta(hours=24)
    cutoff = (now_utc() - timedelta(hours=24)).isoformat().replace("+00:00", "Z")
    query = (
        "query($first:Int,$cutoff:DateTime!){ issues(first:$first, filter: {updatedAt: {gt: $cutoff}}) "
        "{ nodes { updatedAt project { name } } } }"
    )
    payload = {"query": query, "variables": {"first": 300, "cutoff": cutoff}}
    headers = {"Content-Type": "application/json", "Authorization": token}
    try:
        async with session.post(url, headers=headers, json=payload, timeout=45) as r:
            data = await r.json()
    except Exception as e:
        return {"enabled": True, "error": str(e)}
    nodes = (data or {}).get("data", {}).get("issues", {}).get("nodes", [])
    activity = {}
    for n in nodes:
        pname = (n.get("project") or {}).get("name") or "(no project)"
        activity[pname] = activity.get(pname, 0) + 1
    return {"enabled": True, "per_project": activity}


async def fetch_slack_activity(session: aiohttp.ClientSession) -> dict:
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        return {"enabled": False, "error": "missing token"}
    base = "https://slack.com/api"
    headers = {"Authorization": f"Bearer {token}"}
    # List channels
    async with session.get(f"{base}/conversations.list?exclude_archived=true&types=public_channel,private_channel", headers=headers, timeout=30) as r:
        chans = await r.json()
    channels = chans.get("channels", [])
    since_ts = (now_utc() - timedelta(hours=24)).timestamp()
    activity = {}
    # Sample up to 50 channels to improve coverage
    for ch in channels[:50]:
        cid = ch.get("id")
        cname = ch.get("name")
        params = {"channel": cid, "oldest": str(since_ts), "limit": 200}
        try:
            async with session.get(f"{base}/conversations.history", headers=headers, params=params, timeout=30) as hr:
                hist = await hr.json()
            msg_count = len(hist.get("messages", []))
        except Exception:
            msg_count = 0
        activity[cname] = msg_count
    return {"enabled": True, "per_channel": activity}


def combine(asana: dict, linear: dict, slack: dict) -> dict:
    # Basic combine: score = asana_tasks + linear_issues + (slack_msgs mapped by channel matching project name)
    scores = {}
    asana_map = asana.get("per_project", {}) if asana.get("enabled") else {}
    linear_map = linear.get("per_project", {}) if linear.get("enabled") else {}
    slack_map = slack.get("per_channel", {}) if slack.get("enabled") else {}

    # Collect all project names seen in Asana/Linear
    names = set(asana_map.keys()) | set(linear_map.keys())
    for name in names:
        score = asana_map.get(name, 0) + linear_map.get(name, 0)
        # Heuristic: if a channel name matches project name, add channel message count
        if name in slack_map:
            score += slack_map.get(name, 0)
        scores[name] = score

    # If no names, fallback to Slack top channels
    if not scores and slack_map:
        top_ch = max(slack_map.items(), key=lambda x: x[1])
        return {
            "top": {"name": top_ch[0], "score": top_ch[1], "source": "slack_channel"},
            "details": {"asana": asana, "linear": linear, "slack": slack},
        }

    if not scores:
        return {"top": None, "details": {"asana": asana, "linear": linear, "slack": slack}}

    top = max(scores.items(), key=lambda x: x[1])
    return {
        "top": {"name": top[0], "score": top[1], "source": "combined"},
        "details": {"asana": asana, "linear": linear, "slack": slack},
    }


async def main():
    async with aiohttp.ClientSession() as session:
        asana_task = asyncio.create_task(fetch_asana_activity(session))
        linear_task = asyncio.create_task(fetch_linear_activity(session))
        slack_task = asyncio.create_task(fetch_slack_activity(session))
        asana, linear, slack = await asyncio.gather(asana_task, linear_task, slack_task)
        result = combine(asana, linear, slack)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
