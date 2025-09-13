#!/usr/bin/env python3
from __future__ import annotations
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any

try:
    import requests
except Exception:
    print("ERROR: install dependencies: pip install requests pyjwt cryptography redis", file=sys.stderr)
    sys.exit(2)

def load_env_master(path: Path) -> None:
    if not path.exists():
        print(f"FAIL env: missing {path}")
        sys.exit(1)
    for line in path.read_text().splitlines():
        if not line.strip() or line.strip().startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        if not os.getenv(k):
            os.environ[k] = v

def ok(msg: str):
    print(f"OK  {msg}")

def fail(msg: str):
    print(f"FAIL {msg}")

def test_portkey() -> None:
    key = os.getenv('PORTKEY_API_KEY', '')
    if not key:
        fail('PORTKEY_API_KEY not set')
        return
    try:
        r = requests.get('https://api.portkey.ai/v1/models', headers={'x-portkey-api-key': key}, timeout=8)
        if r.status_code == 200:
            ok('Portkey models reachable')
        else:
            fail(f'Portkey models status {r.status_code}: {r.text[:120]}')
    except Exception as e:
        fail(f'Portkey error: {e}')

def test_mcp() -> None:
    ports = [
        ('memory', int(os.getenv('MCP_MEMORY_PORT', '8081'))),
        ('filesystem', int(os.getenv('MCP_FILESYSTEM_PORT', '8082'))),
        ('git', int(os.getenv('MCP_GIT_PORT', '8084'))),
        ('vector', int(os.getenv('MCP_VECTOR_PORT', '8085'))),
    ]
    for name, port in ports:
        try:
            r = requests.get(f'http://localhost:{port}/health', timeout=3)
            if r.status_code == 200:
                ok(f'MCP {name} :{port} healthy')
            else:
                fail(f'MCP {name} :{port} status {r.status_code}')
        except Exception as e:
            fail(f'MCP {name} :{port} error {e}')

def test_redis() -> None:
    url = os.getenv('REDIS_URL', 'redis://localhost:6379/1')
    try:
        import redis  # type: ignore
        r = redis.Redis.from_url(url)
        pong = r.ping()
        if pong:
            ok(f'Redis PING {url}')
        else:
            fail('Redis PING failed')
    except Exception as e:
        fail(f'Redis error {e}')

def test_vector_roundtrip() -> None:
    try:
        rq = {"path": "ENV_CHECK.txt", "content": "env check vector"}
        r = requests.post('http://localhost:'+os.getenv('MCP_VECTOR_PORT','8085')+'/index', json=rq, timeout=5)
        if r.status_code not in (200,201):
            fail(f'Vector index status {r.status_code}')
            return
        rs = requests.post('http://localhost:'+os.getenv('MCP_VECTOR_PORT','8085')+'/search', json={"query":"env check", "limit":1}, timeout=5)
        if rs.status_code==200:
            ok('Vector index/search OK')
        else:
            fail(f'Vector search status {rs.status_code}')
    except Exception as e:
        fail(f'Vector test error {e}')

def test_weaviate() -> None:
    url = os.getenv('WEAVIATE_URL', 'http://localhost:8080')
    try:
        r = requests.get(f'{url}/v1/.well-known/ready', timeout=5)
        if r.status_code == 200:
            ok('Weaviate ready')
        else:
            fail(f'Weaviate status {r.status_code}')
    except Exception as e:
        fail(f'Weaviate error {e}')

def test_github_app() -> None:
    app_id = os.getenv('GITHUB_APP_ID')
    pem = os.getenv('GITHUB_APP_PRIVATE_KEY_PATH')
    inst = os.getenv('GITHUB_APP_INSTALLATION_ID')
    if not app_id or not pem:
        fail('GitHub App: set GITHUB_APP_ID and GITHUB_APP_PRIVATE_KEY_PATH')
        return
    if not Path(pem).expanduser().exists():
        fail('GitHub App: private key path not found')
        return
    if not inst:
        fail('GitHub App: set GITHUB_APP_INSTALLATION_ID')
        return
    ok('GitHub App env present')

def main():
    repo = Path.cwd()
    env_path = repo / '.env.master'
    load_env_master(env_path)
    print('== Env master check ==')
    test_portkey()
    test_mcp()
    test_redis()
    test_weaviate()
    test_github_app()
    test_vector_roundtrip()
    print('== Done ==')

if __name__ == '__main__':
    main()
