# Config Breaking Changes

## New required Embeddings

### Change

- Added new required embeddings for `DRIFTSearch` and base RAG capabilities.

### Migration

- Run a new index, leveraging existing cache.

## Vector Store required by default

### Change

- Vector store is now required by default for all search methods.

### Migration

- Run graphrag init command to generate a new settings.yaml file with the vector store configuration.
- Run a new index, leveraging existing cache.

## Deprecate timestamp paths

### Change

- Remove support for timestamp paths, those using `${timestamp}` directory nesting.
- Use the same directory for storage output and reporting output.

### Migration

- Ensure output directories no longer use `${timestamp}` directory nesting.

**Using Environment Variables**

- Ensure `GRAPHRAG_STORAGE_BASE_DIR` is set to a static directory, e.g., `output` instead of `output/${timestamp}/artifacts`.
- Ensure `GRAPHRAG_REPORTING_BASE_DIR` is set to a static directory, e.g., `output` instead of `output/${timestamp}/reports`

[Full docs on using environment variables for configuration](https://microsoft.github.io/graphrag/config/env_vars/).

**Using Configuration File**

```yaml
# rest of settings.yaml file
# ...

storage:
  type: file
  base_dir: "output" # changed from "output/${timestamp}/artifacts"

reporting:
  type: file
  base_dir: "output" # changed from "output/${timestamp}/reports"
```

[Full docs on using YAML files for configuration](https://microsoft.github.io/graphrag/config/yaml/).
