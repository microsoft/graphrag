# GraphRAG Cache

## Basic

```python
import asyncio
from graphrag_storage import StorageConfig, create_storage, StorageType
from graphrag_cache import CacheConfig, create_cache, CacheType

async def run():
    cache = create_cache(
        CacheConfig(
            type=CacheType.Json
            storage=StorageConfig(
                type=StorageType.File,
                base_dir="cache"
            )
        ),
    )

    await cache.set("my_key", {"some": "object to cache"})
    print(await cache.get("my_key"))

if __name__ == "__main__":
    asyncio.run(run())
```

## Custom Cache

```python
import asyncio
from typing import Any
from graphrag_storage import Storage
from graphrag_cache import Cache, CacheConfig, create_cache, register_cache

class MyCache(Cache):
    def __init__(self, some_setting: str, optional_setting: str = "default setting", **kwargs: Any):
        # Validate settings and initialize
        # View the JsonCache implementation to see how to create a cache that relies on a Storage provider.
        ...

    #Implement rest of interface
    ...

register_cache("MyCache", MyCache)

async def run():
    cache = create_cache(
        CacheConfig(
            type="MyCache",
            some_setting="My Setting"
        )
    )

    # Or use the factory directly to instantiate with a dict instead of using
    # CacheConfig + create_factory
    # from graphrag_cache.cache_factory import cache_factory
    # cache = cache_factory.create(strategy="MyCache", init_args={"some_setting": "My Setting"})

    await cache.set("my_key", {"some": "object to cache"})
    print(await cache.get("my_key"))

if __name__ == "__main__":
    asyncio.run(run())
```

### Details

By default, the `create_cache` comes with the following cache providers registered that correspond to the entries in the `CacheType` enum. 

- `JsonCache`
- `MemoryCache`
- `NoopCache`

The preregistration happens dynamically, e.g., `JsonCache` is only imported and registered if you request a `JsonCache` with `create_cache(CacheType.Json, ...)`. There is no need to manually import and register builtin cache providers when using `create_cache`.

If you want a clean factory with no preregistered cache providers then directly import `cache_factory` and bypass using `create_cache`. The downside is that `cache_factory.create` uses a dict for init args instead of the strongly typed `CacheConfig` used with `create_cache`.

```python
from graphrag_cache.cache_factory import cache_factory
from graphrag_cache.json_cache import JsonCache

# cache_factory has no preregistered providers so you must register any
# providers you plan on using.
# May also register a custom implementation, see above for example.
cache_factory.register("my_cache_impl", JsonCache)

cache = cache_factory.create(strategy="my_cache_impl", init_args={"some_setting": "..."})

...

```