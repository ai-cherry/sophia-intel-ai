
# Sophia AI Platform - Secret Management Dashboard Integration
# Add this to your main dashboard application

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional

class SecretManagementIntegration:
    """Integration class for secret management in main dashboard"""
    
    def __init__(self, dashboard_instance):
        self.dashboard = dashboard_instance
        self.secret_manager = None
        self.env_manager = None
        self._initialize_managers()
    
    def _initialize_managers(self):
        """Initialize secret and environment managers"""
        try:
            from enhanced_secret_manager import EnhancedSecretManager
            from environment_selector import EnvironmentManager
            
            self.secret_manager = EnhancedSecretManager()
            self.env_manager = EnvironmentManager()
        except ImportError as e:
            print(f"Warning: Could not import secret management modules: {e}")
    
    async def get_secret_health_data(self) -> Dict:
        """Get secret health data for dashboard"""
        if not self.secret_manager:
            return {"error": "Secret manager not available"}
        
        try:
            current_env = self.env_manager.current_env or 'development'
            validation_results = await self.secret_manager.validate_all_secrets(current_env)
            health_report = self.secret_manager.generate_secret_health_report(validation_results)
            
            return {
                "health_score": health_report['health_score'],
                "total_secrets": health_report['summary']['total_secrets'],
                "valid_secrets": health_report['summary']['valid_secrets'],
                "invalid_secrets": health_report['summary']['invalid_secrets'],
                "environment": current_env,
                "status": "healthy" if health_report['health_score'] >= 80 else "warning" if health_report['health_score'] >= 60 else "critical",
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def get_environment_data(self) -> Dict:
        """Get environment data for dashboard"""
        if not self.env_manager:
            return {"error": "Environment manager not available"}
        
        try:
            environments = self.env_manager.list_environments()
            current_status = self.env_manager.get_environment_status()
            
            return {
                "environments": environments['environments'],
                "current_environment": environments['current_environment'],
                "current_status": current_status,
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}
    
    async def switch_environment(self, environment: str) -> Dict:
        """Switch environment"""
        if not self.env_manager:
            return {"error": "Environment manager not available"}
        
        try:
            result = self.env_manager.switch_environment(environment)
            return result
        except Exception as e:
            return {"error": str(e)}

# Usage in main dashboard:
# 1. Import this integration class
# 2. Initialize: secret_integration = SecretManagementIntegration(dashboard_instance)
# 3. Add API endpoints that call the integration methods
# 4. Add dashboard widgets that consume the API endpoints
