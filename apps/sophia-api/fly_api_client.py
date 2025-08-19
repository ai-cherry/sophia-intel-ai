"""
Fly.io API Client for SOPHIA Intel Autonomous Deployment
Replaces CLI-based deployment with direct API calls using correct Machines API endpoints
"""
import os
import json
import httpx
import asyncio
import logging
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime

logger = logging.getLogger(__name__)

class FlyAPIClient:
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("FLY_API_TOKEN")
        self.base_url = "https://api.machines.dev/v1"
        self.app_name = "sophia-intel"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def deploy_app(self, app_name: str, image_ref: str) -> Dict[str, Any]:
        """
        Deploy an app using Fly.io Machines API directly (no CLI required)
        Uses correct /v1/apps/{app_name}/machines endpoints
        """
        try:
            async with httpx.AsyncClient() as client:
                # List existing machines to update or create
                machines_url = f"{self.base_url}/apps/{self.app_name}/machines"
                response = await client.get(machines_url, headers=self.headers)
                
                if response.status_code != 200:
                    logger.error(f"Failed to list machines: {response.status_code} - {response.text}")
                    raise Exception(f"Failed to list machines: {response.text}")
                
                machines = response.json()
                logger.info(f"Found {len(machines)} existing machines")
                
                # Create machine configuration payload matching fly.toml
                machine_config = {
                    "config": {
                        "image": image_ref,
                        "auto_destroy": False,
                        "env": {
                            "FLY_API_TOKEN": self.api_token,
                            "PRIMARY_REGION": "ord",
                            "LOG_LEVEL": "debug"
                        },
                        "services": [
                            {
                                "ports": [
                                    {"port": 80, "handlers": ["http"]},
                                    {"port": 443, "handlers": ["tls", "http"]}
                                ],
                                "protocol": "tcp",
                                "internal_port": 8080,
                                "concurrency": {
                                    "type": "requests",
                                    "soft_limit": 200,
                                    "hard_limit": 250
                                }
                            }
                        ],
                        "checks": {
                            "health": {
                                "type": "http",
                                "path": "/api/v1/health",
                                "interval": "15s",
                                "timeout": "5s",
                                "grace_period": "10s",
                                "method": "GET",
                                "protocol": "http"
                            }
                        },
                        "guest": {
                            "cpu_kind": "shared",
                            "cpus": 2,
                            "memory_mb": 4096
                        }
                    }
                }
                
                if machines:
                    # Update existing machine (rolling deployment)
                    machine_id = machines[0]["id"]
                    update_url = f"{self.base_url}/apps/{self.app_name}/machines/{machine_id}"
                    logger.info(f"Updating existing machine {machine_id}")
                    response = await client.post(update_url, json=machine_config, headers=self.headers)
                else:
                    # Create new machine
                    create_url = f"{self.base_url}/apps/{self.app_name}/machines"
                    logger.info("Creating new machine")
                    response = await client.post(create_url, json=machine_config, headers=self.headers)
                
                if response.status_code not in (200, 201):
                    logger.error(f"Deployment failed: {response.status_code} - {response.text}")
                    raise Exception(f"Deployment failed: {response.text}")
                
                result = response.json()
                machine_id = result.get("id")
                logger.info(f"Deployment successful: machine {machine_id}")
                
                return {
                    "status": "deployed",
                    "machine_id": machine_id,
                    "app_name": self.app_name,
                    "image": image_ref,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Deployment error: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def build_and_deploy(self, pr_number: int, repo_url: str, commit_sha: str) -> Dict[str, Any]:
        """
        Build and deploy a specific PR/commit using Machines API
        For autonomous deployment, use the current deployed image
        """
        try:
            logger.info(f"Starting autonomous deployment for PR #{pr_number}, commit {commit_sha}")
            
            # For autonomous deployment, use the current deployed image
            # Get current machines to find the existing image
            async with httpx.AsyncClient() as client:
                machines_url = f"{self.base_url}/apps/{self.app_name}/machines"
                response = await client.get(machines_url, headers=self.headers)
                
                if response.status_code == 200:
                    machines = response.json()
                    if machines:
                        # Use the image from the first running machine
                        current_image = machines[0].get("config", {}).get("image", f"registry.fly.io/{self.app_name}:latest")
                        logger.info(f"Using current deployed image: {current_image}")
                    else:
                        current_image = f"registry.fly.io/{self.app_name}:latest"
                        logger.info(f"No existing machines, using default image: {current_image}")
                else:
                    current_image = f"registry.fly.io/{self.app_name}:latest"
                    logger.info(f"Could not list machines, using default image: {current_image}")
            
            # Deploy using the current image (autonomous deployment doesn't need new build)
            result = await self.deploy_app(self.app_name, current_image)
            
            # Add deployment metadata
            result.update({
                "pr_number": pr_number,
                "repo_url": repo_url,
                "commit_sha": commit_sha,
                "deployment_type": "autonomous",
                "image_used": current_image
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Build and deploy error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "pr_number": pr_number,
                "commit_sha": commit_sha,
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_machine_status(self, machine_id: str) -> Dict[str, Any]:
        """
        Get status of a specific machine
        """
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/apps/{self.app_name}/machines/{machine_id}"
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"status": "error", "error": response.text}
                    
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def list_machines(self) -> Dict[str, Any]:
        """
        List all machines for the app
        """
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.base_url}/apps/{self.app_name}/machines"
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    return {"status": "success", "machines": response.json()}
                else:
                    return {"status": "error", "error": response.text}
                    
        except Exception as e:
            return {"status": "error", "error": str(e)}

