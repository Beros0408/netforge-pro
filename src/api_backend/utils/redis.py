"""
Redis connection utilities.
"""
import redis.asyncio as redis

from ..config import settings

# Create Redis client
redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


async def get_redis() -> redis.Redis:
    """
    Dependency to get Redis client.
    """
    return redis_client


async def ping_redis() -> bool:
    """
    Ping Redis to check connection.
    """
    try:
        return await redis_client.ping()
    except Exception:
        return False