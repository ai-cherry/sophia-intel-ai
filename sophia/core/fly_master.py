"""
SOPHIA V4 Fly Master
Manages Fly.io applications: deploys new versions, scales instances,
retrieves app status, and manages secrets.
"""

import os
import logging
import time
from dataclasses import dataclass
from typing import Optional, Dict, List, Any, Union

import requests

logger = logging.getLogger(__name__)

@dataclass
class FlyAppInfo:
    """Information about a Fly.io application."""
    name: str
    status: str
    region: str
    platform_version: str
    hostname: str

@dataclass
class FlyReleaseInfo:
    """Information about a Fly.io release."""
    id: str
    version: int
    status: str
    description: str
    created_at: str

@dataclass
class FlyMachineInfo:
    """Information about a Fly.io machine."""
    id: str
    name: str
    state: str
    region: str
    instance_id: str
    private_ip: str

class SOPHIAFlyMaster:
    """
    Manages Fly.io applications: deploys new versions, scales instances,
    retrieves app status, and manages secrets.
    
    This class provides autonomous Fly.io operations for Sophia, allowing her to:
    - Deploy applications and services
    - Scale instances up and down
    - Monitor application health and status
    - Manage secrets and configuration
    - Handle machine lifecycle operations
    """

    def __init__(self):
        """
        Initialize Fly master with API credentials.
        
        Raises:
            EnvironmentError: If FLY_API_TOKEN is not set
        """
        self.api_base = "https://api.fly.io/graphql"
        self.machines_api_base = "https://api.machines.dev/v1"
        self.token = os.getenv("FLY_API_TOKEN") or os.getenv("FLY_ACCESS_TOKEN")
        
        if not self.token:
            raise EnvironmentError("FLY_API_TOKEN or FLY_ACCESS_TOKEN is not set in environment")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        logger.info("Initialized Fly.io master")

    def _execute_graphql_query(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query against the Fly.io API.
        
        Args:
            query: GraphQL query string
            variables: Query variables
            
        Returns:
            Query response data
            
        Raises:
            requests.HTTPError: If API call fails
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            response = requests.post(self.api_base, json=payload, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            
            if "errors" in result:
                error_messages = [error["message"] for error in result["errors"]]
                raise RuntimeError(f"GraphQL errors: {', '.join(error_messages)}")
            
            return result.get("data", {})
            
        except requests.RequestException as e:
            logger.error(f"GraphQL query failed: {e}")
            raise

    def get_apps(self) -> List[FlyAppInfo]:
        """
        Get list of all applications.
        
        Returns:
            List of FlyAppInfo objects
            
        Raises:
            requests.HTTPError: If API call fails
        """
        query = """
        query GetApps {
            apps {
                nodes {
                    name
                    status
                    platformVersion
                    hostname
                    organization {
                        slug
                    }
                    regions {
                        code
                    }
                }
            }
        }
        """
        
        try:
            data = self._execute_graphql_query(query)
            apps = []
            
            for app_data in data.get("apps", {}).get("nodes", []):
                regions = [region["code"] for region in app_data.get("regions", [])]
                region = regions[0] if regions else "unknown"
                
                app_info = FlyAppInfo(
                    name=app_data["name"],
                    status=app_data["status"],
                    region=region,
                    platform_version=app_data.get("platformVersion", "unknown"),
                    hostname=app_data.get("hostname", "")
                )
                apps.append(app_info)
            
            logger.info(f"Retrieved {len(apps)} applications")
            return apps
            
        except Exception as e:
            logger.error(f"Failed to get apps: {e}")
            raise

    def get_app_status(self, app_name: str) -> Dict[str, Any]:
        """
        Retrieve the status of an app (deployments, health checks).
        
        Args:
            app_name: Name of the application
            
        Returns:
            Dictionary with app status information
            
        Raises:
            requests.HTTPError: If API call fails
        """
        query = """
        query AppStatus($appName: String!) {
            app(name: $appName) {
                name
                status
                hostname
                platformVersion
                currentRelease {
                    id
                    version
                    status
                    description
                    createdAt
                }
                machines {
                    nodes {
                        id
                        name
                        state
                        region
                        instanceId
                        privateIP
                        checks {
                            name
                            status
                            output
                        }
                    }
                }
            }
        }
        """
        
        variables = {"appName": app_name}
        
        try:
            data = self._execute_graphql_query(query, variables)
            app_data = data.get("app")
            
            if not app_data:
                raise ValueError(f"App {app_name} not found")
            
            # Parse current release
            current_release = None
            if app_data.get("currentRelease"):
                release_data = app_data["currentRelease"]
                current_release = FlyReleaseInfo(
                    id=release_data["id"],
                    version=release_data["version"],
                    status=release_data["status"],
                    description=release_data.get("description", ""),
                    created_at=release_data["createdAt"]
                )
            
            # Parse machines
            machines = []
            for machine_data in app_data.get("machines", {}).get("nodes", []):
                machine_info = FlyMachineInfo(
                    id=machine_data["id"],
                    name=machine_data.get("name", ""),
                    state=machine_data["state"],
                    region=machine_data["region"],
                    instance_id=machine_data.get("instanceId", ""),
                    private_ip=machine_data.get("privateIP", "")
                )
                machines.append(machine_info)
            
            status = {
                "name": app_data["name"],
                "status": app_data["status"],
                "hostname": app_data.get("hostname", ""),
                "platform_version": app_data.get("platformVersion", ""),
                "current_release": current_release,
                "machines": machines,
                "machine_count": len(machines),
                "healthy_machines": len([m for m in machines if m.state == "started"])
            }
            
            logger.info(f"Retrieved status for app {app_name}")
            return status
            
        except Exception as e:
            logger.error(f"Failed to get app status for {app_name}: {e}")
            raise

    def deploy_app(self, app_name: str, image: str, wait_for_deployment: bool = True) -> FlyReleaseInfo:
        """
        Deploy a new image to a Fly.io app.
        
        Args:
            app_name: Name of the application
            image: Docker image to deploy
            wait_for_deployment: Whether to wait for deployment to complete
            
        Returns:
            FlyReleaseInfo with deployment details
            
        Raises:
            requests.HTTPError: If API call fails
        """
        mutation = """
        mutation DeployImage($input: DeployImageInput!) {
            deployImage(input: $input) {
                release {
                    id
                    version
                    status
                    description
                    createdAt
                }
            }
        }
        """
        
        variables = {
            "input": {
                "appId": app_name,
                "image": image
            }
        }
        
        try:
            data = self._execute_graphql_query(mutation, variables)
            release_data = data.get("deployImage", {}).get("release")
            
            if not release_data:
                raise RuntimeError("No release data returned from deployment")
            
            release_info = FlyReleaseInfo(
                id=release_data["id"],
                version=release_data["version"],
                status=release_data["status"],
                description=release_data.get("description", ""),
                created_at=release_data["createdAt"]
            )
            
            logger.info(f"Deployed {image} to {app_name}, release v{release_info.version}")
            
            # Wait for deployment if requested
            if wait_for_deployment:
                self._wait_for_deployment(app_name, release_info.id)
            
            return release_info
            
        except Exception as e:
            logger.error(f"Failed to deploy {image} to {app_name}: {e}")
            raise

    def scale_app(self, app_name: str, count: int, region: Optional[str] = None) -> bool:
        """
        Scale the number of instances for an app.
        
        Args:
            app_name: Name of the application
            count: Number of instances to scale to
            region: Specific region to scale (optional)
            
        Returns:
            True if successful
            
        Raises:
            requests.HTTPError: If API call fails
        """
        mutation = """
        mutation ScaleApp($input: ScaleAppInput!) {
            scaleApp(input: $input) {
                app {
                    name
                }
                placement {
                    count
                    region
                }
            }
        }
        """
        
        scale_input = {
            "appId": app_name,
            "regions": [{"region": region or "ord", "count": count}]
        }
        
        variables = {"input": scale_input}
        
        try:
            data = self._execute_graphql_query(mutation, variables)
            
            if data.get("scaleApp"):
                logger.info(f"Scaled {app_name} to {count} instances")
                return True
            else:
                raise RuntimeError("Scale operation failed")
                
        except Exception as e:
            logger.error(f"Failed to scale {app_name} to {count} instances: {e}")
            raise

    def restart_app(self, app_name: str) -> bool:
        """
        Restart an application.
        
        Args:
            app_name: Name of the application
            
        Returns:
            True if successful
            
        Raises:
            requests.HTTPError: If API call fails
        """
        mutation = """
        mutation RestartApp($input: RestartAppInput!) {
            restartApp(input: $input) {
                app {
                    name
                    status
                }
            }
        }
        """
        
        variables = {
            "input": {
                "appId": app_name
            }
        }
        
        try:
            data = self._execute_graphql_query(mutation, variables)
            
            if data.get("restartApp"):
                logger.info(f"Restarted app {app_name}")
                return True
            else:
                raise RuntimeError("Restart operation failed")
                
        except Exception as e:
            logger.error(f"Failed to restart {app_name}: {e}")
            raise

    def set_secrets(self, app_name: str, secrets: Dict[str, str]) -> bool:
        """
        Set secrets for an application.
        
        Args:
            app_name: Name of the application
            secrets: Dictionary of secret key-value pairs
            
        Returns:
            True if successful
            
        Raises:
            requests.HTTPError: If API call fails
        """
        mutation = """
        mutation SetSecrets($input: SetSecretsInput!) {
            setSecrets(input: $input) {
                app {
                    name
                }
            }
        }
        """
        
        # Convert secrets to the format expected by Fly.io
        secret_inputs = [
            {"key": key, "value": value}
            for key, value in secrets.items()
        ]
        
        variables = {
            "input": {
                "appId": app_name,
                "secrets": secret_inputs
            }
        }
        
        try:
            data = self._execute_graphql_query(mutation, variables)
            
            if data.get("setSecrets"):
                logger.info(f"Set {len(secrets)} secrets for {app_name}")
                return True
            else:
                raise RuntimeError("Set secrets operation failed")
                
        except Exception as e:
            logger.error(f"Failed to set secrets for {app_name}: {e}")
            raise

    def get_secrets(self, app_name: str) -> List[str]:
        """
        Get list of secret names for an application.
        
        Args:
            app_name: Name of the application
            
        Returns:
            List of secret names
            
        Raises:
            requests.HTTPError: If API call fails
        """
        query = """
        query GetSecrets($appName: String!) {
            app(name: $appName) {
                secrets {
                    name
                    digest
                    createdAt
                }
            }
        }
        """
        
        variables = {"appName": app_name}
        
        try:
            data = self._execute_graphql_query(query, variables)
            app_data = data.get("app")
            
            if not app_data:
                raise ValueError(f"App {app_name} not found")
            
            secrets = [secret["name"] for secret in app_data.get("secrets", [])]
            logger.info(f"Retrieved {len(secrets)} secrets for {app_name}")
            return secrets
            
        except Exception as e:
            logger.error(f"Failed to get secrets for {app_name}: {e}")
            raise

    def get_logs(self, app_name: str, lines: int = 100) -> List[str]:
        """
        Get recent logs for an application.
        
        Args:
            app_name: Name of the application
            lines: Number of log lines to retrieve
            
        Returns:
            List of log lines
            
        Note:
            This is a simplified implementation. In practice, you might want to use
            the Fly.io logs API or streaming endpoints for real-time logs.
        """
        # This is a placeholder implementation
        # In a real implementation, you would use the Fly.io logs API
        logger.warning("get_logs is a placeholder implementation")
        return [f"Log line {i} for {app_name}" for i in range(lines)]

    def _wait_for_deployment(self, app_name: str, release_id: str, timeout: int = 300) -> bool:
        """
        Wait for a deployment to complete.
        
        Args:
            app_name: Name of the application
            release_id: ID of the release to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if deployment succeeded
            
        Raises:
            TimeoutError: If deployment doesn't complete within timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                status = self.get_app_status(app_name)
                current_release = status.get("current_release")
                
                if current_release and current_release.id == release_id:
                    if current_release.status == "succeeded":
                        logger.info(f"Deployment {release_id} succeeded")
                        return True
                    elif current_release.status == "failed":
                        raise RuntimeError(f"Deployment {release_id} failed")
                
                time.sleep(10)  # Wait 10 seconds before checking again
                
            except Exception as e:
                logger.warning(f"Error checking deployment status: {e}")
                time.sleep(10)
        
        raise TimeoutError(f"Deployment {release_id} did not complete within {timeout} seconds")

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the Fly.io API connection.
        
        Returns:
            Dictionary with health status
        """
        try:
            # Try to get the list of apps as a health check
            apps = self.get_apps()
            
            return {
                "status": "healthy",
                "apps_count": len(apps),
                "api_accessible": True
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_accessible": False
            }

