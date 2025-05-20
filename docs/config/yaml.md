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

## Language Model Setup

### models

This is a dict of model configurations. The dict key is used to reference this configuration elsewhere when a model instance is desired. In this way, you can specify as many different models as you need, and reference them differentially in the workflow steps.

For example:
```yml
models:
  default_chat_model:
    api_key: ${GRAPHRAG_API_KEY}
    type: openai_chat
    model: gpt-4o
    model_supports_json: true
  default_embedding_model:
    api_key: ${GRAPHRAG_API_KEY}
    type: openai_embedding
    model: text-embedding-ada-002
```

#### Fields

- `api_key` **str** - The OpenAI API key to use.
- `auth_type` **api_key|managed_identity** - Indicate how you want to authenticate requests.
- `type` **openai_chat|azure_openai_chat|openai_embedding|azure_openai_embedding|mock_chat|mock_embeddings** - The type of LLM to use.
- `model` **str** - The model name.
- `encoding_model` **str** - The text encoding model to use. Default is to use the encoding model aligned with the language model (i.e., it is retrieved from tiktoken if unset).
- `api_base` **str** - The API base url to use.
- `api_version` **str** - The API version.
- `deployment_name` **str** - The deployment name to use (Azure).
- `organization` **str** - The client organization.
- `proxy` **str** - The proxy URL to use.
- `audience` **str** - (Azure OpenAI only) The URI of the target Azure resource/service for which a managed identity token is requested. Used if `api_key` is not defined. Default=`https://cognitiveservices.azure.com/.default`
- `model_supports_json` **bool** - Whether the model supports JSON-mode output.
- `request_timeout` **float** - The per-request timeout.
- `tokens_per_minute` **int** - Set a leaky-bucket throttle on tokens-per-minute.
- `requests_per_minute` **int** - Set a leaky-bucket throttle on requests-per-minute.
- `retry_strategy` **str** - Retry strategy to use, "native" is the default and uses the strategy built into the OpenAI SDK. Other allowable values include "exponential_backoff", "random_wait", and "incremental_wait".
- `max_retries` **int** - The maximum number of retries to use.
- `max_retry_wait` **float** - The maximum backoff time.
- `concurrent_requests` **int** The number of open requests to allow at once.
- `async_mode` **asyncio|threaded** The async mode to use. Either `asyncio` or `threaded`.
- `responses` **list[str]** - If this model type is mock, this is a list of response strings to return.
- `n` **int** - The number of completions to generate.
- `max_tokens` **int** - The maximum number of output tokens. Not valid for o-series models.
- `temperature` **float** - The temperature to use. Not valid for o-series models.
- `top_p` **float** - The top-p value to use. Not valid for o-series models.
- `frequency_penalty` **float** - Frequency penalty for token generation. Not valid for o-series models.
- `presence_penalty` **float** - Frequency penalty for token generation. Not valid for o-series models.
- `max_completion_tokens` **int** - Max number of tokens to consume for chat completion. Must be large enough to include an unknown amount for "reasoning" by the model. o-series models only.
- `reasoning_effort` **low|medium|high** - Amount of "thought" for the model to expend reasoning about a response. o-series models only.

## Input Files and Chunking

### input

Our pipeline can ingest .csv, .txt, or .json data from an input folder. See the [inputs page](../index/inputs.md) for more details and examples.

#### Fields

- `type` **file|blob** - The input type to use. Default=`file`
- `file_type` **text|csv|json** - The type of input data to load. Default is `text`
- `base_dir` **str** - The base directory to read input from, relative to the root.
- `connection_string` **str** - (blob only) The Azure Storage connection string.
- `storage_account_blob_url` **str** - The storage account blob URL to use.
- `container_name` **str** - (blob only) The Azure Storage container name.
- `encoding` **str** - The encoding of the input file. Default is `utf-8`
- `file_pattern` **str** - A regex to match input files. Default is `.*\.csv$`, `.*\.txt$`, or `.*\.json$` depending on the specified `file_type`, but you can customize it if needed.
- `file_filter` **dict** - Key/value pairs to filter. Default is None.
- `text_column` **str** - (CSV/JSON only) The text column name. If unset we expect a column named `text`.
- `title_column` **str** - (CSV/JSON only) The title column name, filename will be used if unset.
- `metadata` **list[str]** - (CSV/JSON only) The additional document attributes fields to keep.

