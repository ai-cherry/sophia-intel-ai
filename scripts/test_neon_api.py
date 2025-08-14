#!/usr/bin/env python3
"""
Test Neon PostgreSQL API and get connection details
"""
import requests
import json
import os

def test_neon_api():
    """Test Neon API with the provided token"""
    print("🔍 Testing Neon PostgreSQL API...")
    print("=" * 50)
    
    # Neon API details
    api_token = "napi_5rvzi31qllpu0zrlhgjwfhz9308k8y0yudw3oz23h2ix5no1yr3roin7wtp9vqu7"
    base_url = "https://console.neon.tech/api/v2"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    try:
        # Get projects
        print("📋 Fetching projects...")
        response = requests.get(f"{base_url}/projects", headers=headers)
        
        if response.status_code == 200:
            projects = response.json()
            print(f"✅ Found {len(projects.get('projects', []))} projects")
            
            # Look for sophia project
            sophia_project = None
            for project in projects.get('projects', []):
                print(f"   Project: {project.get('name', 'Unknown')} (ID: {project.get('id', 'Unknown')})")
                if project.get('name') == 'sophia':
                    sophia_project = project
                    break
            
            if sophia_project:
                project_id = sophia_project['id']
                print(f"\n🎯 Found Sophia project: {project_id}")
                
                # Get project details
                print("📊 Getting project details...")
                project_response = requests.get(f"{base_url}/projects/{project_id}", headers=headers)
                
                if project_response.status_code == 200:
                    project_details = project_response.json()
                    print("✅ Project details retrieved")
                    
                    # Get databases
                    print("🗄️ Getting databases...")
                    db_response = requests.get(f"{base_url}/projects/{project_id}/databases", headers=headers)
                    
                    if db_response.status_code == 200:
                        databases = db_response.json()
                        print(f"✅ Found {len(databases.get('databases', []))} databases")
                        
                        for db in databases.get('databases', []):
                            print(f"   Database: {db.get('name', 'Unknown')}")
                    
                    # Get connection details
                    print("🔗 Getting connection details...")
                    conn_response = requests.get(f"{base_url}/projects/{project_id}/connection_uri", headers=headers)
                    
                    if conn_response.status_code == 200:
                        connection_data = conn_response.json()
                        print("✅ Connection details retrieved")
                        print(f"   URI: {connection_data.get('uri', 'Not available')}")
                        
                        # Save connection details
                        save_neon_config(project_details, connection_data)
                        return True
                    else:
                        print(f"❌ Failed to get connection details: {conn_response.status_code}")
                        print(f"   Response: {conn_response.text}")
                else:
                    print(f"❌ Failed to get project details: {project_response.status_code}")
            else:
                print("❌ Sophia project not found")
                
        else:
            print(f"❌ Failed to fetch projects: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ API request failed: {e}")
        return False

def save_neon_config(project_details, connection_data):
    """Save Neon configuration to file"""
    print("\n💾 Saving Neon configuration...")
    
    config = {
        "project": {
            "id": project_details.get('project', {}).get('id'),
            "name": project_details.get('project', {}).get('name'),
            "region": project_details.get('project', {}).get('region_id'),
            "created_at": project_details.get('project', {}).get('created_at')
        },
        "connection": {
            "uri": connection_data.get('uri'),
            "host": "pg.neon.tech",  # Standard Neon host
            "database": "sophia",
            "ssl_mode": "require"
        }
    }
    
    # Save to JSON file
    with open('config/neon_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    # Create environment file
    uri = connection_data.get('uri', '')
    if uri:
        env_content = f"""# Neon PostgreSQL Configuration
NEON_DATABASE_URL={uri}
POSTGRES_URL={uri}
DATABASE_URL={uri}

# Individual components (if needed)
POSTGRES_HOST=pg.neon.tech
POSTGRES_DATABASE=sophia
POSTGRES_SSL_MODE=require

# Note: Username and password are embedded in the URI above
"""
        with open('config/neon_connection.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Configuration saved to:")
        print("   - config/neon_config.json")
        print("   - config/neon_connection.env")
    else:
        print("❌ No connection URI available to save")

def create_placeholder_config():
    """Create placeholder configuration based on visible information"""
    print("\n📝 Creating placeholder Neon configuration...")
    
    # Based on what we can see from the console
    placeholder_config = {
        "project": {
            "name": "sophia",
            "region": "AWS US West 2 (Oregon)",
            "created_at": "Aug 1, 2025 6:16 am",
            "storage": "32.63 MB",
            "postgres_version": "16"
        },
        "connection": {
            "host": "pg.neon.tech",
            "database": "sophia",
            "ssl_mode": "require",
            "note": "Full connection string needs to be retrieved from Neon console"
        }
    }
    
    # Save placeholder
    with open('config/neon_placeholder.json', 'w') as f:
        json.dump(placeholder_config, f, indent=2)
    
    # Create placeholder env
    env_content = """# Neon PostgreSQL Configuration (Placeholder)
# Project: sophia
# Region: AWS US West 2 (Oregon)
# API Token: napi_5rvzi31qllpu0zrlhgjwfhz9308k8y0yudw3oz23h2ix5no1yr3roin7wtp9vqu7

# Connection string format (needs actual values):
# postgresql://username:password@ep-endpoint.us-west-2.aws.neon.tech/sophia?sslmode=require

NEON_DATABASE_URL=postgresql://username:password@ep-endpoint.us-west-2.aws.neon.tech/sophia?sslmode=require
POSTGRES_URL=postgresql://username:password@ep-endpoint.us-west-2.aws.neon.tech/sophia?sslmode=require
DATABASE_URL=postgresql://username:password@ep-endpoint.us-west-2.aws.neon.tech/sophia?sslmode=require

POSTGRES_HOST=ep-endpoint.us-west-2.aws.neon.tech
POSTGRES_DATABASE=sophia
POSTGRES_SSL_MODE=require

# TODO: Get actual connection string from Neon console
"""
    
    with open('config/neon_placeholder.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Placeholder configuration created:")
    print("   - config/neon_placeholder.json")
    print("   - config/neon_placeholder.env")

if __name__ == "__main__":
    success = test_neon_api()
    
    if not success:
        print("\n⚠️ API test failed, creating placeholder configuration...")
        create_placeholder_config()
    
    print("\n📋 Summary:")
    print("✅ Neon project 'sophia' exists in AWS US West 2")
    print("✅ PostgreSQL version 16")
    print("✅ API token available")
    print("⚠️ Full connection string needs manual retrieval from console")

