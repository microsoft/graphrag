# GraphRAG Inputs

> [!WARNING]
> GraphRAG is a research project that explores the functional use of graphs to form a targeted context for question answering. Since our first release in July 2024 the capabilities of frontier models have changed dramatically, and our portfolio of research projects has diversified to match. This project is largely in maintenance mode, and won't be accepting new PRs or implementing new features. We'll perform bug fixes and dependency updates as appropriate, particularly to address CVEs as they arise.

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

1. Import a pdf with MarkItDown:

```bash
pip install 'markitdown[pdf]' # required dependency for pdf processing
```

2. YAML config example for above:

```yaml
input:
  type: markitdown
  file_pattern: ".*\\.pdf$$"
input_storage:
  type: file
  base_dir: "input"
```

[Open the notebook to explore the input example code](example_notebooks/input_example.ipynb)
