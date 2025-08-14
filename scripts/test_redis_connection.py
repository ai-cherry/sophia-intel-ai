#!/usr/bin/env python3
"""
Test Redis Cloud connection with actual credentials
"""
import redis
import os
import sys

def test_redis_connection():
    """Test Redis connection with the actual credentials"""
    print("🔍 Testing Redis Cloud Connection...")
    print("=" * 50)
    
    # Redis connection details
    redis_config = {
        'host': 'redis-15014.force172.us-east-1-1.ec2.redns.redis-cloud.com',
        'port': 15014,
        'password': 'pdM2P5F7oQ26JCCtBuRsrCBrSacqZmr',
        'username': 'default',
        'decode_responses': True,
        'socket_timeout': 5,
        'socket_connect_timeout': 5
    }
    
    try:
        # Create Redis connection
        print(f"📡 Connecting to Redis at {redis_config['host']}:{redis_config['port']}")
        r = redis.Redis(**redis_config)
        
        # Test connection with ping
        print("🏓 Testing connection with PING...")
        response = r.ping()
        if response:
            print("✅ Redis PING successful!")
        
        # Test basic operations
        print("🧪 Testing basic Redis operations...")
        
        # Set a test key
        test_key = "sophia_ai_test"
        test_value = "Hello from Sophia AI!"
        r.set(test_key, test_value, ex=60)  # Expire in 60 seconds
        print(f"✅ SET {test_key} = '{test_value}'")
        
        # Get the test key
        retrieved_value = r.get(test_key)
        print(f"✅ GET {test_key} = '{retrieved_value}'")
        
        # Test Redis info
        print("📊 Redis server info:")
        info = r.info()
        print(f"   Redis version: {info.get('redis_version', 'Unknown')}")
        print(f"   Used memory: {info.get('used_memory_human', 'Unknown')}")
        print(f"   Connected clients: {info.get('connected_clients', 'Unknown')}")
        
        # Clean up test key
        r.delete(test_key)
        print(f"🧹 Cleaned up test key: {test_key}")
        
        print("\n🎉 Redis connection test SUCCESSFUL!")
        return True
        
    except redis.ConnectionError as e:
        print(f"❌ Redis connection failed: {e}")
        return False
    except redis.AuthenticationError as e:
        print(f"❌ Redis authentication failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def generate_connection_strings():
    """Generate various Redis connection string formats"""
    print("\n📝 Redis Connection String Formats:")
    print("=" * 50)
    
    base_url = "redis://default:pdM2P5F7oQ26JCCtBuRsrCBrSacqZmr@redis-15014.force172.us-east-1-1.ec2.redns.redis-cloud.com:15014"
    
    formats = {
        "Standard Redis URL": base_url,
        "Python redis-py": base_url,
        "Node.js ioredis": base_url,
        "Environment Variable": f"REDIS_URL={base_url}",
        "Docker Compose": f"REDIS_URL={base_url}",
        "Kubernetes Secret": base_url
    }
    
    for name, url in formats.items():
        print(f"  {name}: {url}")

if __name__ == "__main__":
    success = test_redis_connection()
    generate_connection_strings()
    
    if success:
        print("\n✅ Redis is ready for Sophia AI integration!")
        sys.exit(0)
    else:
        print("\n❌ Redis connection failed - check credentials and network")
        sys.exit(1)

