# Ollama Hacked Solution  
I am working on integrating Ollama into GraphRAG with the proper configuration. Here is a temporary solution:

## Installation
Clone the repository and install the package using Poetry:

```shell
git clone https://github.com/s106916/graphrag
cd ./graphrag
poetry build
pip install ./dist/graphrag-0.1.1-py3-none-any.whl
```
## Configuration
change  setting.yaml file with the following content:

in embeddings: section change model: ollama:your_embedding_model

  **model: ollama:nomic-embed-text**

setting.yaml
```yaml
encoding_model: cl100k_base
skip_workflows: []
llm:
  api_key: ${GRAPHRAG_API_KEY}
  type: openai_chat # or azure_openai_chat or ollama_chat
  model: mistral
  model_supports_json: true # recommended if this is available for your model.
  # max_tokens: 4000
  # request_timeout: 180.0
  api_base: http://127.0.0.1:11434/v1
  # api_version: '2024-02-01'
  # organization: <organization_id>
  # deployment_name: default
  # tokens_per_minute: 150_000 # set a leaky bucket throttle
  # requests_per_minute: 10_000 # set a leaky bucket throttle
  # max_retries: 10
  # max_retry_wait: 10.0
  # sleep_on_rate_limit_recommendation: true # whether to sleep when azure suggests wait-times
  # concurrent_requests: 5 # the number of parallel inflight requests that may be made
  # temperature: 0 # temperature for sampling
  # top_p: 1 # top-p sampling
  # n: 1 # Number of completions to generate

parallelization:
  stagger: 0.3
  # num_threads: 50 # the number of threads to use for parallel processing

async_mode: threaded # or asyncio

embeddings:
  ## parallelization: override the global parallelization settings for embeddings
  async_mode: threaded # or asyncio
  llm:
    api_key: ${GRAPHRAG_API_KEY}
    type: openai_embedding # or azure_openai_embedding # or ollama_embedding
    model: ollama:nomic-embed-text
    api_base: http://127.0.0.1:11434/v1
    # api_version: '2024-02-01'
    # organization: <organization_id>
    # deployment_name: default-ada
    # tokens_per_minute: 150_000 # set a leaky bucket throttle
    # requests_per_minute: 10_000 # set a leaky bucket throttle
    # max_retries: 10
    # max_retry_wait: 10.0
    # sleep_on_rate_limit_recommendation: true # whether to sleep when azure suggests wait-times
    # concurrent_requests: 25 # the number of parallel inflight requests that may be made
    # batch_size: 16 # the number of documents to send in a single request
    # batch_max_tokens: 8191 # the maximum number of tokens to send in a single request
    # target: required # or optional
```