# Language Model Selection and Overriding

This page contains information on selecting a model to use and options to supply your own model for GraphRAG. Note that this is not a guide to finding the right model for your use case.

## Default Model Support

GraphRAG was built and tested using OpenAI models, so this is the default model set we support. This is not intended to be a limiter or statement of quality or fitness for your use case, only that it's the set we are most familiar with for prompting, tuning, and debugging.

GraphRAG also utilizes a language model wrapper library used by several projects within our team, called fnllm. fnllm provides two important functions for GraphRAG: rate limiting configuration to help us maximize throughput for large indexing jobs, and robust caching of API calls to minimize consumption on repeated indexes for testing, experimentation, or incremental ingest. fnllm uses the OpenAI Python SDK under the covers, so OpenAI-compliant endpoints are a base requirement out-of-the-box.

## Model Selection Considerations

GraphRAG has been most thoroughly tested with the gpt-4 series of models from OpenAI, including gpt-4 gpt-4-turbo, gpt-4o, and gpt-4o-mini. Our [arXiv paper](https://arxiv.org/abs/2404.16130), for example, performed quality evaluation using gpt-4-turbo.

Versions of GraphRAG before 2.2.0 made extensive use of `max_tokens` and `logit_bias` to control generated response length or content. The introduction of the o-series of models added new, non-compatible parameters because these models include a reasoning component that has different consumption patterns and response generation attributes than non-reasoning models. GraphRAG 2.2.0 now supports these models, but there are important differences that need to be understood before you switch.

- Previously, GraphRAG used `max_tokens` to limit responses in a few locations. This is done so that we can have predictable content sizes when building downstream context windows for summarization. We have now switched from using `max_tokens` to use a prompted approach, which is working well in our tests. We suggest using `max_tokens` in your language model config only for budgetary reasons if you want to limit consumption, and not for expected response length control. We now also support the o-series equivalent `max_completion_tokens`, but if you use this keep in mind that there may be some unknown fixed reasoning consumption amount in addition to the response tokens, so it is not a good technique for response control.
- Previously, GraphRAG used a combination of `max_tokens` and `logit_bias` to strictly control a binary yes/no question during gleanings. This is not possible with reasoning models, so again we have switched to a prompted approach. Our tests with gpt-4o, gpt-4o-mini, and o1 show that this works consistently, but could have issues if you have an older or smaller model.
- The o-series models are much slower and more expensive. It may be useful to use an asymmetric approach to model use in your config: you can define as many models as you like in the `models` block of your settings.yaml and reference them by key for every workflow that requires a language model. You could use gpt-4o for indexing and o1 for query, for example. Experiment to find the right balance of cost, speed, and quality for your use case.
- The o-series models contain a form of native native chain-of-thought reasoning that is absent in the non-o-series models. GraphRAG's prompts sometimes contain CoT because it was an effective technique with the gpt-4* series. It may be counterproductive with the o-series, so you may want to tune or even re-write large portions of the prompt templates (particularly for graph and claim extraction).

Example config with asymmetric model use:

```yaml
models:
  extraction_chat_model:
    api_key: ${GRAPHRAG_API_KEY}
    type: openai_chat
    auth_type: api_key
    model: gpt-4o
    model_supports_json: true
  query_chat_model:
    api_key: ${GRAPHRAG_API_KEY}
    type: openai_chat
    auth_type: api_key
    model: o1
    model_supports_json: true

...

extract_graph:
  model_id: extraction_chat_model
  prompt: "prompts/extract_graph.txt"
  entity_types: [organization,person,geo,event]
  max_gleanings: 1

...


global_search:
  chat_model_id: query_chat_model
  map_prompt: "prompts/global_search_map_system_prompt.txt"
  reduce_prompt: "prompts/global_search_reduce_system_prompt.txt"
  knowledge_prompt: "prompts/global_search_knowledge_system_prompt.txt"
```

Another option would be to avoid using a language model at all for the graph extraction, instead using the `fast` [indexing method](../index/methods.md) that uses NLP for portions of the indexing phase in lieu of LLM APIs.

## Using Non-OpenAI Models

As noted above, our primary experience and focus has been on OpenAI models, so this is what is supported out-of-the-box. Many users have requested support for additional model types, but it's out of the scope of our research to handle the many models available today. There are two approaches you can use to connect to a non-OpenAI model:

### Proxy APIs

Many users have used platforms such as [ollama](https://ollama.com/) to proxy the underlying model HTTP calls to a different model provider. This seems to work reasonably well, but we frequently see issues with malformed responses (especially JSON), so if you do this please understand that your model needs to reliably return the specific response formats that GraphRAG expects. If you're having trouble with a model, you may need to try prompting to coax the format, or intercepting the response within your proxy to try and handle malformed responses.

### Model Protocol

As of GraphRAG 2.0.0, we support model injection through the use of a standard chat and embedding Protocol and an accompanying ModelFactory that you can use to register your model implementation. This is not supported with the CLI, so you'll need to use GraphRAG as a library.

- Our Protocol is [defined here](https://github.com/microsoft/graphrag/blob/main/graphrag/language_model/protocol/base.py)
- Our base implementation, which wraps fnllm, [is here](https://github.com/microsoft/graphrag/blob/main/graphrag/language_model/providers/fnllm/models.py)
- We have a simple mock implementation in our tests that you can [reference here](https://github.com/microsoft/graphrag/blob/main/tests/mock_provider.py)

Once you have a model implementation, you need to register it with our ModelFactory:

```python
class MyCustomModel:
    ...
    # implementation

# elsewhere...
ModelFactory.register_chat("my-custom-chat-model", lambda **kwargs: MyCustomModel(**kwargs))
```

Then in your config you can reference the type name you used:

```yaml
models:
  default_chat_model:
    type: my-custom-chat-model


extract_graph:
  model_id: default_chat_model
  prompt: "prompts/extract_graph.txt"
  entity_types: [organization,person,geo,event]
  max_gleanings: 1
```

Note that your custom model will be passed the same params for init and method calls that we use throughout GraphRAG. There is not currently any ability to define custom parameters, so you may need to use closure scope or a factory pattern within your implementation to get custom config values.