# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Content for the init CLI command to generate a default configuration."""

import graphrag.config.defaults as defs
from graphrag.config.defaults import (
    graphrag_config_defaults,
    language_model_defaults,
    vector_store_defaults,
)

INIT_YAML = f"""\
### This config file contains required core defaults that must be set, along with a handful of common optional settings.
### For a full list of available settings, see https://microsoft.github.io/graphrag/config/yaml/

### LLM settings ###
## There are a number of settings to tune the threading and token limits for LLM calls - check the docs.

models:
  {defs.DEFAULT_CHAT_MODEL_ID}:
    type: {defs.DEFAULT_CHAT_MODEL_TYPE.value}
    model_provider: {defs.DEFAULT_MODEL_PROVIDER}
    auth_type: {defs.DEFAULT_CHAT_MODEL_AUTH_TYPE.value} # or azure_managed_identity
    api_key: ${{GRAPHRAG_API_KEY}} # set this in the generated .env file, or remove if managed identity
    model: {defs.DEFAULT_CHAT_MODEL}
    # api_base: https://<instance>.openai.azure.com
    # api_version: 2024-05-01-preview
    model_supports_json: true # recommended if this is available for your model.
    concurrent_requests: {language_model_defaults.concurrent_requests}
    async_mode: {language_model_defaults.async_mode.value} # or asyncio
    retry_strategy: {language_model_defaults.retry_strategy}
    max_retries: {language_model_defaults.max_retries}
    tokens_per_minute: null
    requests_per_minute: null
  {defs.DEFAULT_EMBEDDING_MODEL_ID}:
    type: {defs.DEFAULT_EMBEDDING_MODEL_TYPE.value}
    model_provider: {defs.DEFAULT_MODEL_PROVIDER}
    auth_type: {defs.DEFAULT_EMBEDDING_MODEL_AUTH_TYPE.value}
    api_key: ${{GRAPHRAG_API_KEY}}
    model: {defs.DEFAULT_EMBEDDING_MODEL}
    # api_base: https://<instance>.openai.azure.com
    # api_version: 2024-05-01-preview
    concurrent_requests: {language_model_defaults.concurrent_requests}
    async_mode: {language_model_defaults.async_mode.value} # or asyncio
    retry_strategy: {language_model_defaults.retry_strategy}
    max_retries: {language_model_defaults.max_retries}
    tokens_per_minute: null
    requests_per_minute: null

### Input settings ###

input:
  storage:
    type: {graphrag_config_defaults.input.storage.type.value} # or blob
    base_dir: "{graphrag_config_defaults.input.storage.base_dir}"
  file_type: {graphrag_config_defaults.input.file_type.value} # [csv, text, json]

chunks:
  size: {graphrag_config_defaults.chunks.size}
  overlap: {graphrag_config_defaults.chunks.overlap}
  group_by_columns: [{",".join(graphrag_config_defaults.chunks.group_by_columns)}]

### Output/storage settings ###
## If blob storage is specified in the following four sections,
## connection_string and container_name must be provided

output:
  type: {graphrag_config_defaults.output.type.value} # [file, blob, cosmosdb]
  base_dir: "{graphrag_config_defaults.output.base_dir}"
    
cache:
  type: {graphrag_config_defaults.cache.type.value} # [file, blob, cosmosdb]
  base_dir: "{graphrag_config_defaults.cache.base_dir}"

reporting:
  type: {graphrag_config_defaults.reporting.type.value} # [file, blob]
  base_dir: "{graphrag_config_defaults.reporting.base_dir}"

vector_store:
  {defs.DEFAULT_VECTOR_STORE_ID}:
    type: {vector_store_defaults.type}
    db_uri: {vector_store_defaults.db_uri}
    container_name: {vector_store_defaults.container_name}

### Workflow settings ###

embed_text:
  model_id: {graphrag_config_defaults.embed_text.model_id}
  vector_store_id: {graphrag_config_defaults.embed_text.vector_store_id}

extract_graph:
  model_id: {graphrag_config_defaults.extract_graph.model_id}
  prompt: "prompts/extract_graph.txt"
  entity_types: [{",".join(graphrag_config_defaults.extract_graph.entity_types)}]
  max_gleanings: {graphrag_config_defaults.extract_graph.max_gleanings}

summarize_descriptions:
  model_id: {graphrag_config_defaults.summarize_descriptions.model_id}
  prompt: "prompts/summarize_descriptions.txt"
  max_length: {graphrag_config_defaults.summarize_descriptions.max_length}

extract_graph_nlp:
  text_analyzer:
    extractor_type: {graphrag_config_defaults.extract_graph_nlp.text_analyzer.extractor_type.value} # [regex_english, syntactic_parser, cfg]
  async_mode: {graphrag_config_defaults.extract_graph_nlp.async_mode.value} # or asyncio

cluster_graph:
  max_cluster_size: {graphrag_config_defaults.cluster_graph.max_cluster_size}

extract_claims:
  enabled: false
  model_id: {graphrag_config_defaults.extract_claims.model_id}
  prompt: "prompts/extract_claims.txt"
  description: "{graphrag_config_defaults.extract_claims.description}"
  max_gleanings: {graphrag_config_defaults.extract_claims.max_gleanings}

community_reports:
  model_id: {graphrag_config_defaults.community_reports.model_id}
  graph_prompt: "prompts/community_report_graph.txt"
  text_prompt: "prompts/community_report_text.txt"
  max_length: {graphrag_config_defaults.community_reports.max_length}
  max_input_length: {graphrag_config_defaults.community_reports.max_input_length}

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
  chat_model_id: {graphrag_config_defaults.local_search.chat_model_id}
  embedding_model_id: {graphrag_config_defaults.local_search.embedding_model_id}
  prompt: "prompts/local_search_system_prompt.txt"

global_search:
  chat_model_id: {graphrag_config_defaults.global_search.chat_model_id}
  map_prompt: "prompts/global_search_map_system_prompt.txt"
  reduce_prompt: "prompts/global_search_reduce_system_prompt.txt"
  knowledge_prompt: "prompts/global_search_knowledge_system_prompt.txt"

drift_search:
  chat_model_id: {graphrag_config_defaults.drift_search.chat_model_id}
  embedding_model_id: {graphrag_config_defaults.drift_search.embedding_model_id}
  prompt: "prompts/drift_search_system_prompt.txt"
  reduce_prompt: "prompts/drift_search_reduce_prompt.txt"

basic_search:
  chat_model_id: {graphrag_config_defaults.basic_search.chat_model_id}
  embedding_model_id: {graphrag_config_defaults.basic_search.embedding_model_id}
  prompt: "prompts/basic_search_system_prompt.txt"
"""

INIT_DOTENV = """\
GRAPHRAG_API_KEY=<API_KEY>
"""
