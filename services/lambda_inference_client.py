"""
SOPHIA Intel Lambda Labs Inference Client
Manages inference requests to GH200 servers with fallback to OpenRouter
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import aiohttp
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ServerStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class InferenceServer:
    name: str
    url: str
    role: str  # primary or secondary
    status: ServerStatus = ServerStatus.UNKNOWN
    last_check: Optional[datetime] = None
    response_time: float = 0.0
    error_count: int = 0

class LambdaInferenceClient:
    """Client for managing Lambda Labs GH200 inference servers"""
    
    def __init__(self):
        self.primary_url = os.getenv("LAMBDA_PRIMARY_URL", "http://192.222.51.223:8000")
        self.secondary_url = os.getenv("LAMBDA_SECONDARY_URL", "http://192.222.50.242:8000")
        
        self.servers = [
            InferenceServer("sophia-gh200-primary", self.primary_url, "primary"),
            InferenceServer("sophia-gh200-secondary", self.secondary_url, "secondary")
        ]
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 300  # 5 minutes
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "SOPHIA-Intel/1.0"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def health_check(self, server: InferenceServer) -> bool:
        """Check health of a specific server"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        try:
            start_time = datetime.now()
            async with self.session.get(f"{server.url}/health") as response:
                end_time = datetime.now()
                server.response_time = (end_time - start_time).total_seconds()
                server.last_check = end_time
                
                if response.status == 200:
                    health_data = await response.json()
                    server.status = ServerStatus.HEALTHY if health_data.get("status") == "healthy" else ServerStatus.UNHEALTHY
                    server.error_count = 0
                    return True
                else:
                    server.status = ServerStatus.UNHEALTHY
                    server.error_count += 1
                    return False
                    
        except Exception as e:
            logger.warning(f"Health check failed for {server.name}: {e}")
            server.status = ServerStatus.UNHEALTHY
            server.error_count += 1
            server.last_check = datetime.now()
            return False
    
    async def check_all_servers(self) -> Dict[str, bool]:
        """Check health of all servers"""
        results = {}
        tasks = [self.health_check(server) for server in self.servers]
        health_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for server, result in zip(self.servers, health_results):
            if isinstance(result, Exception):
                results[server.name] = False
                logger.error(f"Health check error for {server.name}: {result}")
            else:
                results[server.name] = result
        
        return results
    
    def get_healthy_servers(self) -> List[InferenceServer]:
        """Get list of healthy servers"""
        return [server for server in self.servers if server.status == ServerStatus.HEALTHY]
    
    def get_primary_server(self) -> Optional[InferenceServer]:
        """Get primary server if healthy"""
        primary = next((s for s in self.servers if s.role == "primary"), None)
        return primary if primary and primary.status == ServerStatus.HEALTHY else None
    
    def get_best_server(self) -> Optional[InferenceServer]:
        """Get the best available server (primary preferred)"""
        # Try primary first
        primary = self.get_primary_server()
        if primary:
            return primary
        
        # Fall back to any healthy server
        healthy_servers = self.get_healthy_servers()
        if healthy_servers:
            # Sort by response time
            return min(healthy_servers, key=lambda s: s.response_time)
        
        return None
    
    async def run_inference(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Run inference on the best available server"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        # Check server health first
        await self.check_all_servers()
        
        # Get best server
        server = self.get_best_server()
        if not server:
            raise RuntimeError("No healthy inference servers available")
        
        # Prepare request
        request_data = {
            "prompt": prompt,
            "max_tokens": kwargs.get("max_tokens", 512),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9)
        }
        
        try:
            logger.info(f"Running inference on {server.name}")
            async with self.session.post(
                f"{server.url}/inference",
                json=request_data
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Inference completed on {server.name}")
                    return {
                        "response": result.get("response", ""),
                        "server": server.name,
                        "tokens_generated": result.get("tokens_generated", 0),
                        "processing_time": result.get("processing_time", 0.0)
                    }
                else:
                    error_text = await response.text()
                    raise RuntimeError(f"Inference failed: HTTP {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Inference error on {server.name}: {e}")
            server.error_count += 1
            
            # Try fallback server if available
            healthy_servers = [s for s in self.get_healthy_servers() if s != server]
            if healthy_servers:
                fallback_server = healthy_servers[0]
                logger.info(f"Trying fallback server: {fallback_server.name}")
                try:
                    async with self.session.post(
                        f"{fallback_server.url}/inference",
                        json=request_data
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                "response": result.get("response", ""),
                                "server": fallback_server.name,
                                "tokens_generated": result.get("tokens_generated", 0),
                                "processing_time": result.get("processing_time", 0.0)
                            }
                except Exception as fallback_error:
                    logger.error(f"Fallback inference failed: {fallback_error}")
            
            raise e
    
    async def get_server_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all servers"""
        await self.check_all_servers()
        
        status = {
            "timestamp": datetime.now().isoformat(),
            "servers": []
        }
        
        for server in self.servers:
            server_info = {
                "name": server.name,
                "url": server.url,
                "role": server.role,
                "status": server.status.value,
                "last_check": server.last_check.isoformat() if server.last_check else None,
                "response_time": server.response_time,
                "error_count": server.error_count
            }
            status["servers"].append(server_info)
        
        healthy_count = len(self.get_healthy_servers())
        status["summary"] = {
            "total_servers": len(self.servers),
            "healthy_servers": healthy_count,
            "unhealthy_servers": len(self.servers) - healthy_count,
            "primary_healthy": self.get_primary_server() is not None
        }
        
        return status

# Convenience functions for backward compatibility
async def run_lambda_inference(prompt: str, **kwargs) -> Dict[str, Any]:
    """Run inference using Lambda Labs servers"""
    async with LambdaInferenceClient() as client:
        return await client.run_inference(prompt, **kwargs)

async def get_lambda_status() -> Dict[str, Any]:
    """Get status of Lambda Labs servers"""
    async with LambdaInferenceClient() as client:
        return await client.get_server_status()

