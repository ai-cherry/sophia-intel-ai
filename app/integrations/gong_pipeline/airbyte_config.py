"""
Programmatic Airbyte Setup and Configuration for Gong Data Ingestion
Handles source/destination configuration and sync job management
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional

import aiohttp
import backoff

logger = logging.getLogger(__name__)


class SyncStatus(str, Enum):
    """Airbyte sync job status"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SourceType(str, Enum):
    """Supported source types"""

    GONG = "source-gong"
    POSTGRES = "source-postgres"
    CUSTOM_API = "source-custom-api"


@dataclass
class AirbyteConnection:
    """Airbyte connection configuration"""

    connection_id: str
    source_id: str
    destination_id: str
    name: str
    status: str
    sync_catalog: dict[str, Any]
    schedule: Optional[dict[str, Any]] = None


@dataclass
class SyncJob:
    """Sync job information"""

    job_id: str
    connection_id: str
    status: SyncStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    records_synced: int = 0
    bytes_synced: int = 0
    error_message: Optional[str] = None


class AirbyteClient:
    """Airbyte API client for programmatic configuration"""

    def __init__(
        self,
        base_url: str = "https://api.airbyte.com/v1",
        client_id: str = None,
        client_secret: str = None,
        access_token: str = None,
    ):
        self.base_url = base_url
        self.client_id = client_id or os.getenv("AIRBYTE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("AIRBYTE_CLIENT_SECRET")
        self.access_token = access_token or os.getenv("AIRBYTE_ACCESS_TOKEN")
        self.workspace_id = None

        if not any([self.access_token, (self.client_id and self.client_secret)]):
            raise ValueError(
                "Either access_token or both client_id and client_secret must be provided"
            )

    async def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers"""
        if self.access_token:
            return {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
            }
        else:
            # OAuth2 flow would be implemented here if needed
            raise NotImplementedError("OAuth2 flow not implemented")

    @backoff.on_exception(backoff.expo, aiohttp.ClientError, max_tries=3)
    async def make_request(
        self, method: str, endpoint: str, data: Optional[dict] = None
    ) -> dict[str, Any]:
        """Make authenticated request to Airbyte API"""
        headers = await self.get_auth_headers()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, json=data) as response:
                if response.status >= 400:
                    error_text = await response.text()
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"API request failed: {error_text}",
                    )

                return await response.json()

    async def get_workspaces(self) -> list[dict[str, Any]]:
        """Get available workspaces"""
        response = await self.make_request("GET", "/workspaces")
        return response.get("data", [])

    async def set_workspace(self, workspace_id: str = None) -> str:
        """Set the workspace for operations"""
        if workspace_id:
            self.workspace_id = workspace_id
        else:
            # Use first available workspace
            workspaces = await self.get_workspaces()
            if workspaces:
                self.workspace_id = workspaces[0]["workspaceId"]
            else:
                raise RuntimeError("No workspaces available")

        logger.info(f"Using workspace: {self.workspace_id}")
        return self.workspace_id

    async def create_gong_source(self, source_name: str, gong_config: dict[str, Any]) -> str:
        """Create Gong source configuration"""
        if not self.workspace_id:
            await self.set_workspace()

        source_config = {
            "name": source_name,
            "workspaceId": self.workspace_id,
            "sourceType": "gong",
            "configuration": {
                "api_key": gong_config["access_key"],
                "client_secret": gong_config["client_secret"],
                "api_url": gong_config.get("api_url", "https://api.gong.io"),
                "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
                "streams": {
                    "calls": {
                        "enabled": True,
                        "sync_mode": "incremental",
                        "cursor_field": "actualStart",
                    },
                    "emails": {
                        "enabled": True,
                        "sync_mode": "incremental",
                        "cursor_field": "sentAt",
                    },
                    "transcripts": {"enabled": True, "sync_mode": "full_refresh"},
                },
            },
        }

        response = await self.make_request("POST", "/sources", source_config)
        source_id = response["sourceId"]
        logger.info(f"Created Gong source: {source_id}")
        return source_id

    async def create_weaviate_destination(
        self, destination_name: str, weaviate_config: dict[str, Any]
    ) -> str:
        """Create Weaviate destination configuration"""
        if not self.workspace_id:
            await self.set_workspace()

        destination_config = {
            "name": destination_name,
            "workspaceId": self.workspace_id,
            "destinationType": "weaviate",
            "configuration": {
                "url": weaviate_config["endpoint"],
                "api_key": weaviate_config.get("api_key"),
                "additional_headers": weaviate_config.get("headers", {}),
                "batch_size": 100,
                "index_objects": True,
                "text_fields": ["content", "summary", "body", "bodyPlainText"],
                "metadata_fields": ["all"],
                "vector_field": "vector",
                "embedding_model": "text-embedding-3-small",
            },
        }

        response = await self.make_request("POST", "/destinations", destination_config)
        destination_id = response["destinationId"]
        logger.info(f"Created Weaviate destination: {destination_id}")
        return destination_id

    async def create_connection(
        self,
        connection_name: str,
        source_id: str,
        destination_id: str,
        sync_catalog: dict[str, Any],
        schedule: Optional[dict[str, Any]] = None,
    ) -> str:
        """Create connection between source and destination"""
        if not self.workspace_id:
            await self.set_workspace()

        connection_config = {
            "name": connection_name,
            "workspaceId": self.workspace_id,
            "sourceId": source_id,
            "destinationId": destination_id,
            "syncCatalog": sync_catalog,
            "status": "active",
        }

        if schedule:
            connection_config["scheduleType"] = "cron"
            connection_config["cronExpression"] = schedule.get(
                "cron", "0 0 * * *"
            )  # Daily at midnight

        response = await self.make_request("POST", "/connections", connection_config)
        connection_id = response["connectionId"]
        logger.info(f"Created connection: {connection_id}")
        return connection_id

    async def trigger_sync(self, connection_id: str) -> str:
        """Trigger manual sync for connection"""
        sync_config = {"connectionId": connection_id, "jobType": "sync"}

        response = await self.make_request("POST", "/jobs", sync_config)
        job_id = response["jobId"]
        logger.info(f"Triggered sync job: {job_id}")
        return job_id

    async def get_job_status(self, job_id: str) -> SyncJob:
        """Get sync job status"""
        response = await self.make_request("GET", f"/jobs/{job_id}")

        return SyncJob(
            job_id=job_id,
            connection_id=response["connectionId"],
            status=SyncStatus(response["status"]),
            created_at=datetime.fromisoformat(response["createdAt"]),
            started_at=datetime.fromisoformat(response["startedAt"])
            if response.get("startedAt")
            else None,
            ended_at=datetime.fromisoformat(response["endedAt"])
            if response.get("endedAt")
            else None,
            records_synced=response.get("recordsSynced", 0),
            bytes_synced=response.get("bytesSynced", 0),
            error_message=response.get("errorMessage"),
        )

    async def wait_for_job_completion(self, job_id: str, timeout_seconds: int = 3600) -> SyncJob:
        """Wait for sync job to complete with timeout"""
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            job = await self.get_job_status(job_id)

            if job.status in [SyncStatus.SUCCEEDED, SyncStatus.FAILED, SyncStatus.CANCELLED]:
                return job

            logger.info(f"Job {job_id} status: {job.status}")
            await asyncio.sleep(30)  # Check every 30 seconds

        raise TimeoutError(f"Job {job_id} did not complete within {timeout_seconds} seconds")

    async def get_connections(self) -> list[AirbyteConnection]:
        """Get all connections in workspace"""
        if not self.workspace_id:
            await self.set_workspace()

        response = await self.make_request("GET", f"/workspaces/{self.workspace_id}/connections")

        connections = []
        for conn_data in response.get("data", []):
            connections.append(
                AirbyteConnection(
                    connection_id=conn_data["connectionId"],
                    source_id=conn_data["sourceId"],
                    destination_id=conn_data["destinationId"],
                    name=conn_data["name"],
                    status=conn_data["status"],
                    sync_catalog=conn_data.get("syncCatalog", {}),
                    schedule=conn_data.get("schedule"),
                )
            )

        return connections


class GongAirbyteOrchestrator:
    """Orchestrates Gong data ingestion via Airbyte"""

    def __init__(
        self,
        airbyte_config: dict[str, str],
        gong_config: dict[str, str],
        weaviate_config: dict[str, str],
    ):
        self.airbyte = AirbyteClient(
            base_url=airbyte_config.get("base_url", "https://api.airbyte.com/v1"),
            client_id=airbyte_config.get("client_id"),
            client_secret=airbyte_config.get("client_secret"),
            access_token=airbyte_config.get("access_token"),
        )
        self.gong_config = gong_config
        self.weaviate_config = weaviate_config

        self.source_id: Optional[str] = None
        self.destination_id: Optional[str] = None
        self.connection_id: Optional[str] = None

    async def setup_pipeline(self) -> dict[str, str]:
        """Set up complete Gong → Airbyte → Weaviate pipeline"""
        try:
            logger.info("Setting up Gong → Airbyte → Weaviate pipeline")

            # Ensure workspace is set
            await self.airbyte.set_workspace()

            # Create Gong source
            self.source_id = await self.airbyte.create_gong_source(
                "sophia-gong-source", self.gong_config
            )

            # Create Weaviate destination
            self.destination_id = await self.airbyte.create_weaviate_destination(
                "sophia-weaviate-destination", self.weaviate_config
            )

            # Create sync catalog for Gong data
            sync_catalog = self.create_gong_sync_catalog()

            # Create connection
            self.connection_id = await self.airbyte.create_connection(
                "sophia-gong-pipeline",
                self.source_id,
                self.destination_id,
                sync_catalog,
                schedule={"cron": "0 */6 * * *"},  # Every 6 hours
            )

            logger.info("Pipeline setup completed successfully")

            return {
                "source_id": self.source_id,
                "destination_id": self.destination_id,
                "connection_id": self.connection_id,
                "status": "ready",
            }

        except Exception as e:
            logger.error(f"Pipeline setup failed: {e}")
            raise

    def create_gong_sync_catalog(self) -> dict[str, Any]:
        """Create sync catalog configuration for Gong streams"""
        return {
            "streams": [
                {
                    "stream": {
                        "name": "calls",
                        "jsonSchema": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "title": {"type": "string"},
                                "url": {"type": "string"},
                                "status": {"type": "string"},
                                "actualStart": {"type": "string", "format": "date-time"},
                                "actualEnd": {"type": "string", "format": "date-time"},
                                "duration": {"type": "integer"},
                                "participants": {"type": "array"},
                                "transcript": {"type": "string"},
                                "summary": {"type": "string"},
                            },
                        },
                    },
                    "config": {
                        "syncMode": "incremental",
                        "cursorField": ["actualStart"],
                        "destinationSyncMode": "append_dedup",
                        "primaryKey": [["id"]],
                        "selected": True,
                    },
                },
                {
                    "stream": {
                        "name": "emails",
                        "jsonSchema": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "subject": {"type": "string"},
                                "body_html": {"type": "string"},
                                "body_plain": {"type": "string"},
                                "from_email": {"type": "string"},
                                "to_emails": {"type": "array"},
                                "sent_at": {"type": "string", "format": "date-time"},
                                "thread_id": {"type": "string"},
                            },
                        },
                    },
                    "config": {
                        "syncMode": "incremental",
                        "cursorField": ["sent_at"],
                        "destinationSyncMode": "append_dedup",
                        "primaryKey": [["id"]],
                        "selected": True,
                    },
                },
                {
                    "stream": {
                        "name": "transcripts",
                        "jsonSchema": {
                            "type": "object",
                            "properties": {
                                "call_id": {"type": "string"},
                                "transcript_id": {"type": "string"},
                                "speaker_id": {"type": "string"},
                                "content": {"type": "string"},
                                "start_time": {"type": "number"},
                                "end_time": {"type": "number"},
                                "confidence": {"type": "number"},
                            },
                        },
                    },
                    "config": {
                        "syncMode": "full_refresh",
                        "destinationSyncMode": "overwrite",
                        "primaryKey": [["transcript_id"]],
                        "selected": True,
                    },
                },
            ]
        }

    async def run_sync(self) -> SyncJob:
        """Run manual sync and wait for completion"""
        if not self.connection_id:
            raise RuntimeError("Pipeline not set up. Call setup_pipeline() first.")

        logger.info("Starting Gong data sync")
        job_id = await self.airbyte.trigger_sync(self.connection_id)

        # Wait for completion
        job = await self.airbyte.wait_for_job_completion(
            job_id, timeout_seconds=7200
        )  # 2 hours timeout

        if job.status == SyncStatus.SUCCEEDED:
            logger.info(f"Sync completed successfully. Records synced: {job.records_synced}")
        else:
            logger.error(f"Sync failed: {job.error_message}")

        return job

    async def get_pipeline_status(self) -> dict[str, Any]:
        """Get current pipeline status"""
        try:
            connections = await self.airbyte.get_connections()

            pipeline_connection = None
            if self.connection_id:
                pipeline_connection = next(
                    (conn for conn in connections if conn.connection_id == self.connection_id), None
                )

            return {
                "pipeline_configured": bool(self.connection_id),
                "connection_status": pipeline_connection.status
                if pipeline_connection
                else "not_found",
                "source_id": self.source_id,
                "destination_id": self.destination_id,
                "connection_id": self.connection_id,
                "total_connections": len(connections),
            }
        except Exception as e:
            logger.error(f"Failed to get pipeline status: {e}")
            return {"error": str(e)}


async def setup_gong_airbyte_pipeline(
    gong_access_key: str = None,
    gong_client_secret: str = None,
    airbyte_client_id: str = None,
    airbyte_client_secret: str = None,
    airbyte_access_token: str = None,
    weaviate_endpoint: str = None,
    weaviate_api_key: str = None,
) -> GongAirbyteOrchestrator:
    """Set up complete Gong → Airbyte → Weaviate pipeline with provided credentials"""

    # Use provided credentials or fall back to environment variables
    airbyte_config = {
        "client_id": airbyte_client_id or os.getenv("AIRBYTE_CLIENT_ID"),
        "client_secret": airbyte_client_secret or os.getenv("AIRBYTE_CLIENT_SECRET"),
        "access_token": airbyte_access_token or os.getenv("AIRBYTE_ACCESS_TOKEN"),
    }

    gong_config = {
        "access_key": gong_access_key or os.getenv("GONG_ACCESS_KEY"),
        "client_secret": gong_client_secret or os.getenv("GONG_CLIENT_SECRET"),
        "api_url": "https://api.gong.io",
    }

    weaviate_config = {
        "endpoint": weaviate_endpoint or os.getenv("WEAVIATE_ENDPOINT"),
        "api_key": weaviate_api_key or os.getenv("WEAVIATE_ADMIN_API_KEY"),
    }

    # Validate required credentials
    missing_creds = []
    if not any(
        [
            airbyte_config["access_token"],
            (airbyte_config["client_id"] and airbyte_config["client_secret"]),
        ]
    ):
        missing_creds.append("Airbyte credentials")
    if not all([gong_config["access_key"], gong_config["client_secret"]]):
        missing_creds.append("Gong credentials")
    if not weaviate_config["endpoint"]:
        missing_creds.append("Weaviate endpoint")

    if missing_creds:
        raise ValueError(f"Missing required credentials: {', '.join(missing_creds)}")

    orchestrator = GongAirbyteOrchestrator(airbyte_config, gong_config, weaviate_config)
    await orchestrator.setup_pipeline()

    return orchestrator


# Example usage and testing
async def main():
    """Example usage of Gong Airbyte setup"""
    try:
        # Use provided credentials from the user
        orchestrator = await setup_gong_airbyte_pipeline(
            gong_access_key="TV33BPZ5UN45QKZCZ2UCAKRXHQ6Q3L5N",
            gong_client_secret="eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNTQxNTA4ODUsImFjY2Vzc0tleSI6IlRWMzNCUFo1VU40NVFLWkNaMlVDQUtSWEhRNlEzTDVOIn0.zgPvDQQIvU1kvF_9ctjcKuqC5xKhlpZo7MH5v7AYufU",
            airbyte_client_id="d78cad36-e800-48c9-8571-1dacbd1b217c",
            airbyte_client_secret="VNZav8LJmsA3xKpoGMaZss3aDHuFS7da",
            airbyte_access_token="eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJ6Z1BPdmhDSC1Ic21OQnhhV3lnLU11dlF6dHJERTBDSEJHZDB2MVh0Vnk0In0...",
            weaviate_endpoint="https://w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud",
            weaviate_api_key="VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf",
        )

        # Check pipeline status
        status = await orchestrator.get_pipeline_status()
        logger.info(f"Pipeline status: {status}")

        # Run initial sync
        if status.get("pipeline_configured"):
            job = await orchestrator.run_sync()
            logger.info(f"Sync job completed: {job}")

    except Exception as e:
        logger.error(f"Pipeline setup failed: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
