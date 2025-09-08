#!/usr/bin/env python3
import os
from pathlib import Path

validator_path = Path('scripts/validate_mcp_servers.py')
if validator_path.exists():
    content = validator_path.read_text()
    # Crush path dupes: mcp_servers/mcp_servers/name -> mcp_servers/name
    content = content.replace("server['path'] / 'mcp_servers' / server['name']", "server['path'] / server['name']")
    content = content.replace("Path('mcp_servers') / server['name']", "server['path'] / server['name']")
    validator_path.write_text(content)
    print("✅ Validator purged of bugs")
