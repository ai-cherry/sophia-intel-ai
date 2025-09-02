#!/usr/bin/env python3
"""
Comprehensive test script for the unified agent system.
Tests all major components and integration points.
"""

import asyncio
import httpx
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8001"

async def test_health() -> bool:
    """Test health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/healthz")
        data = response.json()
        
        print("✅ Health Check:")
        print(f"  Status: {data['status']}")
        print(f"  Systems: {data['systems']}")
        
        return all(data['systems'].values())

async def test_teams() -> bool:
    """Test teams endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/teams")
        teams = response.json()
        
        print("\n✅ Teams Available:")
        for team in teams:
            print(f"  - {team['name']} ({team['id']})")
        
        return len(teams) == 4

async def test_memory() -> bool:
    """Test memory operations."""
    async with httpx.AsyncClient() as client:
        # Add memory
        add_response = await client.post(
            f"{BASE_URL}/memory/add",
            json={
                "topic": "Test Memory",
                "content": "This is a test memory entry",
                "source": "test_script",
                "tags": ["test"],
                "memory_type": "episodic"
            }
        )
        add_data = add_response.json()
        
        # Search memory
        search_response = await client.post(
            f"{BASE_URL}/memory/search",
            json={"query": "test", "top_k": 5}
        )
        search_data = search_response.json()
        
        print("\n✅ Memory System:")
        print(f"  Added: {add_data['status']}")
        print(f"  Found: {search_data['count']} entries")
        
        return add_data['status'] == 'added' and search_data['count'] > 0

async def test_streaming() -> bool:
    """Test streaming team execution."""
    print("\n✅ Testing Streaming Execution:")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream(
            'POST',
            f"{BASE_URL}/teams/run",
            json={
                "team_id": "coding-team",
                "message": "Test task",
                "pool": "balanced",
                "use_memory": True
            }
        ) as response:
            phases_seen = []
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        if 'phase' in data:
                            phase = data['phase']
                            if phase not in phases_seen:
                                phases_seen.append(phase)
                                print(f"  Phase: {phase}")
                    except json.JSONDecodeError:
                        continue
            
            expected_phases = ['planning', 'memory', 'setup', 'generation', 'critic', 'judge', 'gates']
            return all(phase in phases_seen for phase in expected_phases[:4])  # At least first 4 phases

async def test_stats() -> bool:
    """Test statistics endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/stats")
        stats = response.json()
        
        print("\n✅ System Statistics:")
        print(f"  Memory entries: {stats['memory']['total_entries']}")
        print(f"  Graph entities: {stats['graph']['total_entities']}")
        print(f"  Cache entries: {stats['embeddings']['cache']['total_cached']}")
        
        return 'memory' in stats and 'embeddings' in stats

async def main():
    """Run all tests."""
    print("🧪 UNIFIED SYSTEM TEST SUITE")
    print("=" * 40)
    
    tests = [
        ("Health Check", test_health),
        ("Teams Discovery", test_teams),
        ("Memory Operations", test_memory),
        ("Streaming Execution", test_streaming),
        ("Statistics", test_stats)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 40)
    print("📊 TEST RESULTS:")
    
    passed = 0
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Total: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("⚠️ Some tests failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)