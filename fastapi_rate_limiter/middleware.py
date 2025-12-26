import time
from collections import defaultdict
from typing import Tuple

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from .config import RateLimitConfig
from .utils import get_client_ip


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Token bucket rate limiter middleware for FastAPI.
    Supports per-IP and per-authenticated-user limiting.
    """

    def __init__(self, app, config: RateLimitConfig | None = None):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        # bucket: key -> (remaining_tokens: float, last_refill_timestamp: float)
        self.buckets = defaultdict(lambda: (self.config.DEFAULT_LIMIT, time.time()))

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path

        # Get limit and period for this path
        limit, period = self.config.PATH_OVERRIDES.get(
            path, (self.config.DEFAULT_LIMIT, self.config.DEFAULT_PERIOD)
        )

        # Determine rate limit key (user > IP)
        key = self._get_key(request)

        now = time.time()
        tokens, last_refill = self.buckets[key]

        # Refill tokens based on elapsed time
        elapsed = now - last_refill
        new_tokens = tokens + (elapsed * limit / period)
        new_tokens = min(new_tokens, limit)  # Cap at max limit

        if new_tokens >= 1:
            # Allow request
            self.buckets[key] = (new_tokens - 1, now)
            return await call_next(request)
        else:
            # Rate limited
            retry_after = max(1, int(period - elapsed))
            return JSONResponse(
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
                    "X-RateLimit-Reset": str(int(now + period - elapsed)),
                },
            )

    def _get_key(self, request: Request) -> str:
        if self.config.LIMIT_PER_USER:
            user = getattr(request.state, "user", None)
            if user:
                user_id = None
                if isinstance(user, dict):
                    user_id = user.get("id") or user.get("sub")
                elif hasattr(user, "id"):
                    user_id = getattr(user, "id")
                if user_id:
                    return f"user:{user_id}"

        # Fallback to IP
        return f"ip:{get_client_ip(request)}"