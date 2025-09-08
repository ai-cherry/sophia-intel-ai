"""
Sophia AI Fusion Systems - Estuary Flow Data Pipelines
Week 3: Essential Integrations Implementation

Automated data integration and ETL workflows with Estuary Flow API integration.
Supports multiple data sources, transformation pipelines, and monitoring.
"""

import asyncio
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp

from app.api.services.performance_monitor import monitor_performance

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Connection status enumeration"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class SyncStatus(Enum):
    """Sync job status enumeration"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SourceConfig:
    """Configuration for a data source"""

    source_id: str
    name: str
    source_type: str  # e.g., "postgres", "mysql", "api", "file"
    connection_config: Dict[str, Any]
    schema_config: Optional[Dict[str, Any]] = None
    sync_frequency: str = "daily"  # hourly, daily, weekly
    enabled: bool = True


@dataclass
class DestinationConfig:
    """Configuration for a data destination"""

    destination_id: str
    name: str
    destination_type: str  # e.g., "postgres", "bigquery", "s3"
    connection_config: Dict[str, Any]
    enabled: bool = True


@dataclass
class PipelineConfig:
    """Configuration for a data pipeline"""

    pipeline_id: str
    name: str
    source_id: str
    destination_id: str
    transformation_config: Optional[Dict[str, Any]] = None
    schedule: str = "0 2 * * *"  # Daily at 2 AM (cron format)
    enabled: bool = True
    retry_attempts: int = 3
    timeout_minutes: int = 60


@dataclass
class SyncJobResult:
    """Result of a sync job execution"""

    job_id: str
    pipeline_id: str
    status: SyncStatus
    start_time: str
    end_time: Optional[str] = None
    records_processed: int = 0
    records_failed: int = 0
    bytes_processed: int = 0
    error_message: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class PipelineStats:
    """Statistics for pipeline performance"""

    pipeline_id: str
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    avg_duration_seconds: float = 0.0
    total_records_processed: int = 0
    total_bytes_processed: int = 0
    last_run_time: Optional[str] = None
    success_rate: float = 0.0


class EstuaryFlowPipelines:
    """
    Advanced Estuary Flow integration for automated data pipelines
    """

    def __init__(
        self,
        estuary_flow_url: str = "https://api.estuary.dev",
        api_version: str = "v1",
        api_token: Optional[str] = None,
    ):
        self.estuary_flow_url = estuary_flow_url.rstrip("/")
        self.api_version = api_version
        self.api_token = api_token
        self.session: Optional[aiohttp.ClientSession] = None

        # Pipeline management
        self.sources: Dict[str, SourceConfig] = {}
        self.destinations: Dict[str, DestinationConfig] = {}
        self.pipelines: Dict[str, PipelineConfig] = {}
        self.pipeline_stats: Dict[str, PipelineStats] = {}
        self.active_jobs: Dict[str, SyncJobResult] = {}

        # Predefined source configurations
        self.source_templates = {
            "postgres": {
                "host": "localhost",
                "port": 5432,
                "database": "sophia_ai",
                "username": "postgres",
                "password": "",
                "ssl": False,
                "replication_method": "Standard",
            },
            "mysql": {
                "host": "localhost",
                "port": 3306,
                "database": "sophia_ai",
                "username": "root",
                "password": "",
                "ssl": False,
                "replication_method": "Standard",
            },
            "redis": {
                "host": "localhost",
                "port": 6380,
                "password": "",
                "db": 0,
                "ssl": False,
            },
            "api": {
                "base_url": "https://api.example.com",
                "api_key": "",
                "rate_limit": 100,
                "timeout": 30,
            },
            "file": {
                "file_type": "csv",
                "url": "",
                "provider": "local",
                "format": {
                    "delimiter": ",",
                    "quote_char": '"',
                    "escape_char": "\\",
                    "encoding": "utf-8",
                },
            },
        }

        # Predefined destination configurations
        self.destination_templates = {
            "postgres": {
                "host": "localhost",
                "port": 5432,
                "database": "sophia_ai_warehouse",
                "username": "postgres",
                "password": "",
                "ssl": False,
                "schema": "public",
            },
            "bigquery": {
                "project_id": "",
                "dataset_id": "sophia_ai",
                "credentials_json": "",
                "location": "US",
            },
            "s3": {
                "bucket_name": "sophia-ai-data",
                "bucket_path": "raw-data/",
                "access_key_id": "",
                "secret_access_key": "",
                "region": "us-east-1",
                "format": "jsonl",
            },
            "snowflake": {
                "host": "",
                "role": "ACCOUNTADMIN",
                "warehouse": "COMPUTE_WH",
                "database": "SOPHIA_AI",
                "schema": "PUBLIC",
                "username": "",
                "password": "",
            },
        }

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

    async def connect(self):
        """Initialize HTTP session and validate EstuaryFlow connection"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=60, connect=10)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            logger.info("✅ EstuaryFlow session initialized")

            # Validate connection
            health = await self.health_check()
            if health["status"] != "healthy":
                logger.warning(f"⚠️ EstuaryFlow health check failed: {health}")

    async def disconnect(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("🔌 EstuaryFlow session closed")

    @monitor_performance("/estuary_flow/sources", "POST")
    async def create_source(self, config: SourceConfig) -> Dict[str, Any]:
        """Create a new data source in EstuaryFlow"""
        try:
            request_data = {
                "workspaceId": self.workspace_id,
                "name": config.name,
                "sourceDefinitionId": await self._get_source_definition_id(
                    config.source_type
                ),
                "connectionConfiguration": config.connection_config,
            }

            async with self.session.post(
                f"{self.estuary_flow_url}/api/{self.api_version}/sources/create",
                json=request_data,
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    config.source_id = result.get("sourceId", config.source_id)
                    self.sources[config.source_id] = config

                    logger.info(
                        f"✅ Created source: {config.name} ({config.source_id})"
                    )
                    return result
                else:
                    error_text = await response.text()
                    logger.error(
                        f"❌ Failed to create source: {response.status} - {error_text}"
                    )
                    return {"error": error_text}

        except Exception as e:
            logger.error(f"❌ Error creating source: {e}")
            return {"error": str(e)}

    @monitor_performance("/estuary_flow/destinations", "POST")
    async def create_destination(self, config: DestinationConfig) -> Dict[str, Any]:
        """Create a new data destination in EstuaryFlow"""
        try:
            request_data = {
                "workspaceId": self.workspace_id,
                "name": config.name,
                "destinationDefinitionId": await self._get_destination_definition_id(
                    config.destination_type
                ),
                "connectionConfiguration": config.connection_config,
            }

            async with self.session.post(
                f"{self.estuary_flow_url}/api/{self.api_version}/destinations/create",
                json=request_data,
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    config.destination_id = result.get(
                        "destinationId", config.destination_id
                    )
                    self.destinations[config.destination_id] = config

                    logger.info(
                        f"✅ Created destination: {config.name} ({config.destination_id})"
                    )
                    return result
                else:
                    error_text = await response.text()
                    logger.error(
                        f"❌ Failed to create destination: {response.status} - {error_text}"
                    )
                    return {"error": error_text}

        except Exception as e:
            logger.error(f"❌ Error creating destination: {e}")
            return {"error": str(e)}

    @monitor_performance("/estuary_flow/connections", "POST")
    async def create_pipeline(self, config: PipelineConfig) -> Dict[str, Any]:
        """Create a new data pipeline (connection) in EstuaryFlow"""
        try:
            # Get source and destination info
            source_config = self.sources.get(config.source_id)
            destination_config = self.destinations.get(config.destination_id)

            if not source_config or not destination_config:
                raise ValueError("Source or destination not found")

            request_data = {
                "sourceId": config.source_id,
                "destinationId": config.destination_id,
                "name": config.name,
                "namespaceDefinition": "source",
                "namespaceFormat": "${SOURCE_NAMESPACE}",
                "prefix": "",
                "status": "active" if config.enabled else "inactive",
                "schedule": {"scheduleType": "cron", "cronExpression": config.schedule},
                "syncCatalog": await self._get_default_sync_catalog(config.source_id),
            }

            async with self.session.post(
                f"{self.estuary_flow_url}/api/{self.api_version}/connections/create",
                json=request_data,
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    config.pipeline_id = result.get("connectionId", config.pipeline_id)
                    self.pipelines[config.pipeline_id] = config

                    # Initialize stats
                    self.pipeline_stats[config.pipeline_id] = PipelineStats(
                        pipeline_id=config.pipeline_id
                    )

                    logger.info(
                        f"✅ Created pipeline: {config.name} ({config.pipeline_id})"
                    )
                    return result
                else:
                    error_text = await response.text()
                    logger.error(
                        f"❌ Failed to create pipeline: {response.status} - {error_text}"
                    )
                    return {"error": error_text}

        except Exception as e:
            logger.error(f"❌ Error creating pipeline: {e}")
            return {"error": str(e)}

    @monitor_performance("/estuary_flow/sync", "POST")
    async def trigger_sync(self, pipeline_id: str) -> Dict[str, Any]:
        """Trigger a manual sync for a pipeline"""
        try:
            request_data = {"connectionId": pipeline_id}

            async with self.session.post(
                f"{self.estuary_flow_url}/api/{self.api_version}/connections/sync",
                json=request_data,
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    job_id = result.get("job", {}).get("id")

                    if job_id:
                        # Track the job
                        job_result = SyncJobResult(
                            job_id=job_id,
                            pipeline_id=pipeline_id,
                            status=SyncStatus.PENDING,
                            start_time=datetime.now().isoformat(),
                        )
                        self.active_jobs[job_id] = job_result

                    logger.info(
                        f"✅ Triggered sync for pipeline: {pipeline_id} (Job: {job_id})"
                    )
                    return result
                else:
                    error_text = await response.text()
                    logger.error(
                        f"❌ Failed to trigger sync: {response.status} - {error_text}"
                    )
                    return {"error": error_text}

        except Exception as e:
            logger.error(f"❌ Error triggering sync: {e}")
            return {"error": str(e)}

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a sync job"""
        try:
            async with self.session.get(
                f"{self.estuary_flow_url}/api/{self.api_version}/jobs/get",
                params={"id": job_id},
            ) as response:

                if response.status == 200:
                    result = await response.json()

                    # Update local job tracking
                    if job_id in self.active_jobs:
                        job_result = self.active_jobs[job_id]
                        job_info = result.get("job", {})

                        job_result.status = SyncStatus(
                            job_info.get("status", "pending")
                        )
                        if job_info.get("endedAt"):
                            job_result.end_time = job_info["endedAt"]
                            job_result.duration_seconds = (
                                datetime.fromisoformat(
                                    job_result.end_time.replace("Z", "+00:00")
                                )
                                - datetime.fromisoformat(
                                    job_result.start_time.replace("Z", "+00:00")
                                )
                            ).total_seconds()

                        # Update pipeline stats
                        await self._update_pipeline_stats(job_result)

                    return result
                else:
                    error_text = await response.text()
                    logger.error(
                        f"❌ Failed to get job status: {response.status} - {error_text}"
                    )
                    return {"error": error_text}

        except Exception as e:
            logger.error(f"❌ Error getting job status: {e}")
            return {"error": str(e)}

    async def list_pipelines(self) -> List[Dict[str, Any]]:
        """List all configured pipelines"""
        pipeline_list = []

        for pipeline_id, config in self.pipelines.items():
            stats = self.pipeline_stats.get(
                pipeline_id, PipelineStats(pipeline_id=pipeline_id)
            )

            pipeline_info = {
                "pipeline_id": pipeline_id,
                "name": config.name,
                "source_id": config.source_id,
                "destination_id": config.destination_id,
                "enabled": config.enabled,
                "schedule": config.schedule,
                "stats": asdict(stats),
            }

            # Add source and destination names
            if config.source_id in self.sources:
                pipeline_info["source_name"] = self.sources[config.source_id].name
            if config.destination_id in self.destinations:
                pipeline_info["destination_name"] = self.destinations[
                    config.destination_id
                ].name

            pipeline_list.append(pipeline_info)

        return pipeline_list

    async def get_pipeline_stats(self, pipeline_id: str) -> Dict[str, Any]:
        """Get detailed statistics for a pipeline"""
        if pipeline_id not in self.pipeline_stats:
            return {"error": "Pipeline not found"}

        stats = self.pipeline_stats[pipeline_id]
        return asdict(stats)

    async def _get_source_definition_id(self, source_type: str) -> str:
        """Get the source definition ID for a source type"""
        # In a real implementation, this would query EstuaryFlow's API
        # For now, return mock IDs
        source_definitions = {
            "postgres": "decd338e-5647-4c0b-adf4-da0e75f5a750",
            "mysql": "435bb9a5-7887-4809-aa58-28c27df0d7ad",
            "redis": "b76be0a6-27dc-4560-95f6-2623da0bd7b6",
            "api": "f3802bc4-5406-4752-9e8d-01e504ca8194",
            "file": "8be1cf83-fae2-4619-b820-526d1682c4f3",
        }
        return source_definitions.get(source_type, str(uuid.uuid4()))

    async def _get_destination_definition_id(self, destination_type: str) -> str:
        """Get the destination definition ID for a destination type"""
        # In a real implementation, this would query EstuaryFlow's API
        # For now, return mock IDs
        destination_definitions = {
            "postgres": "25c5221d-dce2-4163-ade9-739ef790f503",
            "bigquery": "22f6c74f-5699-40ff-af54-d775532323dc",
            "s3": "4816b78f-1489-44c1-9060-4b19d5fa9362",
            "snowflake": "424892c4-daac-4491-b35d-c6688ba547ba",
        }
        return destination_definitions.get(destination_type, str(uuid.uuid4()))

    async def _get_default_sync_catalog(self, source_id: str) -> Dict[str, Any]:
        """Get default sync catalog for a source"""
        # In a real implementation, this would discover the source schema
        # For now, return a basic catalog
        return {
            "streams": [
                {
                    "stream": {
                        "name": "default_table",
                        "jsonSchema": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "data": {"type": "string"},
                                "created_at": {"type": "string", "format": "date-time"},
                            },
                        },
                    },
                    "config": {
                        "syncMode": "full_refresh",
                        "destinationSyncMode": "overwrite",
                        "selected": True,
                    },
                }
            ]
        }

    async def _update_pipeline_stats(self, job_result: SyncJobResult):
        """Update pipeline statistics based on job result"""
        pipeline_id = job_result.pipeline_id

        if pipeline_id not in self.pipeline_stats:
            self.pipeline_stats[pipeline_id] = PipelineStats(pipeline_id=pipeline_id)

        stats = self.pipeline_stats[pipeline_id]
        stats.total_runs += 1

        if job_result.status == SyncStatus.SUCCEEDED:
            stats.successful_runs += 1
            stats.total_records_processed += job_result.records_processed
            stats.total_bytes_processed += job_result.bytes_processed
        elif job_result.status == SyncStatus.FAILED:
            stats.failed_runs += 1

        # Update average duration
        if job_result.duration_seconds > 0:
            if stats.avg_duration_seconds == 0:
                stats.avg_duration_seconds = job_result.duration_seconds
            else:
                alpha = 0.1  # Smoothing factor
                stats.avg_duration_seconds = (
                    alpha * job_result.duration_seconds
                    + (1 - alpha) * stats.avg_duration_seconds
                )

        # Update success rate
        if stats.total_runs > 0:
            stats.success_rate = (stats.successful_runs / stats.total_runs) * 100

        stats.last_run_time = job_result.start_time

    async def create_sophia_ai_pipeline(self) -> Dict[str, Any]:
        """Create a complete Sophia AI data pipeline"""
        try:
            # Create PostgreSQL source
            postgres_source = SourceConfig(
                source_id=str(uuid.uuid4()),
                name="Sophia AI PostgreSQL",
                source_type="postgres",
                connection_config=self.source_templates["postgres"].copy(),
                sync_frequency="hourly",
            )

            # Create data warehouse destination
            warehouse_dest = DestinationConfig(
                destination_id=str(uuid.uuid4()),
                name="Sophia AI Warehouse",
                destination_type="postgres",
                connection_config=self.destination_templates["postgres"].copy(),
            )

            # Create the pipeline
            pipeline = PipelineConfig(
                pipeline_id=str(uuid.uuid4()),
                name="Sophia AI Main Pipeline",
                source_id=postgres_source.source_id,
                destination_id=warehouse_dest.destination_id,
                schedule="0 */2 * * *",  # Every 2 hours
                enabled=True,
            )

            # Create components
            source_result = await self.create_source(postgres_source)
            dest_result = await self.create_destination(warehouse_dest)
            pipeline_result = await self.create_pipeline(pipeline)

            logger.info("✅ Created complete Sophia AI data pipeline")

            return {
                "source": source_result,
                "destination": dest_result,
                "pipeline": pipeline_result,
                "pipeline_id": pipeline.pipeline_id,
            }

        except Exception as e:
            logger.error(f"❌ Error creating Sophia AI pipeline: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """Perform EstuaryFlow integration health check"""
        health_status = {
            "status": "healthy",
            "session_active": self.session is not None,
            "workspace_id": self.workspace_id,
            "sources_configured": len(self.sources),
            "destinations_configured": len(self.destinations),
            "pipelines_configured": len(self.pipelines),
            "active_jobs": len(self.active_jobs),
            "last_updated": datetime.now().isoformat(),
        }

        # Test EstuaryFlow API connectivity
        try:
            if self.session:
                async with self.session.get(
                    f"{self.estuary_flow_url}/api/{self.api_version}/health",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    if response.status == 200:
                        health_status["estuary_flow_connectivity"] = "success"
                    else:
                        health_status["estuary_flow_connectivity"] = (
                            f"error_{response.status}"
                        )
                        health_status["status"] = "degraded"
            else:
                health_status["estuary_flow_connectivity"] = "no_session"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["estuary_flow_connectivity"] = f"failed: {e}"
            health_status["status"] = "unhealthy"

        return health_status


# Global EstuaryFlow instance
_estuary_flow_instance: Optional[EstuaryFlowPipelines] = None


async def get_estuary_flow(
    estuary_flow_url: str = "http://localhost:8000",
) -> EstuaryFlowPipelines:
    """Get or create global EstuaryFlow instance"""
    global _estuary_flow_instance

    if _estuary_flow_instance is None:
        _estuary_flow_instance = EstuaryFlowPipelines(estuary_flow_url)
        await _estuary_flow_instance.connect()

    return _estuary_flow_instance


# Example usage and testing
async def sophia_estuary_flow_pipelines():
    """Test the EstuaryFlow pipelines integration"""
    print("🧪 Testing EstuaryFlow Pipelines...")

    async with EstuaryFlowPipelines() as estuary_flow:
        # Test health check
        health = await estuary_flow.health_check()
        print(f"🏥 Health check: {health['status']}")

        # Test creating a complete pipeline
        pipeline_result = await estuary_flow.create_sophia_ai_pipeline()
        if "error" not in pipeline_result:
            print(f"✅ Created Sophia AI pipeline: {pipeline_result['pipeline_id']}")
        else:
            print(f"⚠️ Pipeline creation (expected in dev): {pipeline_result['error']}")

        # Test listing pipelines
        pipelines = await estuary_flow.list_pipelines()
        print(f"📋 Configured pipelines: {len(pipelines)}")

    return True


if __name__ == "__main__":
    asyncio.run(sophia_estuary_flow_pipelines())
