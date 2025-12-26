# fastapi-rate-limiter

A simple, lightweight, token-bucket based rate limiting middleware for FastAPI.

- Per-IP limiting by default  
- Optional per-user limiting (when `request.state.user` is set)  
- Configurable global and per-path limits  
- Proper 429 responses with `Retry-After` header  
- No external dependencies beyond FastAPI

## Installation

pip install git+https://github.com/yourusername/fastapi-rate-limiter.git