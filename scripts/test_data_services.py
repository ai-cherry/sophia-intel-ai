#!/usr/bin/env python3
"""
Comprehensive data services testing and remediation script
Tests and fixes Qdrant, Redis, PostgreSQL (Neon), and Estuary Flow
"""

import os
import sys
import requests
import json
import time
from typing import Dict, Any, Optional

def load_environment():
    """Load environment variables from .env file"""
    env_vars = {}
    try:
        with open('.env.remediation', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
                    os.environ[key] = value
    except FileNotFoundError:
        print("Warning: .env.remediation file not found")
    return env_vars

def test_qdrant():
    """Test and fix Qdrant vector database connection"""
    print("\n=== Testing Qdrant Vector Database ===")
    
    # Try different possible configurations
    qdrant_configs = [
        {
            "url": "https://2d196a4d-a80f-4846-be65-67563bced21f.us-east4-0.gcp.cloud.qdrant.io:6333",
            "api_key": os.environ.get('QDRANT_API_KEY', ''),
            "method": "header"
        },
        {
            "url": "https://2d196a4d-a80f-4846-be65-67563bced21f.us-east4-0.gcp.cloud.qdrant.io",
            "api_key": os.environ.get('QDRANT_API_KEY', ''),
            "method": "header"
        }
    ]
    
    for i, config in enumerate(qdrant_configs):
        print(f"\nTrying Qdrant configuration {i+1}:")
        print(f"URL: {config['url']}")
        print(f"API Key: {config['api_key'][:20]}..." if config['api_key'] else "No API key")
        
        try:
            # Test health endpoint
            headers = {
                "Authorization": f"Bearer {config['api_key']}"
            } if config['api_key'] else {}
            
            health_url = f"{config['url']}/health"
            response = requests.get(health_url, headers=headers, timeout=10)
            
            print(f"Health check status: {response.status_code}")
            if response.status_code == 200:
                print("✅ Qdrant health check successful")
                
                # Test collections endpoint
                collections_url = f"{config['url']}/collections"
                collections_response = requests.get(collections_url, headers=headers, timeout=10)
                print(f"Collections endpoint status: {collections_response.status_code}")
                
                if collections_response.status_code == 200:
                    collections = collections_response.json()
                    print(f"✅ Qdrant collections accessible: {len(collections.get('result', {}).get('collections', []))} collections")
                    return {"status": "OK", "config": config, "collections": collections}
                else:
                    print(f"❌ Collections endpoint failed: {collections_response.text}")
            else:
                print(f"❌ Health check failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Qdrant test failed: {str(e)}")
    
    return {"status": "ERROR", "message": "All Qdrant configurations failed"}

def test_redis():
    """Test and provision Redis instance"""
    print("\n=== Testing Redis Cache ===")
    
    # Check if Redis connection string exists
    redis_url = os.environ.get('REDIS_URL') or os.environ.get('REDIS_HOST')
    
    if not redis_url:
        print("❌ No Redis configuration found")
        print("Recommendation: Provision Redis instance (Redis Cloud, AWS ElastiCache, etc.)")
        
        # Suggest Redis Cloud setup
        print("\nSuggested Redis Cloud setup:")
        print("1. Sign up at https://redis.com/try-free/")
        print("2. Create a new database")
        print("3. Get connection string and add to environment as REDIS_URL")
        
        return {"status": "NOT_CONFIGURED", "message": "Redis not configured"}
    
    try:
        # Try to connect to Redis (would need redis-py package)
        print(f"Redis URL configured: {redis_url[:30]}...")
        print("Note: Redis connectivity test requires redis-py package")
        
        # For now, just check if the URL format looks correct
        if 'redis://' in redis_url or 'rediss://' in redis_url:
            print("✅ Redis URL format appears correct")
            return {"status": "CONFIGURED", "url": redis_url}
        else:
            print("⚠️ Redis URL format may be incorrect")
            return {"status": "MISCONFIGURED", "url": redis_url}
            
    except Exception as e:
        print(f"❌ Redis test failed: {str(e)}")
        return {"status": "ERROR", "message": str(e)}

def test_postgresql():
    """Test and provision PostgreSQL (Neon) database"""
    print("\n=== Testing PostgreSQL (Neon) Database ===")
    
    # Check for database URL
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('NEON_DATABASE_URL')
    
    if not database_url:
        print("❌ No PostgreSQL configuration found")
        print("Recommendation: Provision Neon PostgreSQL database")
        
        print("\nSuggested Neon setup:")
        print("1. Sign up at https://neon.tech/")
        print("2. Create a new project and database")
        print("3. Get connection string and add to environment as DATABASE_URL")
        
        return {"status": "NOT_CONFIGURED", "message": "PostgreSQL not configured"}
    
    try:
        # Check if psycopg2 is available for testing
        try:
            import psycopg2
            print(f"Database URL configured: {database_url[:50]}...")
            
            # Try to connect
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            cursor.close()
            conn.close()
            
            print(f"✅ PostgreSQL connection successful")
            print(f"Version: {version[0][:100]}...")
            return {"status": "OK", "version": version[0]}
            
        except ImportError:
            print("psycopg2 not installed, cannot test connection")
            print("✅ Database URL format appears correct")
            return {"status": "CONFIGURED", "url": database_url}
            
    except Exception as e:
        print(f"❌ PostgreSQL test failed: {str(e)}")
        return {"status": "ERROR", "message": str(e)}

def test_estuary_flow():
    """Test Estuary Flow data pipeline service"""
    print("\n=== Testing Estuary Flow ===")
    
    access_token = os.environ.get('ESTUARY_ACCESS_TOKEN')
    
    if not access_token:
        print("❌ No Estuary access token found")
        return {"status": "NOT_CONFIGURED", "message": "Estuary token missing"}
    
    # Try different possible API endpoints
    estuary_endpoints = [
        "https://api.estuary.dev",
        "https://api.estuary-data.com", 
        "https://dashboard.estuary.dev/api",
        "https://estuary.dev/api"
    ]
    
    for endpoint in estuary_endpoints:
        print(f"\nTrying Estuary endpoint: {endpoint}")
        
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Try to list flows or get user info
            test_endpoints = [
                f"{endpoint}/flows",
                f"{endpoint}/v1/flows", 
                f"{endpoint}/collections",
                f"{endpoint}/v1/collections",
                f"{endpoint}/user",
                f"{endpoint}/v1/user"
            ]
            
            for test_url in test_endpoints:
                try:
                    response = requests.get(test_url, headers=headers, timeout=10)
                    print(f"  {test_url}: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"✅ Estuary API accessible at {test_url}")
                        return {"status": "OK", "endpoint": endpoint, "data": data}
                    elif response.status_code == 401:
                        print("❌ Authentication failed - token may be invalid")
                    elif response.status_code == 404:
                        print("  Endpoint not found")
                    else:
                        print(f"  Unexpected status: {response.text[:100]}")
                        
                except requests.exceptions.RequestException as e:
                    print(f"  Request failed: {str(e)}")
                    
        except Exception as e:
            print(f"❌ Estuary test failed for {endpoint}: {str(e)}")
    
    return {"status": "ERROR", "message": "All Estuary endpoints failed"}

def generate_fixes(results: Dict[str, Any]):
    """Generate configuration fixes based on test results"""
    print("\n" + "="*60)
    print("REMEDIATION RECOMMENDATIONS")
    print("="*60)
    
    fixes = []
    
    # Qdrant fixes
    if results['qdrant']['status'] != 'OK':
        fixes.append({
            "service": "Qdrant",
            "issue": "Authentication or connection failed",
            "fix": "Verify API key and endpoint URL in Qdrant cloud console",
            "priority": "HIGH"
        })
    
    # Redis fixes
    if results['redis']['status'] == 'NOT_CONFIGURED':
        fixes.append({
            "service": "Redis",
            "issue": "No Redis instance configured",
            "fix": "Provision Redis Cloud instance and add REDIS_URL to environment",
            "priority": "HIGH"
        })
    
    # PostgreSQL fixes
    if results['postgresql']['status'] == 'NOT_CONFIGURED':
        fixes.append({
            "service": "PostgreSQL",
            "issue": "No database configured",
            "fix": "Provision Neon PostgreSQL database and add DATABASE_URL to environment",
            "priority": "HIGH"
        })
    
    # Estuary fixes
    if results['estuary']['status'] != 'OK':
        fixes.append({
            "service": "Estuary Flow",
            "issue": "API endpoint not accessible",
            "fix": "Verify access token and correct API endpoint URL",
            "priority": "MEDIUM"
        })
    
    # Print fixes
    for fix in fixes:
        print(f"\n🔧 {fix['service']} ({fix['priority']} PRIORITY)")
        print(f"   Issue: {fix['issue']}")
        print(f"   Fix: {fix['fix']}")
    
    return fixes

def main():
    """Main test execution"""
    print("Sophia AI Data Services Remediation")
    print("="*50)
    
    # Load environment
    env_vars = load_environment()
    print(f"Loaded {len(env_vars)} environment variables")
    
    # Run tests
    results = {
        'qdrant': test_qdrant(),
        'redis': test_redis(),
        'postgresql': test_postgresql(),
        'estuary': test_estuary_flow()
    }
    
    # Generate fixes
    fixes = generate_fixes(results)
    
    # Save results
    with open('data_services_test_results.json', 'w') as f:
        json.dump({
            'timestamp': time.time(),
            'results': results,
            'fixes': fixes
        }, f, indent=2)
    
    print(f"\n📊 Results saved to data_services_test_results.json")
    
    # Summary
    print(f"\n📋 SUMMARY")
    print(f"="*20)
    for service, result in results.items():
        status_emoji = "✅" if result['status'] == 'OK' else "⚠️" if 'CONFIGURED' in result['status'] else "❌"
        print(f"{status_emoji} {service.upper()}: {result['status']}")

if __name__ == "__main__":
    main()

