---
title: Default Configuration Mode (using JSON/YAML)
navtitle: Using JSON or YAML
tags: [post]
layout: page
date: 2023-01-03
---

The default configuration mode may be configured by using a `config.json` or `config.yml` file in the data project root. If a `.env` file is present along with this config file, then it will be loaded, and the environment variables defined therein will be available for token replacements in your configuration document using `${ENV_VAR}` syntax.

For example:

```
# .env
API_KEY=some_api_key

# config.json
{
    "llm": {
        "api_key": "${API_KEY}"
    }
}
```

# Config Sections

## input

### Fields

- `type` **file|blob** - The input type to use. Default=`file`
- `file_type` **text|csv** - The type of input data to load. Either `text` or `csv`. Default is `text`
- `file_encoding` **str** - The encoding of the input file. Default is `utf-8`
- `file_pattern` **str** - A regex to match input files. Default is `.*\.csv$` if in csv mode and `.*\.txt$` if in text mode.
- `source_column` **str** - (CSV Mode Only) The source column name.
- `timestamp_column` **str** - (CSV Mode Only) The timestamp column name.
- `timestamp_format` **str** - (CSV Mode Only) The source format.
- `text_column` **str** - (CSV Mode Only) The text column name.
- `title_column` **str** - (CSV Mode Only) The title column name.
- `document_attribute_columns` **list[str]** - (CSV Mode Only) The additional document attributes to include.
- `connection_string` **str** - (blob only) The Azure Storage connection string.
- `container_name` **str** - (blob only) The Azure Storage container name.
- `base_dir` **str** - The base directory to read input from, relative to the root.
- `storage_account_blob_url` **str** - The storage account blob URL to use.

## llm

This is the base LLM configuration section. Other steps may override this configuration with their own LLM configuration.

### Fields

- `api_key` **str** - The OpenAI API key to use.
- `type` **openai_chat|azure_openai_chat|openai_embedding|azure_openai_embedding** - The type of LLM to use.
- `model` **str** - The model name.
- `max_tokens` **int** - The maximum number of output tokens.
- `request_timeout` **float** - The per-request timeout.
- `api_base` **str** - The API base url to use.
- `api_version` **str** - The API version
- `organization` **str** - The client organization.
- `proxy` **str** - The proxy URL to use.
- `cognitive_services_endpoint` **str** - The url endpoint for cognitive services.
- `deployment_name` **str** - The deployment name to use (Azure).
- `model_supports_json` **bool** - Whether the model supports JSON-mode output.
- `tokens_per_minute` **int** - Set a leaky-bucket throttle on tokens-per-minute.
- `requests_per_minute` **int** - Set a leaky-bucket throttle on requests-per-minute.
- `max_retries` **int** - The maximum number of retries to use.
- `max_retry_wait` **float** - The maximum backoff time.
- `sleep_on_rate_limit_recommendation` **bool** - Whether to adhere to sleep recommendations (Azure).
- `concurrent_requests` **int** The number of open requests to allow at once.

## parallelization

### Fields

- `stagger` **float** - The threading stagger value.
- `num_threads` **int** - The maximum number of work threads.

## async_mode

