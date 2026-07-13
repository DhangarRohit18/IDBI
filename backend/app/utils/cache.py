"""
FinTwin AI — Redis Cache Manager
Provides async Redis caching with TTL, cache invalidation, and key namespacing.
"""

from __future__ import annotations

import json
from typing import Any, TypeVar

import structlog
from redis.asyncio import Redis, from_url

from app.config import settings

logger = structlog.get_logger(__name__)

T = TypeVar("T")

# Module-level Redis client instances
_cache_client: Redis | None = None
_session_client: Redis | None = None


async def get_redis_client(db: int | None = None) -> Redis:
    """Get or create async Redis client for the specified DB."""
    global _cache_client
    if db is None:
        db = settings.REDIS_CACHE_DB

    if _cache_client is None:
        url = settings.REDIS_URL.replace("/0", f"/{db}")
        _cache_client = await from_url(
            url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
    return _cache_client


class RedisCache:
    """High-level async Redis cache wrapper."""

    def __init__(self, namespace: str = "fintwin", default_ttl: int | None = None) -> None:
        self._namespace = namespace
        self._default_ttl = default_ttl or settings.REDIS_DEFAULT_TTL
        self._client: Redis | None = None

    async def get_client(self) -> Redis:
        if self._client is None:
            self._client = await get_redis_client(settings.REDIS_CACHE_DB)
        return self._client

    def _key(self, key: str) -> str:
        return f"{self._namespace}:{key}"

    async def get(self, key: str, default: Any = None) -> Any:
        """Get a cached value. Returns default if not found."""
        client = await self.get_client()
        raw = await client.get(self._key(key))
        if raw is None:
            return default
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """Set a value in cache with optional TTL override."""
        client = await self.get_client()
        serialized = json.dumps(value, default=str)
        effective_ttl = ttl if ttl is not None else self._default_ttl
        await client.setex(self._key(key), effective_ttl, serialized)

    async def delete(self, key: str) -> None:
        """Delete a specific cache key."""
        client = await self.get_client()
        await client.delete(self._key(key))

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern. Returns count deleted."""
        client = await self.get_client()
        full_pattern = self._key(pattern)
        keys = await client.keys(full_pattern)
        if keys:
            return await client.delete(*keys)
        return 0

    async def exists(self, key: str) -> bool:
        """Check if a key exists in cache."""
        client = await self.get_client()
        return bool(await client.exists(self._key(key)))

    async def increment(self, key: str, amount: int = 1, ttl: int | None = None) -> int:
        """Atomic increment of a numeric cache value."""
        client = await self.get_client()
        full_key = self._key(key)
        value = await client.incr(full_key, amount)
        if ttl and value == amount:
            # Only set TTL on first increment
            await client.expire(full_key, ttl)
        return value

    async def get_or_set(
        self,
        key: str,
        factory,
        ttl: int | None = None,
    ) -> Any:
        """
        Get from cache, or call factory to compute and cache the value.
        Factory can be sync or async.
        """
        cached = await self.get(key)
        if cached is not None:
            return cached

        import asyncio
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()

        await self.set(key, value, ttl=ttl)
        return value


# Named cache instances for different domains
_portfolio_cache = RedisCache(namespace="portfolio", default_ttl=300)
_twin_cache = RedisCache(namespace="twin", default_ttl=1800)
_risk_cache = RedisCache(namespace="risk", default_ttl=3600)


async def get_cache(namespace: str = "fintwin") -> RedisCache:
    """Get a RedisCache instance for the given namespace."""
    caches = {
        "portfolio": _portfolio_cache,
        "twin": _twin_cache,
        "risk": _risk_cache,
    }
    return caches.get(namespace, RedisCache(namespace=namespace))
