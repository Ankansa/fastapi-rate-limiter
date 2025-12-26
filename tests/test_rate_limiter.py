import time
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_rate_limiter import RateLimiterMiddleware, RateLimitConfig

def test_rate_limiting():
    app = FastAPI()
    app.add_middleware(RateLimiterMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"ok": True}

    client = TestClient(app)

    # First few requests should succeed
    for _ in range(100):
        response = client.get("/test")
        assert response.status_code == 200

    # Next one should be rate limited
    response = client.get("/test")
    assert response.status_code == 429
    assert "Too Many Requests" in response.json()["message"]

    # Wait a bit and it should allow again
    time.sleep(1.1)  # >1 second to get some tokens back
    response = client.get("/test")
    assert response.status_code == 200