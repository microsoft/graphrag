# GraphRAG Storage

```python
from graphrag_storage import StorageConfig, create_storage
from graphrag_storage.file_storage import FileStorage

storage = create_storage(
    StorageConfig(
        type="FileStorage", # or FileStorage.__name__
        base_dir="output"
    )
)

```