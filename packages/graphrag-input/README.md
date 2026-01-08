# GraphRAG Inputs

This package provides input document loading utilities for GraphRAG, supporting multiple file formats including CSV, JSON, JSON Lines, and plain text.

## Supported File Types

- **CSV** - Tabular data with configurable column mappings
- **JSON** - JSON files with configurable property paths
- **JSON Lines** - Line-delimited JSON records
- **Text** - Plain text files

## Examples

Basic usage with the factory:
```python
from graphrag_input import create_input_reader, InputConfig, InputType
from graphrag_storage import StorageConfig, create_storage

config = InputConfig(
    storage=StorageConfig(base_dir="./input"),
    type=InputType.Csv,
    text_column="content",
    title_column="title",
)
storage = create_storage(config.storage)
reader = create_input_reader(config, storage)
documents = await reader.read_files()
```

Using dot notation for nested properties:
```python
from graphrag_input import get_property

data = {"user": {"profile": {"name": "Alice"}}}
name = get_property(data, "user.profile.name")  # Returns "Alice"
```
