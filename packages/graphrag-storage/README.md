# GraphRAG Storage

## Basic

```python
import asyncio
from graphrag_storage import StorageConfig, create_storage, StorageType

async def run():
    storage = create_storage(
        StorageConfig(
            type=StorageType.File
            base_dir="output"
        )
    )

    await storage.set("my_key", "value")
    print(await storage.get("my_key"))

if __name__ == "__main__":
    asyncio.run(run())
```

## Custom Storage

```python
import asyncio
from typing import Any
from graphrag_storage import Storage, StorageConfig, create_storage, register_storage

class MyStorage(Storage):
    def __init__(self, some_setting: str, optional_setting: str = "default setting", **kwargs: Any):
        # Validate settings and initialize
        ...

    #Implement rest of interface
    ...

register_storage("MyStorage", MyStorage)

async def run():
    storage = create_storage(
        StorageConfig(
            type="MyStorage"
            some_setting="My Setting"
        )
    )
    # Or use the factory directly to instantiate with a dict instead of using
    # StorageConfig + create_factory
    # from graphrag_storage.storage_factory import storage_factory
    # storage = storage_factory.create(strategy="MyStorage", init_args={"some_setting": "My Setting"})

    await storage.set("my_key", "value")
    print(await storage.get("my_key"))

if __name__ == "__main__":
    asyncio.run(run())
```

### Details

By default, the `create_storage` comes with the following storage providers registered that correspond to the entries in the `StorageType` enum. 

- `FileStorage`
- `AzureBlobStorage`
- `AzureCosmosStorage`
- `MemoryStorage`

The preregistration happens dynamically, e.g., `FileStorage` is only imported and registered if you request a `FileStorage` with `create_storage(StorageType.File, ...)`. There is no need to manually import and register builtin storage providers when using `create_storage`.

If you want a clean factory with no preregistered storage providers then directly import `storage_factory` and bypass using `create_storage`. The downside is that `storage_factory.create` uses a dict for init args instead of the strongly typed `StorageConfig` used with `create_storage`.

```python
from graphrag_storage.storage_factory import storage_factory
from graphrag_storage.file_storage import FileStorage

# storage_factory has no preregistered providers so you must register any
# providers you plan on using.
# May also register a custom implementation, see above for example.
storage_factory.register("my_storage_key", FileStorage)

storage = storage_factory.create(strategy="my_storage_key", init_args={"base_dir": "...", "other_settings": "..."})

...

```