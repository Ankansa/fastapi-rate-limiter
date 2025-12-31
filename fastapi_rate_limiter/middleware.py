import time
import json
from typing import Tuple, Dict, Any
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from .config import RateLimitConfig
from .utils import get_client_ip, get_redis_pool


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiter middleware for FastAPI using Redis (optional).
    Resets previous path's bucket when client switches to a new path.
    """

    def __init__(self, app, config: RateLimitConfig | None = None):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        # In-memory fallback for tracking last path per client
        self.last_path_by_client: Dict[str, str] = defaultdict(str)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        limit, period = self.config.PATH_OVERRIDES.get(
            path, (self.config.DEFAULT_LIMIT, self.config.DEFAULT_PERIOD)
        )

        client_key = self._get_client_key(request)
        full_key = f"{self.config.REDIS_PREFIX}:{client_key}"
        last_path_key = f"{full_key}:last_path"
        bucket_key = f"{full_key}:bucket:{path}"  # path-specific bucket

        async with get_redis_pool(self.config) as redis_pool:
            # Check if path changed → reset previous bucket if needed
            current_last_path = self.last_path_by_client.get(client_key)
            if current_last_path and current_last_path != path:
                prev_bucket_key = f"{full_key}:bucket:{current_last_path}"
                if redis_pool:
                    await redis_pool.delete(prev_bucket_key)
                # Note: no need to reset in-memory since we use Redis primarily

            # Update last path (in-memory + Redis for consistency across instances)
            self.last_path_by_client[client_key] = path
            if redis_pool:
                await redis_pool.set(last_path_key, path)

            now = time.time()

            if redis_pool:
                # Redis mode
                bucket_data = await redis_pool.get(bucket_key)
                if bucket_data:
                    tokens, last_refill = map(float, json.loads(bucket_data))
                else:
                    tokens, last_refill = float(limit), now

                elapsed = now - last_refill
                new_tokens = min(tokens + elapsed * limit / period, limit)

                if new_tokens >= 1:
                    new_tokens -= 1
                    await redis_pool.set(
                        bucket_key,
                        json.dumps([new_tokens, now]),
                        ex=period * 2  # optional TTL
                    )
                    response = await call_next(request)
                else:
                    retry_after = max(1, int(period - elapsed + 1))
                    response = JSONResponse(
                        status_code=429,
                        content={
                            "status": False,
                            "message": "Too Many Requests",
                            "detail": f"Rate limit exceeded. Retry after {retry_after} seconds.",
                        },
                        headers={
                            "Retry-After": str(retry_after),
                            "X-RateLimit-Limit": str(limit),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(int(now + (period - elapsed + tokens * period / limit))),
                        },
                    )
            else:
                # Fallback in-memory (for testing or no Redis)
                # Simplified version (you can keep old logic or improve)
                raise NotImplementedError("In-memory mode not maintained for path-reset feature. Use Redis.")

            return response

    def _get_client_key(self, request: Request) -> str:
        if self.config.LIMIT_PER_USER:
    
            token = "anonymous"
            
            auth_header = request.headers.get("authorization")
            if auth_header:
                
                token = auth_header.split(" ", 1)[1]
   
            user = getattr(request.state, "user", None)
            if user:
                user_id = None
                if isinstance(user, dict):
                    user_id = user.get("id") or user.get("sub")
                elif hasattr(user, "id"):
                    user_id = getattr(user, "id")
                if user_id:
                    return f"user:{user_id}"
        return f"ip:{get_client_ip(request)},token:{token}"