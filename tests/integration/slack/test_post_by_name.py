import os
import pytest

pytestmark = pytest.mark.integration


def _token() -> str | None:
    return os.getenv("SLACK_BOT_TOKEN") or os.getenv("SLACK_BOT_USER_AUTH")


def _resolve_channel_id(client, name: str) -> str | None:
    # Try to find a public channel by name; fall back to private if permitted
    cursor = None
    for _ in range(10):  # paginate up to ~2k channels worst-case
        resp = client.conversations_list(limit=200, cursor=cursor)
        if not resp.get("ok"):
            return None
        for ch in resp.get("channels", []):
            if ch.get("name") == name.lstrip("#"):
                return ch.get("id")
        cursor = resp.get("response_metadata", {}).get("next_cursor") or None
        if not cursor:
            break
    return None


def test_post_message_by_name_or_id():
    token = _token()
    if not token:
        pytest.skip("SLACK_BOT_TOKEN missing")

    try:
        from slack_sdk import WebClient  # type: ignore
    except Exception:
        pytest.skip("slack_sdk not installed")

    client = WebClient(token=token)

    channel_id = os.getenv("SLACK_TEST_CHANNEL")
    channel_name = os.getenv("SLACK_TEST_CHANNEL_NAME")
    if not channel_id and not channel_name:
        pytest.skip("Provide SLACK_TEST_CHANNEL or SLACK_TEST_CHANNEL_NAME")

    if not channel_id and channel_name:
        channel_id = _resolve_channel_id(client, channel_name)
        if not channel_id:
            pytest.skip(f"Channel name not found: {channel_name}")

    text = "[integration] Slack post-by-name smoke"
    resp = client.chat_postMessage(channel=channel_id, text=text)
    assert resp.get("ok") is True
    assert "ts" in resp

