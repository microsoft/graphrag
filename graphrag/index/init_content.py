# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License
"""Content for the init CLI command."""

import graphrag.config.defaults as defs

INIT_YAML = f"""
encoding_model: cl100k_base
skip_workflows: []
llm:
  api_key: ${{GRAPHRAG_API_KEY}}
  type: {defs.LLM_TYPE.value} # or azure_openai_chat
  model: {defs.LLM_MODEL}
  model_supports_json: true # recommended if this is available for your model.
  # max_tokens: {defs.LLM_MAX_TOKENS}
  # request_timeout: {defs.LLM_REQUEST_TIMEOUT}
  # api_base: https://<instance>.openai.azure.com
  # api_version: 2024-02-15-preview
  # organization: <organization_id>
  # deployment_name: <azure_model_deployment_name>
  # tokens_per_minute: 150_000 # set a leaky bucket throttle
  # requests_per_minute: 10_000 # set a leaky bucket throttle
  # max_retries: {defs.LLM_MAX_RETRIES}
  # max_retry_wait: {defs.LLM_MAX_RETRY_WAIT}
  # sleep_on_rate_limit_recommendation: true # whether to sleep when azure suggests wait-times
  # concurrent_requests: {defs.LLM_CONCURRENT_REQUESTS} # the number of parallel inflight requests that may be made
  # temperature: {defs.LLM_TEMPERATURE} # temperature for sampling
  # top_p: {defs.LLM_TOP_P} # top-p sampling
  # n: {defs.LLM_N} # Number of completions to generate

parallelization:
  stagger: {defs.PARALLELIZATION_STAGGER}
  # num_threads: {defs.PARALLELIZATION_NUM_THREADS} # the number of threads to use for parallel processing

async_mode: {defs.ASYNC_MODE.value} # or asyncio

embeddings:
  ## parallelization: override the global parallelization settings for embeddings
  async_mode: {defs.ASYNC_MODE.value} # or asyncio
  # target: {defs.EMBEDDING_TARGET.value} # or all
  # batch_size: {defs.EMBEDDING_BATCH_SIZE} # the number of documents to send in a single request
  # batch_max_tokens: {defs.EMBEDDING_BATCH_MAX_TOKENS} # the maximum number of tokens to send in a single request
  llm:
    api_key: ${{GRAPHRAG_API_KEY}}
    type: {defs.EMBEDDING_TYPE.value} # or azure_openai_embedding
    model: {defs.EMBEDDING_MODEL}
    # api_base: https://<instance>.openai.azure.com
    # api_version: 2024-02-15-preview
    # organization: <organization_id>
    # deployment_name: <azure_model_deployment_name>
    # tokens_per_minute: 150_000 # set a leaky bucket throttle
    # requests_per_minute: 10_000 # set a leaky bucket throttle
    # max_retries: {defs.LLM_MAX_RETRIES}
    # max_retry_wait: {defs.LLM_MAX_RETRY_WAIT}
    # sleep_on_rate_limit_recommendation: true # whether to sleep when azure suggests wait-times
    # concurrent_requests: {defs.LLM_CONCURRENT_REQUESTS} # the number of parallel inflight requests that may be made

chunks:
  size: {defs.CHUNK_SIZE}
  overlap: {defs.CHUNK_OVERLAP}
  group_by_columns: [{",".join(defs.CHUNK_GROUP_BY_COLUMNS)}] # by default, we don't allow chunks to cross documents

input:
  type: {defs.INPUT_TYPE.value} # or blob
  file_type: {defs.INPUT_FILE_TYPE.value} # or csv
  base_dir: "{defs.INPUT_BASE_DIR}"
  file_encoding: {defs.INPUT_FILE_ENCODING}
  file_pattern: ".*\\\\.txt$"

cache:
  type: {defs.CACHE_TYPE.value} # or blob
  base_dir: "{defs.CACHE_BASE_DIR}"
  # connection_string: <azure_blob_storage_connection_string>
  # container_name: <azure_blob_storage_container_name>

storage:
  type: {defs.STORAGE_TYPE.value} # or blob
  base_dir: "{defs.STORAGE_BASE_DIR}"
  # connection_string: <azure_blob_storage_connection_string>
  # container_name: <azure_blob_storage_container_name>

reporting:
  type: {defs.REPORTING_TYPE.value} # or console, blob
  base_dir: "{defs.REPORTING_BASE_DIR}"
  # connection_string: <azure_blob_storage_connection_string>
  # container_name: <azure_blob_storage_container_name>

entity_extraction:
  ## strategy: fully override the entity extraction strategy.
  ##   type: one of graph_intelligence, graph_intelligence_json and nltk
  ## llm: override the global llm settings for this task
  ## parallelization: override the global parallelization settings for this task
  ## async_mode: override the global async_mode settings for this task
  prompt: "prompts/entity_extraction.txt"
  entity_types: [{",".join(defs.ENTITY_EXTRACTION_ENTITY_TYPES)}]
  max_gleanings: {defs.ENTITY_EXTRACTION_MAX_GLEANINGS}

summarize_descriptions:
  ## llm: override the global llm settings for this task
  ## parallelization: override the global parallelization settings for this task
  ## async_mode: override the global async_mode settings for this task
  prompt: "prompts/summarize_descriptions.txt"
  max_length: {defs.SUMMARIZE_DESCRIPTIONS_MAX_LENGTH}

claim_extraction:
  ## llm: override the global llm settings for this task
  ## parallelization: override the global parallelization settings for this task
  ## async_mode: override the global async_mode settings for this task
  # enabled: true
  prompt: "prompts/claim_extraction.txt"
  description: "{defs.CLAIM_DESCRIPTION}"
  max_gleanings: {defs.CLAIM_MAX_GLEANINGS}

community_reports:
  ## llm: override the global llm settings for this task
  ## parallelization: override the global parallelization settings for this task
  ## async_mode: override the global async_mode settings for this task
  prompt: "prompts/community_report.txt"
  max_length: {defs.COMMUNITY_REPORT_MAX_LENGTH}
  max_input_length: {defs.COMMUNITY_REPORT_MAX_INPUT_LENGTH}

cluster_graph:
  max_cluster_size: {defs.MAX_CLUSTER_SIZE}

embed_graph:
  enabled: false # if true, will generate node2vec embeddings for nodes
  # num_walks: {defs.NODE2VEC_NUM_WALKS}
  # walk_length: {defs.NODE2VEC_WALK_LENGTH}
  # window_size: {defs.NODE2VEC_WINDOW_SIZE}
  # iterations: {defs.NODE2VEC_ITERATIONS}
  # random_seed: {defs.NODE2VEC_RANDOM_SEED}

umap:
  enabled: false # if true, will generate UMAP embeddings for nodes

snapshots:
  graphml: false
  raw_entities: false
  top_level_nodes: false

local_search:
  # text_unit_prop: {defs.LOCAL_SEARCH_TEXT_UNIT_PROP}
  # community_prop: {defs.LOCAL_SEARCH_COMMUNITY_PROP}
  # conversation_history_max_turns: {defs.LOCAL_SEARCH_CONVERSATION_HISTORY_MAX_TURNS}
  # top_k_mapped_entities: {defs.LOCAL_SEARCH_TOP_K_MAPPED_ENTITIES}
  # top_k_relationships: {defs.LOCAL_SEARCH_TOP_K_RELATIONSHIPS}
  # llm_temperature: {defs.LOCAL_SEARCH_LLM_TEMPERATURE} # temperature for sampling
  # llm_top_p: {defs.LOCAL_SEARCH_LLM_TOP_P} # top-p sampling
  # llm_n: {defs.LOCAL_SEARCH_LLM_N} # Number of completions to generate
  # max_tokens: {defs.LOCAL_SEARCH_MAX_TOKENS}

global_search:
  # llm_temperature: {defs.GLOBAL_SEARCH_LLM_TEMPERATURE} # temperature for sampling
  # llm_top_p: {defs.GLOBAL_SEARCH_LLM_TOP_P} # top-p sampling
  # llm_n: {defs.GLOBAL_SEARCH_LLM_N} # Number of completions to generate
  # max_tokens: {defs.GLOBAL_SEARCH_MAX_TOKENS}
  # data_max_tokens: {defs.GLOBAL_SEARCH_DATA_MAX_TOKENS}
  # map_max_tokens: {defs.GLOBAL_SEARCH_MAP_MAX_TOKENS}
  # reduce_max_tokens: {defs.GLOBAL_SEARCH_REDUCE_MAX_TOKENS}
  # concurrency: {defs.GLOBAL_SEARCH_CONCURRENCY}
"""

INIT_DOTENV = """
GRAPHRAG_API_KEY=<API_KEY>
"""
