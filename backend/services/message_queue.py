"""
Message Queue Implementation for SOPHIA Intel
Real async task processing with Celery and Redis
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional, Callable, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from celery import Celery
from celery.result import AsyncResult
from celery.exceptions import Retry, WorkerLostError
import redis.asyncio as redis
from redis.exceptions import ConnectionError

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    STARTED = "started"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"

@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3

class MessageQueue:
    """
    Real message queue implementation with Celery backend
    """
    
    def __init__(self, redis_url: str, queue_name: str = "sophia_intel"):
        self.redis_url = redis_url
        self.queue_name = queue_name
        
        # Initialize Celery app
        self.celery_app = Celery(
            queue_name,
            broker=redis_url,
            backend=redis_url,
            include=['backend.services.message_queue']
        )
        
        # Celery configuration
        self.celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            task_track_started=True,
            task_time_limit=300,  # 5 minutes
            task_soft_time_limit=240,  # 4 minutes
            worker_prefetch_multiplier=1,
            task_acks_late=True,
            worker_disable_rate_limits=False,
            task_compression='gzip',
            result_compression='gzip',
            result_expires=3600,  # 1 hour
            task_routes={
                'chat.*': {'queue': 'chat'},
                'research.*': {'queue': 'research'},
                'mcp.*': {'queue': 'mcp'},
                'intelligence.*': {'queue': 'intelligence'},
            }
        )
        
        # Redis client for direct operations
        self.redis_client = None
        
        # Task registry
        self.task_registry: Dict[str, Callable] = {}
        
        logger.info(f"Message queue initialized with broker: {redis_url}")
    
    async def initialize(self):
        """Initialize Redis client"""
        self.redis_client = redis.from_url(self.redis_url)
        await self.redis_client.ping()
        logger.info("Message queue Redis client initialized")
    
    def register_task(self, name: str, func: Callable, **task_options):
        """Register a task function"""
        task_options.setdefault('bind', True)
        task_options.setdefault('autoretry_for', (Exception,))
        task_options.setdefault('retry_kwargs', {'max_retries': 3, 'countdown': 60})
        
        task = self.celery_app.task(name=name, **task_options)(func)
        self.task_registry[name] = task
        logger.info(f"Task '{name}' registered")
        return task
    
    async def enqueue_task(self, task_name: str, *args, **kwargs) -> str:
        """Enqueue a task for processing"""
        if task_name not in self.task_registry:
            raise ValueError(f"Task '{task_name}' not registered")
        
        task = self.task_registry[task_name]
        
        # Add task metadata
        task_options = kwargs.pop('task_options', {})
        task_options.setdefault('task_id', f"{task_name}_{int(time.time() * 1000)}")
        
        # Enqueue task
        result = task.apply_async(args=args, kwargs=kwargs, **task_options)
        
        # Store task info in Redis
        await self._store_task_info(result.id, task_name, args, kwargs)
        
        logger.info(f"Task '{task_name}' enqueued with ID: {result.id}")
        return result.id
    
    async def get_task_result(self, task_id: str) -> TaskResult:
        """Get task result by ID"""
        result = AsyncResult(task_id, app=self.celery_app)
        
        # Get task info from Redis
        task_info = await self._get_task_info(task_id)
        
        task_result = TaskResult(
            task_id=task_id,
            status=TaskStatus(result.status.lower()),
            result=result.result if result.successful() else None,
            error=str(result.result) if result.failed() else None,
            started_at=task_info.get('started_at'),
            completed_at=task_info.get('completed_at'),
            retry_count=task_info.get('retry_count', 0),
            max_retries=task_info.get('max_retries', 3)
        )
        
        return task_result
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or running task"""
        try:
            self.celery_app.control.revoke(task_id, terminate=True)
            await self._update_task_info(task_id, {'status': 'revoked', 'completed_at': time.time()})
            logger.info(f"Task {task_id} cancelled")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            # Get active tasks
            active_tasks = self.celery_app.control.inspect().active()
            
            # Get scheduled tasks
            scheduled_tasks = self.celery_app.control.inspect().scheduled()
            
            # Get reserved tasks
            reserved_tasks = self.celery_app.control.inspect().reserved()
            
            # Get worker stats
            worker_stats = self.celery_app.control.inspect().stats()
            
            return {
                "active_tasks": len(active_tasks or {}),
                "scheduled_tasks": len(scheduled_tasks or {}),
                "reserved_tasks": len(reserved_tasks or {}),
                "workers": len(worker_stats or {}),
                "worker_stats": worker_stats,
                "registered_tasks": list(self.task_registry.keys())
            }
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {"error": str(e)}
    
    async def _store_task_info(self, task_id: str, task_name: str, args: tuple, kwargs: dict):
        """Store task information in Redis"""
        task_info = {
            "task_name": task_name,
            "args": args,
            "kwargs": kwargs,
            "created_at": time.time(),
            "status": "pending"
        }
        
        await self.redis_client.setex(
            f"task:{task_id}",
            3600,  # 1 hour TTL
            json.dumps(task_info, default=str)
        )
    
    async def _get_task_info(self, task_id: str) -> Dict[str, Any]:
        """Get task information from Redis"""
        try:
            data = await self.redis_client.get(f"task:{task_id}")
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error(f"Failed to get task info for {task_id}: {e}")
        
        return {}
    
    async def _update_task_info(self, task_id: str, updates: Dict[str, Any]):
        """Update task information in Redis"""
        try:
            task_info = await self._get_task_info(task_id)
            task_info.update(updates)
            
            await self.redis_client.setex(
                f"task:{task_id}",
                3600,
                json.dumps(task_info, default=str)
            )
        except Exception as e:
            logger.error(f"Failed to update task info for {task_id}: {e}")
    
    async def close(self):
        """Close message queue connections"""
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Message queue connections closed")

