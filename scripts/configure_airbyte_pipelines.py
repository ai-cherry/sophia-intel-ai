#!/usr/bin/env python3
"""
Airbyte Data Pipeline Configuration Script
Configures sources, destinations, and connections for Sophia Intel platform
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import aiohttp
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class AirbyteConfigurator:
    """Airbyte pipeline configuration manager"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        self.workspace_id = None
        self.session = None
        
        # Credentials from environment
        self.neon_host = os.getenv('NEON_HOST', 'ep-rough-voice-a5xp7uy8.us-east-2.aws.neon.tech')
        self.neon_database = os.getenv('NEON_DATABASE', 'neondb')
        self.neon_username = os.getenv('NEON_USERNAME', 'neondb_owner')
        self.neon_password = os.getenv('NEON_PASSWORD', 'npg_xxxxxxxxx')
        
        self.qdrant_url = os.getenv('QDRANT_URL', 'https://a2a5dc3b-bf37-4907-9398-d49f5c6813ed.us-west-2-0.aws.cloud.qdrant.io')
        self.qdrant_api_key = os.getenv('QDRANT_API_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwiZXhwIjoxNzY1NTkxNjEzfQ.a4uBhUimAhpzdGLLOmSwHwGWF4rAQynEFZG8A9pDHkQ')
        
        self.redis_host = os.getenv('REDIS_HOST', 'redis-12345.upstash.io')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_password = os.getenv('REDIS_PASSWORD', 'redis_password_here')
        
        self.configuration_results = []
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to Airbyte API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with self.session.request(method, url, json=data) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    logger.error(f"Airbyte API error {response.status}: {error_text}")
                    raise Exception(f"API error {response.status}: {error_text}")
                
                return await response.json()
                
        except aiohttp.ClientError as e:
            logger.error(f"Airbyte API client error: {e}")
            raise Exception(f"Client error: {e}")
    
    async def wait_for_airbyte_ready(self, max_attempts: int = 30, delay: int = 10) -> bool:
        """Wait for Airbyte server to be ready"""
        logger.info("Waiting for Airbyte server to be ready...")
        
        for attempt in range(max_attempts):
            try:
                response = await self._make_request("GET", "/health")
                if response.get("available", False):
                    logger.info("Airbyte server is ready!")
                    return True
                    
            except Exception as e:
                logger.debug(f"Attempt {attempt + 1}: Airbyte not ready yet - {e}")
            
            if attempt < max_attempts - 1:
                logger.info(f"Waiting {delay} seconds before next attempt...")
                await asyncio.sleep(delay)
        
        logger.error("Airbyte server failed to become ready")
        return False
    
    async def get_workspace(self) -> Dict:
        """Get or create workspace"""
        try:
            # List workspaces
            workspaces = await self._make_request("POST", "/workspaces/list", {})
            
            if workspaces.get("workspaces"):
                workspace = workspaces["workspaces"][0]
                self.workspace_id = workspace["workspaceId"]
                logger.info(f"Using existing workspace: {workspace['name']}")
                return workspace
            else:
                # Create workspace
                workspace_data = {
                    "name": "Sophia Intel Workspace",
                    "email": "admin@sophia-intel.ai",
                    "anonymousDataCollection": False,
                    "news": False,
                    "securityUpdates": True
                }
                
                workspace = await self._make_request("POST", "/workspaces/create", workspace_data)
                self.workspace_id = workspace["workspaceId"]
                logger.info(f"Created new workspace: {workspace['name']}")
                return workspace
                
        except Exception as e:
            logger.error(f"Error managing workspace: {e}")
            raise
    
    async def create_postgres_destination(self) -> Dict:
        """Create Neon PostgreSQL destination"""
        try:
            destination_data = {
                "workspaceId": self.workspace_id,
                "name": "Neon PostgreSQL",
                "destinationDefinitionId": "25c5221d-dce2-4163-ade9-739ef790f503",  # Postgres destination
                "connectionConfiguration": {
                    "host": self.neon_host,
                    "port": 5432,
                    "database": self.neon_database,
                    "username": self.neon_username,
                    "password": self.neon_password,
                    "ssl": True,
                    "ssl_mode": {
                        "mode": "require"
                    },
                    "schema": "public",
                    "tunnel_method": {
                        "tunnel_method": "NO_TUNNEL"
                    }
                }
            }
            
            destination = await self._make_request("POST", "/destinations/create", destination_data)
            logger.info(f"Created PostgreSQL destination: {destination['destinationId']}")
            
            self.configuration_results.append({
                "type": "destination",
                "name": "Neon PostgreSQL",
                "id": destination['destinationId'],
                "status": "created"
            })
            
            return destination
            
        except Exception as e:
            logger.error(f"Error creating PostgreSQL destination: {e}")
            self.configuration_results.append({
                "type": "destination",
                "name": "Neon PostgreSQL",
                "status": "failed",
                "error": str(e)
            })
            raise
    
    async def create_file_source(self) -> Dict:
        """Create file-based source for testing"""
        try:
            source_data = {
                "workspaceId": self.workspace_id,
                "name": "Local Files Source",
                "sourceDefinitionId": "778daa7c-feaf-4db6-96f3-70fd645acc77",  # File source
                "connectionConfiguration": {
                    "dataset_name": "sophia_test_data",
                    "format": "csv",
                    "url": "/tmp/test_data.csv",
                    "provider": {
                        "storage": "local"
                    }
                }
            }
            
            source = await self._make_request("POST", "/sources/create", source_data)
            logger.info(f"Created file source: {source['sourceId']}")
            
            self.configuration_results.append({
                "type": "source",
                "name": "Local Files Source",
                "id": source['sourceId'],
                "status": "created"
            })
            
            return source
            
        except Exception as e:
            logger.error(f"Error creating file source: {e}")
            self.configuration_results.append({
                "type": "source",
                "name": "Local Files Source",
                "status": "failed",
                "error": str(e)
            })
            raise
    
    async def create_postgres_source(self) -> Dict:
        """Create PostgreSQL source for CDC"""
        try:
            source_data = {
                "workspaceId": self.workspace_id,
                "name": "Neon PostgreSQL Source",
                "sourceDefinitionId": "decd338e-5647-4c0b-adf4-da0e75f5a750",  # Postgres source
                "connectionConfiguration": {
                    "host": self.neon_host,
                    "port": 5432,
                    "database": self.neon_database,
                    "username": self.neon_username,
                    "password": self.neon_password,
                    "ssl": True,
                    "ssl_mode": {
                        "mode": "require"
                    },
                    "schemas": ["public"],
                    "replication_method": {
                        "method": "Standard"
                    },
                    "tunnel_method": {
                        "tunnel_method": "NO_TUNNEL"
                    }
                }
            }
            
            source = await self._make_request("POST", "/sources/create", source_data)
            logger.info(f"Created PostgreSQL source: {source['sourceId']}")
            
            self.configuration_results.append({
                "type": "source",
                "name": "Neon PostgreSQL Source",
                "id": source['sourceId'],
                "status": "created"
            })
            
            return source
            
        except Exception as e:
            logger.error(f"Error creating PostgreSQL source: {e}")
            self.configuration_results.append({
                "type": "source",
                "name": "Neon PostgreSQL Source",
                "status": "failed",
                "error": str(e)
            })
            raise
    
    async def create_connection(self, source_id: str, destination_id: str, name: str) -> Dict:
        """Create connection between source and destination"""
        try:
            connection_data = {
                "sourceId": source_id,
                "destinationId": destination_id,
                "name": name,
                "namespaceDefinition": "source",
                "namespaceFormat": "${SOURCE_NAMESPACE}",
                "prefix": "sophia_",
                "status": "active",
                "schedule": {
                    "scheduleType": "manual"
                },
                "syncCatalog": {
                    "streams": []
                }
            }
            
            connection = await self._make_request("POST", "/connections/create", connection_data)
            logger.info(f"Created connection: {connection['connectionId']}")
            
            self.configuration_results.append({
                "type": "connection",
                "name": name,
                "id": connection['connectionId'],
                "source_id": source_id,
                "destination_id": destination_id,
                "status": "created"
            })
            
            return connection
            
        except Exception as e:
            logger.error(f"Error creating connection {name}: {e}")
            self.configuration_results.append({
                "type": "connection",
                "name": name,
                "status": "failed",
                "error": str(e)
            })
            raise
    
    async def test_connection(self, connection_id: str) -> Dict:
        """Test a connection"""
        try:
            test_data = {"connectionId": connection_id}
            result = await self._make_request("POST", "/connections/check", test_data)
            
            status = result.get("status", "unknown")
            logger.info(f"Connection test result: {status}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error testing connection {connection_id}: {e}")
            return {"status": "failed", "error": str(e)}
    
    async def create_test_data_file(self) -> str:
        """Create test CSV file for file source"""
        test_data = """id,name,email,created_at,data_type
1,John Doe,john@example.com,2025-01-01,user
2,Jane Smith,jane@example.com,2025-01-02,user
3,Bob Johnson,bob@example.com,2025-01-03,user
4,Alice Brown,alice@example.com,2025-01-04,user
5,Charlie Wilson,charlie@example.com,2025-01-05,user
"""
        
        file_path = "/tmp/test_data.csv"
        with open(file_path, 'w') as f:
            f.write(test_data)
        
        logger.info(f"Created test data file: {file_path}")
        return file_path
    
    async def configure_all_pipelines(self) -> Dict:
        """Configure all data pipelines"""
        logger.info("🚀 Starting Airbyte pipeline configuration")
        
        try:
            # Wait for Airbyte to be ready
            if not await self.wait_for_airbyte_ready():
                raise Exception("Airbyte server not ready")
            
            # Get workspace
            workspace = await self.get_workspace()
            logger.info(f"✅ Workspace ready: {workspace['name']}")
            
            # Create test data
            await self.create_test_data_file()
            
            # Create destinations
            postgres_dest = await self.create_postgres_destination()
            logger.info("✅ PostgreSQL destination created")
            
            # Create sources
            file_source = await self.create_file_source()
            logger.info("✅ File source created")
            
            postgres_source = await self.create_postgres_source()
            logger.info("✅ PostgreSQL source created")
            
            # Create connections
            file_to_postgres = await self.create_connection(
                file_source['sourceId'],
                postgres_dest['destinationId'],
                "File to PostgreSQL"
            )
            logger.info("✅ File → PostgreSQL connection created")
            
            # Test connections
            logger.info("🔍 Testing connections...")
            file_test = await self.test_connection(file_to_postgres['connectionId'])
            
            # Summary
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "workspace_id": self.workspace_id,
                "total_configurations": len(self.configuration_results),
                "successful": len([r for r in self.configuration_results if r['status'] == 'created']),
                "failed": len([r for r in self.configuration_results if r['status'] == 'failed']),
                "configurations": self.configuration_results,
                "connection_tests": {
                    "file_to_postgres": file_test.get("status", "unknown")
                }
            }
            
            logger.info("🎉 Pipeline configuration completed!")
            return summary
            
        except Exception as e:
            logger.error(f"Pipeline configuration failed: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "failed",
                "error": str(e),
                "configurations": self.configuration_results
            }


