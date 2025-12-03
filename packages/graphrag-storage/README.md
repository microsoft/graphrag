# GraphRAG Storage

## Basic

```python
import asyncio
from graphrag_storage import StorageConfig, create_storage, StorageType

async def run():
    storage = create_storage(
        StorageConfig(
            type=StorageType.FILE
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
    def __init__(self, some_setting: str, optional_setting: str = "default setting"):
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
