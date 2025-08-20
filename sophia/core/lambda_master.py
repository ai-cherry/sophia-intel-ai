"""
SOPHIA Lambda Master
Manages Lambda Labs GPU instances for compute-intensive AI tasks.
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import aiohttp
import json

logger = logging.getLogger(__name__)

@dataclass
class LambdaInstance:
    """Lambda Labs instance information."""
    id: str
    name: str
    instance_type: str
    region: str
    status: str
    ip: Optional[str] = None
    ssh_key_names: Optional[List[str]] = None
    file_system_names: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    terminated_at: Optional[datetime] = None

@dataclass
class LambdaInstanceType:
    """Lambda Labs instance type information."""
    name: str
    price_cents_per_hour: int
    description: str
    specs: Dict[str, Any]

@dataclass
class LambdaJob:
    """Lambda Labs job specification."""
    name: str
    instance_type: str
    region: str
    ssh_key_names: List[str]
    file_system_names: Optional[List[str]] = None
    quantity: int = 1

class SOPHIALambdaMaster:
    """
    Lambda Labs GPU management for SOPHIA AI orchestrator.
    Provides autonomous GPU instance management for compute-intensive tasks.
    """
    
    def __init__(self):
        """Initialize Lambda master with API credentials."""
        self.api_key = os.getenv("LAMBDA_API_KEY")
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        
        if not self.api_key:
            logger.warning("LAMBDA_API_KEY not found in environment")
        
        # Track instances and costs
        self.active_instances: Dict[str, LambdaInstance] = {}
        self.total_cost_cents = 0
        
        logger.info("Initialized SOPHIALambdaMaster")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Lambda Labs API.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters
            
        Returns:
            API response data
            
        Raises:
            RuntimeError: If API request fails
        """
        if not self.api_key:
            raise RuntimeError("Lambda API key not configured")
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params
                ) as response:
                    response_data = await response.json()
                    
                    if response.status >= 400:
                        error_msg = response_data.get("error", {}).get("message", "Unknown error")
                        logger.error(f"Lambda API error: {response.status} - {error_msg}")
                        raise RuntimeError(f"Lambda API error: {error_msg}")
                    
                    logger.debug(f"Lambda API {method} {endpoint}: {response.status}")
                    return response_data
                    
        except aiohttp.ClientError as e:
            logger.error(f"Lambda API request failed: {e}")
            raise RuntimeError(f"Lambda API request failed: {e}")
    
    async def list_instance_types(self) -> List[LambdaInstanceType]:
        """
        List available Lambda Labs instance types.
        
        Returns:
            List of available instance types
        """
        try:
            response = await self._make_request("GET", "/instance-types")
            
            instance_types = []
            for item in response.get("data", []):
                instance_type = LambdaInstanceType(
                    name=item["name"],
                    price_cents_per_hour=item["price_cents_per_hour"],
                    description=item.get("description", ""),
                    specs=item.get("specs", {})
                )
                instance_types.append(instance_type)
            
            logger.info(f"Retrieved {len(instance_types)} Lambda instance types")
            return instance_types
            
        except Exception as e:
            logger.error(f"Failed to list Lambda instance types: {e}")
            raise
    
    async def list_regions(self) -> List[str]:
        """
        List available Lambda Labs regions.
        
        Returns:
            List of available regions
        """
        try:
            response = await self._make_request("GET", "/regions")
            
            regions = [region["name"] for region in response.get("data", [])]
            logger.info(f"Retrieved {len(regions)} Lambda regions: {regions}")
            return regions
            
        except Exception as e:
            logger.error(f"Failed to list Lambda regions: {e}")
            raise
    
    async def list_ssh_keys(self) -> List[Dict[str, str]]:
        """
        List available SSH keys.
        
        Returns:
            List of SSH key information
        """
        try:
            response = await self._make_request("GET", "/ssh-keys")
            
            ssh_keys = response.get("data", [])
            logger.info(f"Retrieved {len(ssh_keys)} SSH keys")
            return ssh_keys
            
        except Exception as e:
            logger.error(f"Failed to list SSH keys: {e}")
            raise
    
    async def spin_up_gpu(
        self,
        instance_type: str,
        region: str,
        name: Optional[str] = None,
        ssh_key_names: Optional[List[str]] = None,
        file_system_names: Optional[List[str]] = None,
        quantity: int = 1
    ) -> List[LambdaInstance]:
        """
        Spin up GPU instances on Lambda Labs.
        
        Args:
            instance_type: Instance type (e.g., 'gpu_1x_a100')
            region: Region to launch in (e.g., 'us-west-1')
            name: Optional instance name
            ssh_key_names: SSH key names for access
            file_system_names: File system names to attach
            quantity: Number of instances to launch
            
        Returns:
            List of created instances
            
        Raises:
            RuntimeError: If instance creation fails
        """
        try:
            # Use default SSH keys if none provided
            if ssh_key_names is None:
                ssh_keys = await self.list_ssh_keys()
                if ssh_keys:
                    ssh_key_names = [ssh_keys[0]["name"]]
                else:
                    logger.warning("No SSH keys available - instance may not be accessible")
                    ssh_key_names = []
            
            # Generate name if not provided
            if name is None:
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                name = f"sophia-gpu-{timestamp}"
            
            launch_data = {
                "region_name": region,
                "instance_type_name": instance_type,
                "ssh_key_names": ssh_key_names,
                "quantity": quantity,
                "name": name
            }
            
            if file_system_names:
                launch_data["file_system_names"] = file_system_names
            
            logger.info(f"Launching {quantity}x {instance_type} in {region}")
            response = await self._make_request("POST", "/instance-operations/launch", data=launch_data)
            
            # Parse response and create instance objects
            instances = []
            for instance_data in response.get("data", {}).get("instance_ids", []):
                instance = LambdaInstance(
                    id=instance_data,
                    name=name,
                    instance_type=instance_type,
                    region=region,
                    status="booting",
                    ssh_key_names=ssh_key_names,
                    file_system_names=file_system_names,
                    created_at=datetime.now(timezone.utc)
                )
                instances.append(instance)
                self.active_instances[instance.id] = instance
            
            logger.info(f"Successfully launched {len(instances)} instances")
            
            # Log cost tracking
            instance_types = await self.list_instance_types()
            cost_per_hour = next(
                (it.price_cents_per_hour for it in instance_types if it.name == instance_type),
                0
            )
            estimated_cost = cost_per_hour * quantity
            logger.info(f"Estimated cost: {estimated_cost} cents/hour for {quantity} instances")
            
            return instances
            
        except Exception as e:
            logger.error(f"Failed to spin up GPU instances: {e}")
            raise RuntimeError(f"Failed to spin up GPU instances: {e}")
    
    async def list_instances(self) -> List[LambdaInstance]:
        """
        List all Lambda Labs instances.
        
        Returns:
            List of instances
        """
        try:
            response = await self._make_request("GET", "/instances")
            
            instances = []
            for item in response.get("data", []):
                instance = LambdaInstance(
                    id=item["id"],
                    name=item.get("name", ""),
                    instance_type=item["instance_type"]["name"],
                    region=item["region"]["name"],
                    status=item["status"],
                    ip=item.get("ip"),
                    ssh_key_names=[key["name"] for key in item.get("ssh_key_names", [])],
                    file_system_names=[fs["name"] for fs in item.get("file_system_names", [])]
                )
                instances.append(instance)
                
                # Update active instances tracking
                if instance.status in ["active", "booting"]:
                    self.active_instances[instance.id] = instance
                elif instance.id in self.active_instances:
                    del self.active_instances[instance.id]
            
            logger.info(f"Retrieved {len(instances)} Lambda instances")
            return instances
            
        except Exception as e:
            logger.error(f"Failed to list Lambda instances: {e}")
            raise
    
    async def get_instance(self, instance_id: str) -> Optional[LambdaInstance]:
        """
        Get specific instance details.
        
        Args:
            instance_id: Instance ID
            
        Returns:
            Instance details or None if not found
        """
        try:
            response = await self._make_request("GET", f"/instances/{instance_id}")
            
            item = response.get("data", {})
            if not item:
                return None
            
            instance = LambdaInstance(
                id=item["id"],
                name=item.get("name", ""),
                instance_type=item["instance_type"]["name"],
                region=item["region"]["name"],
                status=item["status"],
                ip=item.get("ip"),
                ssh_key_names=[key["name"] for key in item.get("ssh_key_names", [])],
                file_system_names=[fs["name"] for fs in item.get("file_system_names", [])]
            )
            
            logger.info(f"Retrieved instance {instance_id}: {instance.status}")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to get instance {instance_id}: {e}")
            return None
    
    async def run_job(self, job_spec: LambdaJob) -> List[LambdaInstance]:
        """
        Run a job on Lambda Labs instances.
        
        Args:
            job_spec: Job specification
            
        Returns:
            List of instances running the job
        """
        try:
            logger.info(f"Running job: {job_spec.name}")
            
            instances = await self.spin_up_gpu(
                instance_type=job_spec.instance_type,
                region=job_spec.region,
                name=job_spec.name,
                ssh_key_names=job_spec.ssh_key_names,
                file_system_names=job_spec.file_system_names,
                quantity=job_spec.quantity
            )
            
            # Wait for instances to be active
            logger.info("Waiting for instances to become active...")
            await self._wait_for_instances_active([instance.id for instance in instances])
            
            logger.info(f"Job {job_spec.name} running on {len(instances)} instances")
            return instances
            
        except Exception as e:
            logger.error(f"Failed to run job {job_spec.name}: {e}")
            raise
    
    async def tear_down(self, instance_id: str) -> bool:
        """
        Terminate a Lambda Labs instance.
        
        Args:
            instance_id: Instance ID to terminate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Terminating instance {instance_id}")
            
            await self._make_request("POST", "/instance-operations/terminate", data={
                "instance_ids": [instance_id]
            })
            
            # Remove from active instances
            if instance_id in self.active_instances:
                instance = self.active_instances[instance_id]
                instance.status = "terminated"
                instance.terminated_at = datetime.now(timezone.utc)
                del self.active_instances[instance_id]
            
            logger.info(f"Successfully terminated instance {instance_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to terminate instance {instance_id}: {e}")
            return False
    
    async def tear_down_all(self) -> int:
        """
        Terminate all active instances.
        
        Returns:
            Number of instances terminated
        """
        try:
            if not self.active_instances:
                logger.info("No active instances to terminate")
                return 0
            
            instance_ids = list(self.active_instances.keys())
            logger.info(f"Terminating {len(instance_ids)} active instances")
            
            await self._make_request("POST", "/instance-operations/terminate", data={
                "instance_ids": instance_ids
            })
            
            # Update instance statuses
            for instance_id in instance_ids:
                if instance_id in self.active_instances:
                    instance = self.active_instances[instance_id]
                    instance.status = "terminated"
                    instance.terminated_at = datetime.now(timezone.utc)
            
            terminated_count = len(instance_ids)
            self.active_instances.clear()
            
            logger.info(f"Successfully terminated {terminated_count} instances")
            return terminated_count
            
        except Exception as e:
            logger.error(f"Failed to terminate all instances: {e}")
            raise
    
    async def _wait_for_instances_active(
        self,
        instance_ids: List[str],
        timeout_seconds: int = 300,
        poll_interval: int = 10
    ):
        """
        Wait for instances to become active.
        
        Args:
            instance_ids: List of instance IDs to wait for
            timeout_seconds: Maximum time to wait
            poll_interval: Seconds between status checks
        """
        start_time = datetime.now()
        
        while True:
            # Check if timeout exceeded
            if (datetime.now() - start_time).total_seconds() > timeout_seconds:
                raise RuntimeError(f"Timeout waiting for instances to become active")
            
            # Check instance statuses
            all_active = True
            for instance_id in instance_ids:
                instance = await self.get_instance(instance_id)
                if not instance or instance.status != "active":
                    all_active = False
                    break
            
            if all_active:
                logger.info("All instances are now active")
                return
            
            logger.info(f"Waiting for instances to become active... ({poll_interval}s)")
            await asyncio.sleep(poll_interval)
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get cost summary for active instances.
        
        Returns:
            Cost summary information
        """
        summary = {
            "active_instances": len(self.active_instances),
            "total_estimated_cost_cents_per_hour": 0,
            "instances": []
        }
        
        for instance in self.active_instances.values():
            instance_info = {
                "id": instance.id,
                "name": instance.name,
                "instance_type": instance.instance_type,
                "region": instance.region,
                "status": instance.status,
                "created_at": instance.created_at.isoformat() if instance.created_at else None
            }
            summary["instances"].append(instance_info)
        
        return summary
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of Lambda master and instances.
        
        Returns:
            Health status information
        """
        try:
            # Test API connectivity
            await self.list_regions()
            
            # Get active instances
            instances = await self.list_instances()
            active_count = len([i for i in instances if i.status == "active"])
            
            return {
                "status": "healthy",
                "api_connected": True,
                "total_instances": len(instances),
                "active_instances": active_count,
                "cost_summary": self.get_cost_summary(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Lambda health check failed: {e}")
            return {
                "status": "unhealthy",
                "api_connected": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def close(self):
        """Clean up resources."""
        try:
            # Optionally terminate all instances on cleanup
            # Uncomment if you want automatic cleanup
            # await self.tear_down_all()
            
            logger.info("Lambda master cleanup completed")
            
        except Exception as e:
            logger.error(f"Lambda master cleanup failed: {e}")

# Example usage and job specifications
EXAMPLE_JOBS = {
    "training_job": LambdaJob(
        name="sophia-model-training",
        instance_type="gpu_1x_a100",
        region="us-west-1",
        ssh_key_names=["sophia-key"],
        quantity=1
    ),
    "inference_job": LambdaJob(
        name="sophia-inference-cluster",
        instance_type="gpu_1x_rtx6000",
        region="us-east-1",
        ssh_key_names=["sophia-key"],
        quantity=2
    ),
    "research_job": LambdaJob(
        name="sophia-research-compute",
        instance_type="gpu_8x_a100",
        region="us-west-1",
        ssh_key_names=["sophia-key"],
        file_system_names=["sophia-datasets"],
        quantity=1
    )
}