### chunks

These settings configure how we parse documents into text chunks. This is necessary because very large documents may not fit into a single context window, and graph extraction accuracy can be modulated. Also note the `metadata` setting in the input document config, which will replicate document metadata into each chunk.

#### Fields

- `size` **int** - The max chunk size in tokens.
- `overlap` **int** - The chunk overlap in tokens.
- `group_by_columns` **list[str]** - Group documents by these fields before chunking.
- `strategy` **str**[tokens|sentences] - How to chunk the text. 
- `encoding_model` **str** - The text encoding model to use for splitting on token boundaries.
- `prepend_metadata` **bool** - Determines if metadata values should be added at the beginning of each chunk. Default=`False`.
- `chunk_size_includes_metadata` **bool** - Specifies whether the chunk size calculation should include metadata tokens. Default=`False`.

## Outputs and Storage

### output

This section controls the storage mechanism used by the pipeline used for exporting output tables.

#### Fields

- `type` **file|memory|blob|cosmosdb** - The storage type to use. Default=`file`
- `base_dir` **str** - The base directory to write output artifacts to, relative to the root.
- `connection_string` **str** - (blob/cosmosdb only) The Azure Storage connection string.
- `container_name` **str** - (blob/cosmosdb only) The Azure Storage container name.
- `storage_account_blob_url` **str** - (blob only) The storage account blob URL to use.
- `cosmosdb_account_blob_url` **str** - (cosmosdb only) The CosmosDB account blob URL to use.

### update_index_output

The section defines a secondary storage location for running incremental indexing, to preserve your original outputs.

#### Fields

- `type` **file|memory|blob|cosmosdb** - The storage type to use. Default=`file`
- `base_dir` **str** - The base directory to write output artifacts to, relative to the root.
- `connection_string` **str** - (blob/cosmosdb only) The Azure Storage connection string.
- `container_name` **str** - (blob/cosmosdb only) The Azure Storage container name.
- `storage_account_blob_url` **str** - (blob only) The storage account blob URL to use.
- `cosmosdb_account_blob_url` **str** - (cosmosdb only) The CosmosDB account blob URL to use.

### cache

This section controls the cache mechanism used by the pipeline. This is used to cache LLM invocation results for faster performance when re-running the indexing process.

#### Fields

- `type` **file|memory|blob|cosmosdb** - The storage type to use. Default=`file`
- `base_dir` **str** - The base directory to write output artifacts to, relative to the root.
- `connection_string` **str** - (blob/cosmosdb only) The Azure Storage connection string.
- `container_name` **str** - (blob/cosmosdb only) The Azure Storage container name.
- `storage_account_blob_url` **str** - (blob only) The storage account blob URL to use.
- `cosmosdb_account_blob_url` **str** - (cosmosdb only) The CosmosDB account blob URL to use.

### reporting

This section controls the reporting mechanism used by the pipeline, for common events and error messages. The default is to write reports to a file in the output directory. However, you can also choose to write reports to the console or to an Azure Blob Storage container.

#### Fields

- `type` **file|console|blob** - The reporting type to use. Default=`file`
- `base_dir` **str** - The base directory to write reports to, relative to the root.
- `connection_string` **str** - (blob only) The Azure Storage connection string.
- `container_name` **str** - (blob only) The Azure Storage container name.
- `storage_account_blob_url` **str** - The storage account blob URL to use.

### vector_store

Where to put all vectors for the system. Configured for lancedb by default. This is a dict, with the key used to identify individual store parameters (e.g., for text embedding).

#### Fields

