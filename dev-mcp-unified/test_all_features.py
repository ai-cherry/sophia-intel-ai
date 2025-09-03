#!/usr/bin/env python3
"""
Comprehensive test script for MCP server with all enhanced features
"""

import asyncio
import httpx
import json
import sys
import time
from pathlib import Path

# Test configuration
SERVER_URL = "http://localhost:3333"
TIMEOUT = 10

def print_section(title):
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print('='*60)

def print_result(test_name, success, details=""):
    icon = "✅" if success else "❌"
    print(f"{icon} {test_name}: {'PASSED' if success else 'FAILED'}")
    if details:
        print(f"   {details}")

async def test_server_health():
    """Test basic server health"""
    print_section("Server Health Check")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SERVER_URL}/healthz", timeout=TIMEOUT)
            success = response.status_code == 200
            data = response.json() if success else {}
            
            print_result("Health endpoint", success, f"Status: {response.status_code}")
            if success:
                print(f"   Watch enabled: {data.get('watch', False)}")
                print(f"   Index path: {data.get('index', 'Not set')}")
            return success
    except Exception as e:
        print_result("Health endpoint", False, str(e))
        return False

async def test_llm_adapters():
    """Test all LLM adapters"""
    print_section("LLM Adapter Tests")
    
    models = ["claude", "openai", "deepseek", "qwen", "openrouter"]
    results = {}
    
    async with httpx.AsyncClient() as client:
        for model in models:
            try:
                response = await client.post(
                    f"{SERVER_URL}/query",
                    json={
                        "task": "general",
                        "question": f"Test query for {model}",
                        "llm": model
                    },
                    timeout=TIMEOUT
                )
                
                success = response.status_code == 200
                if success:
                    data = response.json()
                    has_response = bool(data.get("text"))
                    print_result(f"{model.upper()} adapter", has_response, 
                               f"Response length: {len(data.get('text', ''))} chars")
                    results[model] = has_response
                else:
                    print_result(f"{model.upper()} adapter", False, 
                               f"HTTP {response.status_code}")
                    results[model] = False
                    
            except Exception as e:
                print_result(f"{model.upper()} adapter", False, str(e)[:50])
                results[model] = False
    
    return results

async def test_streaming():
    """Test streaming endpoint"""
    print_section("Streaming Support")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SERVER_URL}/query/stream",
                json={
                    "task": "general",
                    "question": "Count from 1 to 5",
                    "llm": "claude"
                },
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                chunks_received = 0
                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        chunks_received += 1
                
                print_result("Streaming endpoint", chunks_received > 0, 
                           f"Received {chunks_received} chunks")
                return chunks_received > 0
            else:
                print_result("Streaming endpoint", False, 
                           f"HTTP {response.status_code}")
                return False
                
    except Exception as e:
        print_result("Streaming endpoint", False, str(e))
        return False

async def test_vector_search():
    """Test vector search functionality"""
    print_section("Vector Search")
    
    try:
        async with httpx.AsyncClient() as client:
            # First, try to search
            response = await client.post(
                f"{SERVER_URL}/tools/vec_search",
                json={
                    "query": "function to handle API requests",
                    "k": 5
                },
                timeout=TIMEOUT
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                has_results = len(data.get("results", [])) > 0
                print_result("Vector search", True, 
                           f"Found {len(data.get('results', []))} results")
            else:
                print_result("Vector search", False, 
                           f"HTTP {response.status_code}")
            return success
            
    except Exception as e:
        print_result("Vector search", False, str(e))
        return False

async def test_semantic_search():
    """Test semantic search"""
    print_section("Semantic Search")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SERVER_URL}/tools/search",
                json={"query": "async def"},
                timeout=TIMEOUT
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                results = data.get("results", [])
                print_result("Semantic search", True, 
                           f"Found {len(results)} matches")
            else:
                print_result("Semantic search", False, 
                           f"HTTP {response.status_code}")
            return success
            
    except Exception as e:
        print_result("Semantic search", False, str(e))
        return False

async def test_symbol_lookup():
    """Test symbol lookup"""
    print_section("Symbol Lookup")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SERVER_URL}/tools/symbols",
                json={"file": "dev_mcp_unified/core/mcp_server.py"},
                timeout=TIMEOUT
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                functions = data.get("functions", [])
                classes = data.get("classes", [])
                print_result("Symbol lookup", True, 
                           f"Found {len(functions)} functions, {len(classes)} classes")
            else:
                print_result("Symbol lookup", False, 
                           f"HTTP {response.status_code}")
            return success
            
    except Exception as e:
        print_result("Symbol lookup", False, str(e))
        return False

