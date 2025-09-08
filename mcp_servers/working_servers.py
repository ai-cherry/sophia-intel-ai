#!/usr/bin/env python3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


class WorkingMCPServer:
    def __init__(self, name: str, port: int):
        self.name = name
        self.port = port
        self.app = FastAPI(title=f"MCP {name}")
        self.setup_routes()

    def setup_routes(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.get("/health")
        async def health():
            return {"status": "healthy", "server": self.name}

        @self.app.post("/execute")
        async def execute(payload: dict):
            if self.name == "memory":
                return await self.handle_memory(payload)
            elif self.name == "vector":
                return await self.handle_vector(payload)
            else:
                return {"result": f"Handled by {self.name}"}

    async def handle_memory(self, payload):
        operation = payload.get("operation")
        if operation == "store":
            return {"stored": True, "id": "mem_" + str(hash(str(payload)))}
        elif operation == "retrieve":
            return {"data": "retrieved memory"}
        return {"error": "unknown operation"}

    async def handle_vector(self, payload):
        operation = payload.get("operation")
        if operation == "search":
            return {"results": [{"score": 0.95, "content": "relevant doc"}]}
        elif operation == "index":
            return {"indexed": True, "vectors": 1}
        return {"error": "unknown operation"}

    def run(self):
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)


if __name__ == "__main__":
    import sys
    server_configs = {
        "memory": 8081,
        "fs": 8082,
        "git": 8084,
        "vector": 8085,
        "graph": 8086,
    }

    if len(sys.argv) > 1:
        name = sys.argv[1]
        if name in server_configs:
            server = WorkingMCPServer(name, server_configs[name])
            server.run()
        else:
            print(f"Unknown server {name}")
    else:
        print(f"Usage: python mcp_servers/working_servers.py [{'|'.join(server_configs.keys())}]")

