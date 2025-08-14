#!/usr/bin/env python3
"""
Script to provision and test Redis Cloud and Neon PostgreSQL databases
"""
import os
import sys
import json
import requests
import time
from typing import Dict, Any

# Redis Cloud credentials
REDIS_ACCOUNT_KEY = "A4mmxx43yms087hucu51sxbau5mi9hmnz6u33k43mpauhof6rz2"
REDIS_USER_KEY = "S2ujqhjd8evq894cdaxnli4fp667s7cn31fmah0lqqvp4foszo4"

# Neon credentials  
NEON_API_TOKEN = "napi_5rvzi31qllpu0zrlhgjwfhz9308k8y0yudw3oz23h2ix5no1yr3roin7wtp9vqu7"

def test_redis_cloud_api():
    """Test Redis Cloud API connectivity and list existing databases"""
    print("🔍 Testing Redis Cloud API connectivity...")
    
    headers = {
        "x-api-key": REDIS_ACCOUNT_KEY,
        "x-api-secret-key": REDIS_USER_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        # Test API connectivity by listing subscriptions
        response = requests.get(
            "https://api.redislabs.com/v1/subscriptions",
            headers=headers,
            timeout=30
        )
        
        print(f"Redis API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            subscriptions = response.json()
            print(f"✅ Redis Cloud API connected successfully")
            print(f"📊 Found {len(subscriptions)} subscription(s)")
            
            # List existing databases
            for sub in subscriptions:
                sub_id = sub.get('id')
                print(f"  Subscription ID: {sub_id}")
                
                # Get databases for this subscription
                db_response = requests.get(
                    f"https://api.redislabs.com/v1/subscriptions/{sub_id}/databases",
                    headers=headers,
                    timeout=30
                )
                
                if db_response.status_code == 200:
                    databases = db_response.json()
                    print(f"  📦 Databases: {len(databases)}")
                    
                    for db in databases:
                        print(f"    - {db.get('name')} (ID: {db.get('databaseId')})")
                        print(f"      Status: {db.get('status')}")
                        print(f"      Endpoint: {db.get('publicEndpoint', 'N/A')}")
                        
                        # Get connection info
                        if db.get('status') == 'active':
                            redis_url = f"redis://:{db.get('password', 'PASSWORD')}@{db.get('publicEndpoint', 'ENDPOINT')}"
                            print(f"      Redis URL: {redis_url}")
            
            return True, subscriptions
        else:
            print(f"❌ Redis API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Redis API connection failed: {str(e)}")
        return False, None

def create_redis_database():
    """Create a new Redis database if needed"""
    print("\n🚀 Creating Redis database for Sophia AI...")
    
    headers = {
        "x-api-key": REDIS_ACCOUNT_KEY,
        "x-api-secret-key": REDIS_USER_KEY,
        "Content-Type": "application/json"
    }
    
    # First check if we have any subscriptions
    success, subscriptions = test_redis_cloud_api()
    if not success:
        return None
    
    if not subscriptions:
        print("❌ No Redis subscriptions found. Please create a subscription first.")
        return None
    
    # Use the first subscription
    subscription_id = subscriptions[0]['id']
    print(f"📋 Using subscription ID: {subscription_id}")
    
    # Create database payload
    database_config = {
        "name": "sophia-ai-cache",
        "protocol": "redis",
        "memoryLimitInGb": 0.1,  # 100MB free tier
        "supportOSSClusterApi": False,
        "useExternalEndpointForOSSClusterApi": False,
        "dataPersistence": "none",
        "replication": False,
        "throughputMeasurement": {
            "by": "operations-per-second",
            "value": 1000
        },
        "modules": []
    }
    
    try:
        response = requests.post(
            f"https://api.redislabs.com/v1/subscriptions/{subscription_id}/databases",
            headers=headers,
            json=database_config,
            timeout=30
        )
        
        print(f"Create Database Response: {response.status_code}")
        
        if response.status_code in [200, 201]:
            db_info = response.json()
            print(f"✅ Redis database created successfully!")
            print(f"Database ID: {db_info.get('resourceId')}")
            
            # Wait for database to become active
            print("⏳ Waiting for database to become active...")
            return wait_for_database_active(subscription_id, db_info.get('resourceId'))
            
        else:
            print(f"❌ Failed to create database: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Database creation failed: {str(e)}")
        return None

def wait_for_database_active(subscription_id, database_id, max_wait=300):
    """Wait for Redis database to become active"""
    headers = {
        "x-api-key": REDIS_ACCOUNT_KEY,
        "x-api-secret-key": REDIS_USER_KEY,
        "Content-Type": "application/json"
    }
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(
                f"https://api.redislabs.com/v1/subscriptions/{subscription_id}/databases/{database_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                db_info = response.json()
                status = db_info.get('status')
                print(f"Database status: {status}")
                
                if status == 'active':
                    print("✅ Database is now active!")
                    return db_info
                elif status == 'error':
                    print("❌ Database creation failed")
                    return None
                    
            time.sleep(10)
            
        except Exception as e:
            print(f"Error checking database status: {e}")
            time.sleep(10)
    
    print("❌ Timeout waiting for database to become active")
    return None

def test_neon_api():
    """Test Neon API connectivity and list projects"""
    print("\n🔍 Testing Neon API connectivity...")
    
    headers = {
        "Authorization": f"Bearer {NEON_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            "https://console.neon.tech/api/v2/projects",
            headers=headers,
            timeout=30
        )
        
        print(f"Neon API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            projects = response.json()
            print(f"✅ Neon API connected successfully")
            print(f"📊 Found {len(projects.get('projects', []))} project(s)")
            
            for project in projects.get('projects', []):
                print(f"  Project: {project.get('name')} (ID: {project.get('id')})")
                print(f"    Region: {project.get('region_id')}")
                print(f"    Created: {project.get('created_at')}")
                
                # Get databases for this project
                db_response = requests.get(
                    f"https://console.neon.tech/api/v2/projects/{project.get('id')}/databases",
                    headers=headers,
                    timeout=30
                )
                
                if db_response.status_code == 200:
                    databases = db_response.json()
                    print(f"    📦 Databases: {len(databases.get('databases', []))}")
                    
                    for db in databases.get('databases', []):
                        print(f"      - {db.get('name')} (Owner: {db.get('owner_name')})")
            
            return True, projects.get('projects', [])
        else:
            print(f"❌ Neon API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Neon API connection failed: {str(e)}")
        return False, None

def get_neon_connection_string():
    """Get Neon PostgreSQL connection string"""
    print("\n🔗 Getting Neon connection string...")
    
    success, projects = test_neon_api()
    if not success or not projects:
        return None
    
    # Use the first project (sophia)
    project = projects[0]
    project_id = project.get('id')
    
    headers = {
        "Authorization": f"Bearer {NEON_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get connection details
        response = requests.get(
            f"https://console.neon.tech/api/v2/projects/{project_id}/connection_uri",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            connection_info = response.json()
            connection_uri = connection_info.get('uri')
            
            if connection_uri:
                print(f"✅ Neon connection string obtained")
                print(f"Connection URI: {connection_uri[:50]}...")  # Truncated for security
                return connection_uri
            else:
                print("❌ No connection URI found")
                return None
        else:
            print(f"❌ Failed to get connection string: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to get connection string: {str(e)}")
        return None

def test_database_connections(redis_url=None, postgres_url=None):
    """Test actual database connections"""
    print("\n🧪 Testing database connections...")
    
    results = {}
    
    # Test Redis connection
    if redis_url:
        try:
            import redis
            r = redis.from_url(redis_url)
            r.ping()
            r.set("test_key", "test_value")
            value = r.get("test_key")
            r.delete("test_key")
            
            if value == b"test_value":
                print("✅ Redis connection successful")
                results['redis'] = True
            else:
                print("❌ Redis test failed")
                results['redis'] = False
                
        except ImportError:
            print("⚠️ Redis package not installed, skipping connection test")
            results['redis'] = 'skipped'
        except Exception as e:
            print(f"❌ Redis connection failed: {str(e)}")
            results['redis'] = False
    
    # Test PostgreSQL connection
    if postgres_url:
        try:
            import psycopg2
            conn = psycopg2.connect(postgres_url)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            cursor.close()
            conn.close()
            
            print(f"✅ PostgreSQL connection successful")
            print(f"Version: {version[0][:50]}...")
            results['postgresql'] = True
            
        except ImportError:
            print("⚠️ psycopg2 package not installed, skipping connection test")
            results['postgresql'] = 'skipped'
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {str(e)}")
            results['postgresql'] = False
    
    return results

def update_environment_files(redis_url, postgres_url):
    """Update environment files with database URLs"""
    print("\n📝 Updating environment configuration files...")
    
    env_files = [
        '.env',
        'infra/.env.remediation',
        '.env.remediation'
    ]
    
    for env_file in env_files:
        if os.path.exists(env_file):
            try:
                # Read existing content
                with open(env_file, 'r') as f:
                    content = f.read()
                
                # Update or add Redis URL
                if 'REDIS_URL=' in content:
                    content = re.sub(r'REDIS_URL=.*', f'REDIS_URL={redis_url}', content)
                else:
                    content += f'\nREDIS_URL={redis_url}\n'
                
                # Update or add Database URL
                if 'DATABASE_URL=' in content:
                    content = re.sub(r'DATABASE_URL=.*', f'DATABASE_URL={postgres_url}', content)
                else:
                    content += f'\nDATABASE_URL={postgres_url}\n'
                
                # Write back
                with open(env_file, 'w') as f:
                    f.write(content)
                
                print(f"✅ Updated {env_file}")
                
            except Exception as e:
                print(f"❌ Failed to update {env_file}: {str(e)}")

def main():
    """Main provisioning function"""
    print("🚀 Sophia AI Database Provisioning")
    print("=" * 50)
    
    # Test Redis Cloud API
    redis_success, redis_subscriptions = test_redis_cloud_api()
    
    # Test Neon API
    neon_success, neon_projects = test_neon_api()
    
    if not redis_success:
        print("❌ Cannot proceed without Redis Cloud access")
        return False
    
    if not neon_success:
        print("❌ Cannot proceed without Neon access")
        return False
    
    # Get or create Redis database
    redis_url = None
    if redis_subscriptions:
        # Check if we already have a database
        subscription_id = redis_subscriptions[0]['id']
        headers = {
            "x-api-key": REDIS_ACCOUNT_KEY,
            "x-api-secret-key": REDIS_USER_KEY,
            "Content-Type": "application/json"
        }
        
        try:
            db_response = requests.get(
                f"https://api.redislabs.com/v1/subscriptions/{subscription_id}/databases",
                headers=headers,
                timeout=30
            )
            
            if db_response.status_code == 200:
                databases = db_response.json()
                if databases:
                    # Use existing database
                    db = databases[0]
                    if db.get('status') == 'active':
                        redis_url = f"redis://:{db.get('password')}@{db.get('publicEndpoint')}"
                        print(f"✅ Using existing Redis database: {db.get('name')}")
                    else:
                        print(f"⚠️ Existing database not active: {db.get('status')}")
                else:
                    # Create new database
                    db_info = create_redis_database()
                    if db_info:
                        redis_url = f"redis://:{db_info.get('password')}@{db_info.get('publicEndpoint')}"
        except Exception as e:
            print(f"Error checking existing databases: {e}")
    
    # Get Neon connection string
    postgres_url = get_neon_connection_string()
    
    if redis_url and postgres_url:
        print("\n🎉 Database provisioning completed!")
        print(f"Redis URL: {redis_url[:30]}...")
        print(f"PostgreSQL URL: {postgres_url[:30]}...")
        
        # Test connections
        test_results = test_database_connections(redis_url, postgres_url)
        
        # Update environment files
        import re
        update_environment_files(redis_url, postgres_url)
        
        return True
    else:
        print("❌ Database provisioning failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

