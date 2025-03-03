# GraphRAG Data Model and Config Breaking Changes

This document contains notes about our versioning approach and a log of changes over time that may result in breakage. As of version 1.0 we are aligning more closely with standard [semantic versioning](https://semver.org/) practices. However, this is an ongoing research project that needs to balance experimental progress with stakeholder communication about big feature releases, so there may be times when we don't adhere perfectly to the spec.

There are five surface areas that may be impacted on any given release. They are:

- [CLI](https://microsoft.github.io/graphrag/cli/) - The CLI is the interface most project consumers are using. **Changes to the CLI will conform to standard semver.**
- [API](https://github.com/microsoft/graphrag/tree/main/graphrag/api) - The API layer is the primary interface we expect developers to use if they are consuming the project as a library in their own codebases. **Changes to the API layer modules will conform to standard semver.**
- Internals - Any code modules behind the CLI and API layers are considered "internal" and may change at any time without conforming to strict semver. This is intended to give the research team high flexibility to change our underlying implementation rapidly. We are not enforcing access via tightly controlled `__init__.py` files, so please understand that if you utilize modules other than the index or query API, they may break between releases in a non-semver-compliant manner.
- [settings.yaml](https://microsoft.github.io/graphrag/config/yaml/) - The settings.yaml file may have changes made to it as we adjust configurability. **Changes that affect the settings.yml will result in a minor version bump**. `graphrag init` will always emit compatible starter config, so we recommend always running the command when updating GraphRAG between minor versions, and copying your endpoint information or other customizations over to the new file.
- [Data model](https://microsoft.github.io/graphrag/index/outputs/) - The output data model may change over time as we adjust our approach. **Changes to the data model will conform to standard semver.** Any changes to the output tables will be shimmed for backwards compatibility between major releases, and we'll provide a migration notebook for folks to upgrade without requiring a re-index.

> TL;DR: Always run `graphrag init --path [path] --force` between minor version bumps to ensure you have the latest config format. Run the provided migration notebook between major version bumps if you want to avoid re-indexing prior datasets. Note that this will overwrite your configuration and prompts, so backup if necessary.

# v1

Run the [migration notebook](./docs/examples_notebooks/index_migration_to_v1.ipynb) to convert older tables to the v1 format.

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

- Run the migration notebook (some recent changes may invalidate existing caches, so migrating the format it cheaper than re-indexing).

## New required Embeddings

### Change

- Added new required embeddings for `DRIFTSearch` and base RAG capabilities.

### Migration

- Run a new index, leveraging existing cache.

## Vector Store required by default

### Change

- Vector store is now required by default for all search methods.

### Migration

- Run `graphrag init` command to generate a new settings.yaml file with the vector store configuration.
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
