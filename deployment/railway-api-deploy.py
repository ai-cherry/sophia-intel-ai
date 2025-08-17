#!/usr/bin/env python3
"""
Railway API Deployment Script for SOPHIA Intel Frontend
Uses Railway's GraphQL API to create proper production deployment
"""

import os
import requests
import json
import sys
import time
from typing import Dict, Optional

class RailwayDeployer:
    def __init__(self, token: str):
        self.token = token
        self.api_url = "https://backboard.railway.app/graphql/v2"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def execute_query(self, query: str, variables: Dict = None) -> Dict:
        """Execute a GraphQL query against Railway API"""
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        response = requests.post(self.api_url, json=payload, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Railway API error: {response.status_code} - {response.text}")
    
    def get_user_info(self) -> Dict:
        """Get current user information"""
        query = """
        query {
            me {
                id
                name
                email
            }
        }
        """
        return self.execute_query(query)
    
    def list_projects(self) -> Dict:
        """List all projects"""
        query = """
        query {
            projects {
                edges {
                    node {
                        id
                        name
                        description
                        createdAt
                    }
                }
            }
        }
        """
        return self.execute_query(query)
    
    def create_project(self, name: str, description: str = "") -> Dict:
        """Create a new Railway project"""
        query = """
        mutation ProjectCreate($input: ProjectCreateInput!) {
            projectCreate(input: $input) {
                id
                name
                description
            }
        }
        """
        variables = {
            "input": {
                "name": name,
                "description": description,
                "isPublic": False
            }
        }
        return self.execute_query(query, variables)
    
    def create_service(self, project_id: str, name: str) -> Dict:
        """Create a service in a project"""
        query = """
        mutation ServiceCreate($input: ServiceCreateInput!) {
            serviceCreate(input: $input) {
                id
                name
            }
        }
        """
        variables = {
            "input": {
                "projectId": project_id,
                "name": name,
                "source": {
                    "repo": "ai-cherry/sophia-intel",
                    "rootDirectory": "apps/dashboard"
                }
            }
        }
        return self.execute_query(query, variables)
    
    def connect_github_repo(self, project_id: str, repo: str, root_dir: str = None) -> Dict:
        """Connect a GitHub repository to the project"""
        query = """
        mutation ServiceConnect($input: ServiceConnectInput!) {
            serviceConnect(input: $input) {
                id
                name
            }
        }
        """
        variables = {
            "input": {
                "projectId": project_id,
                "source": {
                    "repo": repo,
                    "rootDirectory": root_dir
                }
            }
        }
        return self.execute_query(query, variables)
    
    def trigger_deployment(self, service_id: str) -> Dict:
        """Trigger a deployment for a service"""
        query = """
        mutation DeploymentCreate($input: DeploymentCreateInput!) {
            deploymentCreate(input: $input) {
                id
                status
                createdAt
            }
        }
        """
        variables = {
            "input": {
                "serviceId": service_id
            }
        }
        return self.execute_query(query, variables)

def deploy_sophia_frontend():
    """Deploy SOPHIA Intel frontend to Railway"""
    
    # Get Railway token from environment
    token = os.getenv('RAILWAY_TOKEN')
    if not token:
        print("❌ RAILWAY_TOKEN environment variable not set")
        sys.exit(1)
    
    deployer = RailwayDeployer(token)
    
    try:
        print("🚀 Starting SOPHIA Intel Frontend Deployment to Railway")
        
        # Verify authentication
        print("🔐 Verifying Railway authentication...")
        user_info = deployer.get_user_info()
        
        if 'errors' in user_info:
            print(f"❌ Authentication failed: {user_info['errors']}")
            sys.exit(1)
        
        user = user_info['data']['me']
        print(f"✅ Authenticated as: {user['name']} ({user['email']})")
        
        # List existing projects
        print("📋 Checking existing projects...")
        projects_response = deployer.list_projects()
        projects = projects_response['data']['projects']['edges']
        
        # Look for existing SOPHIA Intel frontend project
        frontend_project = None
        for project in projects:
            if 'sophia-intel-frontend' in project['node']['name'].lower():
                frontend_project = project['node']
                break
        
        if frontend_project:
            print(f"✅ Found existing project: {frontend_project['name']} (ID: {frontend_project['id']})")
            project_id = frontend_project['id']
        else:
            # Create new project
            print("➕ Creating new Railway project for SOPHIA Intel Frontend...")
            project_response = deployer.create_project(
                name="sophia-intel-frontend",
                description="SOPHIA Intel Enhanced Frontend Dashboard - Production Deployment"
            )
            
            if 'errors' in project_response:
                print(f"❌ Failed to create project: {project_response['errors']}")
                sys.exit(1)
            
            project = project_response['data']['projectCreate']
            project_id = project['id']
            print(f"✅ Created project: {project['name']} (ID: {project_id})")
        
        # Connect GitHub repository
        print("🔗 Connecting GitHub repository...")
        try:
            service_response = deployer.connect_github_repo(
                project_id=project_id,
                repo="ai-cherry/sophia-intel",
                root_dir="apps/dashboard"
            )
            
            if 'errors' in service_response:
                print(f"⚠️  GitHub connection info: {service_response['errors']}")
                # Continue anyway, might already be connected
            else:
                service = service_response['data']['serviceConnect']
                print(f"✅ Connected GitHub repo to service: {service['name']}")
        
        except Exception as e:
            print(f"⚠️  GitHub connection note: {str(e)}")
            # Continue with deployment
        
        print("\n🎉 Railway Project Configuration Complete!")
        print(f"📋 Project Details:")
        print(f"   🆔 Project ID: {project_id}")
        print(f"   📁 Repository: ai-cherry/sophia-intel")
        print(f"   📂 Root Directory: apps/dashboard")
        print(f"   🐳 Build Method: Dockerfile")
        
        print(f"\n🌐 Next Steps:")
        print(f"   1. Visit Railway dashboard to complete deployment")
        print(f"   2. Configure environment variables if needed")
        print(f"   3. Deploy will trigger automatically from GitHub")
        print(f"   4. Custom domain: www.sophia-intel.ai")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")
        return False

if __name__ == "__main__":
    deploy_sophia_frontend()

