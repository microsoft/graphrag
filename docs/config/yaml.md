# Default Configuration Mode (using YAML/JSON)

The default configuration mode may be configured by using a `settings.yml` or `settings.json` file in the data project root. If a `.env` file is present along with this config file, then it will be loaded, and the environment variables defined therein will be available for token replacements in your configuration document using `${ENV_VAR}` syntax. We initialize with YML by default in `graphrag init` but you may use the equivalent JSON form if preferred.

Many of these config values have defaults. Rather than replicate them here, please refer to the [constants in the code](https://github.com/microsoft/graphrag/blob/main/graphrag/config/defaults.py) directly.

For example:

```bash
# .env
GRAPHRAG_API_KEY=some_api_key

# settings.yml
default_chat_model:
  api_key: ${GRAPHRAG_API_KEY}
```

# Config Sections

## Language Model Setup

### models

This is a set of dicts, one for completion model configuration and one for embedding model configuration. The dict keys are used to reference the model configuration elsewhere when a model instance is desired. In this way, you can specify as many different models as you need, and reference them independently in the workflow steps.

For example:

```yml
completion_models:
  default_completion_model:
    model_provider: openai
    model: gpt-4.1
    auth_method: api_key
    api_key: ${GRAPHRAG_API_KEY}

embedding_models:
  default_embedding_model:
    model_provider: openai
    model: text-embedding-3-large
    auth_method: api_key
    api_key: ${GRAPHRAG_API_KEY}
```

#### Fields

- `type` **litellm|mock** - The type of LLM provider to use. GraphRAG uses [LiteLLM](https://docs.litellm.ai/) for calling language models.
- `model_provider` **str** - The model provider to use, e.g., openai, azure, anthropic, etc. [LiteLLM](https://docs.litellm.ai/) is used under the hood which has support for calling 100+ models. [View LiteLLm basic usage](https://docs.litellm.ai/docs/#basic-usage) for details on how models are called (The `model_provider` is the portion prior to `/` while the `model` is the portion following the `/`). [View Language Model Selection](models.md) for more details and examples on using LiteLLM.
- `model` **str** - The model name.
- `call_args`: **dict[str, Any]** - Default arguments to send with every model request. Example, `{"n": 5, "max_completion_tokens": 1000, "temperature": 1.5, "organization": "..." }`
- `api_key` **str|None** - The OpenAI API key to use.
- `api_base` **str|None** - The API base url to use.
- `api_version` **str|None** - The API version.
- `auth_method` **api_key|azure_managed_identity** - Indicate how you want to authenticate requests.
- `azure_deployment_name` **str|None** - The deployment name to use if your model is hosted on Azure. Note that if your deployment name on Azure matches the model name, this is unnecessary.
- retry **RetryConfig|None** - Retry settings. default=`None`, no retries.
  - type **exponential_backoff|immediate** - Type of retry approach. default=`exponential_backoff`
  - max_retries **int|None** - Max retries to take. default=`7`.
  - base_delay **float|None** - Base delay when using `exponential_backoff`. default=`2.0`.
  - jitter **bool|None** - Add jitter to retry delays when using `exponential_backoff`. default=`True`
  - max_delay **float|None** - Maximum retry delay. default=`None`, no max.
- rate_limit **RateLimitConfig|None** - Rate limit settings. default=`None`, no rate limiting.
  - type **sliding_window** - Type of rate limit approach. default=`sliding_window`
  - period_in_seconds **int|None** - Window size for `sliding_window` rate limiting. default=`60`, limit requests per minute.
  - requests_per_period **int|None** - Maximum number of requests per period. default=`None`
  - tokens_per_period **int|None** - Maximum number of tokens per period. default=`None`
- metrics **MetricsConfig|None** - Metric settings. default=`MetricsConfig()`. View [metrics notebook](https://github.com/microsoft/graphrag/blob/main/packages/graphrag-llm/notebooks/04_metrics.ipynb) for more details on metrics.
  - type **default** - The type of `MetricsProcessor` service to use for processing request metrics. default=`default`
  - store **memory** - The type of `MetricsStore` service. default=`memory`.
  - writer **log|file** - The type of `MetricsWriter` to use. Will write out metrics at the end of the process. default`log`, log metrics out using python standard logging at the end of the process.
  - log_level **int|None** - The log level when using `log` writer. default=`20`, log `INFO` messages for metrics.
  - base_dir **str|None** - The directory to write metrics to when using `file` writer. default=`Path.cwd()`.

## Input Files and Chunking

### input

Our pipeline can ingest .csv, .txt, or .json data from an input location. See the [inputs page](../index/inputs.md) for more details and examples.

#### Fields

- `storage` **StorageConfig**
  - `type` **file|memory|blob|cosmosdb** - The storage type to use. Default=`file`
  - `encoding`**str** - The encoding to use for file storage.
  - `base_dir` **str** - The base directory to write output artifacts to, relative to the root.
  - `connection_string` **str** - (blob/cosmosdb only) The Azure Storage connection string.
  - `container_name` **str** - (blob/cosmosdb only) The Azure Storage container name.
  - `account_url` **str** - (blob only) The storage account blob URL to use.
  - `database_name` **str** - (cosmosdb only) The database name to use.
- `type` **text|csv|json** - The type of input data to load. Default is `text`
- `encoding` **str** - The encoding of the input file. Default is `utf-8`
- `file_pattern` **str** - A regex to match input files. Default is `.*\.csv$`, `.*\.txt$`, or `.*\.json$` depending on the specified `type`, but you can customize it if needed.
- `id_column` **str** - The input ID column to use.
- `title_column` **str** - The input title column to use.
- `text_column` **str** - The input text column to use.

### chunking

These settings configure how we parse documents into text chunks. This is necessary because very large documents may not fit into a single context window, and graph extraction accuracy can be modulated. Also note the `metadata` setting in the input document config, which will replicate document metadata into each chunk.

#### Fields

- `type` **tokens|sentence** - The chunking type to use.
- `encoding_model` **str** - The text encoding model to use for splitting on token boundaries.
- `size` **int** - The max chunk size in tokens.
- `overlap` **int** - The chunk overlap in tokens.
- `prepend_metadata` **list[str]** - Metadata fields from the source document to prepend on each chunk.

## Outputs and Storage

### output

This section controls the storage mechanism used by the pipeline used for exporting output tables.

#### Fields

- `type` **file|memory|blob|cosmosdb** - The storage type to use. Default=`file`
- `encoding`**str** - The encoding to use for file storage.
- `base_dir` **str** - The base directory to write output artifacts to, relative to the root.
- `connection_string` **str** - (blob/cosmosdb only) The Azure Storage connection string.
- `container_name` **str** - (blob/cosmosdb only) The Azure Storage container name.
- `account_url` **str** - (blob only) The storage account blob URL to use.
- `database_name` **str** - (cosmosdb only) The database name to use.
- `type` **text|csv|json** - The type of input data to load. Default is `text`
- `encoding` **str** - The encoding of the input file. Default is `utf-8`

### update_output_storage

The section defines a secondary storage location for running incremental indexing, to preserve your original outputs.

#### Fields

- `type` **file|memory|blob|cosmosdb** - The storage type to use. Default=`file`
- `encoding`**str** - The encoding to use for file storage.
- `base_dir` **str** - The base directory to write output artifacts to, relative to the root.
- `connection_string` **str** - (blob/cosmosdb only) The Azure Storage connection string.
- `container_name` **str** - (blob/cosmosdb only) The Azure Storage container name.
- `account_url` **str** - (blob only) The storage account blob URL to use.
- `database_name` **str** - (cosmosdb only) The database name to use.
- `type` **text|csv|json** - The type of input data to load. Default is `text`
- `encoding` **str** - The encoding of the input file. Default is `utf-8`

### cache

This section controls the cache mechanism used by the pipeline. This is used to cache LLM invocation results for faster performance when re-running the indexing process.

#### Fields

- `type` **json|memory|none** - The storage type to use. Default=`json`
- `storage` **StorageConfig**
  - `type` **file|memory|blob|cosmosdb** - The storage type to use. Default=`file`
  - `encoding`**str** - The encoding to use for file storage.
  - `base_dir` **str** - The base directory to write output artifacts to, relative to the root.
  - `connection_string` **str** - (blob/cosmosdb only) The Azure Storage connection string.
  - `container_name` **str** - (blob/cosmosdb only) The Azure Storage container name.
  - `account_url` **str** - (blob only) The storage account blob URL to use.
  - `database_name` **str** - (cosmosdb only) The database name to use.

### reporting

This section controls the reporting mechanism used by the pipeline, for common events and error messages. The default is to write reports to a file in the output directory. However, you can also choose to write reports to an Azure Blob Storage container.

#### Fields

- `type` **file|blob** - The reporting type to use. Default=`file`
- `base_dir` **str** - The base directory to write reports to, relative to the root.
- `connection_string` **str** - (blob only) The Azure Storage connection string.
- `container_name` **str** - (blob only) The Azure Storage container name.
- `account_url` **str** - The storage account blob URL to use.

### vector_store

Where to put all vectors for the system. Configured for lancedb by default. This is a dict, with the key used to identify individual store parameters (e.g., for text embedding).

#### Fields

- `type` **lancedb|azure_ai_search|cosmosdb** - Type of vector store. Default=`lancedb`
- `db_uri` **str** (lancedb only) - The database uri. Default=`storage.base_dir/lancedb`
- `url` **str** (blob/cosmosdb only) - Database / AI Search to be used.
- `api_key` **str** (optional - AI Search only) - The AI Search api key to use.
- `audience` **str** (AI Search only) - Audience for managed identity token if managed identity authentication is used.
- `connection_string` **str** - (cosmosdb only) The Azure Storage connection string.
- `database_name` **str** - (cosmosdb only) Name of the database.

- `index_schema` **dict[str, dict[str, str]]** (optional) - Enables customization for each of your embeddings.
  - `<supported_embedding>`:
    - `index_name` **str**: (optional) - Name for the specific embedding index table.
    - `id_field` **str**: (optional) - Field name to be used as id. Default=`id`
    - `vector_field` **str**: (optional) - Field name to be used as vector. Default=`vector`
    - `vector_size` **int**: (optional) - Vector size for the embeddings. Default=`3072`

The supported embeddings are:

- `text_unit_text`
- `entity_description`
- `community_full_content`

For example:

```yaml
vector_store:
  type: lancedb
  db_uri: output/lancedb
  index_schema:
    text_unit_text:
      index_name: "text-unit-embeddings"
      id_field: "id_custom"
      vector_field: "vector_custom"
      vector_size: 3072
    entity_description:
      id_field: "id_custom"
```

## Workflow Configurations

These settings control each individual workflow as they execute.

### workflows

**list[str]** - This is a list of workflow names to run, in order. GraphRAG has built-in pipelines to configure this, but you can run exactly and only what you want by specifying the list here. Useful if you have done part of the processing yourself.

### embed_text

By default, the GraphRAG indexer will only export embeddings required for our query methods. However, the model has embeddings defined for all plaintext fields, and these can be customized by setting the `target` and `names` fields.

Supported embeddings names are:

- `text_unit_text`
- `entity_description`
- `community_full_content`

#### Fields

- `embedding_model_id` **str** - Name of the model definition to use for text embedding.
- `model_instance_name` **str** - Name of the model singleton instance. Default is "text_embedding". This primarily affects the cache storage partitioning.
- `batch_size` **int** - The maximum batch size to use.
- `batch_max_tokens` **int** - The maximum batch # of tokens.
- `names` **list[str]** - List of the embeddings names to run (must be in supported list).

### extract_graph

Tune the language model-based graph extraction process.

#### Fields

- `completion_model_id` **str** - Name of the model definition to use for API calls.
- `model_instance_name` **str** - Name of the model singleton instance. Default is "extract_graph". This primarily affects the cache storage partitioning.
- `prompt` **str** - The prompt file to use.
- `entity_types` **list[str]** - The entity types to identify.
- `max_gleanings` **int** - The maximum number of gleaning cycles to use.

### summarize_descriptions

#### Fields

- `completion_model_id` **str** - Name of the model definition to use for API calls.
- `model_instance_name` **str** - Name of the model singleton instance. Default is "summarize_descriptions". This primarily affects the cache storage partitioning.
- `prompt` **str** - The prompt file to use.
- `max_length` **int** - The maximum number of output tokens per summarization.
- `max_input_length` **int** - The maximum number of tokens to collect for summarization (this will limit how many descriptions you send to be summarized for a given entity or relationship).

### extract_graph_nlp

Defines settings for NLP-based graph extraction methods.

#### Fields

- `normalize_edge_weights` **bool** - Whether to normalize the edge weights during graph construction. Default=`True`.
- `concurrent_requests` **int** - The number of threads to use for the extraction process.
- `async_mode` **asyncio|threaded** - The async mode to use. Either `asyncio` or `threaded`.
- `text_analyzer` **dict** - Parameters for the NLP model.
  - `extractor_type` **regex_english|syntactic_parser|cfg** - Default=`regex_english`.
  - `model_name` **str** - Name of NLP model (for SpaCy-based models)
  - `max_word_length` **int** - Longest word to allow. Default=`15`.
  - `word_delimiter` **str** - Delimiter to split words. Default ' '.
  - `include_named_entities` **bool** - Whether to include named entities in noun phrases. Default=`True`.
  - `exclude_nouns` **list[str] | None** - List of nouns to exclude. If `None`, we use an internal stopword list.
  - `exclude_entity_tags` **list[str]** - List of entity tags to ignore.
  - `exclude_pos_tags` **list[str]** - List of part-of-speech tags to ignore.
  - `noun_phrase_tags` **list[str]** - List of noun phrase tags to ignore.
  - `noun_phrase_grammars` **dict[str, str]** - Noun phrase grammars for the model (cfg-only).

### prune_graph

Parameters for manual graph pruning. This can be used to optimize the modularity of your graph clusters, by removing overly-connected or rare nodes.

#### Fields

- `min_node_freq` **int** - The minimum node frequency to allow.
- `max_node_freq_std` **float | None** - The maximum standard deviation of node frequency to allow.
- `min_node_degree` **int** - The minimum node degree to allow.
- `max_node_degree_std` **float | None** - The maximum standard deviation of node degree to allow.
- `min_edge_weight_pct` **float** - The minimum edge weight percentile to allow.
- `remove_ego_nodes` **bool** - Remove ego nodes.
- `lcc_only` **bool** - Only use largest connected component.

### cluster_graph

These are the settings used for Leiden hierarchical clustering of the graph to create communities.

#### Fields

- `max_cluster_size` **int** - The maximum cluster size to export.
- `use_lcc` **bool** - Whether to only use the largest connected component.
- `seed` **int** - A randomization seed to provide if consistent run-to-run results are desired. We do provide a default in order to guarantee clustering stability.

### extract_claims

#### Fields

- `enabled` **bool** - Whether to enable claim extraction. Off by default, because claim prompts really need user tuning.
- `completion_model_id` **str** - Name of the model definition to use for API calls.
- `model_instance_name` **str** - Name of the model singleton instance. Default is "extract_claims". This primarily affects the cache storage partitioning.
- `prompt` **str** - The prompt file to use.
- `description` **str** - Describes the types of claims we want to extract.
- `max_gleanings` **int** - The maximum number of gleaning cycles to use.

### community_reports

#### Fields

- `completion_model_id` **str** - Name of the model definition to use for API calls.
- `model_instance_name` **str** - Name of the model singleton instance. Default is "community_reporting". This primarily affects the cache storage partitioning.
- `graph_prompt` **str | None** - The community report extraction prompt to use for graph-based summarization.
- `text_prompt` **str | None** - The community report extraction prompt to use for text-based summarization.
- `max_length` **int** - The maximum number of output tokens per report.
- `max_input_length` **int** - The maximum number of input tokens to use when generating reports.

### snapshots

#### Fields

- `embeddings` **bool** - Export embeddings snapshots to parquet.
- `graphml` **bool** - Export graph snapshot to GraphML.
- `raw_graph` **bool** - Export raw extracted graph before merging.

## Query

### local_search

#### Fields

- `prompt` **str** - The prompt file to use.
- `completion_model_id` **str** - Name of the model definition to use for Chat Completion calls.
- `embedding_model_id` **str** - Name of the model definition to use for Embedding calls.
- `text_unit_prop` **float** - The text unit proportion.
- `community_prop` **float** - The community proportion.
- `conversation_history_max_turns` **int** - The conversation history maximum turns.
- `top_k_entities` **int** - The top k mapped entities.
- `top_k_relationships` **int** - The top k mapped relations.
- `max_context_tokens` **int** - The maximum tokens to use building the request context.

### global_search

#### Fields

- `map_prompt` **str** - The global search mapper prompt to use.
- `reduce_prompt` **str** - The global search reducer to use.
- `completion_model_id` **str** - Name of the model definition to use for Chat Completion calls.
- `knowledge_prompt` **str** - The knowledge prompt file to use.
- `data_max_tokens` **int** - The maximum tokens to use constructing the final response from the reduces responses.
- `map_max_length` **int** - The maximum length to request for map responses, in words.
- `reduce_max_length` **int** - The maximum length to request for reduce responses, in words.
- `dynamic_search_threshold` **int** - Rating threshold in include a community report.
- `dynamic_search_keep_parent` **bool** - Keep parent community if any of the child communities are relevant.
- `dynamic_search_num_repeats` **int** - Number of times to rate the same community report.
- `dynamic_search_use_summary` **bool** - Use community summary instead of full_context.
- `dynamic_search_max_level` **int** - The maximum level of community hierarchy to consider if none of the processed communities are relevant.

### drift_search

#### Fields

- `prompt` **str** - The prompt file to use.
- `reduce_prompt` **str** - The reducer prompt file to use.
- `completion_model_id` **str** - Name of the model definition to use for Chat Completion calls.
- `embedding_model_id` **str** - Name of the model definition to use for Embedding calls.
- `data_max_tokens` **int** - The data llm maximum tokens.
- `reduce_max_tokens` **int** - The maximum tokens for the reduce phase. Only use if a non-o-series model.
- `reduce_temperature` **float** - The temperature to use for token generation in reduce.
- `reduce_max_completion_tokens` **int** - The maximum tokens for the reduce phase. Only use for o-series models.
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
- `local_search_llm_max_gen_tokens` **int** - The maximum number of generated tokens for the LLM in local search. Only use if a non-o-series model.
- `local_search_llm_max_gen_completion_tokens` **int** - The maximum number of generated tokens for the LLM in local search. Only use for o-series models.

### basic_search

#### Fields

- `prompt` **str** - The prompt file to use.
- `completion_model_id` **str** - Name of the model definition to use for Chat Completion calls.
- `embedding_model_id` **str** - Name of the model definition to use for Embedding calls.
- `k` **int** - Number of text units to retrieve from the vector store for context building.
- `max_context_tokens` **int** - The maximum context size to create, in tokens.
