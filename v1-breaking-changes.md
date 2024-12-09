# GraphRAG Data Model and Config Breaking Changes

As we worked toward a cleaner codebase, data model, and configuration for the v1 release, we made a few changes that can break older indexes. During the development process we left shims in place to account for these changes, so that all old indexes will work up until v1.0. However, with the release of 1.0 we are removing these shims to allow the codebase to move forward without the legacy code elements. We are providing a migration notebook so this process should be fairly painless for most users:

1. Rename or move your settings.yml file to back it up.
2. Re-run `graphrag init` to generate a new default settings.yml.
3. Open your old settings.yml and copy any critical settings that you changed. For most people this is likely only the LLM and embedding config.
4. Run the notebook here: [./docs/examples_notebooks/index_migration.ipynb]()

Note that one of the new requirements is that we write embeddings to a vector store during indexing. By default, this uses a local lancedb instance. When you re-generate the default config, a block will be added to reflect this. If you need to write to Azure AI Search instead, we recommend updating these settings before you index, so you don't need to do a separate vector ingest.

All of the breaking changes listed below are accounted for in the four steps above.

## Updated data model

- We have streamlined the data model of the index in a few small ways to align tables more consistently and remove redundant content. Notably:
    - Consistent use of `id` and `human_readable_id` across all tables; this also insures all int IDs are actually saved as ints and never strings
    - Alignment of fields from `create_final_entities` (such as name -> title) with `create_final_nodes`, and removal of redundant content across these tables
    - Rename of `document.raw_content` to `document.text`
    - Rename of `entity.name` to `entity.title`
    - Rename `rank` to `combined_degree` in `create_final_relationships` and removal of `source_degree` and `target_degree`fields
    - Fixed community tables to use a proper UUID for the `id` field, and retain `community` and `human_readable_id` for the short IDs
    - Removal of all embeddings columns from parquet files in favor of direct vector store writes

### Migration

- Run a new index, leveraging existing cache.

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
