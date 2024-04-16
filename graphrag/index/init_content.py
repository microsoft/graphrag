# Copyright (c) 2024 Microsoft Corporation. All rights reserved.
"""Content for the init CLI command."""

from graphrag.index.default_config.parameters.defaults import (
    DEFAULT_ASYNC_MODE,
    DEFAULT_CACHE_BASE_DIR,
    DEFAULT_CACHE_TYPE,
    DEFAULT_CHUNK_GROUP_BY_COLUMNS,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CLAIM_DESCRIPTION,
    DEFAULT_CLAIM_MAX_GLEANINGS,
    DEFAULT_COMMUNITY_REPORT_MAX_INPUT_LENGTH,
    DEFAULT_COMMUNITY_REPORT_MAX_LENGTH,
    DEFAULT_EMBEDDING_BATCH_MAX_TOKENS,
    DEFAULT_EMBEDDING_BATCH_SIZE,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_TARGET,
    DEFAULT_EMBEDDING_TYPE,
    DEFAULT_ENTITY_EXTRACTION_ENTITY_TYPES,
    DEFAULT_INPUT_BASE_DIR,
    DEFAULT_INPUT_FILE_ENCODING,
    DEFAULT_INPUT_TYPE,
    DEFAULT_LLM_CONCURRENT_REQUESTS,
    DEFAULT_LLM_MAX_RETRIES,
    DEFAULT_LLM_MAX_RETRY_WAIT,
    DEFAULT_LLM_MAX_TOKENS,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_REQUEST_TIMEOUT,
    DEFAULT_LLM_TYPE,
    DEFAULT_MAX_CLUSTER_SIZE,
    DEFAULT_NODE2VEC_ITERATIONS,
    DEFAULT_NODE2VEC_NUM_WALKS,
    DEFAULT_NODE2VEC_RANDOM_SEED,
    DEFAULT_NODE2VEC_WALK_LENGTH,
    DEFAULT_NODE2VEC_WINDOW_SIZE,
    DEFAULT_PARALLELIZATION_NUM_THREADS,
    DEFAULT_PARALLELIZATION_STAGGER,
    DEFAULT_REPORTING_BASE_DIR,
    DEFAULT_REPORTING_TYPE,
    DEFAULT_STORAGE_BASE_DIR,
    DEFAULT_STORAGE_TYPE,
    DEFAULT_SUMMARIZE_DESCRIPTIONS_MAX_LENGTH,
)

