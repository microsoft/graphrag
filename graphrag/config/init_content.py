# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Content for the init CLI command to generate a default configuration."""

import graphrag.config.defaults as defs

INIT_YAML = f"""\
### This config file contains required core defaults that must be set, along with a handful of common optional settings.
### For a full list of available settings, see https://github.com/microsoft/graphrag/blob/main/graphrag/config/defaults.py

### LLM settings ###

encoding_model: cl100k_base # this needs to be matched to your model!

llm:
  api_key: ${{GRAPHRAG_API_KEY}} # set this in the generated .env file
  type: {defs.LLM_TYPE.value} # or azure_openai_chat
  model: {defs.LLM_MODEL}
  model_supports_json: true # recommended if this is available for your model.
  # audience: "https://cognitiveservices.azure.com/.default"
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
  async_mode: {defs.ASYNC_MODE.value} # or asyncio
  vector_store:{defs.VECTOR_STORE}
  # vector_store: # configuration for AI Search
    # type: azure_ai_search
    # url: <ai_search_endpoint>
    # api_key: <api_key> # if not set, will attempt to use managed identity. Expects the `Search Index Data Contributor` RBAC role in this case.
    # audience: <optional> # if using managed identity, the audience to use for the token
    # overwrite: true # or false. Only applicable at index creation time
    # container_name: default # A prefix for the AzureAISearch to create indexes. Default: 'default'.
  llm:
    api_key: ${{GRAPHRAG_API_KEY}}
    type: {defs.EMBEDDING_TYPE.value} # or azure_openai_embedding
    model: {defs.EMBEDDING_MODEL}
    # api_base: https://<instance>.openai.azure.com
    # api_version: 2024-02-15-preview
    # audience: "https://cognitiveservices.azure.com/.default"
    # organization: <organization_id>
    # deployment_name: <azure_model_deployment_name>
    # tokens_per_minute: 150_000 # set a leaky bucket throttle
    # requests_per_minute: 10_000 # set a leaky bucket throttle
    # max_retries: {defs.LLM_MAX_RETRIES}
    # max_retry_wait: {defs.LLM_MAX_RETRY_WAIT}
    # sleep_on_rate_limit_recommendation: true # whether to sleep when azure suggests wait-times
    # concurrent_requests: {defs.LLM_CONCURRENT_REQUESTS} # the number of parallel inflight requests that may be made

### Input settings ###

input:
  type: {defs.INPUT_TYPE.value} # or blob
  file_type: {defs.INPUT_FILE_TYPE.value} # or csv
  base_dir: "{defs.INPUT_BASE_DIR}"
  file_encoding: {defs.INPUT_FILE_ENCODING}
  file_pattern: ".*\\\\.txt$"

chunks:
  size: {defs.CHUNK_SIZE}
  overlap: {defs.CHUNK_OVERLAP}
  group_by_columns: [{",".join(defs.CHUNK_GROUP_BY_COLUMNS)}] # by default, we don't allow chunks to cross documents

### Storage settings ###
## If blob storage is specified in the  following four sections,
## connection_string and container_name must be provided

cache:
  type: {defs.CACHE_TYPE.value} # or blob
  base_dir: "{defs.CACHE_BASE_DIR}"

reporting:
  type: {defs.REPORTING_TYPE.value} # or console, blob
  base_dir: "{defs.REPORTING_BASE_DIR}"

storage:
  type: {defs.STORAGE_TYPE.value} # or blob
  base_dir: "{defs.STORAGE_BASE_DIR}"

## Storage to save an updated index (for incremental indexing).
## Enabling this automatically performs an incremental index run with `graphrag index`,
## however, we recommend using `graphrag update`, which will automatically set these at runtime.
update_index_storage:
  # type: {defs.STORAGE_TYPE.value} # or blob
  # base_dir: "{defs.UPDATE_STORAGE_BASE_DIR}"

### Workflow settings ###

skip_workflows: []

entity_extraction:
  prompt: "prompts/entity_extraction.txt"
  entity_types: [{",".join(defs.ENTITY_EXTRACTION_ENTITY_TYPES)}]
  max_gleanings: {defs.ENTITY_EXTRACTION_MAX_GLEANINGS}

summarize_descriptions:
  prompt: "prompts/summarize_descriptions.txt"
  max_length: {defs.SUMMARIZE_DESCRIPTIONS_MAX_LENGTH}

claim_extraction:
  # enabled: true
  prompt: "prompts/claim_extraction.txt"
  description: "{defs.CLAIM_DESCRIPTION}"
  max_gleanings: {defs.CLAIM_MAX_GLEANINGS}

community_reports:
  prompt: "prompts/community_report.txt"
  max_length: {defs.COMMUNITY_REPORT_MAX_LENGTH}
  max_input_length: {defs.COMMUNITY_REPORT_MAX_INPUT_LENGTH}

cluster_graph:
  max_cluster_size: {defs.MAX_CLUSTER_SIZE}

embed_graph:
  enabled: false # if true, will generate node2vec embeddings for nodes

umap:
  enabled: false # if true, will generate UMAP embeddings for nodes

snapshots:
  graphml: false
  raw_entities: false
  top_level_nodes: false
  embeddings: false
  transient: false

### Query settings ###
## The prompt locations for each are required, but each search method has a number of knobs that can be tuned.
## See the defaults file: https://github.com/microsoft/graphrag/blob/main/graphrag/config/defaults.py

local_search:
  prompt: "prompts/local_search_system_prompt.txt"

global_search:
  map_prompt: "prompts/global_search_map_system_prompt.txt"
  reduce_prompt: "prompts/global_search_reduce_system_prompt.txt"
  knowledge_prompt: "prompts/global_search_knowledge_system_prompt.txt"

drift_search:
  prompt: "prompts/drift_search_system_prompt.txt"
"""

INIT_DOTENV = """\
GRAPHRAG_API_KEY=<API_KEY>
"""
