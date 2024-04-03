# LLM Configuration

Ire Indexing is designed for flexibility. Each step in a set of workflows can use a different LLM configuration. 
We support both OpenAI and Azure OpenAI configurations.

In our production workflows, we define LLM parameters in a top-level configuration section within our yaml pipelines. 
We then reference these config sections in the individual workflow steps. 

#### Generic Config Section
```yml
# Create an LLM configuration block
x_config: &x_config
  arg: val
  arg2: val

# Insert the LLM configuration into a workflow step
- step
  << &x_config
```

## LLM Configuration Parameters

### LLM Configuration Parameters


| Parameter                         | Description                                                                                  | Type  | Required or Optional       | Default Value |
| --------------------------------- | -------------------------------------------------------------------------------------------- | ----- | -------------------------- | --------------|
| `type`                            | The type of LLM operation being performed. This may be one of the types listed below         | `str` | required                   | None
| `api_key`                         | The API key to use for the LLM operation.                                                    | `str` | required                   | None
| `model`                           | The model to use for the LLM operation. (e.g. `gpt-4`, `gpt-3.5-turbo`)                      | `str` | required                   | None
| `request_timeout`                 | The maximum number of seconds to wait for a response from the LLM client.                    | `int` | required                   | None
| `api_base`                        | The base URL to use for the LLM operation.                                                   | `str` | required for Azure Open AI | None
| `api_version`                     | The API version to use for the LLM operation.                                                | `str` | required for Azure Open AI | None
| `deployment_name`                 | The model deployment name to use for the LLM operation.                                      | `str` | required for Azure Open AI | None
| `proxy`                           | The proxy to use for the LLM operation.                                                      | `str` | optional for Azure Open AI | None
| `organization`                    | The organization to use for the LLM operation.                                               | `str` | optional for Azure Open AI | None
| `num_threads`                     | The number of threads to use for parallelization.                                            | `int` | optional                   | 1
| `stagger`                         | The time to wait between starting each thread.                                               | `int` | optional                   | 0


<!-- TODO: eventually we should split this up into operation, api_type -->
#### LLM Operation Types
  * **openai_embedding** - perform a text embedding using the OpenAI API
  * **azure_openai_embedding** - perform a text embedding using Azure OpenAI
  * **openai_chat** -  perform a chat-based text completion using the OpenAI API
  * **azure_openai_chat** - perform a chat-based text completion using Azure OpenAI


## Using Environment Variables 
yaml files allow for configuration values to be read from environment variables, and for default values to be provided if the environment variable is not set. 
In our production pipelines, we use a standard set of environment variables to configure our LLMs. 

```yaml
# An example of using environment variables and default values
config_section: &config_section
  config_value: !ENV ${CONFIG_VALUE_ENV_VAR:default_value}
  config_value_optional: !ENV ${CONFIG_VALUE_OPTIONAL_ENV_VAR}
```

## Standard Chat Completion Configuration

The following table lists the environment variables and default values that we use for chat completion in our pipelines. 
These are suggestions, and can be modified to suit your needs.

| Parameter                         | Description                                                                                  | Type  | Default       |
| --------------------------------- | -------------------------------------------------------------------------------------------- | ----- | ------------- |
| `GRAPHRAG_LLM_TYPE`               | The LLM operation type. Either `openai_chat` or `azure_openai_chat`                          | `str` | `openai_chat` |
| `GRAPHRAG_OPENAI_API_KEY`         | The API key.                                                                                 | `str` | `None`        |
| `GRAPHRAG_OPENAI_MODEL`           | The model.                                                                                   | `str` | `gpt-4-turbo-preview`       |
| `GRAPHRAG_MAX_TOKENS`             | The maximum number of tokens.                                                                | `int` | `4000`        |
| `GRAPHRAG_REQUEST_TIMEOUT`        | The maximum number of seconds to wait for a response from the chat client.                   | `int` | `180`         |
| `GRAPHRAG_OPENAI_DEPLOYMENT_NAME` | The AOAI deployment name.                                                                    | `str` | `gpt-4-turbo-preview     `  |
| `GRAPHRAG_OPENAI_API_BASE`        | The AOAI base URL.                                                                           | `str` | `None`        |
| `GRAPHRAG_OPENAI_API_VERSION`     | The AOAI API version.                                                                        | `str` | `None`        |
| `GRAPHRAG_OPENAI_ORGANIZATION`    | The AOAI organization.                                                                       | `str` | `None`        |
| `GRAPHRAG_OPENAI_PROXY`           | The AOAI proxy.                                                                              | `str` | `None`        |

