#!/usr/bin/env bash
set -euo pipefail

# Real webhook signature checks against a running deployment (no mocks).
#
# Usage:
#   BASE_URL="https://api.example.com" \
#   GONG_WEBHOOK_SECRET="..." \
#   SLACK_SIGNING_SECRET="..." \
#   ./scripts/verify_webhooks.sh
#
# Notes:
# - Asana handshake requires setting X-Hook-Secret header and no body; this script
#   verifies echo behavior only. Full Asana event delivery must be tested via Asana.
# - Gong and Slack tests compute valid signatures over a sample payload and expect 2xx.

if [ -z "${BASE_URL:-}" ]; then
  echo "Set BASE_URL to your API origin, e.g. https://api.yourdomain.com" >&2
  exit 1
fi

now_ts() { date +%s; }
hex_hmac_sha256() { # key, data -> hex
  key="$1"; shift
  data="$1"; shift
  printf "%s" "$data" | openssl dgst -sha256 -mac HMAC -macopt "key:${key}" | awk '{print $2}'
}

base64_hmac_sha256() { # key, data -> base64
  key="$1"; shift
  data="$1"; shift
  printf "%s" "$data" | openssl dgst -sha256 -mac HMAC -macopt "key:${key}" -binary | base64
}

section() { echo; echo "== $* =="; }

section "Asana webhook handshake (echo X-Hook-Secret)"
HOOK_SECRET="test-handshake-$(now_ts)"
code=$(curl -s -o /tmp/asana.out -w "%{http_code}" -X POST \
  -H "X-Hook-Secret: ${HOOK_SECRET}" \
  "${BASE_URL}/api/asana/webhooks")
if [ "$code" != "200" ]; then echo "Asana handshake failed: HTTP $code"; cat /tmp/asana.out; exit 1; fi
if ! (curl -s -I -X POST -H "X-Hook-Secret: ${HOOK_SECRET}" "${BASE_URL}/api/asana/webhooks" | grep -q "X-Hook-Secret: ${HOOK_SECRET}"); then
  echo "Asana handshake did not echo X-Hook-Secret header"; exit 1
fi
echo "Asana handshake OK"

section "Gong webhook signature"
if [ -z "${GONG_WEBHOOK_SECRET:-}" ]; then
  echo "Set GONG_WEBHOOK_SECRET to your configured Gong secret" >&2
  exit 1
fi
GONG_PAYLOAD='{"event_type":"transcript.ready","event_id":"local-test-1","timestamp":"2024-10-10T10:10:10Z","call_id":"abc123","data":{}}'
GONG_SIG_HEX=$(hex_hmac_sha256 "$GONG_WEBHOOK_SECRET" "$GONG_PAYLOAD")
code=$(curl -s -o /tmp/gong.out -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -H "X-Gong-Signature: $GONG_SIG_HEX" \
  --data "$GONG_PAYLOAD" \
  "${BASE_URL}/webhooks/gong/")
if [ "$code" -ge 300 ]; then echo "Gong signature test failed: HTTP $code"; cat /tmp/gong.out; exit 1; fi
echo "Gong signature OK"

section "Slack signature guard"
if [ -z "${SLACK_SIGNING_SECRET:-}" ]; then
  echo "Set SLACK_SIGNING_SECRET to your Slack app signing secret" >&2
  exit 1
fi
SLACK_TS=$(now_ts)
SLACK_BODY='token=ignored&team_id=T0001&team_domain=example&channel_id=C2147483705&channel_name=test&user_id=U2147483697&user_name=Steve&command=%2Fsophia&text=help&response_url=https%3A%2F%2Fhooks.slack.com%2Fcommands%2F1234'
BASESTR="v0:${SLACK_TS}:${SLACK_BODY}"
SLACK_SIG_HEX=$(hex_hmac_sha256 "$SLACK_SIGNING_SECRET" "$BASESTR")
code=$(curl -s -o /tmp/slack.out -w "%{http_code}" -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "X-Slack-Request-Timestamp: ${SLACK_TS}" \
  -H "X-Slack-Signature: v0=${SLACK_SIG_HEX}" \
  --data "$SLACK_BODY" \
  "${BASE_URL}/api/slack/commands")
if [ "$code" -ge 300 ]; then echo "Slack signature test failed: HTTP $code"; cat /tmp/slack.out; exit 1; fi
echo "Slack signature OK"

echo
echo "All webhook checks passed against: ${BASE_URL}"
