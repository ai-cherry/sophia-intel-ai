#!/bin/bash
echo '🔧 MCP Server Quick Fix'
echo '====================='

# Kill existing server
pkill -f mcp_server.py 2>/dev/null
lsof -ti:3333 | xargs kill -9 2>/dev/null
sleep 1

# Install dependencies
pip install -q aiohttp aiohttp-cors python-dotenv

# Create directories
mkdir -p core ui

# Create minimal server
cat > core/mcp_server.py << 'PYEOF'
import os, json, asyncio, logging
from aiohttp import web, ClientSession
from dotenv import load_dotenv
import aiohttp_cors

load_dotenv('.env.local')
API_KEY = os.getenv('OPENROUTER_API_KEY', '')
logging.basicConfig(level=logging.INFO)

async def proxy(request):
    async with ClientSession() as session:
        data = await request.json()
        headers = {
            'Authorization': f"Bearer {API_KEY or request.headers.get('Authorization', '')[7:]}",
            'Content-Type': 'application/json'
        }
        async with session.post(
            'https://openrouter.ai/api/v1/chat/completions',
            json=data,
            headers=headers
        ) as resp:
            return web.json_response(await resp.json())

app = web.Application()
app.router.add_post('/proxy/openrouter', proxy)

cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
        allow_methods="*"
    )
})

for route in list(app.router.routes()):
    cors.add(route)

if __name__ == '__main__':
    print('Server starting on http://127.0.0.1:3333')
    web.run_app(app, host='127.0.0.1', port=3333)
PYEOF

# Start server
python3 core/mcp_server.py &
echo "Server started with PID: \$!"
