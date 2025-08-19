"""
SOPHIA V4 Advanced Machine Manager
Production-grade machine management with leasing and robust error handling
Designed for real-world cloud environments beyond Manus shell
"""

import os
import sys
import asyncio
import logging
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

class MachineManagerError(Exception):
    """Custom exception for machine management errors"""
    pass

class AdvancedMachineManager:
    """
    Advanced machine manager for SOPHIA V4
    Handles machine leasing, updates, and lifecycle management
    Production-ready for any cloud environment
    """
    
    def __init__(self, app_name: str = "sophia-intel"):
        self.app_name = app_name
        self.fly_agent = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the Fly.io agent"""
        try:
            self.fly_agent = RobustFlyAgent()
            logger.info("AdvancedMachineManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RobustFlyAgent: {e}")
            raise MachineManagerError(f"Agent initialization failed: {e}")
    
    async def acquire_machine_lease(self, machine_id: str, ttl: str = "30s") -> str:
        """
        Acquire a lease on a machine for safe operations
        Essential for production machine management
        """
        if not self.fly_agent:
            raise MachineManagerError("Fly.io agent not available")
        
        endpoint = f"/apps/{self.app_name}/machines/{machine_id}/lease"
        lease_data = {"ttl": ttl}
        
        try:
            response = await self.fly_agent.machines_request("POST", endpoint, lease_data)
            
            # Extract nonce from different possible response formats
            nonce = (
                response.get("nonce") or 
                response.get("lease", {}).get("nonce") or
                response.get("data", {}).get("nonce")
            )
            
            if not nonce:
                logger.error(f"Failed to extract lease nonce from response: {response}")
                raise MachineManagerError(f"Invalid lease response: {response}")
            
            logger.info(f"Acquired lease for machine {machine_id}: {nonce[:8]}...")
            return nonce
            
        except FlyAPIError as e:
            logger.error(f"Failed to acquire lease for machine {machine_id}: {e}")
            raise MachineManagerError(f"Lease acquisition failed: {e}")
    
    async def release_machine_lease(self, machine_id: str, nonce: str) -> bool:
        """Release a machine lease"""
        if not self.fly_agent:
            raise MachineManagerError("Fly.io agent not available")
        
        endpoint = f"/apps/{self.app_name}/machines/{machine_id}/lease"
        
        try:
            headers = self.fly_agent.headers.copy()
            headers["Fly-Machine-Lease-Nonce"] = nonce
            
            # Use DELETE method to release lease
            import aiohttp
            url = f"{self.fly_agent.config.machines_api}{endpoint}"
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=headers) as response:
                    if response.status in [200, 204]:
                        logger.info(f"Released lease for machine {machine_id}")
                        return True
                    else:
                        logger.warning(f"Lease release returned {response.status}")
                        return False
                        
        except Exception as e:
            logger.warning(f"Failed to release lease for machine {machine_id}: {e}")
            return False
    
    async def update_machine_with_lease(self, machine_id: str, config: Dict[str, Any], ttl: str = "60s") -> Dict[str, Any]:
        """
        Update machine configuration with proper leasing
        Critical for safe production machine updates
        """
        nonce = None
        
        try:
            # Acquire lease
            nonce = await self.acquire_machine_lease(machine_id, ttl)
            
            # Prepare headers with lease nonce
            headers = self.fly_agent.headers.copy()
            headers["Fly-Machine-Lease-Nonce"] = nonce
            
            # Update machine configuration
            endpoint = f"/apps/{self.app_name}/machines/{machine_id}"
            
            import aiohttp
            url = f"{self.fly_agent.config.machines_api}{endpoint}"
            timeout = aiohttp.ClientTimeout(total=120)  # Extended timeout for updates
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=config, timeout=timeout) as response:
                    response_text = await response.text()
                    
                    if response.status not in [200, 202]:
                        logger.error(f"Machine update failed: {response.status} - {response_text}")
                        raise MachineManagerError(f"Update failed: {response.status} - {response_text}")
                    
                    try:
                        result = await response.json()
                        logger.info(f"Machine {machine_id} updated successfully")
                        return result
                    except:
                        # Some responses might not be JSON
                        return {"status": "success", "message": response_text}
        
        finally:
            # Always try to release the lease
            if nonce:
                await self.release_machine_lease(machine_id, nonce)
    
    async def restart_machine_safe(self, machine_id: str) -> Dict[str, Any]:
        """Safely restart a machine with proper error handling"""
        try:
            result = await self.fly_agent.restart_machine(self.app_name, machine_id)
            
            # Wait for machine to come back online
            await self._wait_for_machine_ready(machine_id, timeout=300)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to restart machine {machine_id}: {e}")
            raise MachineManagerError(f"Machine restart failed: {e}")
    
    async def stop_machine_safe(self, machine_id: str) -> Dict[str, Any]:
        """Safely stop a machine"""
        try:
            return await self.fly_agent.stop_machine(self.app_name, machine_id)
        except Exception as e:
            logger.error(f"Failed to stop machine {machine_id}: {e}")
            raise MachineManagerError(f"Machine stop failed: {e}")
    
    async def _wait_for_machine_ready(self, machine_id: str, timeout: int = 300) -> bool:
        """Wait for machine to be ready after restart/update"""
        start_time = datetime.now()
        check_interval = 10  # seconds
        
        while (datetime.now() - start_time).total_seconds() < timeout:
            try:
                status = await self.fly_agent.get_machine_status(self.app_name, machine_id)
                
                machine_state = status.get("state", "").lower()
                if machine_state in ["started", "running"]:
                    logger.info(f"Machine {machine_id} is ready (state: {machine_state})")
                    return True
                
                logger.info(f"Machine {machine_id} state: {machine_state}, waiting...")
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.warning(f"Error checking machine status: {e}")
                await asyncio.sleep(check_interval)
        
        logger.error(f"Machine {machine_id} did not become ready within {timeout} seconds")
        return False
    
    async def get_all_machines_status(self) -> Dict[str, Any]:
        """Get status of all machines for the app"""
        try:
            machines_list = await self.fly_agent.list_machines(self.app_name)
            
            detailed_status = []
            for machine in machines_list:
                machine_id = machine.get("id")
                if machine_id:
                    try:
                        status = await self.fly_agent.get_machine_status(self.app_name, machine_id)
                        detailed_status.append(status)
                    except Exception as e:
                        logger.warning(f"Failed to get status for machine {machine_id}: {e}")
                        detailed_status.append({
                            "id": machine_id,
                            "error": str(e),
                            "basic_info": machine
                        })
            
            return {
                "app_name": self.app_name,
                "machine_count": len(detailed_status),
                "machines": detailed_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get machines status: {e}")
            raise MachineManagerError(f"Status check failed: {e}")
    
    async def update_all_machines_image(self, new_image: str) -> Dict[str, Any]:
        """
        Update all machines to use a new image
        Production-safe with proper leasing and error handling
        """
        try:
            machines_list = await self.fly_agent.list_machines(self.app_name)
            results = []
            
            for machine in machines_list:
                machine_id = machine.get("id")
                if not machine_id:
                    continue
                
                try:
                    # Get current machine config
                    current_status = await self.fly_agent.get_machine_status(self.app_name, machine_id)
                    current_config = current_status.get("config", {})
                    
                    # Update image in config
                    new_config = current_config.copy()
                    new_config["image"] = new_image
                    
                    # Update machine with lease
                    result = await self.update_machine_with_lease(machine_id, new_config)
                    
                    results.append({
                        "machine_id": machine_id,
                        "success": True,
                        "result": result
                    })
                    
                    logger.info(f"Updated machine {machine_id} to image {new_image}")
                    
                except Exception as e:
                    logger.error(f"Failed to update machine {machine_id}: {e}")
                    results.append({
                        "machine_id": machine_id,
                        "success": False,
                        "error": str(e)
                    })
            
            success_count = sum(1 for r in results if r["success"])
            total_count = len(results)
            
            return {
                "app_name": self.app_name,
                "new_image": new_image,
                "total_machines": total_count,
                "successful_updates": success_count,
                "failed_updates": total_count - success_count,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to update machines: {e}")
            raise MachineManagerError(f"Bulk update failed: {e}")
    
    async def cleanup_stopped_machines(self) -> Dict[str, Any]:
        """Clean up stopped or failed machines"""
        try:
            machines_list = await self.fly_agent.list_machines(self.app_name)
            cleanup_results = []
            
            for machine in machines_list:
                machine_id = machine.get("id")
                if not machine_id:
                    continue
                
                try:
                    status = await self.fly_agent.get_machine_status(self.app_name, machine_id)
                    state = status.get("state", "").lower()
                    
                    if state in ["stopped", "failed", "destroyed"]:
                        logger.info(f"Cleaning up machine {machine_id} (state: {state})")
                        
                        # Try to destroy the machine
                        endpoint = f"/apps/{self.app_name}/machines/{machine_id}"
                        await self.fly_agent.machines_request("DELETE", endpoint)
                        
                        cleanup_results.append({
                            "machine_id": machine_id,
                            "state": state,
                            "action": "destroyed",
                            "success": True
                        })
                        
                except Exception as e:
                    logger.warning(f"Failed to cleanup machine {machine_id}: {e}")
                    cleanup_results.append({
                        "machine_id": machine_id,
                        "action": "cleanup_failed",
                        "error": str(e),
                        "success": False
                    })
            
            return {
                "app_name": self.app_name,
                "cleanup_results": cleanup_results,
                "machines_cleaned": len([r for r in cleanup_results if r["success"]]),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Machine cleanup failed: {e}")
            raise MachineManagerError(f"Cleanup failed: {e}")

# Factory function for easy instantiation
def create_machine_manager(app_name: str = "sophia-intel") -> AdvancedMachineManager:
    """Create an advanced machine manager"""
    return AdvancedMachineManager(app_name)

# CLI interface for direct execution
if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="SOPHIA V4 Machine Management")
    parser.add_argument("--app", default="sophia-intel", help="Fly.io app name")
    parser.add_argument("--status", action="store_true", help="Get all machines status")
    parser.add_argument("--restart", help="Restart specific machine by ID")
    parser.add_argument("--stop", help="Stop specific machine by ID")
    parser.add_argument("--update-image", help="Update all machines to new image")
    parser.add_argument("--cleanup", action="store_true", help="Cleanup stopped machines")
    
    args = parser.parse_args()
    
    manager = create_machine_manager(args.app)
    
    try:
        if args.status:
            result = asyncio.run(manager.get_all_machines_status())
        elif args.restart:
            result = asyncio.run(manager.restart_machine_safe(args.restart))
        elif args.stop:
            result = asyncio.run(manager.stop_machine_safe(args.stop))
        elif args.update_image:
            result = asyncio.run(manager.update_all_machines_image(args.update_image))
        elif args.cleanup:
            result = asyncio.run(manager.cleanup_stopped_machines())
        else:
            parser.print_help()
            sys.exit(1)
        
        print(json.dumps(result, indent=2))
        
    except MachineManagerError as e:
        print(f"❌ Machine management failed: {e}")
        sys.exit(1)

