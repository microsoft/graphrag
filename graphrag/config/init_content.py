# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Content for the init CLI command to generate a default configuration."""

import graphrag.config.defaults as defs

INIT_YAML = f"""\
### This config file contains required core defaults that must be set, along with a handful of common optional settings.
### For a full list of available settings, see https://microsoft.github.io/graphrag/config/yaml/

### LLM settings ###
## There are a number of settings to tune the threading and token limits for LLM calls - check the docs.

models:
  {defs.DEFAULT_CHAT_MODEL_ID}:
    type: {defs.LLM_TYPE.value} # or azure_openai_chat
    # api_base: https://<instance>.openai.azure.com
    # api_version: 2024-05-01-preview
    auth_type: {defs.AUTH_TYPE.value} # or azure_managed_identity
    api_key: ${{GRAPHRAG_API_KEY}} # set this in the generated .env file
    # audience: "https://cognitiveservices.azure.com/.default"
    # organization: <organization_id>
    model: {defs.LLM_MODEL}
    # deployment_name: <azure_model_deployment_name>
    # encoding_model: {defs.ENCODING_MODEL} # automatically set by tiktoken if left undefined
    model_supports_json: true # recommended if this is available for your model.
    concurrent_requests: {defs.LLM_CONCURRENT_REQUESTS} # max number of simultaneous LLM requests allowed
    async_mode: {defs.ASYNC_MODE.value} # or asyncio
    retry_strategy: native
    max_retries: -1                   # set to -1 for dynamic retry logic (most optimal setting based on server response)
    tokens_per_minute: 0              # set to 0 to disable rate limiting
    requests_per_minute: 0            # set to 0 to disable rate limiting
  {defs.DEFAULT_EMBEDDING_MODEL_ID}:
    type: {defs.EMBEDDING_TYPE.value} # or azure_openai_embedding
    # api_base: https://<instance>.openai.azure.com
    # api_version: 2024-05-01-preview
    auth_type: {defs.AUTH_TYPE.value} # or azure_managed_identity
    api_key: ${{GRAPHRAG_API_KEY}}
    # audience: "https://cognitiveservices.azure.com/.default"
    # organization: <organization_id>
    model: {defs.EMBEDDING_MODEL}
    # deployment_name: <azure_model_deployment_name>
    # encoding_model: {defs.ENCODING_MODEL} # automatically set by tiktoken if left undefined
    model_supports_json: true # recommended if this is available for your model.
    concurrent_requests: {defs.LLM_CONCURRENT_REQUESTS} # max number of simultaneous LLM requests allowed
    async_mode: {defs.ASYNC_MODE.value} # or asyncio
    retry_strategy: native
    max_retries: -1                   # set to -1 for dynamic retry logic (most optimal setting based on server response)
    tokens_per_minute: 0              # set to 0 to disable rate limiting
    requests_per_minute: 0            # set to 0 to disable rate limiting

vector_store:
  {defs.VECTOR_STORE_DEFAULT_ID}:
    type: {defs.VECTOR_STORE_TYPE}
    db_uri: {defs.VECTOR_STORE_DB_URI}
    container_name: {defs.VECTOR_STORE_CONTAINER_NAME}
    overwrite: {defs.VECTOR_STORE_OVERWRITE}

embed_text:
  model_id: {defs.DEFAULT_EMBEDDING_MODEL_ID}
  vector_store_id: {defs.VECTOR_STORE_DEFAULT_ID}

### Input settings ###

input:
  type: {defs.INPUT_TYPE.value} # or blob
  file_type: {defs.INPUT_FILE_TYPE.value} # or csv
  base_dir: "{defs.INPUT_BASE_DIR}"
  file_encoding: {defs.INPUT_FILE_ENCODING}
  file_pattern: ".*\\\\.txt$$"

chunks:
  size: {defs.CHUNK_SIZE}
  overlap: {defs.CHUNK_OVERLAP}
  group_by_columns: [{",".join(defs.CHUNK_GROUP_BY_COLUMNS)}]

### Output settings ###
## If blob storage is specified in the following four sections,
## connection_string and container_name must be provided

cache:
  type: {defs.CACHE_TYPE.value} # [file, blob, cosmosdb]
  base_dir: "{defs.CACHE_BASE_DIR}"

reporting:
  type: {defs.REPORTING_TYPE.value} # [file, blob, cosmosdb]
  base_dir: "{defs.REPORTING_BASE_DIR}"

output:
  type: {defs.OUTPUT_TYPE.value} # [file, blob, cosmosdb]
  base_dir: "{defs.OUTPUT_BASE_DIR}"

### Workflow settings ###

extract_graph:
  model_id: {defs.EXTRACT_GRAPH_MODEL_ID}
  prompt: "prompts/extract_graph.txt"
  entity_types: [{",".join(defs.EXTRACT_GRAPH_ENTITY_TYPES)}]
  max_gleanings: {defs.EXTRACT_GRAPH_MAX_GLEANINGS}

summarize_descriptions:
  model_id: {defs.SUMMARIZE_MODEL_ID}
  prompt: "prompts/summarize_descriptions.txt"
  max_length: {defs.SUMMARIZE_DESCRIPTIONS_MAX_LENGTH}

extract_graph_nlp:
  text_analyzer:
    extractor_type: {defs.NLP_EXTRACTOR_TYPE.value} # [regex_english, syntactic_parser, cfg]

extract_claims:
  enabled: false
  model_id: {defs.EXTRACT_CLAIMS_MODEL_ID}
  prompt: "prompts/extract_claims.txt"
  description: "{defs.DESCRIPTION}"
  max_gleanings: {defs.CLAIM_MAX_GLEANINGS}

community_reports:
  model_id: {defs.COMMUNITY_REPORT_MODEL_ID}
  graph_prompt: "prompts/community_report_graph.txt"
  text_prompt: "prompts/community_report_text.txt"
  max_length: {defs.COMMUNITY_REPORT_MAX_LENGTH}
  max_input_length: {defs.COMMUNITY_REPORT_MAX_INPUT_LENGTH}

cluster_graph:
  max_cluster_size: {defs.MAX_CLUSTER_SIZE}

embed_graph:
  enabled: false # if true, will generate node2vec embeddings for nodes

umap:
  enabled: false # if true, will generate UMAP embeddings for nodes (embed_graph must also be enabled)

snapshots:
  graphml: false
  embeddings: false

### Query settings ###
## The prompt locations are required here, but each search method has a number of optional knobs that can be tuned.
## See the config docs: https://microsoft.github.io/graphrag/config/yaml/#query

local_search:
  prompt: "prompts/local_search_system_prompt.txt"

global_search:
  map_prompt: "prompts/global_search_map_system_prompt.txt"
  reduce_prompt: "prompts/global_search_reduce_system_prompt.txt"
  knowledge_prompt: "prompts/global_search_knowledge_system_prompt.txt"

drift_search:
  prompt: "prompts/drift_search_system_prompt.txt"
  reduce_prompt: "prompts/drift_search_reduce_prompt.txt"

basic_search:
  prompt: "prompts/basic_search_system_prompt.txt"
"""

INIT_DOTENV = """\
GRAPHRAG_API_KEY=<API_KEY>
"""
