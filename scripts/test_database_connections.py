#!/usr/bin/env python3
"""
Test script for Redis and PostgreSQL database connections
Run this after configuring the actual database URLs
"""
import os
import sys

def test_redis_connection():
    """Test Redis connection"""
    redis_url = os.environ.get('REDIS_URL')
    if not redis_url or 'REDIS_PASSWORD' in redis_url:
        print("❌ REDIS_URL not configured or still contains template values")
        return False
    
    try:
        import redis
        r = redis.from_url(redis_url)
        r.ping()
        
        # Test basic operations
        r.set("sophia_test", "connection_successful")
        value = r.get("sophia_test")
        r.delete("sophia_test")
        
        if value == b"connection_successful":
            print("✅ Redis connection successful")
            return True
        else:
            print("❌ Redis test operation failed")
            return False
            
    except ImportError:
        print("❌ Redis package not installed: pip install redis")
        return False
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")
        return False

def test_postgresql_connection():
    """Test PostgreSQL connection"""
    postgres_url = os.environ.get('DATABASE_URL')
    if not postgres_url or 'username:password' in postgres_url:
        print("❌ DATABASE_URL not configured or still contains template values")
        return False
    
    try:
        import psycopg2
        conn = psycopg2.connect(postgres_url)
        cursor = conn.cursor()
        
        # Test basic operations
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        cursor.execute("SELECT current_database();")
        database = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        print(f"✅ PostgreSQL connection successful")
        print(f"Database: {database[0]}")
        print(f"Version: {version[0][:50]}...")
        return True
        
    except ImportError:
        print("❌ psycopg2 package not installed: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {str(e)}")
        return False

def main():
    """Test both database connections"""
    print("🧪 Testing Sophia AI Database Connections")
    print("=" * 50)
    
    # Load environment variables
    env_files = ['.env', 'infra/.env.remediation', '.env.remediation']
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"📋 Loading {env_file}")
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value
            break
    
    redis_success = test_redis_connection()
    postgres_success = test_postgresql_connection()
    
    if redis_success and postgres_success:
        print("\n🎉 All database connections successful!")
        return True
    else:
        print("\n❌ Some database connections failed")
        print("\nNext steps:")
        print("1. Configure actual Redis URL in environment files")
        print("2. Configure actual PostgreSQL URL in environment files") 
        print("3. Run this test script again")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
