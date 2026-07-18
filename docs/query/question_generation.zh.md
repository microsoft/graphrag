# 问题生成 ❔

## 基于实体的问题生成

[问题生成](https://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/query/question_gen/)方法将知识图谱中的结构化数据与输入文档中的非结构化数据结合起来，以生成与特定实体相关的候选问题。

## 方法论
给定一个先前用户问题列表，问题生成方法使用与[本地搜索](local_search.md)中相同的上下文构建方法来提取并优先处理相关的结构化和非结构化数据，包括实体、关系、协变量、社区报告和原始文本块。然后，这些数据记录会被整合到单个 LLM 提示中，以生成候选后续问题，这些问题代表了数据中最重要或最紧急的信息内容或主题。

## 配置

下面是[Question Generation class](https://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/query/question_gen/local_gen.py)的关键参数：

* `model`: 用于生成响应的语言模型聊天补全对象
* `context_builder`: 用于从知识模型对象集合准备上下文数据的[上下文构建器](https://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/query/structured_search/local_search/mixed_context.py)对象，使用与本地搜索中相同的上下文构建器类
* `system_prompt`: 用于生成候选问题的提示模板。默认模板可在[system_prompt](https://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/prompts/query/question_gen_system_prompt.py)中找到
* `llm_params`: 传递给 LLM 调用的附加参数字典（例如 `temperature`、`max_tokens`）
* `context_builder_params`: 在为问题生成提示构建上下文时，传递给[`context_builder`](https://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/query/structured_search/local_search/mixed_context.py)对象的附加参数字典
* `callbacks`: 可选的回调函数，可用于为 LLM 的补全流事件提供自定义事件处理器

## 使用方法

可在以下[notebook](../examples_notebooks/local_search.ipynb)中找到问题生成功能的示例。