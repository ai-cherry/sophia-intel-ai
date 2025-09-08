#!/usr/bin/env python3
"""
Comprehensive Cache Deletion Script for Sophia AI Platform
Clears all cache data from all identified cache systems
"""

import asyncio
import glob
import logging
import os
import shutil
import sys
from pathlib import Path

# Add project paths
sys.path.insert(0, "/appsil/sophia-main")
sys.path.insert(0, "/appsil/sophia-main/mcp_servers")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class CacheCleaner:
    """Comprehensive cache cleaning utility"""

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://redis-cloud.upstash.io:6379")
        self.results = {
            "enhanced_cache": {"cleared": False, "details": {}},
            "performance_cache": {"cleared": False, "details": {}},
            "redis_cache": {"cleared": False, "details": {}},
            "file_cache": {"cleared": False, "details": {}},
            "temp_files": {"cleared": False, "details": {}},
            "errors": [],
        }

    async def clear_all_caches(self):
        """Clear all cache systems"""
        logger.info("🧹 Starting comprehensive cache cleanup...")

        # Clear different cache types
        await self.clear_enhanced_cache_system()
        await self.clear_performance_cache()
        await self.clear_redis_cache()
        await self.clear_file_caches()
        await self.clear_temp_files()

        # Report results
        self.print_results()

        return self.results

    async def clear_enhanced_cache_system(self):
        """Clear Enhanced Multi-Tier Cache System"""
        try:
            logger.info("🔄 Clearing Enhanced Cache System...")

            from mcp_servers.base.enhanced_cache_system import (
                CacheStrategy,
                create_cache_system,
            )

            # Create test instance to clear any existing data
            cache_system = create_cache_system(
                strategy=CacheStrategy.PERFORMANCE, redis_url=self.redis_url
            )

            await cache_system.initialize()

            # Get stats before clearing
            stats_before = await cache_system.get_comprehensive_stats()

            # Clear L1 cache
            await cache_system.l1_cache.clear()
            logger.info("  ✅ L1 memory cache cleared")

            # Clear L2 Redis cache if connected
            if cache_system.l2_cache and cache_system.l2_cache.is_connected:
                await cache_system.l2_cache.clear()
                logger.info("  ✅ L2 Redis cache cleared")

            # Shutdown properly
            await cache_system.shutdown()

            self.results["enhanced_cache"] = {
                "cleared": True,
                "details": {
                    "l1_cache": "cleared",
                    "l2_cache": "cleared" if cache_system.l2_cache else "not_available",
                    "stats_before": stats_before,
                },
            }

        except Exception as e:
            error_msg = f"Error clearing Enhanced cache: {e}"
            logger.error(f"  ❌ {error_msg}")
            self.results["errors"].append(error_msg)
            self.results["enhanced_cache"]["cleared"] = False

    async def clear_performance_cache(self):
        """Clear Performance cache system"""
        try:
            logger.info("🔄 Clearing Performance cache...")

            from mcp_servers.base.performance import get_cache_manager

            # Clear global cache manager
            cache_manager = get_cache_manager()
            stats_before = cache_manager.get_stats()
            cache_manager.clear()

            # Reset global instance
            import mcp_servers.base.performance as perf_module

            perf_module._global_cache_manager = None

            logger.info("  ✅ Performance cache cleared")

            self.results["performance_cache"] = {
                "cleared": True,
                "details": {
                    "global_cache_manager": "cleared",
                    "stats_before": stats_before,
                },
            }

        except Exception as e:
            error_msg = f"Error clearing Performance cache: {e}"
            logger.error(f"  ❌ {error_msg}")
            self.results["errors"].append(error_msg)
            self.results["performance_cache"]["cleared"] = False

    async def clear_redis_cache(self):
        """Clear Redis cache data"""
        try:
            logger.info("🔄 Clearing Redis cache...")

            try:
                import redis.asyncio as aioredis

                redis_available = True
            except ImportError:
                redis_available = False
                logger.warning("  ⚠️ aioredis not available")

            if redis_available:
                try:
                    # Connect to Redis
                    redis_client = await aioredis.from_url(
                        self.redis_url,
                        encoding=None,
                        decode_responses=False,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                    )

                    # Test connection
                    await redis_client.ping()

                    # Get cache keys before clearing
                    patterns = [
                        "sophia:cache:*",
                        "ai_cache:*",
                        "cache:*",
                        "mcp:*",
                        "*cache*",
                    ]

                    total_cleared = 0
                    pattern_results = {}

                    for pattern in patterns:
                        keys = await redis_client.keys(pattern)
                        if keys:
                            deleted = await redis_client.delete(*keys)
                            total_cleared += deleted
                            pattern_results[pattern] = deleted
                            logger.info(
                                f"    🗑️ Cleared {deleted} keys matching '{pattern}'"
                            )

                    await redis_client.close()

                    self.results["redis_cache"] = {
                        "cleared": True,
                        "details": {
                            "total_keys_cleared": total_cleared,
                            "patterns_cleared": pattern_results,
                            "redis_url": self.redis_url,
                        },
                    }

                    logger.info(
                        f"  ✅ Redis cache cleared ({total_cleared} keys total)"
                    )

                except Exception as redis_error:
                    logger.warning(f"  ⚠️ Redis connection failed: {redis_error}")
                    self.results["redis_cache"] = {
                        "cleared": False,
                        "details": {
                            "error": str(redis_error),
                            "reason": "connection_failed",
                        },
                    }
            else:
                self.results["redis_cache"] = {
                    "cleared": False,
                    "details": {
                        "error": "aioredis not available",
                        "reason": "module_not_found",
                    },
                }

        except Exception as e:
            error_msg = f"Error clearing Redis cache: {e}"
            logger.error(f"  ❌ {error_msg}")
            self.results["errors"].append(error_msg)
            self.results["redis_cache"]["cleared"] = False

    async def clear_file_caches(self):
        """Clear file-based caches"""
        try:
            logger.info("🔄 Clearing file-based caches...")

            # Define cache directories and patterns
            cache_patterns = [
                "**/__pycache__",
                "**/.pytest_cache",
                "**/node_modules/.cache",
                "**/cache",
                "**/tmp",
                "**/*.cache",
                "**/.cache",
            ]

            project_root = Path("/appsil/sophia-main")
            cleared_items = []
            total_size = 0

            for pattern in cache_patterns:
                for item in project_root.glob(pattern):
                    if item.exists():
                        try:
                            size_before = (
                                self._get_directory_size(item)
                                if item.is_dir()
                                else item.stat().st_size
                            )

                            if item.is_dir():
                                shutil.rmtree(item)
                                logger.info(
                                    f"    🗑️ Removed directory: {item.relative_to(project_root)}"
                                )
                            else:
                                item.unlink()
                                logger.info(
                                    f"    🗑️ Removed file: {item.relative_to(project_root)}"
                                )

                            cleared_items.append(str(item.relative_to(project_root)))
                            total_size += size_before

                        except Exception as e:
                            logger.warning(f"    ⚠️ Could not remove {item}: {e}")

            self.results["file_cache"] = {
                "cleared": True,
                "details": {
                    "items_cleared": len(cleared_items),
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "cleared_items": cleared_items[:20],  # Limit output
                },
            }

            logger.info(
                f"  ✅ File caches cleared ({len(cleared_items)} items, {total_size/(1024*1024):.1f} MB)"
            )

        except Exception as e:
            error_msg = f"Error clearing file caches: {e}"
            logger.error(f"  ❌ {error_msg}")
            self.results["errors"].append(error_msg)
            self.results["file_cache"]["cleared"] = False

    async def clear_temp_files(self):
        """Clear temporary files"""
        try:
            logger.info("🔄 Clearing temporary files...")

            temp_patterns = [
                "/tmp/sophia_*",
                "/tmp/mcp_*",
                "/tmp/cache_*",
                "/appsil/sophia-main/**/*.tmp",
                "/appsil/sophia-main/**/*.temp",
            ]

            cleared_files = []
            total_size = 0

            for pattern in temp_patterns:
                for file_path in glob.glob(pattern, recursive=True):
                    try:
                        path_obj = Path(file_path)
                        if path_obj.exists():
                            size = path_obj.stat().st_size
                            path_obj.unlink()
                            cleared_files.append(file_path)
                            total_size += size
                            logger.info(f"    🗑️ Removed temp file: {file_path}")
                    except Exception as e:
                        logger.warning(f"    ⚠️ Could not remove {file_path}: {e}")

            self.results["temp_files"] = {
                "cleared": True,
                "details": {
                    "files_cleared": len(cleared_files),
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "cleared_files": cleared_files[:10],  # Limit output
                },
            }

            logger.info(
                f"  ✅ Temp files cleared ({len(cleared_files)} files, {total_size/(1024*1024):.1f} MB)"
            )

        except Exception as e:
            error_msg = f"Error clearing temp files: {e}"
            logger.error(f"  ❌ {error_msg}")
            self.results["errors"].append(error_msg)
            self.results["temp_files"]["cleared"] = False

    def _get_directory_size(self, path: Path) -> int:
        """Get total size of directory"""
        total_size = 0
        try:
            for item in path.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception:return total_size

    def print_results(self):
        """Print detailed results"""
        logger.info("\n" + "=" * 60)
        logger.info("🧹 CACHE CLEANUP RESULTS")
        logger.info("=" * 60)

        for cache_type, result in self.results.items():
            if cache_type == "errors":
                continue

            status = "✅ CLEARED" if result["cleared"] else "❌ FAILED"
            logger.info(f"\n{cache_type.upper()}: {status}")

            if result.get("details"):
                for key, value in result["details"].items():
                    if isinstance(value, dict):
                        logger.info(f"  {key}: {len(value)} items")
                    elif isinstance(value, list):
                        logger.info(f"  {key}: {len(value)} items")
                    else:
                        logger.info(f"  {key}: {value}")

        if self.results["errors"]:
            logger.error(f"\n❌ ERRORS ({len(self.results['errors'])}):")
            for error in self.results["errors"]:
                logger.error(f"  • {error}")

        # Summary
        total_cleared = sum(
            1
            for result in self.results.values()
            if isinstance(result, dict) and result.get("cleared")
        )
        total_systems = len([k for k in self.results.keys() if k != "errors"])

        logger.info(
            f"\n📊 SUMMARY: {total_cleared}/{total_systems} cache systems cleared"
        )

        if total_cleared == total_systems:
            logger.info("🎉 All cache systems successfully cleared!")
        else:
            logger.warning(
                "⚠️ Some cache systems could not be cleared (see errors above)"
            )

async def main():
    """Main function"""
    try:
        cleaner = CacheCleaner()
        results = await cleaner.clear_all_caches()

        # Return non-zero exit code if there were errors
        if results["errors"]:
            sys.exit(1)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        logger.info("\n🛑 Cache cleanup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error during cache cleanup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
