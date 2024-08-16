from typing import Any, Optional
import json

from .pipeline_cache import PipelineCache


class RedisCache(PipelineCache):
    """Redis pipeline cache class definition."""
    _redis: Any
    _ttl: Optional[int] = None
    _prefix: Optional[str] = ""

    def __init__(
            self,
            redis_: Any,
            *,
            ttl: Optional[int] = None,
            prefix: Optional[str] = ""):
        """
        Initialize an instance of RedisCache.

        This method initializes an object with Redis caching capabilities.
        It takes a `redis_` parameter, which should be an instance of a Redis
        client class (`redis.Redis`), allowing the object
        to interact with a Redis server for caching purposes.

        Parameters:
            redis_ (Any): An instance of a Redis client class
                (`redis.Redis`) to be used for caching.
                This allows the object to communicate with a
                Redis server for caching operations.
            ttl (int, optional): Time-to-live (TTL) for cached items in seconds.
                If provided, it sets the time duration for how long cached
                items will remain valid. If not provided, cached items will not
                have an automatic expiration.
        """
        try:
            from redis import Redis
        except ImportError:
            raise ImportError(
                "Could not import `redis` python package. "
                "Please install it with `pip install redis`."
            )
        if not isinstance(redis_, Redis):
            raise ValueError("Please pass a valid `redis.Redis` client.")
        self._redis = redis_
        self._ttl = ttl
        self._prefix = prefix

    async def get(self, key: str) -> Any:
        """Get the value for the given key.
        """
        key = self._create_cache_key(key)
        value = self._redis.get(key)
        if value:
            return json.loads(value)
        return value

    async def set(self, key: str, value: Any, debug_data: dict | None = None) -> None:
        """Set the value for the given key."""
        key = self._create_cache_key(key)
        self._redis.set(key, json.dumps(value), ex=self._ttl)

    async def has(self, key: str) -> bool:
        """Return True if the given key exists in the storage.
        """
        key = self._create_cache_key(key)
        return self._redis.exists(key)

    async def delete(self, key: str) -> None:
        """Delete the given key from the storage.
        """
        key = self._create_cache_key(key)
        self._redis.delete(key)

    async def clear(self) -> None:
        """Clear the storage."""
        self._redis.flushdb(asynchronous=False)

    def _create_cache_key(self, key: str) -> str:
        """Create a cache key for the given key."""
        return f"{self._prefix}{key}"

    def child(self, name: str) -> PipelineCache:
        """Create a child cache with the given name.

        Args:
            - name - The name to create the sub cache with.
        """
        return self


def create_redis_cache(connection_string) -> PipelineCache:
    """Create a memory cache."""
    from redis import Redis
    _redis = Redis.from_url(connection_string, decode_responses=True)
    _redis.ping()

    return RedisCache(_redis)