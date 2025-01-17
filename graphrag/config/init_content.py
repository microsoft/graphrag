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
    api_key: ${{GRAPHRAG_API_KEY}} # set this in the generated .env file
    type: {defs.LLM_TYPE.value} # or azure_openai_chat
    model: {defs.LLM_MODEL}
    model_supports_json: true # recommended if this is available for your model.
    parallelization_num_threads: {defs.PARALLELIZATION_NUM_THREADS}
    parallelization_stagger: {defs.PARALLELIZATION_STAGGER}
    async_mode: {defs.ASYNC_MODE.value} # or asyncio
    # audience: "https://cognitiveservices.azure.com/.default"
    # api_base: https://<instance>.openai.azure.com
    # api_version: 2024-02-15-preview
    # organization: <organization_id>
    # deployment_name: <azure_model_deployment_name>
  {defs.DEFAULT_EMBEDDING_MODEL_ID}:
    api_key: ${{GRAPHRAG_API_KEY}}
    type: {defs.EMBEDDING_TYPE.value} # or azure_openai_embedding
    model: {defs.EMBEDDING_MODEL}
    parallelization_num_threads: {defs.PARALLELIZATION_NUM_THREADS}
    parallelization_stagger: {defs.PARALLELIZATION_STAGGER}
    async_mode: {defs.ASYNC_MODE.value} # or asyncio
    # api_base: https://<instance>.openai.azure.com
    # api_version: 2024-02-15-preview
    # audience: "https://cognitiveservices.azure.com/.default"
    # organization: <organization_id>
    # deployment_name: <azure_model_deployment_name>

vector_store:
    type: {defs.VECTOR_STORE_TYPE}
    db_uri: {defs.VECTOR_STORE_DB_URI}
    container_name: {defs.VECTOR_STORE_CONTAINER_NAME}
    overwrite: {defs.VECTOR_STORE_OVERWRITE}

embeddings:
  model_id: {defs.DEFAULT_EMBEDDING_MODEL_ID}

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
  type: {defs.CACHE_TYPE.value} # one of [blob, cosmosdb, file]
  base_dir: "{defs.CACHE_BASE_DIR}"

reporting:
  type: {defs.REPORTING_TYPE.value} # or console, blob
  base_dir: "{defs.REPORTING_BASE_DIR}"

output:
  type: {defs.OUTPUT_TYPE.value} # one of [blob, cosmosdb, file]
  base_dir: "{defs.OUTPUT_BASE_DIR}"

## only turn this on if running `graphrag index` with custom settings
## we normally use `graphrag update` with the defaults
update_index_output:
  # type: {defs.OUTPUT_TYPE.value} # or blob
  # base_dir: "{defs.UPDATE_OUTPUT_BASE_DIR}"

### Workflow settings ###

entity_extraction:
  model_id: {defs.ENTITY_EXTRACTION_MODEL_ID}
  prompt: "prompts/entity_extraction.txt"
  entity_types: [{",".join(defs.ENTITY_EXTRACTION_ENTITY_TYPES)}]
  max_gleanings: {defs.ENTITY_EXTRACTION_MAX_GLEANINGS}

summarize_descriptions:
  model_id: {defs.SUMMARIZE_MODEL_ID}
  prompt: "prompts/summarize_descriptions.txt"
  max_length: {defs.SUMMARIZE_DESCRIPTIONS_MAX_LENGTH}

claim_extraction:
  enabled: false
  model_id: {defs.CLAIM_EXTRACTION_MODEL_ID}
  prompt: "prompts/claim_extraction.txt"
  description: "{defs.CLAIM_DESCRIPTION}"
  max_gleanings: {defs.CLAIM_MAX_GLEANINGS}

community_reports:
  model_id: {defs.COMMUNITY_REPORT_MODEL_ID}
  prompt: "prompts/community_report.txt"
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
  transient: false

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
