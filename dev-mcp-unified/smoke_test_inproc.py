import os
from fastapi.testclient import TestClient
from dev_mcp_unified.core.mcp_server import app

os.environ.setdefault("MCP_WATCH", "true")

client = TestClient(app)

def run():
    r = client.get("/healthz")
    print("health:", r.status_code, r.json())
    for llm in ["claude","openai","qwen","deepseek","openrouter"]:
        r = client.post("/query", json={"task":"general","question":f"hello {llm}","llm":llm})
        print(llm, ":", r.status_code, r.json())

if __name__ == "__main__":
    run()

