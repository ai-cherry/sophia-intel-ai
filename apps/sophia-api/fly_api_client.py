"""
Fly.io API Client for SOPHIA Intel Autonomous Deployment
Replaces CLI-based deployment with direct API calls
"""
import os
import json
import httpx
import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class FlyAPIClient:
    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.getenv("FLY_API_TOKEN")
        self.base_url = "https://api.fly.io/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    async def deploy_app(self, app_name: str, image_ref: str) -> Dict[str, Any]:
        """
        Deploy an app using Fly.io API directly (no CLI required)
        """
        try:
            async with httpx.AsyncClient() as client:
                # Get current app configuration
                app_response = await client.get(
                    f"{self.base_url}/apps/{app_name}",
                    headers=self.headers
                )
                
                if app_response.status_code != 200:
                    return {
                        "status": "error",
                        "error": f"Failed to get app info: {app_response.text}"
                    }
                
                # Create deployment
                deployment_data = {
                    "image": image_ref,
                    "strategy": "rolling"
                }
                
                deploy_response = await client.post(
                    f"{self.base_url}/apps/{app_name}/deployments",
                    headers=self.headers,
                    json=deployment_data
                )
                
                if deploy_response.status_code not in [200, 201]:
                    return {
                        "status": "error", 
                        "error": f"Deployment failed: {deploy_response.text}"
                    }
                
                deployment = deploy_response.json()
                deployment_id = deployment.get("id")
                
                # Monitor deployment status
                status = await self._wait_for_deployment(app_name, deployment_id)
                
                return {
                    "status": "success",
                    "deployment_id": deployment_id,
                    "deployment_status": status
                }
                
        except Exception as e:
            logger.error(f"Fly.io API deployment failed: {str(e)}")
            return {
                "status": "error",
                "error": f"API deployment failed: {str(e)}"
            }
    
    async def _wait_for_deployment(self, app_name: str, deployment_id: str, timeout: int = 300) -> str:
        """
        Wait for deployment to complete
        """
        async with httpx.AsyncClient() as client:
            for _ in range(timeout // 10):  # Check every 10 seconds
                try:
                    response = await client.get(
                        f"{self.base_url}/apps/{app_name}/deployments/{deployment_id}",
                        headers=self.headers
                    )
                    
                    if response.status_code == 200:
                        deployment = response.json()
                        status = deployment.get("status", "unknown")
                        
                        if status in ["successful", "failed"]:
                            return status
                    
                    await asyncio.sleep(10)
                    
                except Exception as e:
                    logger.warning(f"Error checking deployment status: {e}")
                    await asyncio.sleep(10)
            
            return "timeout"
    
    async def build_and_deploy(self, app_name: str, source_path: str) -> Dict[str, Any]:
        """
        Build and deploy from source using Fly.io remote builder
        """
        try:
            async with httpx.AsyncClient(timeout=600.0) as client:
                # Create build
                build_data = {
                    "source_path": source_path,
                    "build_args": {}
                }
                
                build_response = await client.post(
                    f"{self.base_url}/apps/{app_name}/builds",
                    headers=self.headers,
                    json=build_data
                )
                
                if build_response.status_code not in [200, 201]:
                    return {
                        "status": "error",
                        "error": f"Build failed: {build_response.text}"
                    }
                
                build = build_response.json()
                build_id = build.get("id")
                
                # Wait for build to complete
                build_status = await self._wait_for_build(app_name, build_id)
                
                if build_status != "successful":
                    return {
                        "status": "error",
                        "error": f"Build failed with status: {build_status}"
                    }
                
                # Get the built image reference
                image_ref = build.get("image_ref")
                
                # Deploy the built image
                return await self.deploy_app(app_name, image_ref)
                
        except Exception as e:
            logger.error(f"Build and deploy failed: {str(e)}")
            return {
                "status": "error",
                "error": f"Build and deploy failed: {str(e)}"
            }
    
    async def _wait_for_build(self, app_name: str, build_id: str, timeout: int = 600) -> str:
        """
        Wait for build to complete
        """
        async with httpx.AsyncClient() as client:
            for _ in range(timeout // 10):  # Check every 10 seconds
                try:
                    response = await client.get(
                        f"{self.base_url}/apps/{app_name}/builds/{build_id}",
                        headers=self.headers
                    )
                    
                    if response.status_code == 200:
                        build = response.json()
                        status = build.get("status", "unknown")
                        
                        if status in ["successful", "failed"]:
                            return status
                    
                    await asyncio.sleep(10)
                    
                except Exception as e:
                    logger.warning(f"Error checking build status: {e}")
                    await asyncio.sleep(10)
            
            return "timeout"

    async def get_app_status(self, app_name: str) -> Dict[str, Any]:
        """
        Get current app status
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/apps/{app_name}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    return {
                        "status": "success",
                        "app": response.json()
                    }
                else:
                    return {
                        "status": "error",
                        "error": f"Failed to get app status: {response.text}"
                    }
                    
        except Exception as e:
            return {
                "status": "error", 
                "error": f"API error: {str(e)}"
            }

