"""Content for the init CLI command."""

INIT_YAML = """
encoding_model: cl100k_base
skip_workflows: []
llm:
  api_key: ${GRAPHRAG_API_KEY}
  type: openai_chat # or azure_openai_chat
  model: gpt-4-turbo-preview
  model_supports_json: true # recommended if this is available for your model.
  # max_tokens: 4000
  # request_timeout: 180.0
  # api_base: https://<instance>.openai.azure.com
  # api_version: 2024-02-15-preview
  # organization: <organization_id>
  # deployment_name: <azure_model_deployment_name>
  # tokens_per_minute: 150_000 # set a leaky bucket throttle
  # requests_per_minute: 10_000 # set a leaky bucket throttle
  # max_retries: 10
  # max_retry_wait: 10.0
  # sleep_on_rate_limit_recommendation: true # whether to sleep when azure suggests wait-times
  # concurrent_requests: 25 # the number of parallel inflight requests that may be made

parallelization:
  stagger: 0.3
  # num_threads: 50 # the number of threads to use for parallel processing

async_mode: threaded # or asyncio

embeddings:
  llm:
    api_key: ${GRAPHRAG_API_KEY}
    type: openai_embedding # or azure_openai_embedding
    model: text-embedding-3-small
    # api_base: https://<instance>.openai.azure.com
    # api_version: 2024-02-15-preview
    # organization: <organization_id>
    # deployment_name: <azure_model_deployment_name>
    # tokens_per_minute: 150_000 # set a leaky bucket throttle
    # requests_per_minute: 10_000 # set a leaky bucket throttle
    # max_retries: 10
    # max_retry_wait: 10.0
    # sleep_on_rate_limit_recommendation: true # whether to sleep when azure suggests wait-times
    # concurrent_requests: 25 # the number of parallel inflight requests that may be made
    # batch_size: 16 # the number of documents to send in a single request
    # batch_max_tokens: 8191 # the maximum number of tokens to send in a single request
    # target: required # or optional
  
  parallelization:
    stagger: 0.3
    # num_threads: 50 # the number of threads to use for parallel processing

  async_mode: threaded # or asyncio

chunks:
  size: 300
  overlap: 100
  group_by_columns: ["id"] # by default, we don't allow chunks to cross documents
    
input:
  type: csv
  base_dir: input
  file_encoding: utf-8
  file_pattern: ".*\\\\.csv$"

cache:
  type: file # or blob
  base_dir: cache
  # connection_string: <azure_blob_storage_connection_string>
  # container_name: <azure_blob_storage_container_name>

storage:
  type: file # or blob
  base_dir: "output/${timestamp}/artifacts"
  # connection_string: <azure_blob_storage_connection_string>
  # container_name: <azure_blob_storage_container_name>

reporting:
  type: file # or console, blob
  base_dir: "output/${timestamp}/reports"
  # connection_string: <azure_blob_storage_connection_string>
  # container_name: <azure_blob_storage_container_name>

entity_extraction:
  # llm: override the global llm settings for this task
  # parallelization: override the global parallelization settings for this task
  # async_mode: override the global async_mode settings for this task
  prompt: "prompts/entity_extraction.txt"
  entity_types: ["organization", "person", "geo", "event"]
  max_gleanings: 0

summarize_descriptions:
  # llm: override the global llm settings for this task
  # parallelization: override the global parallelization settings for this task
  # async_mode: override the global async_mode settings for this task
  prompt: "prompts/summarize_descriptions.txt"
  max_length: 500

claim_extraction:
   # llm: override the global llm settings for this task
  # parallelization: override the global parallelization settings for this task
  # async_mode: override the global async_mode settings for this task
  prompt: "prompts/claim_extraction.txt"
  description: "Any claims or facts that could be relevant to information discovery."
  max_gleanings: 0

community_report:
  # llm: override the global llm settings for this task
  # parallelization: override the global parallelization settings for this task
  # async_mode: override the global async_mode settings for this task
  prompt: "prompts/community_report.txt"
  max_length: 1500
  max_input_length: 12_000

cluster_graph:
  max_cluster_size: 10

embed_graph:
  is_enabled: false # if true, will generate node2vec embeddings for nodes
  # num_walks: 10
  # walk_length: 40
  # window_size: 2
  # iterations: 3
  # random_seed: 597832

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