# Global message queue instance
_message_queue: Optional[MessageQueue] = None

def get_message_queue() -> MessageQueue:
    """Get global message queue instance"""
    if _message_queue is None:
        raise RuntimeError("Message queue not initialized")
    return _message_queue

async def initialize_message_queue(redis_url: str, queue_name: str = "sophia_intel") -> MessageQueue:
    """Initialize global message queue"""
    global _message_queue
    _message_queue = MessageQueue(redis_url, queue_name)
    await _message_queue.initialize()
    return _message_queue

# Task definitions for SOPHIA Intel

@dataclass
class ChatTaskData:
    """Chat task data structure"""
    message: str
    user_id: str
    session_id: str
    backend: str
    features: Dict[str, bool]

@dataclass
class ResearchTaskData:
    """Research task data structure"""
    query: str
    depth: str
    sources: List[str]
    user_id: str

@dataclass
class MCPTaskData:
    """MCP task data structure"""
    operation: str
    server_key: str
    parameters: Dict[str, Any]

# Task implementations
async def process_chat_task(task_data: ChatTaskData) -> Dict[str, Any]:
    """Process chat task asynchronously"""
    logger.info(f"Processing chat task for user {task_data.user_id}")
    
    # Import here to avoid circular imports
    from backend.domains.chat.service import ChatService
    
    chat_service = ChatService()
    
    try:
        result = await chat_service.process_message(
            message=task_data.message,
            user_id=task_data.user_id,
            session_id=task_data.session_id,
            backend=task_data.backend,
            features=task_data.features
        )
        
        return {
            "status": "success",
            "result": result,
            "processed_at": time.time()
        }
    except Exception as e:
        logger.error(f"Chat task failed: {e}")
        raise

async def process_research_task(task_data: ResearchTaskData) -> Dict[str, Any]:
    """Process research task asynchronously"""
    logger.info(f"Processing research task: {task_data.query}")
    
    # Import here to avoid circular imports
    from backend.enhanced_web_research import EnhancedWebResearch
    
    research_service = EnhancedWebResearch()
    
    try:
        result = await research_service.comprehensive_research(
            query=task_data.query,
            depth=task_data.depth,
            sources=task_data.sources
        )
        
        return {
            "status": "success",
            "result": result,
            "processed_at": time.time()
        }
    except Exception as e:
        logger.error(f"Research task failed: {e}")
        raise

async def process_mcp_task(task_data: MCPTaskData) -> Dict[str, Any]:
    """Process MCP task asynchronously"""
    logger.info(f"Processing MCP task: {task_data.operation}")
    
    # Import here to avoid circular imports
    from backend.domains.mcp.service import MCPService
    
    mcp_service = MCPService()
    
    try:
        result = await mcp_service.execute_operation(
            operation=task_data.operation,
            server_key=task_data.server_key,
            parameters=task_data.parameters
        )
        
        return {
            "status": "success",
            "result": result,
            "processed_at": time.time()
        }
    except Exception as e:
        logger.error(f"MCP task failed: {e}")
        raise

def register_sophia_tasks(mq: MessageQueue):
    """Register all SOPHIA Intel tasks"""
    
    # Chat tasks
    mq.register_task("chat.process_message", process_chat_task)
    
    # Research tasks
    mq.register_task("research.comprehensive_search", process_research_task)
    
    # MCP tasks
    mq.register_task("mcp.execute_operation", process_mcp_task)
    
    logger.info("All SOPHIA Intel tasks registered")

