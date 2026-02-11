# GraphRAG Storage

This package provides a unified storage abstraction layer with support for multiple backends including file system, Azure Blob, Azure Cosmos, and memory storage. It features a factory-based creation system with configuration-driven setup and extensible architecture for implementing custom storage providers.

## Basic

This example creates a file storage system using the GraphRAG storage package's configuration system. The example shows setting up file storage in a specified directory and demonstrates basic storage operations like setting and getting key-value pairs.

[Open the notebook to explore the basic storage example code](example_notebooks/basic_storage_example.ipynb)

## Custom Storage

Here we create a custom storage implementation by extending the base Storage class and registering it with the GraphRAG storage system. Once registered, the custom storage can be instantiated through the factory pattern using either StorageConfig or directly via storage_factory, enabling extensible storage solutions for different backends.

[Open the notebook to explore the custom storage example code](example_notebooks/basic_storage_example.ipynb)


## Details

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