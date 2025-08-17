"""
SOPHIA Intel Application Bootstrap
Proper dependency injection and service lifecycle management
"""

import asyncio
import logging
from typing import Dict, Any

from backend.core.dependency_container import DependencyContainer
from backend.core.service_registry import ServiceRegistry
from backend.config.settings import SophiaConfig, config

# Import service classes
from backend.domains.chat.service_v2 import ChatService

logger = logging.getLogger(__name__)


class SophiaApplication:
    """Main application class with proper architecture"""
    
    def __init__(self):
        self.container = DependencyContainer()
        self.settings = config
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the application"""
        if self._initialized:
            return
        
        try:
            # Register core services
            self._register_services()
            
            # Initialize all services
            await self.container.initialize_all()
            
            # Initialize service registry
            ServiceRegistry.initialize(self.container)
            
            self._initialized = True
            logger.info("SOPHIA Intel application initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            await self.shutdown()
            raise
    
    async def shutdown(self) -> None:
        """Shutdown the application gracefully"""
        try:
            await self.container.shutdown_all()
            self._initialized = False
            logger.info("SOPHIA Intel application shutdown complete")
        except Exception as e:
            logger.error(f"Error during application shutdown: {e}")
    
    def _register_services(self) -> None:
        """Register all services with their dependencies"""
        
        # Chat Service - no dependencies for now
        self.container.register_service(
            name="chat_service",
            service_class=ChatService,
            dependencies=[],
            config={"settings": self.settings}
        )
        
        # Future services can be registered here with proper dependencies
        # Example:
        # self.container.register_service(
        #     name="research_service", 
        #     service_class=ResearchService,
        #     dependencies=["chat_service"],
        #     config={"settings": self.settings}
        # )
    
    async def health_check(self) -> Dict[str, Any]:
        """Application health check"""
        if not self._initialized:
            return {
                "status": "not_initialized",
                "message": "Application not initialized"
            }
        
        return await self.container.health_check_all()
    
    def get_service(self, name: str):
        """Get a service by name"""
        return self.container.get_service(name)
    
    @property
    def is_initialized(self) -> bool:
        """Check if application is initialized"""
        return self._initialized


# Global application instance
app = SophiaApplication()


async def get_application() -> SophiaApplication:
    """Get the initialized application instance"""
    if not app.is_initialized:
        await app.initialize()
    return app


async def main():
    """Main entry point for testing"""
    try:
        # Initialize application
        await app.initialize()
        
        # Test chat service
        chat_service = app.get_service("chat_service")
        
        # Test health check
        health = await app.health_check()
        print("Application Health:", health)
        
        # Test chat functionality
        from backend.domains.chat.models import ChatRequest
        
        request = ChatRequest(
            message="What is Python programming?",
            session_id="test_session_123"
        )
        
        response = await chat_service.process_chat_request(request)
        print("Chat Response:", response.message)
        print("Backend Used:", response.backend_used)
        
    except Exception as e:
        logger.error(f"Application error: {e}")
    finally:
        await app.shutdown()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

