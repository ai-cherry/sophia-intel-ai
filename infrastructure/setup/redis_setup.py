#!/usr/bin/env python3
"""
Redis Setup and Configuration for Sophia AI Platform
Implements L1 cache layer with namespace isolation and performance optimization
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

class RedisSetup:
    """Redis setup and configuration manager"""

    def __init__(self, config_path: str | None = None):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.redis_client = None

    def _load_config(self, config_path: str | None) -> dict[str, Any]:
        """Load Redis configuration"""
        if config_path and Path(config_path).exists():
            with open(config_path) as f:
                return json.load(f)

        return {
            "redis_host": os.getenv("REDIS_HOST", "localhost"),
            "redis_port": int(os.getenv("REDIS_PORT", "6379")),
            "redis_password": os.getenv("REDIS_PASSWORD", ""),
            "redis_db": int(os.getenv("REDIS_DB", "0")),
            "max_connections": 100,
            "socket_timeout": 5,
            "socket_connect_timeout": 5,
            "retry_on_timeout": True,
            "health_check_interval": 30,
            "namespaces": ["business", "coding", "shared"],
            "ttl_defaults": {
                "short_term": 3600,  # 1 hour
                "medium_term": 86400,  # 24 hours
                "long_term": 604800,  # 7 days
            },
        }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger("redis_setup")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - REDIS_SETUP - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def setup_redis(self) -> bool:
        """Setup Redis connection and configuration"""
        try:
            self.logger.info("Starting Redis setup...")

            # Check if Redis is running
            if not await self._check_redis_running():
                self.logger.info("Redis not running, attempting to start...")
                if not await self._start_redis():
                    return False

            # Create Redis connection
            if not await self._create_connection():
                return False

            # Configure Redis for Sophia AI
            if not await self._configure_redis():
                return False

            # Setup namespace isolation
            if not await self._setup_namespaces():
                return False

            # Validate setup
            if not await self._validate_setup():
                return False

            self.logger.info("Redis setup completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Redis setup failed: {e}")
            return False

    async def _check_redis_running(self) -> bool:
        """Check if Redis is running"""
        try:
            # Try to connect to Redis
            sophia_client = redis.Redis(
                host=self.config["redis_host"],
                port=self.config["redis_port"],
                password=self.config["redis_password"] or None,
                socket_timeout=2,
                socket_connect_timeout=2,
            )

            await sophia_client.ping()
            await sophia_client.close()

            self.logger.info("Redis is running")
            return True

        except Exception as e:
            self.logger.info(f"Redis not accessible: {e}")
            return False

    async def _start_redis(self) -> bool:
        """Start Redis server"""
        try:
            # Check if Redis is installed
            result = subprocess.run(
                ["which", "redis-server"], capture_output=True, text=True
            )

            if result.returncode != 0:
                self.logger.info("Installing Redis...")
                install_result = subprocess.run(
                    [
                        "sudo",
                        "apt-get",
                        "update",
                        "&&",
                        "sudo",
                        "apt-get",
                        "install",
                        "-y",
                        "redis-server",
                    ],
                    capture_output=True,
                    text=True,
                    shell=True,
                )

                if install_result.returncode != 0:
                    self.logger.error("Failed to install Redis")
                    return False

            # Start Redis server
            self.logger.info("Starting Redis server...")
            start_result = subprocess.run(
                ["sudo", "systemctl", "start", "redis-server"],
                capture_output=True,
                text=True,
            )

            if start_result.returncode != 0:
                # Try starting Redis directly
                subprocess.Popen(
                    [
                        "redis-server",
                        "--daemonize",
                        "yes",
                        "--port",
                        str(self.config["redis_port"]),
                    ]
                )

            # Wait for Redis to start
            await asyncio.sleep(3)

            # Verify Redis is running
            return await self._check_redis_running()

        except Exception as e:
            self.logger.error(f"Failed to start Redis: {e}")
            return False

    async def _create_connection(self) -> bool:
        """Create Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=self.config["redis_host"],
                port=self.config["redis_port"],
                password=self.config["redis_password"] or None,
                db=self.config["redis_db"],
                max_connections=self.config["max_connections"],
                socket_timeout=self.config["socket_timeout"],
                socket_connect_timeout=self.config["socket_connect_timeout"],
                retry_on_timeout=self.config["retry_on_timeout"],
                decode_responses=True,
            )

            # Test connection
            await self.redis_client.ping()

            self.logger.info("Redis connection established")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create Redis connection: {e}")
            return False

    async def _configure_redis(self) -> bool:
        """Configure Redis for optimal performance"""
        try:
            # Set Redis configuration for Sophia AI
            config_commands = [
                ("maxmemory-policy", "allkeys-lru"),
                ("timeout", "300"),
                ("tcp-keepalive", "60"),
                ("save", "900 1 300 10 60 10000"),  # Background saves
            ]

            for key, value in config_commands:
                try:
                    await self.redis_client.config_set(key, value)
                    self.logger.info(f"Set Redis config: {key} = {value}")
                except Exception as e:
                    self.logger.warning(f"Could not set {key}: {e}")

            return True

        except Exception as e:
            self.logger.error(f"Redis configuration failed: {e}")
            return False

    async def _setup_namespaces(self) -> bool:
        """Setup namespace isolation in Redis"""
        try:
            # Create namespace prefixes and validate isolation
            for namespace in self.config["namespaces"]:
                sophia_key = f"{namespace}:setup_test"
                sophia_value = f"sophia_value_{namespace}"

                # Set test value
                await self.redis_client.set(sophia_key, sophia_value, ex=60)

                # Verify value
                retrieved_value = await self.redis_client.get(sophia_key)
                if retrieved_value != sophia_value:
                    self.logger.error(f"Namespace test failed for {namespace}")
                    return False

                # Clean up test key
                await self.redis_client.delete(sophia_key)

                self.logger.info(f"Namespace {namespace} setup validated")

            return True

        except Exception as e:
            self.logger.error(f"Namespace setup failed: {e}")
            return False

    async def _validate_setup(self) -> bool:
        """Validate complete Redis setup"""
        try:
            # Test basic operations
            sophia_operations = [
                ("SET", "sophia:test:key", "sophia_value"),
                ("GET", "sophia:test:key"),
                ("DEL", "sophia:test:key"),
            ]

            for operation in sophia_operations:
                if operation[0] == "SET":
                    await self.redis_client.set(operation[1], operation[2])
                elif operation[0] == "GET":
                    value = await self.redis_client.get(operation[1])
                    if value != "sophia_value":
                        self.logger.error("Redis GET operation failed")
                        return False
                elif operation[0] == "DEL":
                    await self.redis_client.delete(operation[1])

            # Test namespace isolation
            await self.redis_client.set("business:test", "business_value")
            await self.redis_client.set("coding:test", "coding_value")

            business_value = await self.redis_client.get("business:test")
            coding_value = await self.redis_client.get("coding:test")

            if business_value != "business_value" or coding_value != "coding_value":
                self.logger.error("Namespace isolation test failed")
                return False

            # Clean up test keys
            await self.redis_client.delete("business:test", "coding:test")

            # Test performance
            start_time = time.time()
            for i in range(100):
                await self.redis_client.set(f"perf:test:{i}", f"value_{i}")

            for i in range(100):
                await self.redis_client.get(f"perf:test:{i}")

            # Clean up performance test keys
            keys_to_delete = [f"perf:test:{i}" for i in range(100)]
            await self.redis_client.delete(*keys_to_delete)

            end_time = time.time()
            operations_per_second = 200 / (end_time - start_time)

            self.logger.info(f"Redis performance: {operations_per_second:.0f} ops/sec")

            if operations_per_second < 1000:
                self.logger.warning("Redis performance below expected threshold")

            return True

        except Exception as e:
            self.logger.error(f"Redis validation failed: {e}")
            return False

    async def get_redis_info(self) -> dict[str, Any]:
        """Get Redis server information"""
        try:
            if not self.redis_client:
                return {"error": "Redis client not initialized"}

            info = await self.redis_client.info()

            return {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory_human"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "uptime_in_seconds": info.get("uptime_in_seconds"),
            }

        except Exception as e:
            return {"error": str(e)}

    async def cleanup(self):
        """Cleanup Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            self.logger.info("Redis connection closed")

# Main execution
if __name__ == "__main__":

    async def main():
        print("🔧 Redis Setup for Sophia AI Platform")

        setup = RedisSetup()

        # Setup Redis
        success = await setup.setup_redis()

        if success:
            print("✅ Redis setup completed successfully")

            # Get Redis info
            info = await setup.get_redis_info()
            print("\n📊 Redis Information:")
            for key, value in info.items():
                print(f"   - {key}: {value}")

            # Save setup results
            setup_results = {
                "setup_successful": success,
                "redis_info": info,
                "config": setup.config,
                "timestamp": time.time(),
            }

            with open("redis_setup_results.json", "w") as f:
                json.dump(setup_results, f, indent=2)

            print("\n📄 Setup results saved to: redis_setup_results.json")
        else:
            print("❌ Redis setup failed")

        # Cleanup
        await setup.cleanup()

    asyncio.run(main())
