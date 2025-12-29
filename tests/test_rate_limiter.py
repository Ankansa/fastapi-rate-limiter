from fastapi import FastAPI
from fastapi_rate_limiter import RateLimiterMiddleware, RateLimitConfig

app = FastAPI()

# Optional: customize configuration
config = RateLimitConfig()
config.DEFAULT_LIMIT = 60
config.DEFAULT_PERIOD = 60
config.REDIS_URL = "redis://localhost:6379/0"  # Enable distributed limiting
config.PATH_OVERRIDES["/login"] = (5, 60)

app.add_middleware(RateLimiterMiddleware, config=config)
# Or with defaults: app.add_middleware(RateLimiterMiddleware)

@app.get("/")
async def root():
    return {"message": "Hello!"}