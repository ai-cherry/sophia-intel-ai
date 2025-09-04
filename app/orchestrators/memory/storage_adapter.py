"""
Storage Adapter for Memory System
==================================
Handles local and cloud storage with automatic fallback
"""

import json
import pickle
import logging
from typing import Any, Dict, Optional
from pathlib import Path
from abc import ABC, abstractmethod
import asyncio
import aiofiles
import os

logger = logging.getLogger(__name__)


class StorageAdapter(ABC):
    """Abstract base class for storage adapters"""
    
    @abstractmethod
    async def save(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """Save data to storage"""
        pass
        
    @abstractmethod
    async def load(self, key: str) -> Optional[Any]:
        """Load data from storage"""
        pass
        
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete data from storage"""
        pass
        
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass


class LocalStorageAdapter(StorageAdapter):
    """Local file system storage adapter"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def _get_file_path(self, key: str) -> Path:
        """Get file path for key"""
        # Sanitize key for filesystem
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.base_path / f"{safe_key}.pkl"
        
    async def save(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """Save data to local file"""
        try:
            file_path = self._get_file_path(key)
            
            # Serialize data
            serialized = pickle.dumps(data)
            
            # Write to file asynchronously
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(serialized)
                
            # Store TTL metadata if provided
            if ttl:
                meta_path = file_path.with_suffix('.meta')
                import time
                meta_data = {
                    'expires_at': time.time() + ttl,
                    'created_at': time.time()
                }
                async with aiofiles.open(meta_path, 'w') as f:
                    await f.write(json.dumps(meta_data))
                    
            logger.debug(f"Saved data to local storage: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to local storage: {e}")
            return False
            
    async def load(self, key: str) -> Optional[Any]:
        """Load data from local file"""
        try:
            file_path = self._get_file_path(key)
            
            if not file_path.exists():
                return None
                
            # Check TTL if metadata exists
            meta_path = file_path.with_suffix('.meta')
            if meta_path.exists():
                async with aiofiles.open(meta_path, 'r') as f:
                    meta_data = json.loads(await f.read())
                    import time
                    if meta_data.get('expires_at', float('inf')) < time.time():
                        # Data expired
                        await self.delete(key)
                        return None
                        
            # Read data
            async with aiofiles.open(file_path, 'rb') as f:
                serialized = await f.read()
                
            data = pickle.loads(serialized)
            logger.debug(f"Loaded data from local storage: {key}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading from local storage: {e}")
            return None
            
    async def delete(self, key: str) -> bool:
        """Delete data from local storage"""
        try:
            file_path = self._get_file_path(key)
            meta_path = file_path.with_suffix('.meta')
            
            if file_path.exists():
                file_path.unlink()
            if meta_path.exists():
                meta_path.unlink()
                
            logger.debug(f"Deleted from local storage: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from local storage: {e}")
            return False
            
    async def exists(self, key: str) -> bool:
        """Check if key exists in storage"""
        file_path = self._get_file_path(key)
        return file_path.exists()


class S3StorageAdapter(StorageAdapter):
    """AWS S3 storage adapter for cloud deployments"""
    
    def __init__(self, bucket_name: str, region: str = 'us-east-1'):
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize S3 client"""
        try:
            import boto3
            self.s3_client = boto3.client(
                's3',
                region_name=self.region
            )
        except ImportError:
            logger.warning("boto3 not installed, S3 storage unavailable")
        except Exception as e:
            logger.error(f"Error initializing S3 client: {e}")
            
    async def save(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """Save data to S3"""
        if not self.s3_client:
            return False
            
        try:
            # Serialize data
            serialized = pickle.dumps(data)
            
            # Prepare metadata
            metadata = {}
            if ttl:
                import time
                metadata['expires-at'] = str(int(time.time() + ttl))
                
            # Upload to S3
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.s3_client.put_object,
                self.bucket_name,
                key,
                serialized,
                metadata
            )
            
            logger.debug(f"Saved data to S3: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving to S3: {e}")
            return False
            
    async def load(self, key: str) -> Optional[Any]:
        """Load data from S3"""
        if not self.s3_client:
            return None
            
        try:
            # Get object from S3
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                self.s3_client.get_object,
                self.bucket_name,
                key
            )
            
            # Check expiration
            metadata = response.get('Metadata', {})
            if 'expires-at' in metadata:
                import time
                if float(metadata['expires-at']) < time.time():
                    # Data expired
                    await self.delete(key)
                    return None
                    
            # Deserialize data
            serialized = response['Body'].read()
            data = pickle.loads(serialized)
            
            logger.debug(f"Loaded data from S3: {key}")
            return data
            
        except self.s3_client.exceptions.NoSuchKey:
            return None
        except Exception as e:
            logger.error(f"Error loading from S3: {e}")
            return None
            
    async def delete(self, key: str) -> bool:
        """Delete data from S3"""
        if not self.s3_client:
            return False
            
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.s3_client.delete_object,
                self.bucket_name,
                key
            )
            
            logger.debug(f"Deleted from S3: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting from S3: {e}")
            return False
            
    async def exists(self, key: str) -> bool:
        """Check if key exists in S3"""
        if not self.s3_client:
            return False
            
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.s3_client.head_object,
                self.bucket_name,
                key
            )
            return True
        except self.s3_client.exceptions.NoSuchKey:
            return False
        except Exception:
            return False


class HybridStorageAdapter(StorageAdapter):
    """Hybrid storage with local cache and cloud backup"""
    
    def __init__(self, local_adapter: StorageAdapter, cloud_adapter: StorageAdapter):
        self.local = local_adapter
        self.cloud = cloud_adapter
        
    async def save(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """Save to both local and cloud storage"""
        # Save to local first (faster)
        local_success = await self.local.save(key, data, ttl)
        
        # Then save to cloud in background
        if self.cloud:
            asyncio.create_task(self.cloud.save(key, data, ttl))
            
        return local_success
        
    async def load(self, key: str) -> Optional[Any]:
        """Load from local first, fallback to cloud"""
        # Try local first
        data = await self.local.load(key)
        if data is not None:
            return data
            
        # Fallback to cloud
        if self.cloud:
            data = await self.cloud.load(key)
            if data is not None:
                # Cache locally for next time
                await self.local.save(key, data)
                return data
                
        return None
        
    async def delete(self, key: str) -> bool:
        """Delete from both storages"""
        local_success = await self.local.delete(key)
        
        if self.cloud:
            cloud_success = await self.cloud.delete(key)
            return local_success and cloud_success
            
        return local_success
        
    async def exists(self, key: str) -> bool:
        """Check if exists in either storage"""
        if await self.local.exists(key):
            return True
            
        if self.cloud:
            return await self.cloud.exists(key)
            
        return False


class StorageFactory:
    """Factory for creating appropriate storage adapter"""
    
    @staticmethod
    def create_adapter(config: Dict[str, Any]) -> StorageAdapter:
        """Create storage adapter based on configuration"""
        storage_type = config.get('type', 'local')
        
        if storage_type == 'local':
            base_path = config.get('base_path', '/tmp/ai_memory')
            return LocalStorageAdapter(base_path)
            
        elif storage_type == 'cloud':
            provider = config.get('provider', 'local')
            
            if provider == 's3':
                bucket = config.get('bucket', 'ai-memory-storage')
                region = config.get('region', 'us-east-1')
                return S3StorageAdapter(bucket, region)
            else:
                # Fallback to local if cloud provider not supported
                local_cache = config.get('local_cache', '/tmp/ai_memory_cache')
                return LocalStorageAdapter(local_cache)
                
        elif storage_type == 'hybrid':
            # Create both local and cloud adapters
            local_path = config.get('local_path', '/tmp/ai_memory_local')
            local_adapter = LocalStorageAdapter(local_path)
            
            cloud_config = config.get('cloud', {})
            cloud_adapter = StorageFactory.create_adapter(cloud_config)
            
            return HybridStorageAdapter(local_adapter, cloud_adapter)
            
        else:
            # Default to local storage
            return LocalStorageAdapter('/tmp/ai_memory_default')