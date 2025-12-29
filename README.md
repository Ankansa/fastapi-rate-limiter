# fastapi-rate-limiter

A simple yet powerful token-bucket based rate limiting middleware for FastAPI.

### Features

- Per-IP limiting by default
- Optional per-authenticated-user limiting (when `request.state.user` is set)
- Configurable global defaults and per-path overrides
- Proper `429 Too Many Requests` responses with `Retry-After` and rate limit headers
- **Redis support** for distributed, multi-worker/process rate limiting
- **Unique behavior**: When a client switches from one endpoint to another, the previous endpoint's token bucket is reset (full tokens again)
- No heavy dependencies (only `redis` optional)

## Installation

```bash
pip install git+https://github.com/yourusername/fastapi-rate-limiter.git