- `type` **lancedb|azure_ai_search|cosmosdb** - Type of vector store. Default=`lancedb`
- `db_uri` **str** (only for lancedb) - The database uri. Default=`storage.base_dir/lancedb`
- `url` **str** (only for AI Search) - AI Search endpoint
- `api_key` **str** (optional - only for AI Search) - The AI Search api key to use.
- `audience` **str** (only for AI Search) - Audience for managed identity token if managed identity authentication is used.
- `container_name` **str** - The name of a vector container. This stores all indexes (tables) for a given dataset ingest. Default=`default`
- `database_name` **str** - (cosmosdb only) Name of the database.
- `overwrite` **bool** (only used at index creation time) - Overwrite collection if it exist. Default=`True`

## Workflow Configurations

These settings control each individual workflow as they execute.

### workflows

**list[str]** - This is a list of workflow names to run, in order. GraphRAG has built-in pipelines to configure this, but you can run exactly and only what you want by specifying the list here. Useful if you have done part of the processing yourself.

### embed_text

By default, the GraphRAG indexer will only export embeddings required for our query methods. However, the model has embeddings defined for all plaintext fields, and these can be customized by setting the `target` and `names` fields.

Supported embeddings names are:

- `text_unit.text`
- `document.text`
- `entity.title`
- `entity.description`
- `relationship.description`
- `community.title`
- `community.summary`
- `community.full_content`

#### Fields

- `model_id` **str** - Name of the model definition to use for text embedding.
- `vector_store_id` **str** - Name of vector store definition to write to.
- `batch_size` **int** - The maximum batch size to use.
- `batch_max_tokens` **int** - The maximum batch # of tokens.
- `names` **list[str]** - List of the embeddings names to run (must be in supported list).

### extract_graph

Tune the language model-based graph extraction process.

#### Fields

- `model_id` **str** - Name of the model definition to use for API calls.
- `prompt` **str** - The prompt file to use.
- `entity_types` **list[str]** - The entity types to identify.
- `max_gleanings` **int** - The maximum number of gleaning cycles to use.

### summarize_descriptions

#### Fields

- `model_id` **str** - Name of the model definition to use for API calls.
- `prompt` **str** - The prompt file to use.
- `max_length` **int** - The maximum number of output tokens per summarization.
- `max_input_length` **int** - The maximum number of tokens to collect for summarization (this will limit how many descriptions you send to be summarized for a given entity or relationship).

### extract_graph_nlp

Defines settings for NLP-based graph extraction methods.

#### Fields

- `normalize_edge_weights` **bool** - Whether to normalize the edge weights during graph construction. Default=`True`.
- `text_analyzer` **dict** - Parameters for the NLP model.
  - extractor_type **regex_english|syntactic_parser|cfg** - Default=`regex_english`.
  - model_name **str** - Name of NLP model (for SpaCy-based models)
  - max_word_length **int** - Longest word to allow. Default=`15`.
  - word_delimiter **str** - Delimiter to split words. Default ' '.
  - include_named_entities **bool** - Whether to include named entities in noun phrases. Default=`True`.
  - exclude_nouns **list[str] | None** - List of nouns to exclude. If `None`, we use an internal stopword list.
  - exclude_entity_tags **list[str]** - List of entity tags to ignore.
  - exclude_pos_tags **list[str]** - List of part-of-speech tags to ignore.
  - noun_phrase_tags **list[str]** - List of noun phrase tags to ignore.
  - noun_phrase_grammars **dict[str, str]** - Noun phrase grammars for the model (cfg-only).

### prune_graph

Parameters for manual graph pruning. This can be used to optimize the modularity of your graph clusters, by removing overly-connected or rare nodes.

#### Fields

- min_node_freq **int** - The minimum node frequency to allow.
- max_node_freq_std **float | None** - The maximum standard deviation of node frequency to allow.
- min_node_degree **int** - The minimum node degree to allow.
- max_node_degree_std **float | None** - The maximum standard deviation of node degree to allow.
- min_edge_weight_pct **float** - The minimum edge weight percentile to allow.
- remove_ego_nodes **bool** - Remove ego nodes.
- lcc_only **bool** - Only use largest connected component.

### cluster_graph

