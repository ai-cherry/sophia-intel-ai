"""
Background Indexing System for Sophia Intel AI
Handles asynchronous indexing of documents and code.
"""

from celery import Celery, Task
from celery.result import AsyncResult
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
import logging
import hashlib
import json
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

# Import indexing dependencies
from app.memory.supermemory_mcp import SupermemoryStore, MemoryEntry, MemoryType
from app.memory.dual_tier_embeddings import DualTierEmbedder
from app.core.config import settings

logger = logging.getLogger(__name__)

# ============================================
# Celery Configuration
# ============================================

celery_app = Celery(
    'sophia_intel_indexing',
    broker=settings.redis_url or 'redis://localhost:6379/0',
    backend=settings.redis_url or 'redis://localhost:6379/0'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # Soft limit at 55 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

# ============================================
# Data Models
# ============================================

class IndexingStatus(str, Enum):
    """Indexing task status."""
    PENDING = "pending"
    STARTED = "started"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class IndexingTask:
    """Represents an indexing task."""
    task_id: str
    path: str
    recursive: bool = True
    force: bool = False
    file_patterns: List[str] = None
    exclude_patterns: List[str] = None
    status: IndexingStatus = IndexingStatus.PENDING
    progress: int = 0
    total_files: int = 0
    indexed_files: int = 0
    failed_files: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

# ============================================
# Indexing Tasks
# ============================================

@celery_app.task(bind=True, name='index_directory')
def index_directory(
    self: Task,
    path: str,
    recursive: bool = True,
    force: bool = False,
    file_patterns: List[str] = None,
    exclude_patterns: List[str] = None
) -> Dict[str, Any]:
    """
    Index a directory of files.
    
    Args:
        path: Directory path to index
        recursive: Include subdirectories
        force: Force reindexing even if already indexed
        file_patterns: File patterns to include (e.g., ['*.py', '*.js'])
        exclude_patterns: Patterns to exclude (e.g., ['__pycache__', '*.pyc'])
    """
    task = IndexingTask(
        task_id=self.request.id,
        path=path,
        recursive=recursive,
        force=force,
        file_patterns=file_patterns or ['*'],
        exclude_patterns=exclude_patterns or []
    )
    
    try:
        task.status = IndexingStatus.STARTED
        task.start_time = datetime.utcnow()
        
        # Update task state
        self.update_state(
            state='PROCESSING',
            meta=task.to_dict()
        )
        
        # Get files to index
        files = collect_files(
            Path(path),
            recursive=recursive,
            include_patterns=task.file_patterns,
            exclude_patterns=task.exclude_patterns
        )
        
        task.total_files = len(files)
        logger.info(f"Found {task.total_files} files to index in {path}")
        
        # Process files in batches
        batch_size = settings.index_batch_size
        
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            
            # Process batch
            results = process_file_batch(batch, force=force)
            
            # Update progress
            task.indexed_files += results['success']
            task.failed_files += results['failed']
            task.progress = int((task.indexed_files / task.total_files) * 100)
            
            # Update task state
            self.update_state(
                state='PROCESSING',
                meta=task.to_dict()
            )
            
            logger.info(f"Indexed batch: {results['success']} success, {results['failed']} failed")
        
        # Complete task
        task.status = IndexingStatus.COMPLETED
        task.end_time = datetime.utcnow()
        task.progress = 100
        
        result = task.to_dict()
        logger.info(f"Indexing completed: {task.indexed_files}/{task.total_files} files")
        
        return result
        
    except Exception as e:
        task.status = IndexingStatus.FAILED
        task.error_message = str(e)
        task.end_time = datetime.utcnow()
        
        logger.error(f"Indexing failed: {e}")
        
        self.update_state(
            state='FAILURE',
            meta=task.to_dict()
        )
        
        raise

@celery_app.task(bind=True, name='index_file')
def index_file(
    self: Task,
    file_path: str,
    force: bool = False
) -> Dict[str, Any]:
    """Index a single file."""
    try:
        # Check if already indexed
        if not force and is_file_indexed(file_path):
            return {
                "status": "skipped",
                "file": file_path,
                "reason": "already_indexed"
            }
        
        # Read file content
        content = read_file_content(file_path)
        
        if not content:
            return {
                "status": "skipped",
                "file": file_path,
                "reason": "empty_or_binary"
            }
        
        # Extract metadata
        metadata = extract_file_metadata(file_path)
        
        # Create memory entry
        memory = MemoryEntry(
            topic=f"File: {Path(file_path).name}",
            content=content,
            source="file_index",
            tags=metadata.get("tags", []),
            memory_type=MemoryType.PROCEDURAL,
            metadata=metadata
        )
        
        # Store in memory system
        result = asyncio.run(store_indexed_content(memory))
        
        return {
            "status": "success",
            "file": file_path,
            "hash_id": result.get("hash_id"),
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Failed to index file {file_path}: {e}")
        return {
            "status": "failed",
            "file": file_path,
            "error": str(e)
        }

@celery_app.task(bind=True, name='update_embeddings')
def update_embeddings(
    self: Task,
    memory_ids: List[str] = None,
    batch_size: int = 100
) -> Dict[str, Any]:
    """Update embeddings for memory entries."""
    try:
        # Get memory store
        memory_store = SupermemoryStore()
        embedder = DualTierEmbedder()
        
        # Get entries to update
        if memory_ids:
            entries = [memory_store.get_memory(mid) for mid in memory_ids]
        else:
            # Get all entries without embeddings
            entries = memory_store.get_entries_without_embeddings()
        
        total = len(entries)
        updated = 0
        failed = 0
        
        # Process in batches
        for i in range(0, total, batch_size):
            batch = entries[i:i + batch_size]
            
            # Generate embeddings
            texts = [e.content for e in batch]
            embeddings = asyncio.run(embedder.get_embeddings_batch(texts))
            
            # Update entries
            for entry, embedding in zip(batch, embeddings):
                if embedding:
                    entry.embedding = embedding
                    memory_store.update_memory(entry)
                    updated += 1
                else:
                    failed += 1
            
            # Update progress
            progress = int((i + len(batch)) / total * 100)
            self.update_state(
                state='PROCESSING',
                meta={
                    'progress': progress,
                    'updated': updated,
                    'failed': failed,
                    'total': total
                }
            )
        
        return {
            "status": "completed",
            "total": total,
            "updated": updated,
            "failed": failed
        }
        
    except Exception as e:
        logger.error(f"Failed to update embeddings: {e}")
        raise

# ============================================
# Helper Functions
# ============================================

def collect_files(
    root_path: Path,
    recursive: bool = True,
    include_patterns: List[str] = None,
    exclude_patterns: List[str] = None
) -> List[Path]:
    """Collect files to index based on patterns."""
    files = []
    
    # Default patterns
    if not include_patterns:
        include_patterns = ['*.py', '*.js', '*.ts', '*.jsx', '*.tsx', '*.md', '*.txt']
    
    if not exclude_patterns:
        exclude_patterns = [
            '__pycache__', '*.pyc', 'node_modules', '.git',
            '*.log', '*.tmp', '.DS_Store', 'venv', '.env'
        ]
    
    # Walk directory
    if recursive:
        for pattern in include_patterns:
            files.extend(root_path.rglob(pattern))
    else:
        for pattern in include_patterns:
            files.extend(root_path.glob(pattern))
    
    # Filter excludes
    filtered = []
    for file in files:
        skip = False
        for exclude in exclude_patterns:
            if exclude in str(file):
                skip = True
                break
        if not skip and file.is_file():
            filtered.append(file)
    
    return filtered

def process_file_batch(
    files: List[Path],
    force: bool = False
) -> Dict[str, int]:
    """Process a batch of files."""
    success = 0
    failed = 0
    
    for file in files:
        try:
            result = index_file.apply_async(
                args=[str(file), force]
            ).get(timeout=30)
            
            if result['status'] == 'success':
                success += 1
            else:
                failed += 1
                
        except Exception as e:
            logger.error(f"Failed to index {file}: {e}")
            failed += 1
    
    return {'success': success, 'failed': failed}

def is_file_indexed(file_path: str) -> bool:
    """Check if file is already indexed."""
    # Generate file hash
    file_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]
    
    # Check in memory store
    # This would query the database to see if this file hash exists
    return False  # Simplified for now

def read_file_content(file_path: str) -> Optional[str]:
    """Read file content safely."""
    try:
        path = Path(file_path)
        
        # Check file size (skip large files)
        if path.stat().st_size > 10 * 1024 * 1024:  # 10MB
            return None
        
        # Try to read as text
        try:
            return path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Try other encodings
            for encoding in ['latin-1', 'cp1252']:
                try:
                    return path.read_text(encoding=encoding)
                except:
                    continue
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return None

def extract_file_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from file."""
    path = Path(file_path)
    
    metadata = {
        "file_path": str(path),
        "file_name": path.name,
        "file_type": path.suffix,
        "file_size": path.stat().st_size,
        "modified_time": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
        "tags": []
    }
    
    # Add tags based on file type
    if path.suffix in ['.py']:
        metadata['tags'].append('python')
    elif path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
        metadata['tags'].append('javascript')
    elif path.suffix in ['.md']:
        metadata['tags'].append('documentation')
    
    # Add directory as tag
    if path.parent.name:
        metadata['tags'].append(path.parent.name)
    
    return metadata

async def store_indexed_content(memory: MemoryEntry) -> Dict[str, Any]:
    """Store indexed content in memory system."""
    # This would connect to the actual memory store
    # For now, return mock result
    return {
        "hash_id": hashlib.sha256(memory.content.encode()).hexdigest()[:16],
        "status": "stored"
    }

# ============================================
# Task Management
# ============================================

class IndexingManager:
    """Manages indexing tasks."""
    
    @staticmethod
    def start_indexing(
        path: str,
        **kwargs
    ) -> str:
        """Start an indexing task."""
        task = index_directory.apply_async(
            args=[path],
            kwargs=kwargs
        )
        return task.id
    
    @staticmethod
    def get_task_status(task_id: str) -> Dict[str, Any]:
        """Get status of an indexing task."""
        result = AsyncResult(task_id, app=celery_app)
        
        if result.state == 'PENDING':
            return {
                'task_id': task_id,
                'status': 'pending',
                'progress': 0
            }
        elif result.state == 'PROCESSING':
            return {
                'task_id': task_id,
                'status': 'processing',
                **result.info
            }
        elif result.state == 'SUCCESS':
            return {
                'task_id': task_id,
                'status': 'completed',
                **result.result
            }
        else:  # FAILURE
            return {
                'task_id': task_id,
                'status': 'failed',
                'error': str(result.info)
            }
    
    @staticmethod
    def cancel_task(task_id: str) -> bool:
        """Cancel an indexing task."""
        celery_app.control.revoke(task_id, terminate=True)
        return True
    
    @staticmethod
    def list_active_tasks() -> List[Dict[str, Any]]:
        """List all active indexing tasks."""
        inspect = celery_app.control.inspect()
        active = inspect.active()
        
        tasks = []
        if active:
            for worker, task_list in active.items():
                for task in task_list:
                    if task['name'].startswith('index_'):
                        tasks.append({
                            'task_id': task['id'],
                            'name': task['name'],
                            'args': task['args'],
                            'worker': worker
                        })
        
        return tasks

# Export components
__all__ = [
    'celery_app',
    'index_directory',
    'index_file',
    'update_embeddings',
    'IndexingManager',
    'IndexingTask',
    'IndexingStatus'
]