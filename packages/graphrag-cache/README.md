# GraphRAG Cache

This package contains a collection of utilities to handle GraphRAG caching implementation.

### Basic

This example shows how to create a JSON cache with file storage using the GraphRAG cache package's configuration system. 

[Open the notebook to explore the basic example code](example-notebooks/basic_cache_example.ipynb)

### Custom Cache

This example demonstrates how to create a custom cache implementation by extending the base Cache class and registering it with the GraphRAG cache system. Once registered, the custom cache can be instantiated through the factory pattern using either CacheConfig or directly via cache_factory, allowing for extensible caching solutions tailored to specific needs.

[Open the notebook to explore the basic custom example code](example-notebooks/custom_cache_example.ipynb)

#### Details

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