async def test_background_jobs():
    """Test background job system"""
    print_section("Background Jobs")
    
    try:
        async with httpx.AsyncClient() as client:
            # Submit a job
            response = await client.post(
                f"{SERVER_URL}/background/run",
                json={
                    "kind": "index",
                    "payload": {"path": "."}
                },
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                job_id = data.get("job_id")
                print_result("Job submission", bool(job_id), f"Job ID: {job_id[:8]}...")
                
                # Wait a bit
                await asyncio.sleep(2)
                
                # Check job status
                response = await client.get(
                    f"{SERVER_URL}/background/logs?job_id={job_id}",
                    timeout=TIMEOUT
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "unknown")
                    print_result("Job status check", True, f"Status: {status}")
                    return True
                else:
                    print_result("Job status check", False, 
                               f"HTTP {response.status_code}")
                    return False
            else:
                print_result("Job submission", False, 
                           f"HTTP {response.status_code}")
                return False
                
    except Exception as e:
        print_result("Background jobs", False, str(e))
        return False

async def test_openrouter_routing():
    """Test OpenRouter smart routing"""
    print_section("OpenRouter Smart Routing")
    
    tasks = [
        ("code_generation", "Write a Python function"),
        ("analysis", "Analyze this architecture"),
        ("testing", "Generate unit tests"),
        ("documentation", "Write documentation")
    ]
    
    try:
        async with httpx.AsyncClient() as client:
            for task_type, question in tasks:
                response = await client.post(
                    f"{SERVER_URL}/query",
                    json={
                        "task": task_type,
                        "question": question,
                        "llm": "openrouter"
                    },
                    timeout=TIMEOUT
                )
                
                success = response.status_code == 200
                if success:
                    data = response.json()
                    provider = data.get("provider", "unknown")
                    print_result(f"Route {task_type}", True, 
                               f"Routed to: {provider}")
                else:
                    print_result(f"Route {task_type}", False, 
                               f"HTTP {response.status_code}")
        return True
        
    except Exception as e:
        print_result("OpenRouter routing", False, str(e))
        return False

def test_ui_availability():
    """Check if UI files exist"""
    print_section("UI Availability")
    
    ui_files = [
        "dev-mcp-unified/ui/multi-chat.html",
        "dev-mcp-unified/ui/multi-chat-enhanced.html"
    ]
    
    for ui_file in ui_files:
        path = Path(ui_file)
        exists = path.exists()
        print_result(f"UI file {path.name}", exists, 
                   f"Size: {path.stat().st_size} bytes" if exists else "File not found")
    
    return all(Path(f).exists() for f in ui_files)

def check_monitoring_stats():
    """Check monitoring stats file"""
    print_section("Monitoring Stats")
    
    stats_file = Path("stats/mcp_stats.json")
    if stats_file.exists():
        with open(stats_file) as f:
            stats = json.load(f)
        
        print_result("Stats file exists", True, f"Last update: {stats.get('last_update', 'Unknown')}")
        
        if 'memory' in stats:
            mem = stats['memory']
            print(f"   Memory usage: {mem.get('percent', 0):.1f}%")
        
        if 'processes' in stats:
            procs = stats['processes']
            print(f"   Monitored processes: {procs.get('total_monitored', 0)}")
        
        return True
    else:
        print_result("Stats file exists", False, "Run monitoring service first")
        return False

async def main():
    print("\n" + "="*60)
    print("🚀 MCP Server Comprehensive Test Suite")
    print("="*60)
    print(f"Server URL: {SERVER_URL}")
    print(f"Testing all enhanced features...")
    
    # Check if server is running
    server_healthy = await test_server_health()
    if not server_healthy:
        print("\n⚠️  Server is not running! Start it with:")
        print("   cd ~/sophia-intel-ai")
        print("   ./dev-mcp-unified/run_local.sh")
        return
    
    # Run all tests
    test_results = {
        "Health": server_healthy,
        "LLM Adapters": await test_llm_adapters(),
        "Streaming": await test_streaming(),
        "Vector Search": await test_vector_search(),
        "Semantic Search": await test_semantic_search(),
        "Symbol Lookup": await test_symbol_lookup(),
        "Background Jobs": await test_background_jobs(),
        "OpenRouter": await test_openrouter_routing(),
        "UI Files": test_ui_availability(),
        "Monitoring": check_monitoring_stats()
    }
    
    # Summary
    print_section("Test Summary")
    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your MCP server is fully operational.")
        print("\n📝 Next steps:")
        print("  1. Open the enhanced UI: open dev-mcp-unified/ui/multi-chat-enhanced.html")
        print("  2. Start monitoring: python3 dev_mcp_unified/monitoring/monitor.py")
        print("  3. Use the CLI: ./dev-mcp-unified/mcp query --llm claude 'your question'")
    else:
        print("\n⚠️  Some tests failed. Check the configuration and API keys.")
        print("  Ensure all API keys are set in dev-mcp-unified/.env.local")

if __name__ == "__main__":
    asyncio.run(main())