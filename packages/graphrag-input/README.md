# GraphRAG Inputs

This package provides input document loading utilities for GraphRAG, supporting multiple file formats including CSV, JSON, JSON Lines, and plain text.

## Supported File Types

The following four standard file formats are supported out of the box:

- **CSV** - Tabular data with configurable column mappings
- **JSON** - JSON files with configurable property paths
- **JSON Lines** - Line-delimited JSON records
- **Text** - Plain text files

### Markitdown Support

Additionally, we support the `InputType.MarkItDown` format, which uses the [MarkItDown](https://github.com/microsoft/markitdown) library to import any supported file type. The MarkItDown converter can handle a wide variety of file formats including Office documents, PDFs, HTML, and more.

**Note:** Additional optional dependencies may need to be installed depending on the file type you're processing. The choice of converter is determined by MarkItDowns's processing logic, which primarily uses the file extension to select the appropriate converter. Please refer to the [MarkItDown repository](https://github.com/microsoft/markitdown) for installation instructions and detailed information about supported formats.

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

Import a pdf with MarkItDown:

```bash
pip install 'markitdown[pdf]' # required dependency for pdf processing
```

```python
from graphrag_input import create_input_reader, InputConfig, InputType
from graphrag_storage import StorageConfig, create_storage

config = InputConfig(
    storage=StorageConfig(base_dir="./input"),
    type=InputType.MarkitDown,
    file_pattern=".*\\.pdf$"
)
storage = create_storage(config.storage)
reader = create_input_reader(config, storage)
documents = await reader.read_files()
```

YAML config example for above:
```yaml
input:
  storage:
    type: file
    base_dir: "input"
  type: markitdown
  file_pattern: ".*\\.pdf$$"
```

Note that when specifying column names for data extraction, we can handle nested objects (e.g., in JSON) with dot notation:
```python
from graphrag_input import get_property

data = {"user": {"profile": {"name": "Alice"}}}
name = get_property(data, "user.profile.name")  # Returns "Alice"
```
