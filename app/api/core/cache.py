"""Redis cache configuration"""
import logging
import os
import redis.asyncio as aioredis
logger = logging.getLogger(__name__)
REDIS_URL = os.getenv("REDIS_URL", "${REDIS_URL}")
redis_client = None
async def init_redis():
    """Initialize Redis connection"""
    global redis_client
    redis_client = await aioredis.from_url(REDIS_URL)
    await redis_client.ping()
    logger.info("Redis initialized")
async def check_connection():
    """Check if Redis is accessible"""
    if not redis_client:
        return False
    try:
        await redis_client.ping()
        return True
    except:
        return False
async def get_redis():
    """Get Redis client"""
    if not redis_client:
        await init_redis()
    return redis_client
