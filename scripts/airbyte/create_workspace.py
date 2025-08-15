#!/usr/bin/env python3
"""
Airbyte Workspace and Connection Management
Creates workspaces, sources, destinations, and connections via REST API
"""

import asyncio
import json
import os
import sys
from typing import Dict, List, Optional, Any
import httpx
import argparse
from datetime import datetime

class AirbyteManager:
    def __init__(self, api_url: str = "http://localhost:8001/api/v1"):
        self.api_url = api_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Airbyte API health"""
        try:
            response = await self.client.get(f"{self.api_url}/health")
            response.raise_for_status()
            return {"status": "healthy", "response": response.json()}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def list_workspaces(self) -> List[Dict[str, Any]]:
        """List all workspaces"""
        try:
            response = await self.client.post(
                f"{self.api_url}/workspaces/list",
                json={}
            )
            response.raise_for_status()
            return response.json().get("workspaces", [])
        except Exception as e:
            print(f"Error listing workspaces: {e}")
            return []
    
    async def create_workspace(self, name: str, email: str) -> Optional[Dict[str, Any]]:
        """Create a new workspace"""
        try:
            workspace_data = {
                "name": name,
                "email": email,
                "anonymousDataCollection": False,
                "news": False,
                "securityUpdates": True
            }
            
            response = await self.client.post(
                f"{self.api_url}/workspaces/create",
                json=workspace_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error creating workspace: {e}")
            return None
    
    async def get_or_create_workspace(self, name: str, email: str) -> Optional[str]:
        """Get existing workspace or create new one, return workspace ID"""
        workspaces = await self.list_workspaces()
        
        # Check if workspace already exists
        for workspace in workspaces:
            if workspace.get("name") == name:
                print(f"✅ Found existing workspace: {name}")
                return workspace.get("workspaceId")
        
        # Create new workspace
        print(f"🔄 Creating new workspace: {name}")
        workspace = await self.create_workspace(name, email)
        if workspace:
            workspace_id = workspace.get("workspaceId")
            print(f"✅ Created workspace: {name} (ID: {workspace_id})")
            return workspace_id
        
        return None
    
    async def create_neon_destination(self, workspace_id: str, neon_url: str) -> Optional[Dict[str, Any]]:
        """Create Neon PostgreSQL destination"""
        try:
            # Parse Neon connection string
            # Format: postgresql://user:password@host:port/database
            if not neon_url.startswith("postgresql://"):
                raise ValueError("Invalid Neon URL format")
            
            # Extract components (simplified parsing)
            url_parts = neon_url.replace("postgresql://", "").split("@")
            if len(url_parts) != 2:
                raise ValueError("Invalid Neon URL format")
            
            user_pass = url_parts[0].split(":")
            host_db = url_parts[1].split("/")
            host_port = host_db[0].split(":")
            
            destination_config = {
                "name": "Sophia-Neon-PostgreSQL",
                "destinationDefinitionId": "25c5221d-dce2-4163-ade9-739ef790f503",  # Postgres destination
                "workspaceId": workspace_id,
                "connectionConfiguration": {
                    "host": host_port[0],
                    "port": int(host_port[1]) if len(host_port) > 1 else 5432,
                    "database": host_db[1] if len(host_db) > 1 else "postgres",
                    "username": user_pass[0],
                    "password": user_pass[1] if len(user_pass) > 1 else "",
                    "ssl": True,
                    "ssl_mode": {
                        "mode": "require"
                    },
                    "schema": "public"
                }
            }
            
            response = await self.client.post(
                f"{self.api_url}/destinations/create",
                json=destination_config
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error creating Neon destination: {e}")
            return None
    
    async def create_redis_destination(self, workspace_id: str, redis_url: str) -> Optional[Dict[str, Any]]:
        """Create Redis destination (if Redis connector is available)"""
        try:
            # Note: Redis destination may not be available in all Airbyte versions
            # This is a placeholder for when it becomes available
            destination_config = {
                "name": "Sophia-Redis",
                "destinationDefinitionId": "redis-destination-id",  # Placeholder
                "workspaceId": workspace_id,
                "connectionConfiguration": {
                    "host": redis_url,
                    "port": 6379,
                    "password": "",
                    "ssl": True
                }
            }
            
            response = await self.client.post(
                f"{self.api_url}/destinations/create",
                json=destination_config
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Redis destination not available or error: {e}")
            return None
    
    async def create_minio_destination(self, workspace_id: str, minio_config: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Create MinIO S3-compatible destination"""
        try:
            destination_config = {
                "name": "Sophia-MinIO-S3",
                "destinationDefinitionId": "4816b78f-1489-44c1-9060-4b19d5fa9362",  # S3 destination
                "workspaceId": workspace_id,
                "connectionConfiguration": {
                    "s3_bucket_name": minio_config.get("bucket", "sophia-data"),
                    "s3_bucket_path": "airbyte-data",
                    "s3_bucket_region": "us-east-1",
                    "access_key_id": minio_config.get("access_key"),
                    "secret_access_key": minio_config.get("secret_key"),
                    "s3_endpoint": minio_config.get("endpoint", "http://localhost:9000"),
                    "s3_path_format": "${NAMESPACE}/${STREAM_NAME}/${YEAR}_${MONTH}_${DAY}_${EPOCH}_",
                    "file_name_pattern": "{part_number}",
                    "format": {
                        "format_type": "JSONL"
                    }
                }
            }
            
            response = await self.client.post(
                f"{self.api_url}/destinations/create",
                json=destination_config
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error creating MinIO destination: {e}")
            return None
    
    async def create_postgres_source(self, workspace_id: str, postgres_config: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Create PostgreSQL source for CDC"""
        try:
            source_config = {
                "name": "Sophia-Postgres-CDC",
                "sourceDefinitionId": "decd338e-5647-4c0b-adf4-da0e75f5a750",  # Postgres source
                "workspaceId": workspace_id,
                "connectionConfiguration": {
                    "host": postgres_config.get("host"),
                    "port": int(postgres_config.get("port", 5432)),
                    "database": postgres_config.get("database"),
                    "username": postgres_config.get("username"),
                    "password": postgres_config.get("password"),
                    "ssl": True,
                    "ssl_mode": {
                        "mode": "require"
                    },
                    "replication_method": {
                        "method": "CDC",
                        "replication_slot": "airbyte_slot",
                        "publication": "airbyte_publication"
                    },
                    "schemas": ["public"]
                }
            }
            
            response = await self.client.post(
                f"{self.api_url}/sources/create",
                json=source_config
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error creating Postgres source: {e}")
            return None
    
    async def create_connection(self, workspace_id: str, source_id: str, destination_id: str, 
                              name: str, sync_mode: str = "incremental") -> Optional[Dict[str, Any]]:
        """Create a connection between source and destination"""
        try:
            connection_config = {
                "name": name,
                "workspaceId": workspace_id,
                "sourceId": source_id,
                "destinationId": destination_id,
                "syncCatalog": {
                    "streams": []  # Will be populated based on source discovery
                },
                "schedule": {
                    "scheduleType": "manual"  # Start with manual, can be changed to cron later
                },
                "status": "active"
            }
            
            response = await self.client.post(
                f"{self.api_url}/connections/create",
                json=connection_config
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error creating connection: {e}")
            return None
    
    async def list_sources(self, workspace_id: str) -> List[Dict[str, Any]]:
        """List sources in workspace"""
        try:
            response = await self.client.post(
                f"{self.api_url}/sources/list",
                json={"workspaceId": workspace_id}
            )
            response.raise_for_status()
            return response.json().get("sources", [])
        except Exception as e:
            print(f"Error listing sources: {e}")
            return []
    
    async def list_destinations(self, workspace_id: str) -> List[Dict[str, Any]]:
        """List destinations in workspace"""
        try:
            response = await self.client.post(
                f"{self.api_url}/destinations/list",
                json={"workspaceId": workspace_id}
            )
            response.raise_for_status()
            return response.json().get("destinations", [])
        except Exception as e:
            print(f"Error listing destinations: {e}")
            return []

async def setup_sophia_workspace():
    """Set up complete Sophia Intel workspace with Neon integration"""
    
    # Configuration from environment
    neon_url = os.getenv("NEON_DATABASE_URL")
    redis_url = os.getenv("REDIS_URL")
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
    minio_access_key = os.getenv("MINIO_ACCESS_KEY_ID", "minioadmin")
    minio_secret_key = os.getenv("MINIO_SECRET_ACCESS_KEY", "minioadmin123")
    
    if not neon_url:
        print("❌ NEON_DATABASE_URL environment variable required")
        return False
    
    async with AirbyteManager() as manager:
        # Health check
        print("🔍 Checking Airbyte health...")
        health = await manager.health_check()
        if health["status"] != "healthy":
            print(f"❌ Airbyte unhealthy: {health.get('error')}")
            return False
        print("✅ Airbyte is healthy")
        
        # Create workspace
        workspace_id = await manager.get_or_create_workspace(
            "Sophia Intel", 
            "admin@sophia-intel.ai"
        )
        if not workspace_id:
            print("❌ Failed to create workspace")
            return False
        
        # Create Neon destination
        print("🔄 Creating Neon PostgreSQL destination...")
        neon_dest = await manager.create_neon_destination(workspace_id, neon_url)
        if neon_dest:
            print(f"✅ Created Neon destination: {neon_dest.get('destinationId')}")
        else:
            print("❌ Failed to create Neon destination")
            return False
        
        # Create MinIO destination
        print("🔄 Creating MinIO S3 destination...")
        minio_config = {
            "endpoint": minio_endpoint,
            "access_key": minio_access_key,
            "secret_key": minio_secret_key,
            "bucket": "sophia-data"
        }
        minio_dest = await manager.create_minio_destination(workspace_id, minio_config)
        if minio_dest:
            print(f"✅ Created MinIO destination: {minio_dest.get('destinationId')}")
        else:
            print("⚠️ MinIO destination creation failed (may not be critical)")
        
        # List current sources and destinations
        sources = await manager.list_sources(workspace_id)
        destinations = await manager.list_destinations(workspace_id)
        
        print(f"\n📊 Workspace Summary:")
        print(f"  Workspace ID: {workspace_id}")
        print(f"  Sources: {len(sources)}")
        print(f"  Destinations: {len(destinations)}")
        
        for dest in destinations:
            print(f"    - {dest.get('name')} ({dest.get('destinationId')})")
        
        print("\n✅ Sophia Intel workspace setup complete!")
        print("\nNext steps:")
        print("1. Access Airbyte at http://localhost:8000")
        print("2. Configure your sources (Gong, Files, etc.)")
        print("3. Create connections to sync data")
        
        return True

async def main():
    parser = argparse.ArgumentParser(description="Airbyte Workspace Management")
    parser.add_argument("--setup", action="store_true", help="Set up Sophia Intel workspace")
    parser.add_argument("--health", action="store_true", help="Check Airbyte health")
    
    args = parser.parse_args()
    
    if args.health:
        async with AirbyteManager() as manager:
            health = await manager.health_check()
            print(json.dumps(health, indent=2))
            return health["status"] == "healthy"
    
    if args.setup:
        return await setup_sophia_workspace()
    
    # Default: show help
    parser.print_help()
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

