#!/usr/bin/env python3
"""
Airbyte API Client for Sophia Intel Platform
Real API integration with comprehensive error handling and logging.
"""
import os
import json
import httpx
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

class AirbyteClient:
    """Airbyte Cloud API client with full CRUD operations."""
    
    def __init__(self, access_token: str = None):
        self.access_token = access_token or os.environ.get("AIRBYTE_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("AIRBYTE_ACCESS_TOKEN environment variable or access_token parameter required")
        
        self.base_url = "https://api.airbyte.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.workspace_id = None
        
    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated request to Airbyte API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=self.headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=self.headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=self.headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                error_detail = f"HTTP {e.response.status_code}: {e.response.text}"
                raise Exception(f"Airbyte API error: {error_detail}")
            except Exception as e:
                raise Exception(f"Request failed: {str(e)}")
    
    async def get_workspaces(self) -> List[Dict]:
        """Get all workspaces for the authenticated user."""
        result = await self._request("GET", "/workspaces")
        return result.get("data", [])
    
    async def get_workspace_id(self) -> str:
        """Get the first workspace ID (auto-select for single workspace users)."""
        if not self.workspace_id:
            workspaces = await self.get_workspaces()
            if not workspaces:
                raise Exception("No workspaces found")
            self.workspace_id = workspaces[0]["workspaceId"]
        return self.workspace_id
    
    async def get_connections(self, workspace_id: str = None) -> List[Dict]:
        """Get all connections in a workspace."""
        if not workspace_id:
            workspace_id = await self.get_workspace_id()
        
        result = await self._request("GET", f"/connections?workspaceId={workspace_id}")
        return result.get("data", [])
    
    async def get_sources(self, workspace_id: str = None) -> List[Dict]:
        """Get all sources in a workspace."""
        if not workspace_id:
            workspace_id = await self.get_workspace_id()
        
        result = await self._request("GET", f"/sources?workspaceId={workspace_id}")
        return result.get("data", [])
    
    async def get_destinations(self, workspace_id: str = None) -> List[Dict]:
        """Get all destinations in a workspace."""
        if not workspace_id:
            workspace_id = await self.get_workspace_id()
        
        result = await self._request("GET", f"/destinations?workspaceId={workspace_id}")
        return result.get("data", [])
    
    async def get_source_definitions(self) -> List[Dict]:
        """Get available source connector definitions."""
        result = await self._request("GET", "/source-definitions")
        return result.get("data", [])
    
    async def get_destination_definitions(self) -> List[Dict]:
        """Get available destination connector definitions."""
        result = await self._request("GET", "/destination-definitions")
        return result.get("data", [])
    
    async def create_source(self, workspace_id: str, name: str, 
                           source_definition_id: str, configuration: Dict) -> Dict:
        """Create a new source."""
        data = {
            "workspaceId": workspace_id,
            "name": name,
            "sourceDefinitionId": source_definition_id,
            "configuration": configuration
        }
        return await self._request("POST", "/sources", data)
    
    async def create_destination(self, workspace_id: str, name: str,
                               destination_definition_id: str, configuration: Dict) -> Dict:
        """Create a new destination."""
        data = {
            "workspaceId": workspace_id,
            "name": name,
            "destinationDefinitionId": destination_definition_id,
            "configuration": configuration
        }
        return await self._request("POST", "/destinations", data)
    
    async def create_connection(self, source_id: str, destination_id: str,
                              name: str = None, configuration: Dict = None) -> Dict:
        """Create a new connection between source and destination."""
        data = {
            "sourceId": source_id,
            "destinationId": destination_id,
            "name": name or f"Connection {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "configuration": configuration or {
                "syncMode": "full_refresh",
                "destinationSyncMode": "overwrite"
            }
        }
        return await self._request("POST", "/connections", data)
    
    async def trigger_sync(self, connection_id: str) -> Dict:
        """Trigger a manual sync for a connection."""
        data = {"connectionId": connection_id}
        return await self._request("POST", "/jobs", data)
    
    async def get_connection_status(self, connection_id: str) -> Dict:
        """Get the status of a connection."""
        return await self._request("GET", f"/connections/{connection_id}")
    
    async def health_check(self) -> Dict:
        """Comprehensive health check of Airbyte integration."""
        try:
            # Test basic connectivity
            workspaces = await self.get_workspaces()
            workspace_id = await self.get_workspace_id()
            
            # Get current resources
            sources = await self.get_sources(workspace_id)
            destinations = await self.get_destinations(workspace_id)
            connections = await self.get_connections(workspace_id)
            
            # Get available connectors
            source_defs = await self.get_source_definitions()
            dest_defs = await self.get_destination_definitions()
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "workspace": {
                    "id": workspace_id,
                    "name": workspaces[0]["name"] if workspaces else "Unknown"
                },
                "resources": {
                    "sources": len(sources),
                    "destinations": len(destinations),
                    "connections": len(connections)
                },
                "available_connectors": {
                    "sources": len(source_defs),
                    "destinations": len(dest_defs)
                },
                "api_endpoints_tested": [
                    "/workspaces",
                    "/sources",
                    "/destinations", 
                    "/connections",
                    "/source-definitions",
                    "/destination-definitions"
                ]
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

# Example usage and testing
async def main():
    """Test Airbyte client functionality."""
    print("AIRBYTE CLIENT TEST")
    print("=" * 40)
    
    try:
        client = AirbyteClient()
        
        # Run health check
        health = await client.health_check()
        print(f"Health Check: {json.dumps(health, indent=2)}")
        
        if health["status"] == "healthy":
            print("\n✅ Airbyte integration is working!")
            
            # List some popular connectors
            source_defs = await client.get_source_definitions()
            postgres_sources = [s for s in source_defs if "postgres" in s.get("name", "").lower()]
            
            if postgres_sources:
                print(f"\n📊 Found {len(postgres_sources)} PostgreSQL source connectors")
                for src in postgres_sources[:3]:
                    print(f"  - {src['name']}: {src['sourceDefinitionId']}")
        else:
            print(f"\n❌ Health check failed: {health.get('error')}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

