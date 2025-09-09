#!/usr/bin/env python3
import sys

import requests

sys.path.append("/path/to/sophia-intel-ai")


def health_check():
    try:
        # Check API health
        response = requests.get(f"http://localhost:{os.getenv('AGENT_API_PORT','8003')}/api/slack/health", timeout=10)
        health_data = response.json()

        if not health_data.get("integration_enabled"):
            print("WARNING: Slack integration disabled")

        # Check Looker connection
        looker_response = requests.get(
            f"http://localhost:{os.getenv('AGENT_API_PORT','8003')}/api/business/looker/health", timeout=10
        )
        if looker_response.status_code != 200:
            print("WARNING: Looker connection issues")

        print("✅ Health check passed")

    except Exception as e:
        print(f"❌ Health check failed: {e}")


if __name__ == "__main__":
    health_check()
