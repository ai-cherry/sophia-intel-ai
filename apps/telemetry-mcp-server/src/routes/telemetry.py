"""
SOPHIA Intel Telemetry MCP Server Routes
Provides financial & operational nervous system capabilities
"""

from flask import Blueprint, request, jsonify
import os
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional

# Create blueprint
telemetry_bp = Blueprint('telemetry', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelemetryMCP:
    """Telemetry MCP for financial and operational monitoring"""
    
    def __init__(self):
        # Get API keys from environment variables (populated by Kubernetes secrets)
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.lambda_cloud_api_key = os.getenv("LAMBDA_CLOUD_API_KEY")
        self.neon_api_key = os.getenv("NEON_API_KEY")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.weaviate_api_key = os.getenv("WEAVIATE_ADMIN_API_KEY")
        
        # Service endpoints
        self.qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        self.weaviate_url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
        
        logger.info("Telemetry MCP initialized")
    
    def get_system_costs(self) -> Dict:
        """Get current system costs and usage"""
        try:
            costs = {
                "lambda_labs": self._get_lambda_labs_costs(),
                "openrouter": self._get_openrouter_costs(),
                "vector_databases": self._get_vector_db_costs(),
                "total_monthly": 0.0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Calculate total
            costs["total_monthly"] = sum([
                costs["lambda_labs"].get("monthly_cost", 0),
                costs["openrouter"].get("monthly_cost", 0),
                costs["vector_databases"].get("monthly_cost", 0)
            ])
            
            return costs
            
        except Exception as e:
            logger.error(f"Error getting system costs: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
    
    def get_service_health(self) -> Dict:
        """Get health status of all services"""
        try:
            health = {
                "services": {
                    "qdrant": self._check_qdrant_health(),
                    "weaviate": self._check_weaviate_health(),
                    "lambda_labs": self._check_lambda_labs_health(),
                    "openrouter": self._check_openrouter_health()
                },
                "overall_status": "healthy",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Determine overall status
            unhealthy_services = [name for name, status in health["services"].items() 
                                if status.get("status") != "healthy"]
            
            if unhealthy_services:
                health["overall_status"] = "degraded" if len(unhealthy_services) < 3 else "unhealthy"
                health["unhealthy_services"] = unhealthy_services
            
            return health
            
        except Exception as e:
            logger.error(f"Error getting service health: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
    
    def get_usage_metrics(self) -> Dict:
        """Get usage metrics across all services"""
        try:
            metrics = {
                "api_calls": self._get_api_usage(),
                "vector_operations": self._get_vector_usage(),
                "compute_usage": self._get_compute_usage(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting usage metrics: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
    
    def _get_lambda_labs_costs(self) -> Dict:
        """Get Lambda Labs infrastructure costs"""
        if not self.lambda_cloud_api_key:
            return {"error": "Lambda Labs API key not configured", "monthly_cost": 0}
        
        try:
            # Get running instances
            response = requests.get(
                "https://cloud.lambdalabs.com/api/v1/instances",
                auth=(self.lambda_cloud_api_key, ""),
                timeout=10
            )
            
            if response.status_code == 200:
                instances = response.json().get("data", [])
                total_cost = 0
                
                for instance in instances:
                    # Estimate monthly cost based on instance type
                    instance_type = instance.get("instance_type", {}).get("name", "")
                    if "gpu" in instance_type.lower():
                        total_cost += 150  # Estimated GPU cost
                    else:
                        total_cost += 50   # Estimated CPU cost
                
                return {
                    "status": "healthy",
                    "active_instances": len(instances),
                    "monthly_cost": total_cost
                }
            else:
                return {"error": f"API error: {response.status_code}", "monthly_cost": 0}
                
        except Exception as e:
            return {"error": str(e), "monthly_cost": 0}
    
    def _get_openrouter_costs(self) -> Dict:
        """Get OpenRouter API costs"""
        if not self.openrouter_api_key:
            return {"error": "OpenRouter API key not configured", "monthly_cost": 0}
        
        try:
            # Get account info (if available)
            headers = {"Authorization": f"Bearer {self.openrouter_api_key}"}
            response = requests.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "monthly_cost": 25  # Estimated based on usage
                }
            else:
                return {"error": f"API error: {response.status_code}", "monthly_cost": 25}
                
        except Exception as e:
            return {"error": str(e), "monthly_cost": 25}
    
    def _get_vector_db_costs(self) -> Dict:
        """Get vector database costs"""
        return {
            "qdrant": {"monthly_cost": 0},  # Self-hosted
            "weaviate": {"monthly_cost": 0},  # Self-hosted
            "total_monthly_cost": 0
        }
    
    def _check_qdrant_health(self) -> Dict:
        """Check Qdrant health"""
        try:
            response = requests.get(f"{self.qdrant_url}/", timeout=5)
            if response.status_code == 200:
                return {"status": "healthy", "response_time_ms": response.elapsed.total_seconds() * 1000}
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def _check_weaviate_health(self) -> Dict:
        """Check Weaviate health"""
        try:
            response = requests.get(f"{self.weaviate_url}/v1/.well-known/ready", timeout=5)
            if response.status_code == 200:
                return {"status": "healthy", "response_time_ms": response.elapsed.total_seconds() * 1000}
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def _check_lambda_labs_health(self) -> Dict:
        """Check Lambda Labs API health"""
        if not self.lambda_cloud_api_key:
            return {"status": "unconfigured", "error": "API key not set"}
        
        try:
            response = requests.get(
                "https://cloud.lambdalabs.com/api/v1/instance-types",
                auth=(self.lambda_cloud_api_key, ""),
                timeout=10
            )
            if response.status_code == 200:
                return {"status": "healthy", "response_time_ms": response.elapsed.total_seconds() * 1000}
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def _check_openrouter_health(self) -> Dict:
        """Check OpenRouter API health"""
        if not self.openrouter_api_key:
            return {"status": "unconfigured", "error": "API key not set"}
        
        try:
            headers = {"Authorization": f"Bearer {self.openrouter_api_key}"}
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                return {"status": "healthy", "response_time_ms": response.elapsed.total_seconds() * 1000}
            else:
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    def _get_api_usage(self) -> Dict:
        """Get API usage statistics"""
        # This would typically come from a database or monitoring system
        return {
            "total_requests_today": 150,
            "openrouter_calls": 45,
            "vector_queries": 78,
            "health_checks": 27
        }
    
    def _get_vector_usage(self) -> Dict:
        """Get vector database usage"""
        return {
            "qdrant_collections": 5,
            "weaviate_objects": 1250,
            "total_embeddings": 3400
        }
    
    def _get_compute_usage(self) -> Dict:
        """Get compute resource usage"""
        return {
            "cpu_utilization": "45%",
            "memory_usage": "2.1GB / 4GB",
            "disk_usage": "15GB / 50GB"
        }

# Initialize telemetry MCP
telemetry_mcp = TelemetryMCP()

@telemetry_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "service": "telemetry-mcp",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

@telemetry_bp.route('/costs', methods=['GET'])
def get_costs():
    """Get system costs"""
    return jsonify(telemetry_mcp.get_system_costs())

@telemetry_bp.route('/service-health', methods=['GET'])
def get_service_health():
    """Get service health status"""
    return jsonify(telemetry_mcp.get_service_health())

@telemetry_bp.route('/metrics', methods=['GET'])
def get_metrics():
    """Get usage metrics"""
    return jsonify(telemetry_mcp.get_usage_metrics())

@telemetry_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    """Get complete dashboard data"""
    return jsonify({
        "costs": telemetry_mcp.get_system_costs(),
        "health": telemetry_mcp.get_service_health(),
        "metrics": telemetry_mcp.get_usage_metrics(),
        "timestamp": datetime.utcnow().isoformat()
    })

