from fastapi import FastAPI
from fastapi_rate_limiter import RateLimiterMiddleware, RateLimitConfig

app = FastAPI(title="My API with Rate Limiting")

# Optional: customize config
custom_config = RateLimitConfig()
custom_config.DEFAULT_LIMIT = 200
custom_config.PATH_OVERRIDES["/api/v1/auth/login"] = (3, 60)

app.add_middleware(RateLimiterMiddleware, config=custom_config)
# Or simply: app.add_middleware(RateLimiterMiddleware)

@app.get("/")
async def root():
    return {"message": "Hello! You're within rate limits."}