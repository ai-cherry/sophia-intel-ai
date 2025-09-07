#!/usr/bin/env bash
set -euo pipefail

cd "/Users/lynnmusil/sophia-intel-ai"
if [ -f .env.artemis.local ]; then
  # shellcheck disable=SC1091
  source .env.artemis.local
fi

# Minimal cleanup implemented via stdio MCP client
python3 - <<'PY'
import datetime as dt
import json
from pathlib import Path
from app.mcp.clients.stdio_client import StdioMCPClient

client = StdioMCPClient(Path.cwd())
now = dt.datetime.utcnow()

def iso(s: str) -> dt.datetime:
    try:
        return dt.datetime.fromisoformat(s.replace('Z',''))
    except Exception:
        return dt.datetime.min

# Expired: has expires: tag in the past
res = client.memory_search('collab AND expires:', limit=500)
items = (res.get('results') if isinstance(res, dict) else res) or []
expired = []
for it in items:
    for t in it.get('tags') or []:
        if t.startswith('expires:'):
            try:
                exp = iso(t.split(':',1)[1])
                if exp.replace(tzinfo=None) <= now:
                    expired.append(it)
                    break
            except Exception:
                pass
for it in expired:
    id_tag = next((t for t in (it.get('tags') or []) if t.startswith('id:')), None)
    collab_id = id_tag.split(':',1)[1] if id_tag else 'unknown'
    client.memory_add(
        topic=f'collab_archived:{collab_id}',
        content=f'Archived expired entry {it.get("topic")}',
        source='artemis-run',
        tags=['collab','archived', f'id:{collab_id}'],
        memory_type='episodic',
    )
print(json.dumps({'archived_expired': len(expired)}))

# Stale: any collab older than 7d without archived tag
cutoff = now - dt.timedelta(days=7)
res2 = client.memory_search('collab', limit=500)
items2 = (res2.get('results') if isinstance(res2, dict) else res2) or []
stale = [
    it for it in items2
    if iso(it.get('timestamp','1970-01-01')).replace(tzinfo=None) < cutoff
    and not any(t == 'archived' for t in (it.get('tags') or []))
]
for it in stale:
    id_tag = next((t for t in (it.get('tags') or []) if t.startswith('id:')), None)
    collab_id = id_tag.split(':',1)[1] if id_tag else 'unknown'
    client.memory_add(
        topic=f'collab_archived:{collab_id}',
        content=f'Archived stale entry {it.get("topic")}',
        source='artemis-run',
        tags=['collab','archived', f'id:{collab_id}'],
        memory_type='episodic',
    )
print(json.dumps({'archived_stale': len(stale)}))
PY

# Remove .mcp_backups older than 30 days
python3 - <<'PY'
import datetime as dt
import os
from pathlib import Path

root = Path('.mcp_backups')
removed = 0
if root.exists():
    cutoff = dt.datetime.now().timestamp() - (30*24*3600)
    for p in root.rglob('*'):
        try:
            if p.is_file() and p.stat().st_mtime < cutoff:
                p.unlink()
                removed += 1
        except Exception:
            pass
print(f"removed_backups={removed}")
PY

echo "Artemis daily cleanup completed."
exit 0
