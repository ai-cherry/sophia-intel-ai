#!/usr/bin/env python3
"""
Cache Verification Script - Verify all caches have been cleared
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project paths
sys.path.insert(0, "/appsil/sophia-main")
sys.path.insert(0, "/appsil/sophia-main/mcp_servers")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_caches_cleared():
    """Verify all cache systems are cleared"""
    logger.info("🔍 Verifying cache systems are cleared...")

    verification_results = {
        "enhanced_cache": {"clear": False, "details": {}},
        "performance_cache": {"clear": False, "details": {}},
        "file_cache": {"clear": False, "details": {}},
        "all_clear": False,
    }

    # 1. Verify Enhanced cache system
    try:
        from mcp_servers.base.enhanced_cache_system import (
            CacheStrategy,
            create_cache_system,
        )

        cache_system = create_cache_system(strategy=CacheStrategy.BALANCED)
        await cache_system.initialize()

        l1_stats = cache_system.l1_cache.get_stats()
        l1_entries = l1_stats.get("entries", 0)

        # L2 cache check
        l2_entries = 0
        if cache_system.l2_cache and cache_system.l2_cache.is_connected:
            l2_stats = await cache_system.l2_cache.get_stats()
            l2_entries = l2_stats.get("total_keys", 0)

        verification_results["enhanced_cache"] = {
            "clear": l1_entries == 0 and l2_entries == 0,
            "details": {
                "l1_entries": l1_entries,
                "l2_entries": l2_entries,
                "l1_stats": l1_stats,
            },
        }

        await cache_system.shutdown()
        logger.info(f"  📊 Enhanced cache: L1={l1_entries}, L2={l2_entries} items")

    except Exception as e:
        logger.warning(f"  ⚠️ Could not verify Enhanced cache: {e}")

    # 3. Verify Performance cache
    try:
        from mcp_servers.base.performance import get_cache_manager

        cache_manager = get_cache_manager()
        stats = cache_manager.get_stats()
        active_entries = stats.get("active_entries", 0)

        verification_results["performance_cache"] = {
            "clear": active_entries == 0,
            "details": {"active_entries": active_entries, "stats": stats},
        }
        logger.info(f"  📊 Performance cache: {active_entries} active entries")

    except Exception as e:
        logger.warning(f"  ⚠️ Could not verify Performance cache: {e}")

    # 4. Verify file caches are cleared
    try:
        project_root = Path("/appsil/sophia-main")

        # Check for common cache directories
        cache_dirs = list(project_root.glob("**/__pycache__"))
        pytest_cache_dirs = list(project_root.glob("**/.pytest_cache"))

        total_cache_dirs = len(cache_dirs) + len(pytest_cache_dirs)

        verification_results["file_cache"] = {
            "clear": total_cache_dirs == 0,
            "details": {
                "pycache_dirs": len(cache_dirs),
                "pytest_cache_dirs": len(pytest_cache_dirs),
                "total_dirs": total_cache_dirs,
            },
        }
        logger.info(f"  📊 File cache: {total_cache_dirs} cache directories found")

    except Exception as e:
        logger.warning(f"  ⚠️ Could not verify file caches: {e}")

    # Overall verification
    all_clear = all(
        result.get("clear", False)
        for result in verification_results.values()
        if isinstance(result, dict) and "clear" in result
    )

    verification_results["all_clear"] = all_clear

    # Print results
    logger.info("\n" + "=" * 50)
    logger.info("🔍 CACHE VERIFICATION RESULTS")
    logger.info("=" * 50)

    for cache_type, result in verification_results.items():
        if cache_type == "all_clear":
            continue

        if isinstance(result, dict) and "clear" in result:
            status = "✅ CLEAR" if result["clear"] else "❌ NOT CLEAR"
            logger.info(f"\n{cache_type.upper()}: {status}")

            if result.get("details"):
                for key, value in result["details"].items():
                    if isinstance(value, dict):
                        logger.info(f"  {key}: {len(value)} items")
                    else:
                        logger.info(f"  {key}: {value}")

    if all_clear:
        logger.info("\n🎉 ALL CACHES SUCCESSFULLY CLEARED!")
    else:
        logger.warning("\n⚠️ Some caches may still contain data")

    return verification_results

if __name__ == "__main__":
    asyncio.run(verify_caches_cleared())
