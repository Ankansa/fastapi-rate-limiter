from fastapi import Request
import redis.asyncio as redis
from contextlib import asynccontextmanager
from .config import RateLimitConfig

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


@asynccontextmanager
async def get_redis_pool(config: RateLimitConfig):
    if config.REDIS_URL:
        pool = redis.from_url(config.REDIS_URL, decode_responses=True)
        try:
            yield pool
        finally:
            await pool.close()
    else:
        yield None  # in-memory mode