**asyncio|threaded** The async mode to use. Either `asyncio` or `threaded.

## embeddings

### Fields

- `llm` (see LLM top-level config)
- `parallelization` (see Parallelization top-level config)
- `async_mode` (see Async Mode top-level config)
- `batch_size` **int** - The maximum batch size to use.
- `batch_max_tokens` **int** - The maximum batch #-tokens.
- `target` **required|all** - Determines which set of embeddings to emit.
- `skip` **list[str]** - Which embeddings to skip.
- `strategy` **dict** - Fully override the text-embedding strategy.

## chunks

### Fields

- `size` **int** - The max chunk size in tokens.
- `overlap` **int** - The chunk overlap in tokens.
- `group_by_columns` **list[str]** - group documents by fields before chunking.
- `strategy` **dict** - Fully override the chunking strategy.

## cache

### Fields

- `type` **file|memory|none|blob** - The cache type to use. Default=`file`
- `connection_string` **str** - (blob only) The Azure Storage connection string.
- `container_name` **str** - (blob only) The Azure Storage container name.
- `base_dir` **str** - The base directory to write cache to, relative to the root.
- `storage_account_blob_url` **str** - The storage account blob URL to use.

## storage

### Fields

- `type` **file|memory|blob** - The storage type to use. Default=`file`
- `connection_string` **str** - (blob only) The Azure Storage connection string.
- `container_name` **str** - (blob only) The Azure Storage container name.
- `base_dir` **str** - The base directory to write reports to, relative to the root.
- `storage_account_blob_url` **str** - The storage account blob URL to use.

## reporting

### Fields

- `type` **file|console|blob** - The reporting type to use. Default=`file`
- `connection_string` **str** - (blob only) The Azure Storage connection string.
- `container_name` **str** - (blob only) The Azure Storage container name.
- `base_dir` **str** - The base directory to write reports to, relative to the root.
- `storage_account_blob_url` **str** - The storage account blob URL to use.

## entity_extraction

### Fields

- `llm` (see LLM top-level config)
- `parallelization` (see Parallelization top-level config)
- `async_mode` (see Async Mode top-level config)
- `prompt` **str** - The prompt file to use.
- `entity_types` **list[str]** - The entity types to identify.
- `max_gleanings` **int** - The maximum number of gleaning cycles to use.
- `strategy` **dict** - Fully override the entity extraction strategy.

## summarize_descriptions

### Fields

- `llm` (see LLM top-level config)
- `parallelization` (see Parallelization top-level config)
- `async_mode` (see Async Mode top-level config)
- `prompt` **str** - The prompt file to use.
- `max_length` **int** - The maximum number of output tokens per summarization.
- `strategy` **dict** - Fully override the summarize description strategy.

## claim_extraction

### Fields

- `enabled` **bool** - Whether to enable claim extraction. default=False
- `llm` (see LLM top-level config)
- `parallelization` (see Parallelization top-level config)
- `async_mode` (see Async Mode top-level config)
- `prompt` **str** - The prompt file to use.
- `description` **str** - Describes the types of claims we want to extract.
- `max_gleanings` **int** - The maximum number of gleaning cycles to use.
- `strategy` **dict** - Fully override the claim extraction strategy.

## community_reports

### Fields

- `llm` (see LLM top-level config)
- `parallelization` (see Parallelization top-level config)
- `async_mode` (see Async Mode top-level config)
- `prompt` **str** - The prompt file to use.
- `max_length` **int** - The maximum number of output tokens per report.
- `max_input_length` **int** - The maximum number of input tokens to use when generating reports.
- `strategy` **dict** - Fully override the community reports strategy.

## cluster_graph

### Fields

- `max_cluster_size` **int** - The maximum cluster size to emit.
- `strategy` **dict** - Fully override the cluster_graph strategy.

## embed_graph

### Fields

- `enabled` **bool** - Whether to enable graph embeddings.
- `num_walks` **int** - The node2vec number of walks.
- `walk_length` **int** - The node2vec walk length.
- `window_size` **int** - The node2vec window size.
- `iterations` **int** - The node2vec number of iterations.
- `random_seed` **int** - The node2vec random seed.
- `strategy` **dict** - Fully override the embed graph strategy.

## umap

### Fields

- `enabled` **bool** - Whether to enable UMAP layouts.

## snapshots

### Fields

- `graphml` **bool** - Emit graphml snapshots.
- `raw_entities` **bool** - Emit raw entity snapshots.
- `top_level_nodes` **bool** - Emit top-level-node snapshots.

## encoding_model

**str** - The text encoding model to use. Default is `cl100k_base`.

## skip_workflows

**list[str]** - Which workflow names to skip.