These are the settings used for Leiden hierarchical clustering of the graph to create communities.

#### Fields

- `max_cluster_size` **int** - The maximum cluster size to export.
- `use_lcc` **bool** - Whether to only use the largest connected component.
- `seed` **int** - A randomization seed to provide if consistent run-to-run results are desired. We do provide a default in order to guarantee clustering stability.

### extract_claims

#### Fields

- `enabled` **bool** - Whether to enable claim extraction. Off by default, because claim prompts really need user tuning.
- `model_id` **str** - Name of the model definition to use for API calls.
- `prompt` **str** - The prompt file to use.
- `description` **str** - Describes the types of claims we want to extract.
- `max_gleanings` **int** - The maximum number of gleaning cycles to use.

### community_reports

#### Fields

- `model_id` **str** - Name of the model definition to use for API calls.
- `prompt` **str** - The prompt file to use.
- `max_length` **int** - The maximum number of output tokens per report.
- `max_input_length` **int** - The maximum number of input tokens to use when generating reports.

### embed_graph

We use node2vec to embed the graph. This is primarily used for visualization, so it is not turned on by default.

#### Fields

- `enabled` **bool** - Whether to enable graph embeddings.
- `dimensions` **int** - Number of vector dimensions to produce.
- `num_walks` **int** - The node2vec number of walks.
- `walk_length` **int** - The node2vec walk length.
- `window_size` **int** - The node2vec window size.
- `iterations` **int** - The node2vec number of iterations.
- `random_seed` **int** - The node2vec random seed.
- `strategy` **dict** - Fully override the embed graph strategy.

### umap

Indicates whether we should run UMAP dimensionality reduction. This is used to provide an x/y coordinate to each graph node, suitable for visualization. If this is not enabled, nodes will receive a 0/0 x/y coordinate. If this is enabled, you *must* enable graph embedding as well.

#### Fields

- `enabled` **bool** - Whether to enable UMAP layouts.

### snapshots

#### Fields

- `embeddings` **bool** - Export embeddings snapshots to parquet.
- `graphml` **bool** - Export graph snapshots to GraphML.

## Query

### local_search

#### Fields

- `chat_model_id` **str** - Name of the model definition to use for Chat Completion calls.
- `embedding_model_id` **str** - Name of the model definition to use for Embedding calls.
- `prompt` **str** - The prompt file to use.
- `text_unit_prop` **float** - The text unit proportion. 
- `community_prop` **float** - The community proportion.
- `conversation_history_max_turns` **int** - The conversation history maximum turns.
- `top_k_entities` **int** - The top k mapped entities.
- `top_k_relationships` **int** - The top k mapped relations.
- `max_context_tokens` **int** - The maximum tokens to use building the request context.

### global_search

#### Fields

- `chat_model_id` **str** - Name of the model definition to use for Chat Completion calls.
- `map_prompt` **str** - The mapper prompt file to use.
- `reduce_prompt` **str** - The reducer prompt file to use.
- `knowledge_prompt` **str** - The knowledge prompt file to use.
- `map_prompt` **str | None** - The global search mapper prompt to use.
- `reduce_prompt` **str | None** - The global search reducer to use.
- `knowledge_prompt` **str | None** - The global search general prompt to use.
- `max_context_tokens` **int** - The maximum context size to create, in tokens.
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

- `chat_model_id` **str** - Name of the model definition to use for Chat Completion calls.
- `embedding_model_id` **str** - Name of the model definition to use for Embedding calls.
- `prompt` **str** - The prompt file to use.
- `reduce_prompt` **str** - The reducer prompt file to use.
- `data_max_tokens` **int** - The data llm maximum tokens.
- `reduce_max_tokens` **int** - The maximum tokens for the reduce phase. Only use if a non-o-series model.
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

- `chat_model_id` **str** - Name of the model definition to use for Chat Completion calls.
- `embedding_model_id` **str** - Name of the model definition to use for Embedding calls.
- `prompt` **str** - The prompt file to use.
- `k` **int | None** - Number of text units to retrieve from the vector store for context building.
