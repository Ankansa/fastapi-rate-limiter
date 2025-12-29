from fastapi import FastAPI
from fastapi_rate_limiter import RateLimiterMiddleware, RateLimitConfig

app = FastAPI()

config = RateLimitConfig()
config.DEFAULT_LIMIT = 5
config.DEFAULT_PERIOD = 60
config.REDIS_URL = "redis://localhost:6379/0"  # Required for path reset behavior
config.PATH_OVERRIDES["/api/a"] = (3, 60)
config.PATH_OVERRIDES["/api/b"] = (10, 60)

app.add_middleware(RateLimiterMiddleware, config=config)

@app.get("/api/a")
async def api_a():
    return {"path": "a"}

@app.get("/api/b")
async def api_b():
    return {"path": "b"}