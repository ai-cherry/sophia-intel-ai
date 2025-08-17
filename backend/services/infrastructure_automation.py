"""
Infrastructure Automation Service for SOPHIA Intel
Complete IaC automation with Lambda Labs, Qdrant, GitHub, and Pulumi integration
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import aiohttp
import subprocess
from pathlib import Path

from .circuit_breaker import get_circuit_breaker, CircuitBreakerConfig

logger = logging.getLogger(__name__)

class InfrastructureOperation(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SCALE = "scale"
    BACKUP = "backup"
    RESTORE = "restore"
    MONITOR = "monitor"

@dataclass
class InfrastructureRequest:
    """Infrastructure automation request"""
    operation: InfrastructureOperation
    service: str  # lambda_labs, qdrant, github, pulumi
    resource_type: str  # instance, collection, repository, stack
    parameters: Dict[str, Any]
    user_id: str
    correlation_id: str

@dataclass
class InfrastructureResult:
    """Infrastructure operation result"""
    success: bool
    resource_id: Optional[str] = None
    details: Dict[str, Any] = None
    error: Optional[str] = None
    duration: float = 0.0
    cost_impact: Optional[float] = None

class LambdaLabsAutomation:
    """Lambda Labs infrastructure automation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.circuit_breaker = get_circuit_breaker("lambda_labs_automation", CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=60,
            success_threshold=2,
            timeout=30.0
        ))
    
    async def create_instance(self, instance_type: str, region: str, name: str, ssh_key_names: List[str]) -> InfrastructureResult:
        """Create new Lambda Labs instance"""
        async def _create():
            async with aiohttp.ClientSession() as session:
                payload = {
                    "region_name": region,
                    "instance_type_name": instance_type,
                    "ssh_key_names": ssh_key_names,
                    "name": name
                }
                
                async with session.post(
                    f"{self.base_url}/instance-operations/launch",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return InfrastructureResult(
                            success=True,
                            resource_id=data["data"]["instance_ids"][0],
                            details=data["data"],
                            cost_impact=self._calculate_instance_cost(instance_type)
                        )
                    else:
                        error_data = await response.json()
                        return InfrastructureResult(
                            success=False,
                            error=error_data.get("error", {}).get("message", "Unknown error")
                        )
        
        start_time = time.time()
        try:
            result = await self.circuit_breaker.call(_create)
            result.duration = time.time() - start_time
            logger.info(f"Lambda Labs instance created: {name} ({result.resource_id})")
            return result
        except Exception as e:
            logger.error(f"Failed to create Lambda Labs instance: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )
    
    async def terminate_instance(self, instance_id: str) -> InfrastructureResult:
        """Terminate Lambda Labs instance"""
        async def _terminate():
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/instance-operations/terminate",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"instance_ids": [instance_id]}
                ) as response:
                    if response.status == 200:
                        return InfrastructureResult(success=True, resource_id=instance_id)
                    else:
                        error_data = await response.json()
                        return InfrastructureResult(
                            success=False,
                            error=error_data.get("error", {}).get("message", "Unknown error")
                        )
        
        start_time = time.time()
        try:
            result = await self.circuit_breaker.call(_terminate)
            result.duration = time.time() - start_time
            logger.info(f"Lambda Labs instance terminated: {instance_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to terminate Lambda Labs instance: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )
    
    async def list_instances(self) -> List[Dict[str, Any]]:
        """List all Lambda Labs instances"""
        async def _list():
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/instances",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["data"]
                    else:
                        raise Exception(f"Failed to list instances: {response.status}")
        
        try:
            return await self.circuit_breaker.call(_list)
        except Exception as e:
            logger.error(f"Failed to list Lambda Labs instances: {e}")
            return []
    
    async def auto_scale_decision(self, metrics: Dict[str, Any]) -> Optional[InfrastructureRequest]:
        """AI-powered auto-scaling decision"""
        # Analyze metrics and decide if scaling is needed
        cpu_usage = metrics.get("cpu_usage", 0)
        gpu_usage = metrics.get("gpu_usage", 0)
        queue_length = metrics.get("queue_length", 0)
        
        # Scale up conditions
        if (cpu_usage > 80 or gpu_usage > 85 or queue_length > 10):
            return InfrastructureRequest(
                operation=InfrastructureOperation.CREATE,
                service="lambda_labs",
                resource_type="instance",
                parameters={
                    "instance_type": "gpu_1x_a100_sxm4",
                    "region": "us-east-1",
                    "name": f"sophia-auto-scale-{int(time.time())}",
                    "ssh_key_names": ["sophia-production-key"]
                },
                user_id="system",
                correlation_id=f"autoscale-{int(time.time())}"
            )
        
        # Scale down conditions (implement logic to identify idle instances)
        # This would require more sophisticated monitoring
        
        return None
    
    def _calculate_instance_cost(self, instance_type: str) -> float:
        """Calculate estimated hourly cost for instance type"""
        cost_map = {
            "gpu_1x_a100_sxm4": 1.10,
            "gpu_1x_h100_pcie": 2.49,
            "gpu_1x_gh200": 3.50,
            "gpu_8x_a100_sxm4": 8.80,
            "gpu_8x_h100_sxm4": 19.92
        }
        return cost_map.get(instance_type, 0.0)

class QdrantAutomation:
    """Qdrant cluster automation"""
    
    def __init__(self, url: str, api_key: Optional[str] = None):
        self.url = url
        self.api_key = api_key
        self.circuit_breaker = get_circuit_breaker("qdrant_automation", CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,
            success_threshold=2,
            timeout=15.0
        ))
    
    async def create_collection(self, collection_name: str, vector_config: Dict[str, Any]) -> InfrastructureResult:
        """Create Qdrant collection"""
        async def _create():
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["api-key"] = self.api_key
            
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    f"{self.url}/collections/{collection_name}",
                    headers=headers,
                    json=vector_config
                ) as response:
                    if response.status in [200, 201]:
                        return InfrastructureResult(
                            success=True,
                            resource_id=collection_name,
                            details={"collection_name": collection_name, "config": vector_config}
                        )
                    else:
                        error_data = await response.text()
                        return InfrastructureResult(
                            success=False,
                            error=f"Failed to create collection: {error_data}"
                        )
        
        start_time = time.time()
        try:
            result = await self.circuit_breaker.call(_create)
            result.duration = time.time() - start_time
            logger.info(f"Qdrant collection created: {collection_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to create Qdrant collection: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )
    
    async def optimize_collection(self, collection_name: str) -> InfrastructureResult:
        """Optimize Qdrant collection performance"""
        async def _optimize():
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["api-key"] = self.api_key
            
            async with aiohttp.ClientSession() as session:
                # Get collection info
                async with session.get(
                    f"{self.url}/collections/{collection_name}",
                    headers=headers
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Collection not found: {collection_name}")
                    
                    collection_info = await response.json()
                
                # Perform optimization operations
                optimizations = []
                
                # Create index if needed
                async with session.post(
                    f"{self.url}/collections/{collection_name}/index",
                    headers=headers,
                    json={"field_name": "payload", "field_schema": "keyword"}
                ) as response:
                    if response.status in [200, 201]:
                        optimizations.append("index_created")
                
                # Optimize vectors
                async with session.post(
                    f"{self.url}/collections/{collection_name}/cluster/optimize",
                    headers=headers
                ) as response:
                    if response.status in [200, 202]:
                        optimizations.append("vectors_optimized")
                
                return InfrastructureResult(
                    success=True,
                    resource_id=collection_name,
                    details={"optimizations": optimizations}
                )
        
        start_time = time.time()
        try:
            result = await self.circuit_breaker.call(_optimize)
            result.duration = time.time() - start_time
            logger.info(f"Qdrant collection optimized: {collection_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to optimize Qdrant collection: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )

class GitHubAutomation:
    """GitHub repository automation"""
    
    def __init__(self, token: str, org: str = "ai-cherry"):
        self.token = token
        self.org = org
        self.base_url = "https://api.github.com"
        self.circuit_breaker = get_circuit_breaker("github_automation", CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,
            success_threshold=2,
            timeout=15.0
        ))
    
    async def create_repository(self, name: str, description: str, private: bool = True) -> InfrastructureResult:
        """Create GitHub repository"""
        async def _create():
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            payload = {
                "name": name,
                "description": description,
                "private": private,
                "auto_init": True,
                "gitignore_template": "Python"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/orgs/{self.org}/repos",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 201:
                        data = await response.json()
                        return InfrastructureResult(
                            success=True,
                            resource_id=data["full_name"],
                            details=data
                        )
                    else:
                        error_data = await response.json()
                        return InfrastructureResult(
                            success=False,
                            error=error_data.get("message", "Unknown error")
                        )
        
        start_time = time.time()
        try:
            result = await self.circuit_breaker.call(_create)
            result.duration = time.time() - start_time
            logger.info(f"GitHub repository created: {name}")
            return result
        except Exception as e:
            logger.error(f"Failed to create GitHub repository: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )
    
    async def update_workflow(self, repo: str, workflow_file: str, content: str) -> InfrastructureResult:
        """Update GitHub Actions workflow"""
        async def _update():
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Get current file SHA
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/repos/{self.org}/{repo}/contents/.github/workflows/{workflow_file}",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        file_data = await response.json()
                        sha = file_data["sha"]
                    else:
                        sha = None
                
                # Update or create file
                payload = {
                    "message": f"Update workflow: {workflow_file}",
                    "content": content,
                    "branch": "main"
                }
                
                if sha:
                    payload["sha"] = sha
                
                async with session.put(
                    f"{self.base_url}/repos/{self.org}/{repo}/contents/.github/workflows/{workflow_file}",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        return InfrastructureResult(
                            success=True,
                            resource_id=f"{repo}/{workflow_file}",
                            details=data
                        )
                    else:
                        error_data = await response.json()
                        return InfrastructureResult(
                            success=False,
                            error=error_data.get("message", "Unknown error")
                        )
        
        start_time = time.time()
        try:
            result = await self.circuit_breaker.call(_update)
            result.duration = time.time() - start_time
            logger.info(f"GitHub workflow updated: {repo}/{workflow_file}")
            return result
        except Exception as e:
            logger.error(f"Failed to update GitHub workflow: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )

class PulumiAutomation:
    """Pulumi infrastructure automation"""
    
    def __init__(self, access_token: str, org: str = "scoobyjava-org"):
        self.access_token = access_token
        self.org = org
        self.circuit_breaker = get_circuit_breaker("pulumi_automation", CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=60,
            success_threshold=1,
            timeout=300.0  # 5 minutes for infrastructure operations
        ))
    
    async def deploy_stack(self, project: str, stack: str, config: Dict[str, Any]) -> InfrastructureResult:
        """Deploy Pulumi stack"""
        async def _deploy():
            # Set environment variables
            env = {
                "PULUMI_ACCESS_TOKEN": self.access_token,
                **config.get("env", {})
            }
            
            # Run pulumi up
            cmd = [
                "pulumi", "up", "--yes", "--non-interactive",
                "--stack", f"{self.org}/{project}/{stack}"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return InfrastructureResult(
                    success=True,
                    resource_id=f"{project}/{stack}",
                    details={
                        "stdout": stdout.decode(),
                        "stderr": stderr.decode()
                    }
                )
            else:
                return InfrastructureResult(
                    success=False,
                    error=f"Pulumi deployment failed: {stderr.decode()}"
                )
        
        start_time = time.time()
        try:
            result = await self.circuit_breaker.call(_deploy)
            result.duration = time.time() - start_time
            logger.info(f"Pulumi stack deployed: {project}/{stack}")
            return result
        except Exception as e:
            logger.error(f"Failed to deploy Pulumi stack: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )
    
    async def destroy_stack(self, project: str, stack: str) -> InfrastructureResult:
        """Destroy Pulumi stack"""
        async def _destroy():
            env = {"PULUMI_ACCESS_TOKEN": self.access_token}
            
            cmd = [
                "pulumi", "destroy", "--yes", "--non-interactive",
                "--stack", f"{self.org}/{project}/{stack}"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return InfrastructureResult(
                    success=True,
                    resource_id=f"{project}/{stack}",
                    details={
                        "stdout": stdout.decode(),
                        "stderr": stderr.decode()
                    }
                )
            else:
                return InfrastructureResult(
                    success=False,
                    error=f"Pulumi destroy failed: {stderr.decode()}"
                )
        
        start_time = time.time()
        try:
            result = await self.circuit_breaker.call(_destroy)
            result.duration = time.time() - start_time
            logger.info(f"Pulumi stack destroyed: {project}/{stack}")
            return result
        except Exception as e:
            logger.error(f"Failed to destroy Pulumi stack: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e),
                duration=time.time() - start_time
            )

class InfrastructureAutomationService:
    """Main infrastructure automation service"""
    
    def __init__(self, config: Dict[str, Any]):
        self.lambda_labs = LambdaLabsAutomation(config["lambda_labs"]["api_key"])
        self.qdrant = QdrantAutomation(config["qdrant"]["url"], config["qdrant"].get("api_key"))
        self.github = GitHubAutomation(config["github"]["token"], config["github"].get("org", "ai-cherry"))
        self.pulumi = PulumiAutomation(config["pulumi"]["access_token"], config["pulumi"].get("org", "scoobyjava-org"))
        
        # AI decision engine
        self.decision_engine = InfrastructureDecisionEngine()
        
        logger.info("Infrastructure automation service initialized")
    
    async def execute_request(self, request: InfrastructureRequest) -> InfrastructureResult:
        """Execute infrastructure automation request"""
        logger.info(f"Executing {request.operation.value} on {request.service}.{request.resource_type}")
        
        try:
            if request.service == "lambda_labs":
                return await self._handle_lambda_labs_request(request)
            elif request.service == "qdrant":
                return await self._handle_qdrant_request(request)
            elif request.service == "github":
                return await self._handle_github_request(request)
            elif request.service == "pulumi":
                return await self._handle_pulumi_request(request)
            else:
                return InfrastructureResult(
                    success=False,
                    error=f"Unknown service: {request.service}"
                )
        except Exception as e:
            logger.error(f"Infrastructure request failed: {e}")
            return InfrastructureResult(
                success=False,
                error=str(e)
            )
    
    async def _handle_lambda_labs_request(self, request: InfrastructureRequest) -> InfrastructureResult:
        """Handle Lambda Labs requests"""
        if request.operation == InfrastructureOperation.CREATE:
            return await self.lambda_labs.create_instance(**request.parameters)
        elif request.operation == InfrastructureOperation.DELETE:
            return await self.lambda_labs.terminate_instance(request.parameters["instance_id"])
        else:
            return InfrastructureResult(
                success=False,
                error=f"Unsupported Lambda Labs operation: {request.operation.value}"
            )
    
    async def _handle_qdrant_request(self, request: InfrastructureRequest) -> InfrastructureResult:
        """Handle Qdrant requests"""
        if request.operation == InfrastructureOperation.CREATE:
            return await self.qdrant.create_collection(**request.parameters)
        elif request.operation == InfrastructureOperation.UPDATE:
            return await self.qdrant.optimize_collection(request.parameters["collection_name"])
        else:
            return InfrastructureResult(
                success=False,
                error=f"Unsupported Qdrant operation: {request.operation.value}"
            )
    
    async def _handle_github_request(self, request: InfrastructureRequest) -> InfrastructureResult:
        """Handle GitHub requests"""
        if request.operation == InfrastructureOperation.CREATE:
            return await self.github.create_repository(**request.parameters)
        elif request.operation == InfrastructureOperation.UPDATE:
            return await self.github.update_workflow(**request.parameters)
        else:
            return InfrastructureResult(
                success=False,
                error=f"Unsupported GitHub operation: {request.operation.value}"
            )
    
    async def _handle_pulumi_request(self, request: InfrastructureRequest) -> InfrastructureResult:
        """Handle Pulumi requests"""
        if request.operation == InfrastructureOperation.CREATE:
            return await self.pulumi.deploy_stack(**request.parameters)
        elif request.operation == InfrastructureOperation.DELETE:
            return await self.pulumi.destroy_stack(**request.parameters)
        else:
            return InfrastructureResult(
                success=False,
                error=f"Unsupported Pulumi operation: {request.operation.value}"
            )
    
    async def ai_infrastructure_recommendations(self, metrics: Dict[str, Any]) -> List[InfrastructureRequest]:
        """AI-powered infrastructure recommendations"""
        return await self.decision_engine.analyze_and_recommend(metrics)

class InfrastructureDecisionEngine:
    """AI-powered infrastructure decision engine"""
    
    async def analyze_and_recommend(self, metrics: Dict[str, Any]) -> List[InfrastructureRequest]:
        """Analyze metrics and provide infrastructure recommendations"""
        recommendations = []
        
        # Lambda Labs scaling recommendations
        if metrics.get("gpu_utilization", 0) > 85:
            recommendations.append(InfrastructureRequest(
                operation=InfrastructureOperation.CREATE,
                service="lambda_labs",
                resource_type="instance",
                parameters={
                    "instance_type": "gpu_1x_gh200",
                    "region": "us-east-1",
                    "name": f"sophia-scale-{int(time.time())}",
                    "ssh_key_names": ["sophia-production-key"]
                },
                user_id="ai_engine",
                correlation_id=f"ai-rec-{int(time.time())}"
            ))
        
        # Qdrant optimization recommendations
        if metrics.get("qdrant_query_time", 0) > 1000:  # ms
            recommendations.append(InfrastructureRequest(
                operation=InfrastructureOperation.UPDATE,
                service="qdrant",
                resource_type="collection",
                parameters={
                    "collection_name": "sophia_vectors"
                },
                user_id="ai_engine",
                correlation_id=f"ai-opt-{int(time.time())}"
            ))
        
        return recommendations

# Global infrastructure automation service
_infrastructure_service: Optional[InfrastructureAutomationService] = None

def get_infrastructure_service() -> InfrastructureAutomationService:
    """Get global infrastructure automation service"""
    if _infrastructure_service is None:
        raise RuntimeError("Infrastructure automation service not initialized")
    return _infrastructure_service

async def initialize_infrastructure_service(config: Dict[str, Any]) -> InfrastructureAutomationService:
    """Initialize global infrastructure automation service"""
    global _infrastructure_service
    _infrastructure_service = InfrastructureAutomationService(config)
    return _infrastructure_service

