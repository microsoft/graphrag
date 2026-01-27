# Language Model Selection and Overriding

This page contains information on selecting a model to use and options to supply your own model for GraphRAG. Note that this is not a guide to finding the right model for your use case.

## Default Model Support

GraphRAG was built and tested using OpenAI models, so this is the default model set we support. This is not intended to be a limiter or statement of quality or fitness for your use case, only that it's the set we are most familiar with for prompting, tuning, and debugging.

GraphRAG uses [LiteLLM](https://docs.litellm.ai/) for calling language models. LiteLLM provides support for 100+ models though it is important to note that when choosing a model it must support returning [structured outputs](https://openai.com/index/introducing-structured-outputs-in-the-api/) adhering to a [JSON schema](https://docs.litellm.ai/docs/completion/json_mode).

Example using LiteLLM as the language model manager for GraphRAG:

```yaml
completion_models:
  default_completion_model:
    model_provider: gemini
    model: gemini-2.5-flash-lite
    auth_method: api_key
    api_key: ${GEMINI_API_KEY}

embedding_models:
  default_embedding_model:
    model_provider: gemini
    model: gemini-embedding-001
    auth_method: api_key
    api_key: ${GEMINI_API_KEY}
```

See [Detailed Configuration](yaml.md) for more details on configuration. [View LiteLLM basic usage](https://docs.litellm.ai/docs/#basic-usage) for details on how models are called (The `model_provider` is the portion prior to `/` while the `model` is the portion following the `/`).

## Model Selection Considerations

GraphRAG has been most thoroughly tested with the gpt-4 series of models from OpenAI, including gpt-4 gpt-4-turbo, gpt-4o, and gpt-4o-mini. Our [arXiv paper](https://arxiv.org/abs/2404.16130), for example, performed quality evaluation using gpt-4-turbo. As stated above, non-OpenAI models are supported through the use of LiteLLM but the suite of gpt-4 series of models from OpenAI remain the most tested and supported suite of models for GraphRAG – in other words, these are the models we know best and can help resolve issues with.

Versions of GraphRAG before 2.2.0 made extensive use of `max_tokens` and `logit_bias` to control generated response length or content. The introduction of the o-series of models added new, non-compatible parameters because these models include a reasoning component that has different consumption patterns and response generation attributes than non-reasoning models. GraphRAG 2.2.0 now supports these models, but there are important differences that need to be understood before you switch.

- Previously, GraphRAG used `max_tokens` to limit responses in a few locations. This is done so that we can have predictable content sizes when building downstream context windows for summarization. We have now switched from using `max_tokens` to use a prompted approach, which is working well in our tests. We suggest using `max_tokens` in your language model config only for budgetary reasons if you want to limit consumption, and not for expected response length control. We now also support the o-series equivalent `max_completion_tokens`, but if you use this keep in mind that there may be some unknown fixed reasoning consumption amount in addition to the response tokens, so it is not a good technique for response control.
- Previously, GraphRAG used a combination of `max_tokens` and `logit_bias` to strictly control a binary yes/no question during gleanings. This is not possible with reasoning models, so again we have switched to a prompted approach. Our tests with gpt-4o, gpt-4o-mini, and o1 show that this works consistently, but could have issues if you have an older or smaller model.
- The o-series models are much slower and more expensive. It may be useful to use an asymmetric approach to model use in your config: you can define as many models as you like in the `models` block of your settings.yaml and reference them by key for every workflow that requires a language model. You could use gpt-4o for indexing and o1 for query, for example. Experiment to find the right balance of cost, speed, and quality for your use case.
- The o-series models contain a form of native native chain-of-thought reasoning that is absent in the non-o-series models. GraphRAG's prompts sometimes contain CoT because it was an effective technique with the gpt-4\* series. It may be counterproductive with the o-series, so you may want to tune or even re-write large portions of the prompt templates (particularly for graph and claim extraction).

Example config with asymmetric model use:

```yaml
completion_models:
  extraction_completion_model:
    model_provider: openai
    model: gpt-4o
    auth_method: api_key
    api_key: ${GRAPHRAG_API_KEY}
  query_completion_model:
    model_provider: openai
    model: o1
    auth_method: api_key
    api_key: ${GRAPHRAG_API_KEY}
...
extract_graph:
  completion_model_id: extraction_completion_model
  prompt: "prompts/extract_graph.txt"
  entity_types: [organization, person, geo, event]
  max_gleanings: 1
...
global_search:
  completion_model_id: query_completion_model
  map_prompt: "prompts/global_search_map_system_prompt.txt"
  reduce_prompt: "prompts/global_search_reduce_system_prompt.txt"
  knowledge_prompt: "prompts/global_search_knowledge_system_prompt.txt"
```

Another option would be to avoid using a language model at all for the graph extraction, instead using the `fast` [indexing method](../index/methods.md) that uses NLP for portions of the indexing phase in lieu of LLM APIs.

## Using Custom Models

LiteLLM supports hundreds of models, but cases may still exist in which some users wish to use models not supported by LiteLLM. There are two approaches one can use to connect to unsupported models:

### Proxy APIs

Many users have used platforms such as [ollama](https://ollama.com/) and [LiteLLM Proxy Server](https://docs.litellm.ai/docs/simple_proxy) to proxy the underlying model HTTP calls to a different model provider. This seems to work reasonably well, but we frequently see issues with malformed responses (especially JSON), so if you do this please understand that your model needs to reliably return the specific response formats that GraphRAG expects. If you're having trouble with a model, you may need to try prompting to coax the format, or intercepting the response within your proxy to try and handle malformed responses.

### Model Protocol

We support model injection through the use of a standard completion and embedding Protocol and accompanying factories that you can use to register your model implementation. This is not supported with the CLI, so you'll need to use GraphRAG as a library.

- Our Protocol is [defined here](https://github.com/microsoft/graphrag/blob/main/packages/graphrag-llm/graphrag_llm/completion/completion.py)
- We have a simple mock implementation in our tests that you can [reference here](https://github.com/microsoft/graphrag/blob/main/packages/graphrag-llm/graphrag_llm/completion/mock_llm_completion.py)

Once you have a model implementation, you need to register it with our completion model factory or embedding model factory:

```python
from graphrag_llm.completion import LLMCompletion, register_completion

class MyCustomCompletionModel(LLMCompletion):
    ...
    # implementation

# elsewhere...
register_completion("my-custom-completion-model", MyCustomCompletionModel)
```

Then in your config you can reference the type name you used:

```yaml
completion_models:
  default_completion_model:
    type: my-custom-completion-model
    ...

extract_graph:
  completion_model_id: default_completion_model
  prompt: "prompts/extract_graph.txt"
  entity_types: [organization, person, geo, event]
  max_gleanings: 1
```

Note that your custom model will be passed the same params for init and method calls that we use throughout GraphRAG. There is not currently any ability to define custom parameters, so you may need to use closure scope or a factory pattern within your implementation to get custom config values.