async def main():
    """Main configuration runner"""
    logger.info("🔧 Airbyte Data Pipeline Configurator")
    
    # Set up environment variables if not set
    os.environ.setdefault('NEON_HOST', 'ep-rough-voice-a5xp7uy8.us-east-2.aws.neon.tech')
    os.environ.setdefault('NEON_DATABASE', 'neondb')
    os.environ.setdefault('NEON_USERNAME', 'neondb_owner')
    os.environ.setdefault('NEON_PASSWORD', 'npg_xxxxxxxxx')
    
    async with AirbyteConfigurator() as configurator:
        results = await configurator.configure_all_pipelines()
        
        # Save results
        results_file = Path(__file__).parent.parent / "airbyte_pipeline_config_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print("\n" + "="*60)
        print("📊 AIRBYTE PIPELINE CONFIGURATION SUMMARY")
        print("="*60)
        print(f"Timestamp: {results.get('timestamp', 'Unknown')}")
        print(f"Workspace ID: {results.get('workspace_id', 'Unknown')}")
        print(f"Total Configurations: {results.get('total_configurations', 0)}")
        print(f"Successful: {results.get('successful', 0)}")
        print(f"Failed: {results.get('failed', 0)}")
        
        if results.get('configurations'):
            print("\nConfiguration Details:")
            for config in results['configurations']:
                status_icon = "✅" if config['status'] == 'created' else "❌"
                print(f"  {status_icon} {config['type'].title()}: {config['name']}")
                if config['status'] == 'failed':
                    print(f"    Error: {config.get('error', 'Unknown error')}")
        
        if results.get('connection_tests'):
            print("\nConnection Tests:")
            for conn_name, status in results['connection_tests'].items():
                status_icon = "✅" if status == "succeeded" else "⚠️" if status == "unknown" else "❌"
                print(f"  {status_icon} {conn_name}: {status}")
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        # Overall status
        if results.get('status') == 'failed':
            print("❌ Configuration failed!")
            return 1
        elif results.get('failed', 0) > 0:
            print("⚠️  Configuration completed with some failures")
            return 1
        else:
            print("🎉 Configuration completed successfully!")
            return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

