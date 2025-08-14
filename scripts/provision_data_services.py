#!/usr/bin/env python3
"""
Data services provisioning script
Helps provision Redis Cloud and Neon PostgreSQL instances
"""

import os
import json
import requests
from typing import Dict, Any

def provision_redis_cloud():
    """Guide for Redis Cloud provisioning"""
    print("\n=== Redis Cloud Provisioning Guide ===")
    print("Since we cannot automatically provision Redis Cloud, here's the manual process:")
    print()
    print("1. Go to https://redis.com/try-free/")
    print("2. Sign up with GitHub account (scoobyjava)")
    print("3. Create a new subscription (Free tier available)")
    print("4. Create a new database:")
    print("   - Name: sophia-intel-cache")
    print("   - Region: US East (closest to Lambda Labs)")
    print("   - Memory: 30MB (free tier)")
    print("5. Get the connection details:")
    print("   - Endpoint: redis-xxxxx.c1.us-east1-2.gce.cloud.redislabs.com:12345")
    print("   - Password: generated password")
    print("6. Format as: redis://default:PASSWORD@ENDPOINT")
    print()
    
    # Check if user wants to input Redis URL manually
    redis_url = input("If you have provisioned Redis, enter the connection URL (or press Enter to skip): ").strip()
    
    if redis_url:
        # Validate Redis URL format
        if redis_url.startswith(('redis://', 'rediss://')):
            print("✅ Redis URL format looks correct")
            
            # Update .env file
            update_env_file('REDIS_URL', redis_url)
            print("✅ Redis URL added to .env.remediation")
            
            return {"status": "CONFIGURED", "url": redis_url}
        else:
            print("❌ Invalid Redis URL format. Should start with redis:// or rediss://")
            return {"status": "ERROR", "message": "Invalid URL format"}
    
    return {"status": "PENDING", "message": "Manual provisioning required"}

def provision_neon_postgresql():
    """Guide for Neon PostgreSQL provisioning"""
    print("\n=== Neon PostgreSQL Provisioning Guide ===")
    print("Since we cannot automatically provision Neon, here's the manual process:")
    print()
    print("1. Go to https://neon.tech/")
    print("2. Sign up with GitHub account (scoobyjava)")
    print("3. Create a new project:")
    print("   - Project name: sophia-intel")
    print("   - Region: US East (AWS us-east-1)")
    print("   - PostgreSQL version: 15 (latest)")
    print("4. Create a database:")
    print("   - Database name: sophia_intel")
    print("5. Get the connection string from the dashboard")
    print("   - Format: postgresql://username:password@host/database?sslmode=require")
    print()
    
    # Check if user wants to input DATABASE_URL manually
    db_url = input("If you have provisioned Neon PostgreSQL, enter the connection URL (or press Enter to skip): ").strip()
    
    if db_url:
        # Validate PostgreSQL URL format
        if db_url.startswith(('postgresql://', 'postgres://')):
            print("✅ PostgreSQL URL format looks correct")
            
            # Update .env file
            update_env_file('DATABASE_URL', db_url)
            print("✅ Database URL added to .env.remediation")
            
            return {"status": "CONFIGURED", "url": db_url}
        else:
            print("❌ Invalid PostgreSQL URL format. Should start with postgresql:// or postgres://")
            return {"status": "ERROR", "message": "Invalid URL format"}
    
    return {"status": "PENDING", "message": "Manual provisioning required"}

def fix_qdrant_config():
    """Attempt to fix Qdrant configuration"""
    print("\n=== Fixing Qdrant Configuration ===")
    
    current_key = os.environ.get('QDRANT_API_KEY', '')
    print(f"Current API key: {current_key[:20]}..." if current_key else "No API key found")
    
    # The key format suggests it might be a cluster ID, not an API key
    if current_key and len(current_key) == 36:  # UUID format
        print("The current key appears to be a cluster ID (UUID format)")
        print("Qdrant Cloud API keys typically start with 'qk-' or are longer")
        
        # Suggest getting the correct API key
        print("\nTo fix Qdrant access:")
        print("1. Go to https://cloud.qdrant.io/")
        print("2. Log in to your account")
        print("3. Go to your cluster dashboard")
        print("4. Generate or copy the API key (not the cluster ID)")
        print("5. The API key should be different from the cluster ID")
        
        new_key = input("If you have the correct API key, enter it here (or press Enter to skip): ").strip()
        
        if new_key:
            update_env_file('QDRANT_API_KEY', new_key)
            print("✅ Updated Qdrant API key")
            return {"status": "UPDATED", "key": new_key}
    
    return {"status": "NEEDS_MANUAL_FIX", "message": "Requires correct API key from Qdrant Cloud"}

def fix_estuary_config():
    """Attempt to fix Estuary Flow configuration"""
    print("\n=== Fixing Estuary Flow Configuration ===")
    
    current_token = os.environ.get('ESTUARY_ACCESS_TOKEN', '')
    print(f"Current token: {current_token[:20]}..." if current_token else "No token found")
    
    # The dashboard endpoints returned 200 but empty responses
    print("Dashboard endpoints are responding but returning empty data")
    print("This suggests the token might be valid but for a different API version")
    
    print("\nTo fix Estuary Flow access:")
    print("1. Go to https://dashboard.estuary.dev/")
    print("2. Log in to your account")
    print("3. Go to Settings or API section")
    print("4. Generate a new access token or verify the current one")
    print("5. Check the API documentation for the correct endpoints")
    
    # Try to find the correct API endpoint
    print("\nBased on testing, the dashboard API is accessible at:")
    print("https://dashboard.estuary.dev/api/")
    print("But it may require different authentication or API version")
    
    return {"status": "NEEDS_INVESTIGATION", "message": "API endpoints found but authentication unclear"}

def update_env_file(key: str, value: str):
    """Update .env.remediation file with new key-value pair"""
    env_file = '.env.remediation'
    
    # Read existing content
    lines = []
    key_found = False
    
    try:
        with open(env_file, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        pass
    
    # Update or add the key
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            key_found = True
            break
    
    if not key_found:
        lines.append(f"{key}={value}\n")
    
    # Write back to file
    with open(env_file, 'w') as f:
        f.writelines(lines)

def main():
    """Main provisioning workflow"""
    print("Sophia AI Data Services Provisioning")
    print("="*50)
    
    results = {}
    
    # Provision Redis
    results['redis'] = provision_redis_cloud()
    
    # Provision PostgreSQL
    results['postgresql'] = provision_neon_postgresql()
    
    # Fix existing services
    results['qdrant'] = fix_qdrant_config()
    results['estuary'] = fix_estuary_config()
    
    # Save results
    with open('provisioning_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📊 Provisioning results saved to provisioning_results.json")
    
    # Summary
    print(f"\n📋 PROVISIONING SUMMARY")
    print(f"="*30)
    for service, result in results.items():
        status_emoji = "✅" if result['status'] in ['CONFIGURED', 'UPDATED'] else "⚠️" if result['status'] == 'PENDING' else "❌"
        print(f"{status_emoji} {service.upper()}: {result['status']}")
        if 'message' in result:
            print(f"   {result['message']}")

if __name__ == "__main__":
    main()