INIT_YAML = f"""
encoding_model: cl100k_base
skip_workflows: []
llm:
  api_key: ${{GRAPHRAG_API_KEY}}
  type: {DEFAULT_LLM_TYPE.value} # or azure_openai_chat
  model: {DEFAULT_LLM_MODEL}
  model_supports_json: true # recommended if this is available for your model.
  # max_tokens: {DEFAULT_LLM_MAX_TOKENS}
  # request_timeout: {DEFAULT_LLM_REQUEST_TIMEOUT}
  # api_base: https://<instance>.openai.azure.com
  # api_version: 2024-02-15-preview
  # organization: <organization_id>
  # deployment_name: <azure_model_deployment_name>
  # tokens_per_minute: 150_000 # set a leaky bucket throttle
  # requests_per_minute: 10_000 # set a leaky bucket throttle
  # max_retries: {DEFAULT_LLM_MAX_RETRIES}
  # max_retry_wait: {DEFAULT_LLM_MAX_RETRY_WAIT}
  # sleep_on_rate_limit_recommendation: true # whether to sleep when azure suggests wait-times
  # concurrent_requests: {DEFAULT_LLM_CONCURRENT_REQUESTS} # the number of parallel inflight requests that may be made

parallelization:
  stagger: {DEFAULT_PARALLELIZATION_STAGGER}
  # num_threads: {DEFAULT_PARALLELIZATION_NUM_THREADS} # the number of threads to use for parallel processing

async_mode: {DEFAULT_ASYNC_MODE.value} # or asyncio

embeddings:
  ## parallelization: override the global parallelization settings for embeddings
  async_mode: {DEFAULT_ASYNC_MODE.value} # or asyncio
  llm:
    api_key: ${{GRAPHRAG_API_KEY}}
    type: {DEFAULT_EMBEDDING_TYPE.value} # or azure_openai_embedding
    model: {DEFAULT_EMBEDDING_MODEL}
    # api_base: https://<instance>.openai.azure.com
    # api_version: 2024-02-15-preview
    # organization: <organization_id>
    # deployment_name: <azure_model_deployment_name>
    # tokens_per_minute: 150_000 # set a leaky bucket throttle
    # requests_per_minute: 10_000 # set a leaky bucket throttle
    # max_retries: {DEFAULT_LLM_MAX_RETRIES}
    # max_retry_wait: {DEFAULT_LLM_MAX_RETRY_WAIT}
    # sleep_on_rate_limit_recommendation: true # whether to sleep when azure suggests wait-times
    # concurrent_requests: {DEFAULT_LLM_CONCURRENT_REQUESTS} # the number of parallel inflight requests that may be made
    # batch_size: {DEFAULT_EMBEDDING_BATCH_SIZE} # the number of documents to send in a single request
    # batch_max_tokens: {DEFAULT_EMBEDDING_BATCH_MAX_TOKENS} # the maximum number of tokens to send in a single request
    # target: {DEFAULT_EMBEDDING_TARGET.value} # or optional
  


chunks:
  size: {DEFAULT_CHUNK_SIZE}
  overlap: {DEFAULT_CHUNK_OVERLAP}
  group_by_columns: [{",".join(DEFAULT_CHUNK_GROUP_BY_COLUMNS)}] # by default, we don't allow chunks to cross documents
    
input:
  type: {DEFAULT_INPUT_TYPE.value}
  base_dir: "{DEFAULT_INPUT_BASE_DIR}"
  file_encoding: {DEFAULT_INPUT_FILE_ENCODING}
  file_pattern: ".*\\\\.csv$"

cache:
  type: {DEFAULT_CACHE_TYPE.value} # or blob
  base_dir: "{DEFAULT_CACHE_BASE_DIR}"
  # connection_string: <azure_blob_storage_connection_string>
  # container_name: <azure_blob_storage_container_name>

storage:
  type: {DEFAULT_STORAGE_TYPE.value} # or blob
  base_dir: "{DEFAULT_STORAGE_BASE_DIR}"
  # connection_string: <azure_blob_storage_connection_string>
  # container_name: <azure_blob_storage_container_name>

reporting:
  type: {DEFAULT_REPORTING_TYPE.value} # or console, blob
  base_dir: "{DEFAULT_REPORTING_BASE_DIR}"
  # connection_string: <azure_blob_storage_connection_string>
  # container_name: <azure_blob_storage_container_name>

entity_extraction:
  ## llm: override the global llm settings for this task
  ## parallelization: override the global parallelization settings for this task
  ## async_mode: override the global async_mode settings for this task
  prompt: "prompts/entity_extraction.txt"
  entity_types: [{",".join(DEFAULT_ENTITY_EXTRACTION_ENTITY_TYPES)}]
  max_gleanings: 0

summarize_descriptions:
  ## llm: override the global llm settings for this task
  ## parallelization: override the global parallelization settings for this task
  ## async_mode: override the global async_mode settings for this task
  prompt: "prompts/summarize_descriptions.txt"
  max_length: {DEFAULT_SUMMARIZE_DESCRIPTIONS_MAX_LENGTH}

claim_extraction:
  ## llm: override the global llm settings for this task
  ## parallelization: override the global parallelization settings for this task
  ## async_mode: override the global async_mode settings for this task
  prompt: "prompts/claim_extraction.txt"
  description: "{DEFAULT_CLAIM_DESCRIPTION}"
  max_gleanings: {DEFAULT_CLAIM_MAX_GLEANINGS}

community_report:
  ## llm: override the global llm settings for this task
  ## parallelization: override the global parallelization settings for this task
  ## async_mode: override the global async_mode settings for this task
  prompt: "prompts/community_report.txt"
  max_length: {DEFAULT_COMMUNITY_REPORT_MAX_LENGTH}
  max_input_length: {DEFAULT_COMMUNITY_REPORT_MAX_INPUT_LENGTH}

cluster_graph:
  max_cluster_size: {DEFAULT_MAX_CLUSTER_SIZE}

embed_graph:
  is_enabled: false # if true, will generate node2vec embeddings for nodes
  # num_walks: {DEFAULT_NODE2VEC_NUM_WALKS}
  # walk_length: {DEFAULT_NODE2VEC_WALK_LENGTH}
  # window_size: {DEFAULT_NODE2VEC_WINDOW_SIZE}
  # iterations: {DEFAULT_NODE2VEC_ITERATIONS}
  # random_seed: {DEFAULT_NODE2VEC_RANDOM_SEED}

umap:
  is_enabled: false # if true, will generate UMAP embeddings for nodes

snapshots:
  graphml: false
  raw_entities: false
  top_level_nodes: false
"""

INIT_DOTENV = """
GRAPHRAG_API_KEY=<API_KEY>
"""
