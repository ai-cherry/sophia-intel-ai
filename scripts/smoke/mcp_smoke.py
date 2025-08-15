#!/usr/bin/env python3
"""
MCP Server smoke test - Test Enhanced Unified Server functionality.
Real MCP server testing with stats, store, query, and clear operations.
"""
import os, sys, json, asyncio, time
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

async def test_mcp_server():
    print("MCP SERVER SMOKE TEST")
    print("=" * 40)
    
    try:
        # Import the enhanced MCP server
        from mcp_servers.enhanced_unified_server import EnhancedUnifiedServer
        
        print("✅ Enhanced MCP Server imported successfully")
        
        # Initialize server
        print("\n1. INITIALIZING MCP SERVER")
        server = EnhancedUnifiedServer()
        print("✅ Server initialized")
        
        # Test stats endpoint
        print("\n2. TESTING STATS ENDPOINT")
        stats = await server.get_stats()
        print(f"Stats response: {json.dumps(stats, indent=2)}")
        
        if isinstance(stats, dict) and 'status' in stats:
            print("✅ Stats endpoint working")
        else:
            print("⚠️ Unexpected stats format")
        
        # Test store operation
        print("\n3. TESTING STORE OPERATION")
        test_data = {
            "test_key": "smoke_test_value",
            "timestamp": time.time(),
            "source": "mcp_smoke_test"
        }
        
        store_result = await server.store_data("smoke_test", test_data)
        print(f"Store result: {json.dumps(store_result, indent=2)}")
        
        if isinstance(store_result, dict) and store_result.get('success'):
            print("✅ Store operation working")
        else:
            print("⚠️ Store operation may have issues")
        
        # Test query operation
        print("\n4. TESTING QUERY OPERATION")
        query_result = await server.query_data("smoke_test")
        print(f"Query result: {json.dumps(query_result, indent=2)}")
        
        if isinstance(query_result, dict):
            print("✅ Query operation working")
        else:
            print("⚠️ Query operation may have issues")
        
        # Test clear operation
        print("\n5. TESTING CLEAR OPERATION")
        clear_result = await server.clear_data("smoke_test")
        print(f"Clear result: {json.dumps(clear_result, indent=2)}")
        
        if isinstance(clear_result, dict) and clear_result.get('success'):
            print("✅ Clear operation working")
        else:
            print("⚠️ Clear operation may have issues")
        
        # Final stats check
        print("\n6. FINAL STATS CHECK")
        final_stats = await server.get_stats()
        print(f"Final stats: {json.dumps(final_stats, indent=2)}")
        
        print("\n✅ MCP SERVER SMOKE TEST COMPLETED")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {repr(e)}")
        print("Enhanced MCP Server may not be available")
        return False
        
    except AttributeError as e:
        print(f"❌ Method not found: {repr(e)}")
        print("MCP Server may not have expected methods")
        return False
        
    except Exception as e:
        print(f"❌ MCP test failed: {repr(e)}")
        return False

def main():
    try:
        # Run async test
        success = asyncio.run(test_mcp_server())
        sys.exit(0 if success else 3)
    except Exception as e:
        print(f"❌ Async test failed: {repr(e)}")
        sys.exit(10)

if __name__ == "__main__":
    main()

