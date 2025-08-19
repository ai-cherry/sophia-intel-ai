"""
SOPHIA V4 Production Deployment Agent
Real-world cloud deployment system - no Manus dependencies
Works in any Python environment: production servers, CI/CD, Docker, local dev
"""

import os
import sys
import json
import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

# Import our RobustFlyAgent
try:
    from .fly_agent import RobustFlyAgent, FlyAPIError
except ImportError:
    # Handle relative imports in different environments
    sys.path.append(str(Path(__file__).parent))
    from fly_agent import RobustFlyAgent, FlyAPIError

logger = logging.getLogger(__name__)

class DeploymentError(Exception):
    """Custom exception for deployment errors"""
    pass

class ProductionDeploymentAgent:
    """
    Production-grade deployment agent for SOPHIA V4
    Designed for real-world cloud environments beyond Manus shell
    """
    
    def __init__(self, app_name: str = "sophia-intel"):
        self.app_name = app_name
        self.fly_agent = None
        self._initialize_environment()
        self._setup_logging()
    
    def _initialize_environment(self):
        """Initialize environment and validate credentials"""
        # Check for required environment variables
        required_vars = [
            "FLY_ORG_TOKEN",  # Primary token for org-level operations
            "GITHUB_TOKEN",   # For GitHub operations
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                # Try alternative names
                alt_names = {
                    "FLY_ORG_TOKEN": ["FLY_API_TOKEN", "FLY_AUTH_TOKEN"],
                    "GITHUB_TOKEN": ["GITHUB_PAT", "GH_TOKEN"]
                }
                
                found = False
                for alt_name in alt_names.get(var, []):
                    if os.getenv(alt_name):
                        os.environ[var] = os.getenv(alt_name)
                        found = True
                        break
                
                if not found:
                    missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"Missing environment variables: {missing_vars}")
            logger.info("Deployment may have limited functionality")
        
        # Initialize Fly agent if token is available
        try:
            self.fly_agent = RobustFlyAgent()
            logger.info("RobustFlyAgent initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize RobustFlyAgent: {e}")
    
    def _setup_logging(self):
        """Setup production-grade logging"""
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # Configure logging for production environments
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                # Add file handler if log directory exists
                *([logging.FileHandler('/var/log/sophia/deployment.log')] 
                  if os.path.exists('/var/log/sophia') else [])
            ]
        )
    
    def _run_command(self, command: List[str], timeout: int = 300) -> Dict[str, Any]:
        """
        Run shell command with proper error handling
        Works in any environment - no Manus shell dependencies
        """
        try:
            logger.info(f"Executing command: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False  # Don't raise on non-zero exit
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout} seconds")
            raise DeploymentError(f"Command timeout: {' '.join(command)}")
        except FileNotFoundError:
            logger.error(f"Command not found: {command[0]}")
            raise DeploymentError(f"Command not found: {command[0]}")
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            raise DeploymentError(f"Command failed: {e}")
    
    def _check_flyctl_available(self) -> bool:
        """Check if flyctl is available in the environment"""
        try:
            result = self._run_command(["flyctl", "version"])
            return result["success"]
        except DeploymentError:
            return False
    
    def _install_flyctl(self) -> bool:
        """Install flyctl in production environments"""
        logger.info("Installing flyctl...")
        
        try:
            # Try different installation methods based on environment
            if os.path.exists("/usr/bin/curl") or os.path.exists("/bin/curl"):
                # Standard Linux installation
                install_cmd = [
                    "sh", "-c", 
                    "curl -L https://fly.io/install.sh | sh"
                ]
                result = self._run_command(install_cmd)
                
                if result["success"]:
                    # Add to PATH for current session
                    flyctl_path = os.path.expanduser("~/.fly/bin")
                    if flyctl_path not in os.environ.get("PATH", ""):
                        os.environ["PATH"] = f"{flyctl_path}:{os.environ.get('PATH', '')}"
                    return True
            
            # Alternative: try package managers
            package_managers = [
                (["brew", "install", "flyctl"], "Homebrew"),
                (["apt-get", "update", "&&", "apt-get", "install", "-y", "flyctl"], "APT"),
                (["yum", "install", "-y", "flyctl"], "YUM")
            ]
            
            for cmd, name in package_managers:
                try:
                    result = self._run_command(cmd)
                    if result["success"]:
                        logger.info(f"flyctl installed via {name}")
                        return True
                except DeploymentError:
                    continue
            
            logger.error("Failed to install flyctl via any method")
            return False
            
        except Exception as e:
            logger.error(f"flyctl installation failed: {e}")
            return False
    
    async def deploy_with_flyctl(self, image_ref: str, strategy: str = "immediate") -> Dict[str, Any]:
        """Deploy using flyctl command - works in any environment"""
        if not self._check_flyctl_available():
            if not self._install_flyctl():
                raise DeploymentError("flyctl not available and installation failed")
        
        # Set Fly.io token for flyctl
        fly_token = os.getenv("FLY_ORG_TOKEN") or os.getenv("FLY_API_TOKEN")
        if fly_token:
            os.environ["FLY_API_TOKEN"] = fly_token
        
        deploy_cmd = [
            "flyctl", "deploy",
            "--app", self.app_name,
            "--image", image_ref,
            "--strategy", strategy,
            "--wait-timeout", "10m"
        ]
        
        result = self._run_command(deploy_cmd, timeout=600)  # 10 minutes
        
        if not result["success"]:
            logger.error(f"flyctl deploy failed: {result['stderr']}")
            raise DeploymentError(f"Deployment failed: {result['stderr']}")
        
        logger.info("Deployment completed successfully via flyctl")
        return {
            "method": "flyctl",
            "success": True,
            "output": result["stdout"],
            "timestamp": datetime.now().isoformat()
        }
    
    async def deploy_with_api(self, image_ref: str, strategy: str = "IMMEDIATE") -> Dict[str, Any]:
        """Deploy using Fly.io API - fallback method"""
        if not self.fly_agent:
            raise DeploymentError("Fly.io API agent not available")
        
        try:
            result = await self.fly_agent.deploy_image(self.app_name, image_ref, strategy)
            logger.info("Deployment completed successfully via API")
            
            return {
                "method": "api",
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except FlyAPIError as e:
            logger.error(f"API deployment failed: {e}")
            raise DeploymentError(f"API deployment failed: {e}")
    
    async def deploy_robust(self, image_ref: str) -> Dict[str, Any]:
        """
        Robust deployment with multiple fallback methods
        Designed for production reliability
        """
        deployment_methods = [
            ("flyctl", self.deploy_with_flyctl),
            ("api", self.deploy_with_api)
        ]
        
        last_error = None
        
        for method_name, method in deployment_methods:
            try:
                logger.info(f"Attempting deployment via {method_name}")
                result = await method(image_ref)
                
                # Verify deployment success
                if await self.verify_deployment():
                    logger.info(f"Deployment successful via {method_name}")
                    return result
                else:
                    logger.warning(f"Deployment via {method_name} completed but verification failed")
                    
            except Exception as e:
                logger.warning(f"Deployment via {method_name} failed: {e}")
                last_error = e
                continue
        
        # All methods failed
        raise DeploymentError(f"All deployment methods failed. Last error: {last_error}")
    
    async def verify_deployment(self, max_attempts: int = 10, delay: int = 30) -> bool:
        """Verify deployment success with health checks"""
        hostname = f"{self.app_name}.fly.dev"
        
        for attempt in range(max_attempts):
            logger.info(f"Health check attempt {attempt + 1}/{max_attempts}")
            
            # Try multiple health endpoints
            health_paths = ["/health", "/api/v1/health", "/"]
            
            for path in health_paths:
                if self.fly_agent:
                    is_healthy = await self.fly_agent.health_check(hostname, path)
                    if is_healthy:
                        logger.info(f"Health check passed: {hostname}{path}")
                        return True
            
            if attempt < max_attempts - 1:
                logger.info(f"Health check failed, waiting {delay} seconds...")
                await asyncio.sleep(delay)
        
        logger.error("All health check attempts failed")
        return False
    
    async def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status"""
        status = {
            "app_name": self.app_name,
            "timestamp": datetime.now().isoformat(),
            "flyctl_available": self._check_flyctl_available(),
            "api_available": self.fly_agent is not None
        }
        
        if self.fly_agent:
            try:
                app_info = await self.fly_agent.get_app_info(self.app_name)
                machines = await self.fly_agent.list_machines(self.app_name)
                
                status.update({
                    "app_info": app_info,
                    "machines": machines,
                    "health_check": await self.verify_deployment(max_attempts=1)
                })
                
            except Exception as e:
                status["api_error"] = str(e)
        
        return status
    
    def run_deployment(self, image_ref: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for deployment - works in any Python environment
        Can be called from scripts, CI/CD, or any production system
        """
        try:
            # Handle different event loop scenarios
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is already running (e.g., in Jupyter, some web frameworks)
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.deploy_robust(image_ref))
                        return future.result(timeout=900)  # 15 minutes
                else:
                    return loop.run_until_complete(self.deploy_robust(image_ref))
            except RuntimeError:
                # No event loop exists, create one
                return asyncio.run(self.deploy_robust(image_ref))
                
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            raise DeploymentError(f"Deployment failed: {e}")

# Factory function for easy instantiation
def create_deployment_agent(app_name: str = "sophia-intel") -> ProductionDeploymentAgent:
    """Create a production deployment agent"""
    return ProductionDeploymentAgent(app_name)

# CLI interface for direct execution
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SOPHIA V4 Production Deployment")
    parser.add_argument("--image", required=True, help="Docker image reference to deploy")
    parser.add_argument("--app", default="sophia-intel", help="Fly.io app name")
    parser.add_argument("--status", action="store_true", help="Get deployment status only")
    
    args = parser.parse_args()
    
    agent = create_deployment_agent(args.app)
    
    if args.status:
        # Get status only
        status = asyncio.run(agent.get_deployment_status())
        print(json.dumps(status, indent=2))
    else:
        # Deploy
        try:
            result = agent.run_deployment(args.image)
            print(f"✅ Deployment successful: {json.dumps(result, indent=2)}")
        except DeploymentError as e:
            print(f"❌ Deployment failed: {e}")
            sys.exit(1)

