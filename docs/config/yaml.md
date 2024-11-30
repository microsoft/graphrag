# Default Configuration Mode (using YAML/JSON)

The default configuration mode may be configured by using a `settings.yml` or `settings.json` file in the data project root. If a `.env` file is present along with this config file, then it will be loaded, and the environment variables defined therein will be available for token replacements in your configuration document using `${ENV_VAR}` syntax. We initialize with YML by default in `graphrag init` but you may use the equivalent JSON form if preferred.

Many of these config values have defaults. Rather than replicate them here, please refer to the [constants in the code](https://github.com/microsoft/graphrag/blob/main/graphrag/config/defaults.py) directly.

For example:

```
# .env
GRAPHRAG_API_KEY=some_api_key

# settings.yml
llm: 
  api_key: ${GRAPHRAG_API_KEY}
```

# Config Sections

## Indexing

### llm

This is the base LLM configuration section. Other steps may override this configuration with their own LLM configuration.

#### Fields

- `api_key` **str** - The OpenAI API key to use.
- `type` **openai_chat|azure_openai_chat|openai_embedding|azure_openai_embedding** - The type of LLM to use.
- `model` **str** - The model name.
- `max_tokens` **int** - The maximum number of output tokens.
- `request_timeout` **float** - The per-request timeout.
- `api_base` **str** - The API base url to use.
- `api_version` **str** - The API version
- `organization` **str** - The client organization.
- `proxy` **str** - The proxy URL to use.
- `audience` **str** - (Azure OpenAI only) The URI of the target Azure resource/service for which a managed identity token is requested. Used if `api_key` is not defined. Default=`https://cognitiveservices.azure.com/.default`
- `deployment_name` **str** - The deployment name to use (Azure).
- `model_supports_json` **bool** - Whether the model supports JSON-mode output.
- `tokens_per_minute` **int** - Set a leaky-bucket throttle on tokens-per-minute.
- `requests_per_minute` **int** - Set a leaky-bucket throttle on requests-per-minute.
- `max_retries` **int** - The maximum number of retries to use.
- `max_retry_wait` **float** - The maximum backoff time.
- `sleep_on_rate_limit_recommendation` **bool** - Whether to adhere to sleep recommendations (Azure).
- `concurrent_requests` **int** The number of open requests to allow at once.
- `temperature` **float** - The temperature to use.
- `top_p` **float** - The top-p value to use.
- `n` **int** - The number of completions to generate.

### parallelization

#### Fields

- `stagger` **float** - The threading stagger value.
- `num_threads` **int** - The maximum number of work threads.

### async_mode

**asyncio|threaded** The async mode to use. Either `asyncio` or `threaded.

### embeddings

#### Fields

- `llm` (see LLM top-level config)
- `parallelization` (see Parallelization top-level config)
- `async_mode` (see Async Mode top-level config)
- `batch_size` **int** - The maximum batch size to use.
- `batch_max_tokens` **int** - The maximum batch # of tokens.
- `target` **required|all|none** - Determines which set of embeddings to export.
- `skip` **list[str]** - Which embeddings to skip. Only useful if target=all to customize the list.
- `vector_store` **dict** - The vector store to use. Configured for lancedb by default.
    - `type` **str** - `lancedb` or `azure_ai_search`. Default=`lancedb`
    - `db_uri` **str** (only for lancedb) - The database uri. Default=`storage.base_dir/lancedb`
    - `url` **str** (only for AI Search) - AI Search endpoint
    - `api_key` **str** (optional - only for AI Search) - The AI Search api key to use.
    - `audience` **str** (only for AI Search) - Audience for managed identity token if managed identity authentication is used.
    - `overwrite` **bool** (only used at index creation time) - Overwrite collection if it exist. Default=`True`
    - `container_name` **str** - The name of a vector container. This stores all indexes (tables) for a given dataset ingest. Default=`default`
- `strategy` **dict** - Fully override the text-embedding strategy.

### input

#### Fields

- `type` **file|blob** - The input type to use. Default=`file`
- `file_type` **text|csv** - The type of input data to load. Either `text` or `csv`. Default is `text`
- `base_dir` **str** - The base directory to read input from, relative to the root.
- `connection_string` **str** - (blob only) The Azure Storage connection string.
- `storage_account_blob_url` **str** - The storage account blob URL to use.
- `container_name` **str** - (blob only) The Azure Storage container name.
- `file_encoding` **str** - The encoding of the input file. Default is `utf-8`
- `file_pattern` **str** - A regex to match input files. Default is `.*\.csv$` if in csv mode and `.*\.txt$` if in text mode.
- `file_filter` **dict** - Key/value pairs to filter. Default is None.
- `source_column` **str** - (CSV Mode Only) The source column name.
- `timestamp_column` **str** - (CSV Mode Only) The timestamp column name.
- `timestamp_format` **str** - (CSV Mode Only) The source format.
- `text_column` **str** - (CSV Mode Only) The text column name.
- `title_column` **str** - (CSV Mode Only) The title column name.
- `document_attribute_columns` **list[str]** - (CSV Mode Only) The additional document attributes to include.

### chunks

#### Fields

- `size` **int** - The max chunk size in tokens.
- `overlap` **int** - The chunk overlap in tokens.
- `group_by_columns` **list[str]** - group documents by fields before chunking.
- `encoding_model` **str** - The text encoding model to use. Default is to use the top-level encoding model.
- `strategy` **dict** - Fully override the chunking strategy.

### cache

#### Fields

- `type` **file|memory|none|blob** - The cache type to use. Default=`file`
- `connection_string` **str** - (blob only) The Azure Storage connection string.
- `container_name` **str** - (blob only) The Azure Storage container name.
- `base_dir` **str** - The base directory to write cache to, relative to the root.
- `storage_account_blob_url` **str** - The storage account blob URL to use.

### storage

#### Fields

- `type` **file|memory|blob** - The storage type to use. Default=`file`
- `connection_string` **str** - (blob only) The Azure Storage connection string.
- `container_name` **str** - (blob only) The Azure Storage container name.
- `base_dir` **str** - The base directory to write output artifacts to, relative to the root.
- `storage_account_blob_url` **str** - The storage account blob URL to use.

### update_index_storage

#### Fields

- `type` **file|memory|blob** - The storage type to use. Default=`file`
- `connection_string` **str** - (blob only) The Azure Storage connection string.
- `container_name` **str** - (blob only) The Azure Storage container name.
- `base_dir` **str** - The base directory to write output artifacts to, relative to the root.
- `storage_account_blob_url` **str** - The storage account blob URL to use.

### reporting

#### Fields

- `type` **file|console|blob** - The reporting type to use. Default=`file`
- `connection_string` **str** - (blob only) The Azure Storage connection string.
- `container_name` **str** - (blob only) The Azure Storage container name.
- `base_dir` **str** - The base directory to write reports to, relative to the root.
- `storage_account_blob_url` **str** - The storage account blob URL to use.

### entity_extraction

#### Fields

- `llm` (see LLM top-level config)
- `parallelization` (see Parallelization top-level config)
- `async_mode` (see Async Mode top-level config)
- `prompt` **str** - The prompt file to use.
- `entity_types` **list[str]** - The entity types to identify.
- `max_gleanings` **int** - The maximum number of gleaning cycles to use.
- `encoding_model` **str** - The text encoding model to use. By default, this will use the top-level encoding model.
- `strategy` **dict** - Fully override the entity extraction strategy.

### summarize_descriptions

#### Fields

- `llm` (see LLM top-level config)
- `parallelization` (see Parallelization top-level config)
- `async_mode` (see Async Mode top-level config)
- `prompt` **str** - The prompt file to use.
- `max_length` **int** - The maximum number of output tokens per summarization.
- `strategy` **dict** - Fully override the summarize description strategy.

### claim_extraction

#### Fields

- `enabled` **bool** - Whether to enable claim extraction. Off by default, because claim prompts really need user tuning.
- `llm` (see LLM top-level config)
- `parallelization` (see Parallelization top-level config)
- `async_mode` (see Async Mode top-level config)
- `prompt` **str** - The prompt file to use.
- `description` **str** - Describes the types of claims we want to extract.
- `max_gleanings` **int** - The maximum number of gleaning cycles to use.
- `encoding_model` **str** - The text encoding model to use. By default, this will use the top-level encoding model.
- `strategy` **dict** - Fully override the claim extraction strategy.

### community_reports

#### Fields

- `llm` (see LLM top-level config)
- `parallelization` (see Parallelization top-level config)
- `async_mode` (see Async Mode top-level config)
- `prompt` **str** - The prompt file to use.
- `max_length` **int** - The maximum number of output tokens per report.
- `max_input_length` **int** - The maximum number of input tokens to use when generating reports.
- `strategy` **dict** - Fully override the community reports strategy.

### cluster_graph

#### Fields

- `max_cluster_size` **int** - The maximum cluster size to export.
- `strategy` **dict** - Fully override the cluster_graph strategy.

### embed_graph

#### Fields

- `enabled` **bool** - Whether to enable graph embeddings.
- `num_walks` **int** - The node2vec number of walks.
- `walk_length` **int** - The node2vec walk length.
- `window_size` **int** - The node2vec window size.
- `iterations` **int** - The node2vec number of iterations.
- `random_seed` **int** - The node2vec random seed.
- `strategy` **dict** - Fully override the embed graph strategy.

### umap

#### Fields

- `enabled` **bool** - Whether to enable UMAP layouts.

### snapshots

#### Fields

- `embeddings` **bool** - Export embeddings snapshots to parquet.
- `graphml` **bool** - Export graph snapshots to GraphML.
- `raw_entities` **bool** - Export raw entity snapshots to JSON.
- `top_level_nodes` **bool** - Export top-level-node snapshots to JSON.
- `transient` **bool** - Export transient workflow tables snapshots to parquet.

### encoding_model

**str** - The text encoding model to use. Default=`cl100k_base`.

### skip_workflows

**list[str]** - Which workflow names to skip.

## Query

### local_search

#### Fields

- `prompt` **str** - The prompt file to use.
- `text_unit_prop` **float** - The text unit proportion. 
- `community_prop` **float** - The community proportion.
- `conversation_history_max_turns` **int** - The conversation history maximum turns.
- `top_k_entities` **int** - The top k mapped entities.
- `top_k_relationships` **int** - The top k mapped relations.
- `temperature` **float | None** - The temperature to use for token generation.
- `top_p` **float | None** - The top-p value to use for token generation.
- `n` **int | None** - The number of completions to generate.
- `max_tokens` **int** - The maximum tokens.
- `llm_max_tokens` **int** - The LLM maximum tokens.

### global_search

#### Fields

- `map_prompt` **str** - The mapper prompt file to use.
- `reduce_prompt` **str** - The reducer prompt file to use.
- `knowledge_prompt` **str** - The knowledge prompt file to use.
- `map_prompt` **str | None** - The global search mapper prompt to use.
- `reduce_prompt` **str | None** - The global search reducer to use.
- `knowledge_prompt` **str | None** - The global search general prompt to use.
- `temperature` **float | None** - The temperature to use for token generation.
- `top_p` **float | None** - The top-p value to use for token generation.
- `n` **int | None** - The number of completions to generate.
- `max_tokens` **int** - The maximum context size in tokens.
- `data_max_tokens` **int** - The data llm maximum tokens.
- `map_max_tokens` **int** - The map llm maximum tokens.
- `reduce_max_tokens` **int** - The reduce llm maximum tokens.
- `concurrency` **int** - The number of concurrent requests.
- `dynamic_search_llm` **str** - LLM model to use for dynamic community selection.
- `dynamic_search_threshold` **int** - Rating threshold in include a community report.
- `dynamic_search_keep_parent` **bool** - Keep parent community if any of the child communities are relevant.
- `dynamic_search_num_repeats` **int** - Number of times to rate the same community report.
- `dynamic_search_use_summary` **bool** - Use community summary instead of full_context.
- `dynamic_search_concurrent_coroutines` **int** - Number of concurrent coroutines to rate community reports.
- `dynamic_search_max_level` **int** - The maximum level of community hierarchy to consider if none of the processed communities are relevant.

### drift_search

#### Fields

- `prompt` **str** - The prompt file to use.
- `temperature` **float** - The temperature to use for token generation.",
- `top_p` **float** - The top-p value to use for token generation.
- `n` **int** - The number of completions to generate.
- `max_tokens` **int** - The maximum context size in tokens.
- `data_max_tokens` **int** - The data llm maximum tokens.
- `concurrency` **int** - The number of concurrent requests.
- `drift_k_followups` **int** - The number of top global results to retrieve.
- `primer_folds` **int** - The number of folds for search priming.
- `primer_llm_max_tokens` **int** - The maximum number of tokens for the LLM in primer.
- `n_depth` **int** - The number of drift search steps to take.
- `local_search_text_unit_prop` **float** - The proportion of search dedicated to text units.
- `local_search_community_prop` **float** - The proportion of search dedicated to community properties.
- `local_search_top_k_mapped_entities` **int** - The number of top K entities to map during local search.
- `local_search_top_k_relationships` **int** - The number of top K relationships to map during local search.
- `local_search_max_data_tokens` **int** - The maximum context size in tokens for local search.
- `local_search_temperature` **float** - The temperature to use for token generation in local search.
- `local_search_top_p` **float** - The top-p value to use for token generation in local search.
- `local_search_n` **int** - The number of completions to generate in local search.
- `local_search_llm_max_gen_tokens` **int** - The maximum number of generated tokens for the LLM in local search.
