"""
FinTwin AI — Redis-Based Rate Limiter
Sliding window rate limiting per user and per IP.
"""

from __future__ import annotations

import time
from functools import wraps
from typing import Callable

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.utils.cache import RedisCache

logger = structlog.get_logger(__name__)


class RateLimiter:
    """Sliding window rate limiter using Redis sorted sets."""

    def __init__(self, cache: RedisCache) -> None:
        self._cache = cache

    async def is_allowed(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit.
        
        Returns:
            tuple of (is_allowed, current_count, remaining)
        """
        redis = await self._cache.get_client()
        now = time.time()
        window_start = now - window_seconds

        pipe = redis.pipeline()
        # Remove old requests outside the window
        pipe.zremrangebyscore(key, 0, window_start)
        # Count requests in current window
        pipe.zcard(key)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Set expiry on key
        pipe.expire(key, window_seconds + 1)
        results = await pipe.execute()

        current_count = results[1]
        remaining = max(0, limit - current_count - 1)
        allowed = current_count < limit

        if not allowed:
            logger.warning("Rate limit exceeded", key=key, count=current_count, limit=limit)

        return allowed, current_count + 1, remaining


def rate_limit(
    limit: int | None = None,
    window_seconds: int = 60,
    key_func: Callable[[Request], str] | None = None,
) -> Callable:
    """
    FastAPI route decorator for rate limiting.
    
    Args:
        limit: max requests per window (defaults to settings.RATE_LIMIT_PER_USER_PER_MIN)
        window_seconds: time window in seconds
        key_func: custom function to extract rate limit key from request
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            from app.utils.cache import get_cache
            cache = await get_cache()
            limiter = RateLimiter(cache)

            effective_limit = limit or settings.RATE_LIMIT_PER_USER_PER_MIN

            if key_func:
                key = key_func(request)
            elif hasattr(request.state, "current_user"):
                key = f"ratelimit:user:{request.state.current_user.id}:{request.url.path}"
            else:
                ip = request.client.host if request.client else "unknown"
                key = f"ratelimit:ip:{ip}:{request.url.path}"

            allowed, count, remaining = await limiter.is_allowed(
                key, effective_limit, window_seconds
            )

            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded. Please try again later.",
                        "code": "RATE_LIMIT_EXCEEDED",
                        "field_errors": {},
                    },
                    headers={
                        "X-RateLimit-Limit": str(effective_limit),
                        "X-RateLimit-Remaining": "0",
                        "Retry-After": str(window_seconds),
                    },
                )

            response = await func(request, *args, **kwargs)
            return response

        return wrapper
    return decorator