These can be either specified by environment variables or by a YAML file. The YAML property should included in the pipeline configuration file as follows:

### Standard Embedding Configuration

The following table lists the environment variables and default values that we use for text embeddings in our pipelines. 
These are suggestions, and can be modified to suit your needs.

| Parameter                                | Description                                                                                       | Type  | Default                  |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------- | ----- | ------------------------ |
| `GRAPHRAG_EMBEDDING_LLM_TYPE`            | The embedding client to use. Either `openai_embedding` or `azure_openai_embedding`                | `str` | `openai_embedding`       |
| `GRAPHRAG_OPENAI_EMBEDDING_API_KEY`      | The API key to use for the embedding client.                                                      | `str` | `None`                   |
| `GRAPHRAG_OPENAI_EMBEDDING_MODEL`        | The model to use for the embedding client.                                                        | `str` | `text-embedding-3-small` |
| `GRAPHRAG_OPENAI_EMBEDDING_API_BASE`     | The AOAI base URL to use for the embedding client.                                                | `str` | `None`                   |
| `GRAPHRAG_OPENAI_EMBEDDING_API_VERSION`  | The AOAI API version to use for the embedding client.                                             | `str` | `None`                   |
| `GRAPHRAG_OPENAI_EMBEDDING_ORGANIZATION` | The AOAI organization to use for the embedding client.                                            | `str` | `None`                   |
| `GRAPHRAG_EMBEDDING_OPENAI_PROXY`        | The AOAI proxy to use for the embedding client.                                                   | `str` | `None`                   |


### Example LLM Configurations

#### Chat Completion 

```yaml
llm_config: &llm_config
  type: !ENV ${GRAPHRAG_LLM_TYPE:openai_chat}
  api_key: !ENV ${GRAPHRAG_OPENAI_API_KEY}
  model: !ENV ${GRAPHRAG_OPENAI_MODEL:gpt-4-turbo-preview
  deployment_name: !ENV ${GRAPHRAG_OPENAI_DEPLOYMENT_NAME:gpt-4-turbo-preview

  # max_tokens: !ENV ${GRAPHRAG_MAX_TOKENS:4000}
  request_timeout: !ENV ${GRAPHRAG_REQUEST_TIMEOUT:180} # 3 minutes because translation can be time intensive

  # Azure specific
  api_base: !ENV ${GRAPHRAG_OPENAI_API_BASE}
  api_version: !ENV ${GRAPHRAG_OPENAI_API_VERSION}
  organization: !ENV ${GRAPHRAG_OPENAI_ORGANIZATION}
  proxy: !ENV ${GRAPHRAG_OPENAI_PROXY}
```

#### Text Embeddings
```yaml
embedding_config: &embedding_config
  type: !ENV ${GRAPHRAG_EMBEDDING_LLM_TYPE:openai_embedding}
  api_key: !ENV ${GRAPHRAG_OPENAI_EMBEDDING_API_KEY}
  model: !ENV ${GRAPHRAG_OPENAI_EMBEDDING_MODEL:text-embedding-3-small}

  # Azure specific
  api_base: !ENV ${GRAPHRAG_OPENAI_EMBEDDING_API_BASE}
  api_version: !ENV ${GRAPHRAG_OPENAI_EMBEDDING_API_VERSION}
  organization: !ENV ${GRAPHRAG_OPENAI_EMBEDDING_ORGANIZATION}
  proxy: !ENV ${GRAPHRAG_EMBEDDING_OPENAI_PROXY}
```

#### Parallelization
```yaml
# Example (usable in any LLM configuration)
sample_llm_parallel_config: &sample_llm_parallel_config 
  # This should be based on our TPM limit + our RPM
  num_threads: 3

  # for gpt-4 we have ~200RPM so ~3.33 a second
  # so we start a thread every 0.3 seconds or so
  stagger: 0.4
```
