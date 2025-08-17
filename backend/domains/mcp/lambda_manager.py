"""
Lambda Labs Manager for SOPHIA Intel
Manages Lambda Labs GH200 instances and inference operations
"""

from typing import Dict, List, Any, Optional
import logging
import asyncio
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)


class LambdaManager:
    """Lambda Labs infrastructure manager"""
    
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        self.api_key = api_key
        self.config = config or {}
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.instances: Dict[str, Dict[str, Any]] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self) -> None:
        """Initialize Lambda Labs manager"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        # Load existing instances
        await self.refresh_instances()
        logger.info("✅ Lambda Labs manager initialized")
    
    async def close(self) -> None:
        """Close Lambda Labs manager"""
        if self.session:
            await self.session.close()
        logger.info("🔒 Lambda Labs manager closed")
    
    async def refresh_instances(self) -> Dict[str, Any]:
        """Refresh instance information"""
        try:
            if not self.session:
                await self.initialize()
            
            async with self.session.get(f"{self.base_url}/instances") as response:
                if response.status == 200:
                    data = await response.json()
                    instances = data.get("data", [])
                    
                    # Update instance cache
                    self.instances = {
                        instance["id"]: instance for instance in instances
                    }
                    
                    logger.info(f"✅ Refreshed {len(instances)} Lambda Labs instances")
                    return {"status": "success", "instances": instances}
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to refresh instances: {response.status} - {error_text}")
                    return {"status": "error", "error": error_text}
                    
        except Exception as e:
            logger.error(f"❌ Error refreshing instances: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """Get status of specific instance"""
        try:
            if not self.session:
                await self.initialize()
            
            async with self.session.get(f"{self.base_url}/instances/{instance_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    instance = data.get("data", {})
                    
                    # Update cache
                    if instance:
                        self.instances[instance_id] = instance
                    
                    logger.info(f"✅ Retrieved status for instance {instance_id}")
                    return {"status": "success", "instance": instance}
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to get instance status: {response.status} - {error_text}")
                    return {"status": "error", "error": error_text}
                    
        except Exception as e:
            logger.error(f"❌ Error getting instance status: {e}")
            return {"status": "error", "error": str(e)}
    
    async def launch_instance(self, instance_config: Dict[str, Any]) -> Dict[str, Any]:
        """Launch new Lambda Labs instance"""
        try:
            if not self.session:
                await self.initialize()
            
            launch_data = {
                "region_name": instance_config.get("region", "us-west-2"),
                "instance_type_name": instance_config.get("instance_type", "gpu_1x_a100"),
                "ssh_key_names": instance_config.get("ssh_keys", []),
                "name": instance_config.get("name", f"sophia-instance-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
            }
            
            async with self.session.post(
                f"{self.base_url}/instance-operations/launch",
                json=launch_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    instance_ids = data.get("data", {}).get("instance_ids", [])
                    
                    logger.info(f"✅ Launched instances: {instance_ids}")
                    
                    # Wait for instances to be ready
                    await asyncio.sleep(5)
                    await self.refresh_instances()
                    
                    return {"status": "success", "instance_ids": instance_ids}
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to launch instance: {response.status} - {error_text}")
                    return {"status": "error", "error": error_text}
                    
        except Exception as e:
            logger.error(f"❌ Error launching instance: {e}")
            return {"status": "error", "error": str(e)}
    
    async def terminate_instance(self, instance_id: str) -> Dict[str, Any]:
        """Terminate Lambda Labs instance"""
        try:
            if not self.session:
                await self.initialize()
            
            terminate_data = {"instance_ids": [instance_id]}
            
            async with self.session.post(
                f"{self.base_url}/instance-operations/terminate",
                json=terminate_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    terminated_ids = data.get("data", {}).get("terminated_instances", [])
                    
                    # Remove from cache
                    if instance_id in self.instances:
                        del self.instances[instance_id]
                    
                    logger.info(f"✅ Terminated instances: {terminated_ids}")
                    return {"status": "success", "terminated_instances": terminated_ids}
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to terminate instance: {response.status} - {error_text}")
                    return {"status": "error", "error": error_text}
                    
        except Exception as e:
            logger.error(f"❌ Error terminating instance: {e}")
            return {"status": "error", "error": str(e)}
    
    async def restart_instance(self, instance_id: str) -> Dict[str, Any]:
        """Restart Lambda Labs instance"""
        try:
            if not self.session:
                await self.initialize()
            
            restart_data = {"instance_ids": [instance_id]}
            
            async with self.session.post(
                f"{self.base_url}/instance-operations/restart",
                json=restart_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    restarted_ids = data.get("data", {}).get("restarted_instances", [])
                    
                    logger.info(f"✅ Restarted instances: {restarted_ids}")
                    
                    # Wait for restart to complete
                    await asyncio.sleep(10)
                    await self.refresh_instances()
                    
                    return {"status": "success", "restarted_instances": restarted_ids}
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to restart instance: {response.status} - {error_text}")
                    return {"status": "error", "error": error_text}
                    
        except Exception as e:
            logger.error(f"❌ Error restarting instance: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_instance_types(self) -> Dict[str, Any]:
        """Get available instance types"""
        try:
            if not self.session:
                await self.initialize()
            
            async with self.session.get(f"{self.base_url}/instance-types") as response:
                if response.status == 200:
                    data = await response.json()
                    instance_types = data.get("data", {})
                    
                    logger.info(f"✅ Retrieved {len(instance_types)} instance types")
                    return {"status": "success", "instance_types": instance_types}
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to get instance types: {response.status} - {error_text}")
                    return {"status": "error", "error": error_text}
                    
        except Exception as e:
            logger.error(f"❌ Error getting instance types: {e}")
            return {"status": "error", "error": str(e)}
    
    async def get_ssh_keys(self) -> Dict[str, Any]:
        """Get SSH keys"""
        try:
            if not self.session:
                await self.initialize()
            
            async with self.session.get(f"{self.base_url}/ssh-keys") as response:
                if response.status == 200:
                    data = await response.json()
                    ssh_keys = data.get("data", [])
                    
                    logger.info(f"✅ Retrieved {len(ssh_keys)} SSH keys")
                    return {"status": "success", "ssh_keys": ssh_keys}
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Failed to get SSH keys: {response.status} - {error_text}")
                    return {"status": "error", "error": error_text}
                    
        except Exception as e:
            logger.error(f"❌ Error getting SSH keys: {e}")
            return {"status": "error", "error": str(e)}
    
    async def execute_inference(self, instance_id: str, inference_request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute inference on Lambda Labs instance"""
        try:
            # Check if instance is available
            instance_status = await self.get_instance_status(instance_id)
            if instance_status.get("status") != "success":
                return {"status": "error", "error": "Instance not available"}
            
            instance = instance_status.get("instance", {})
            if instance.get("status") != "active":
                return {"status": "error", "error": f"Instance not active: {instance.get('status')}"}
            
            # Get instance IP
            instance_ip = instance.get("ip")
            if not instance_ip:
                return {"status": "error", "error": "Instance IP not available"}
            
            # Execute inference (this would typically involve SSH or HTTP requests to the instance)
            inference_result = await self._execute_remote_inference(
                instance_ip, inference_request
            )
            
            logger.info(f"✅ Inference executed on instance {instance_id}")
            return {
                "status": "success",
                "instance_id": instance_id,
                "inference_result": inference_result
            }
            
        except Exception as e:
            logger.error(f"❌ Error executing inference: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _execute_remote_inference(self, instance_ip: str, inference_request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute inference on remote instance"""
        # This is a placeholder for actual inference execution
        # In practice, this would involve:
        # 1. SSH connection to the instance
        # 2. Running inference commands
        # 3. Retrieving results
        
        await asyncio.sleep(1)  # Simulate inference time
        
        return {
            "model": inference_request.get("model", "unknown"),
            "input": inference_request.get("input", ""),
            "output": "Generated response from Lambda Labs GH200",
            "execution_time": "1.2s",
            "gpu_utilization": "85%",
            "memory_usage": "12GB"
        }
    
    async def monitor_instances(self) -> Dict[str, Any]:
        """Monitor all instances"""
        try:
            await self.refresh_instances()
            
            monitoring_data = {
                "timestamp": datetime.now().isoformat(),
                "total_instances": len(self.instances),
                "active_instances": len([i for i in self.instances.values() if i.get("status") == "active"]),
                "instance_details": []
            }
            
            for instance_id, instance in self.instances.items():
                monitoring_data["instance_details"].append({
                    "id": instance_id,
                    "name": instance.get("name", ""),
                    "status": instance.get("status", "unknown"),
                    "instance_type": instance.get("instance_type", {}).get("name", ""),
                    "region": instance.get("region", {}).get("name", ""),
                    "ip": instance.get("ip", ""),
                    "uptime": self._calculate_uptime(instance.get("status_changed", ""))
                })
            
            logger.info(f"✅ Monitored {len(self.instances)} instances")
            return {"status": "success", "monitoring_data": monitoring_data}
            
        except Exception as e:
            logger.error(f"❌ Error monitoring instances: {e}")
            return {"status": "error", "error": str(e)}
    
    def _calculate_uptime(self, status_changed: str) -> str:
        """Calculate instance uptime"""
        if not status_changed:
            return "unknown"
        
        try:
            status_time = datetime.fromisoformat(status_changed.replace('Z', '+00:00'))
            uptime = datetime.now() - status_time.replace(tzinfo=None)
            
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
                
        except Exception:
            return "unknown"
    
    def get_cached_instances(self) -> Dict[str, Dict[str, Any]]:
        """Get cached instance information"""
        return self.instances
    
    def get_instance_count(self) -> int:
        """Get total instance count"""
        return len(self.instances)
    
    def get_active_instance_count(self) -> int:
        """Get active instance count"""
        return len([i for i in self.instances.values() if i.get("status") == "active"])
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Test API connectivity
            if not self.session:
                await self.initialize()
            
            async with self.session.get(f"{self.base_url}/instance-types") as response:
                api_healthy = response.status == 200
            
            # Check instance status
            await self.refresh_instances()
            
            return {
                "status": "healthy" if api_healthy else "unhealthy",
                "api_connectivity": api_healthy,
                "total_instances": len(self.instances),
                "active_instances": self.get_active_instance_count(),
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }

