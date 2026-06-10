# 语言模型选择与覆盖

本页包含有关选择要使用的模型以及为 GraphRAG 提供自有模型选项的信息。请注意，这不是关于为你的使用场景寻找合适模型的指南。

## 默认模型支持

GraphRAG 使用 OpenAI 模型构建并测试，因此这是我们默认支持的模型集。这并不是有意限制，也不是对其质量或是否适合你的使用场景的评价，只是因为这是我们在提示、调优和调试方面最熟悉的一组模型。

GraphRAG 使用 [LiteLLM](https://docs.litellm.ai/) 调用语言模型。LiteLLM 提供对 100+ 模型的支持，但需要注意的是，在选择模型时，它必须支持返回遵循 [JSON schema](https://docs.litellm.ai/docs/completion/json_mode) 的[结构化输出](https://openai.com/index/introducing-structured-outputs-in-the-api/)。

使用 LiteLLM 作为 GraphRAG 的语言模型管理器的示例：

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

有关配置的更多详细信息，请参阅 [详细配置](yaml.md)。有关如何调用模型的详细信息，请参阅 [LiteLLM 基本用法](https://docs.litellm.ai/docs/#basic-usage)（`model_provider` 是 `/` 之前的部分，而 `model` 是 `/` 之后的部分）。

## 模型选择注意事项

GraphRAG 已经使用 OpenAI 的 gpt-4 系列模型进行了最充分的测试，包括 gpt-4、gpt-4-turbo、gpt-4o 和 gpt-4o-mini。例如，我们的 [arXiv 论文](https://arxiv.org/abs/2404.16130) 使用 gpt-4-turbo 进行了质量评估。如上所述，非 OpenAI 模型可通过 LiteLLM 获得支持，但 OpenAI 的 gpt-4 系列模型仍然是 GraphRAG 中测试最充分、支持最完善的一组模型——换句话说，这些是我们最了解、也最能帮助解决相关问题的模型。

2.2.0 之前的 GraphRAG 版本大量使用 `max_tokens` 和 `logit_bias` 来控制生成响应的长度或内容。o 系列模型的引入带来了新的、不兼容的参数，因为这些模型包含推理组件，其消耗模式和响应生成特性与非推理模型不同。GraphRAG 2.2.0 现在支持这些模型，但在切换之前，需要先理解一些重要差异。

- 以前，GraphRAG 在少数位置使用 `max_tokens` 来限制响应。这是为了在构建下游摘要的上下文窗口时，让内容大小具有可预测性。现在我们已经从使用 `max_tokens` 切换为使用基于提示的方法，并且在测试中效果良好。我们建议仅出于预算原因在你的语言模型配置中使用 `max_tokens`，如果你想限制消耗，而不是用于控制预期响应长度。我们现在也支持 o 系列对应的 `max_completion_tokens`，但如果你使用它，请记住，除了响应 token 之外，可能还存在一些未知的固定推理消耗，因此这并不是控制响应的好技术。
- 以前，GraphRAG 在 gleanings 期间使用 `max_tokens` 和 `logit_bias` 的组合来严格控制一个二元的 yes/no 问题。这在推理模型中不可行，因此我们再次切换到了基于提示的方法。我们对 gpt-4o、gpt-4o-mini 和 o1 的测试表明这种方法运行稳定，但如果你使用的是较旧或较小的模型，可能会出现问题。
- o 系列模型更慢且成本更高。在配置中采用非对称的模型使用方式可能会很有帮助：你可以在 `settings.yaml` 的 `models` 块中定义任意数量的模型，并通过键为每个需要语言模型的工作流引用它们。例如，你可以在索引时使用 gpt-4o，在查询时使用 o1。请通过实验找到适合你使用场景的成本、速度和质量平衡点。
- o 系列模型包含一种原生的 chain-of-thought 推理形式，而非 o 系列模型中没有。GraphRAG 的提示有时包含 CoT，因为这在 gpt-4\* 系列中是一种有效技术。对于 o 系列，这可能适得其反，因此你可能需要调整，甚至重写大部分提示模板（尤其是用于图谱和声明提取的部分）。

使用非对称模型的示例配置：

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

另一种选择是在图谱提取中完全不使用语言模型，而是使用 `fast` [索引方法](../index/methods.md)，该方法在索引阶段的部分环节中使用 NLP 来替代 LLM API。

## 使用自定义模型

LiteLLM 支持数百种模型，但在某些情况下，一些用户仍可能希望使用 LiteLLM 不支持的模型。可使用两种方法连接到不受支持的模型：

### 代理 API

许多用户使用诸如 [ollama](https://ollama.com/) 和 [LiteLLM Proxy Server](https://docs.litellm.ai/docs/simple_proxy) 之类的平台，将底层模型 HTTP 调用代理到其他模型提供商。这看起来运行得相当不错，但我们经常看到格式错误的响应问题（尤其是 JSON），因此如果你这样做，请理解你的模型需要能够可靠地返回 GraphRAG 所期望的特定响应格式。如果你在使用某个模型时遇到问题，可能需要尝试通过提示来引导其输出格式，或者在代理内部拦截响应，以尝试处理格式错误的响应。

### 模型协议

我们支持通过标准 completion 和 embedding Protocol 及其配套工厂来注入模型，你可以使用它们注册你的模型实现。这在 CLI 中不受支持，因此你需要将 GraphRAG 作为库来使用。

- 我们的 Protocol [定义在这里](https://github.com/microsoft/graphrag/blob/main/packages/graphrag-llm/graphrag_llm/completion/completion.py)
- 我们在测试中有一个简单的 mock 实现，你可以[在这里参考](https://github.com/microsoft/graphrag/blob/main/packages/graphrag-llm/graphrag_llm/completion/mock_llm_completion.py)

一旦你有了模型实现，就需要将其注册到我们的 completion model factory 或 embedding model factory 中：

```python
from graphrag_llm.completion import LLMCompletion, register_completion

class MyCustomCompletionModel(LLMCompletion):
    ...
    # implementation

# elsewhere...
register_completion("my-custom-completion-model", MyCustomCompletionModel)
```

然后你可以在配置中引用你使用的类型名称：

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

请注意，你的自定义模型将在初始化和方法调用时接收与我们在整个 GraphRAG 中使用的相同参数。目前还无法定义自定义参数，因此你可能需要在你的实现中使用闭包作用域或工厂模式来获取自定义配置值。