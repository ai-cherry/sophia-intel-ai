#!/usr/bin/env python3
"""
Slack live smoke test (Web API)

Reads tokens from environment or .env.local (if present):
  - SLACK_BOT_TOKEN (required)
  - SLACK_TEST_CHANNEL (optional channel ID; if set, posts a test message)

Usage:
  python tools/slack/smoke.py
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Optional

def main() -> int:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        load_dotenv = None  # optional

    if load_dotenv:
        env_path = Path.cwd() / ".env.local"
        if env_path.exists():
            load_dotenv(str(env_path))

    bot = os.getenv("SLACK_BOT_TOKEN")
    if not bot:
        print("SLACK_BOT_TOKEN not set. Export it or put into .env.local.")
        return 2

    try:
        from slack_sdk import WebClient  # type: ignore
    except Exception:
        print("Install slack_sdk: pip install slack_sdk python-dotenv")
        return 2

    client = WebClient(token=bot)

    # 1) auth.test
    auth = client.auth_test()
    if not auth.get("ok"):
        print(f"auth.test failed: {auth}")
        return 1
    print(f"auth.test ok for team={auth.get('team')} user_id={auth.get('user_id')}")

    # 2) conversations.list (public channels)
    chans = client.conversations_list(limit=10)
    names = [c.get("name") for c in chans.get("channels", [])]
    print(f"channels: {names}")

    # 3) optional post
    chan = os.getenv("SLACK_TEST_CHANNEL")  # channel ID like C0123456
    if chan:
        msg = "Sophia Slack smoke test: hello from tools/slack/smoke.py"
        resp = client.chat_postMessage(channel=chan, text=msg)
        if not resp.get("ok"):
            print(f"chat.postMessage failed: {resp}")
            return 1
        ts = resp.get("ts")
        print(f"posted message ts={ts} in {chan}")
    else:
        print("Set SLACK_TEST_CHANNEL to post a test message (channel ID)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

