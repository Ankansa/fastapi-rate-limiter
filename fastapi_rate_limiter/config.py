from typing import Dict, Tuple

class RateLimitConfig:
    """
    Configuration class for the rate limiter.
    Customize defaults and path-specific overrides here or via instance.
    """
    DEFAULT_LIMIT: int = 100          # requests
    DEFAULT_PERIOD: int = 60          # seconds

    # Path-specific overrides: path -> (limit, period_in_seconds)
    PATH_OVERRIDES: Dict[str, Tuple[int, int]] = {
        # "/api/v1/auth/login": (5, 60),
        # "/api/v1/auth/register": (20, 60),
        # "/api/v1/auth/reset-password": (10, 300),
        # Add more as needed
    }

    LIMIT_PER_USER: bool = True       # Use authenticated user ID when available

    # Redis settings
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"  # None = use in-memory
    REDIS_PREFIX: str = "rate_limiter"