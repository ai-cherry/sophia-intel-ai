"""
Estuary Flow Configuration and Client

This module provides configuration and client functionality for Estuary Flow integration.
Estuary Flow is used for real-time data streaming and ETL operations.
"""

import os
import json
import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import base64


class EstuaryConfig:
    """Configuration for Estuary Flow integration."""
    
    def __init__(self):
        # Estuary credentials from environment or provided values
        self.jwt_token = os.getenv(
            "ESTUARY_JWT_TOKEN",
            "eyJhbGciOiJIUzI1NiIsImtpZCI6IlhaYXZsWHkrajczYUxwYlEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2V5cmNubXV6enlyaXlwZGFqd2RrLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiJkNDRmMDBhNC05NmE1LTQyMWItYTkxZS02ODVmN2I3NDg5ZTMiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzU1MjA3OTU4LCJpYXQiOjE3NTUyMDQzNTgsImVtYWlsIjoibXVzaWxseW5uQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZ2l0aHViIiwicHJvdmlkZXJzIjpbImdpdGh1YiJdfSwidXNlcl9tZXRhZGF0YSI6eyJhdmF0YXJfdXJsIjoiaHR0cHM6Ly9hdmF0YXJzLmdpdGh1YnVzZXJjb250ZW50LmNvbS91LzEyNDQxODk1Mz92PTQiLCJlbWFpbCI6Im11c2lsbHlubkBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZnVsbF9uYW1lIjoiTHlubiBNdXNpbCIsImlzcyI6Imh0dHBzOi8vYXBpLmdpdGh1Yi5jb20iLCJuYW1lIjoiTHlubiBNdXNpbCIsInBob25lX3ZlcmlmaWVkIjpmYWxzZSwicHJlZmVycmVkX3VzZXJuYW1lIjoic2Nvb2J5amF2YSIsInByb3ZpZGVyX2lkIjoiMTI0NDE4OTUzIiwic3ViIjoiMTI0NDE4OTUzIiwidXNlcl9uYW1lIjoic2Nvb2J5amF2YSJ9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6Im9hdXRoIiwidGltZXN0YW1wIjoxNzU1MjA0MzU4fV0sInNlc3Npb25faWQiOiIxNWJmN2Y3OC01MGUyLTQxYzgtODE1MC03N2Q3ZTc4ZWRiMjYiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.SD2UNyLMvpIEiIPod3m7FjSBiVipmsMmMY7a-TsFTwc"
        )
        
        self.refresh_token = os.getenv(
            "ESTUARY_REFRESH_TOKEN",
            "eyJpZCI6IjEyOjExOjc0OjE2OjljOmFmOjhjOjAwIiwic2VjcmV0IjoiYjM4NWU1NTktODgwNy00NzhjLWJiY2QtMWRlMzIxZTM3YmZhIn0="
        )
        
        # Estuary API endpoints
        self.api_base_url = "https://api.estuary.dev"
        self.dashboard_url = "https://dashboard.estuary.dev"
        
        # Default configuration
        self.tenant = "sophia-intel"
        self.namespace = "sophia/"
        
    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for Estuary API requests."""
        return {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }


class EstuaryClient:
    """Client for interacting with Estuary Flow API."""
    
    def __init__(self, config: Optional[EstuaryConfig] = None):
        self.config = config or EstuaryConfig()
        self.client = httpx.AsyncClient(
            base_url=self.config.api_base_url,
            headers=self.config.get_headers(),
            timeout=30.0
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Estuary Flow API health and authentication."""
        try:
            response = await self.client.get("/v1/auth/me")
            if response.status_code == 200:
                user_info = response.json()
                return {
                    "status": "healthy",
                    "authenticated": True,
                    "user": user_info.get("email", "unknown"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "authenticated": False,
                    "error": f"HTTP {response.status_code}",
                    "timestamp": datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "authenticated": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def list_collections(self) -> Dict[str, Any]:
        """List available collections in the tenant."""
        try:
            response = await self.client.get("/v1/collections")
            if response.status_code == 200:
                collections = response.json()
                return {
                    "success": True,
                    "collections": collections,
                    "count": len(collections.get("collections", []))
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_capture(self, capture_name: str, source_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new capture for data ingestion."""
        capture_spec = {
            "name": f"{self.config.namespace}{capture_name}",
            "endpoint": {
                "connector": {
                    "image": "ghcr.io/estuary/source-http-ingest:dev",
                    "config": source_config
                }
            },
            "bindings": [
                {
                    "resource": {
                        "stream": "sophia_data",
                        "syncMode": "incremental"
                    },
                    "target": f"{self.config.namespace}sophia_raw_data"
                }
            ]
        }
        
        try:
            response = await self.client.post("/v1/captures", json=capture_spec)
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "capture": response.json(),
                    "name": capture_name
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_materialization(self, materialization_name: str, target_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new materialization for data output."""
        materialization_spec = {
            "name": f"{self.config.namespace}{materialization_name}",
            "endpoint": {
                "connector": {
                    "image": "ghcr.io/estuary/materialize-postgres:dev",
                    "config": target_config
                }
            },
            "bindings": [
                {
                    "source": f"{self.config.namespace}sophia_raw_data",
                    "resource": {
                        "table": "sophia_processed_data"
                    }
                }
            ]
        }
        
        try:
            response = await self.client.post("/v1/materializations", json=materialization_spec)
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "materialization": response.json(),
                    "name": materialization_name
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_capture_status(self, capture_name: str) -> Dict[str, Any]:
        """Get status of a specific capture."""
        try:
            response = await self.client.get(f"/v1/captures/{self.config.namespace}{capture_name}")
            if response.status_code == 200:
                return {
                    "success": True,
                    "status": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Configuration for Sophia Intel specific use cases
SOPHIA_CAPTURE_CONFIG = {
    "name": "sophia_ai_data_capture",
    "source_config": {
        "endpoint": "https://api.sophia-intel.ai/data/stream",
        "method": "GET",
        "headers": {
            "Accept": "application/json"
        },
        "interval": "5m"
    }
}

SOPHIA_MATERIALIZATION_CONFIG = {
    "name": "sophia_ai_data_output",
    "target_config": {
        "host": "localhost",
        "port": 5432,
        "database": "sophia",
        "schema": "estuary",
        "user": "sophia",
        "password": "${POSTGRES_PASSWORD}"
    }
}


async def setup_sophia_estuary_flow():
    """Set up Estuary Flow for Sophia Intel platform."""
    async with EstuaryClient() as client:
        # Health check
        health = await client.health_check()
        print(f"Estuary Health: {health}")
        
        if not health.get("authenticated"):
            return {
                "success": False,
                "error": "Authentication failed",
                "health": health
            }
        
        # List existing collections
        collections = await client.list_collections()
        print(f"Collections: {collections}")
        
        # Create capture
        capture_result = await client.create_capture(
            SOPHIA_CAPTURE_CONFIG["name"],
            SOPHIA_CAPTURE_CONFIG["source_config"]
        )
        print(f"Capture creation: {capture_result}")
        
        # Create materialization
        materialization_result = await client.create_materialization(
            SOPHIA_MATERIALIZATION_CONFIG["name"],
            SOPHIA_MATERIALIZATION_CONFIG["target_config"]
        )
        print(f"Materialization creation: {materialization_result}")
        
        return {
            "success": True,
            "health": health,
            "collections": collections,
            "capture": capture_result,
            "materialization": materialization_result
        }


if __name__ == "__main__":
    import asyncio
    
    async def main():
        result = await setup_sophia_estuary_flow()
        print(json.dumps(result, indent=2))
    
    asyncio.run(main())

