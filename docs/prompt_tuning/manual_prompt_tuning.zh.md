# 手动提示调优 ⚙️

GraphRAG 索引器默认会使用一组提示，这些提示旨在知识发现这一广泛场景中良好运行。
不过，针对你的特定用例对提示进行调优是很常见的需求。
我们提供了一种实现方式：允许你指定自定义提示文件，每个文件都会在内部使用一系列 token 替换。

这些提示中的每一个都可以通过编写纯文本的自定义提示文件来覆盖。我们使用 `{token_name}` 形式的 token 替换，可用 token 的说明如下所示。

## 索引提示

### 实体/关系提取

[提示来源](http://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/prompts/index/extract_graph.py)

#### Tokens

- **{input_text}** - 要处理的输入文本。
- **{entity_types}** - 实体类型列表
- **{tuple_delimiter}** - 用于分隔元组内值的分隔符。单个元组用于表示单个实体或关系。
- **{record_delimiter}** - 用于分隔元组实例的分隔符。
- **{completion_delimiter}** - 指示生成完成的标记。

### 汇总实体/关系描述

[提示来源](http://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/prompts/index/summarize_descriptions.py)

#### Tokens

- **{entity_name}** - 实体名称，或关系的源/目标对。
- **{description_list}** - 实体或关系的描述列表。

### 声明提取

[提示来源](http://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/prompts/index/extract_claims.py)

#### Tokens

- **{input_text}** - 要处理的输入文本。
- **{tuple_delimiter}** - 用于分隔元组内值的分隔符。单个元组用于表示单个实体或关系。
- **{record_delimiter}** - 用于分隔元组实例的分隔符。
- **{completion_delimiter}** - 指示生成完成的标记。
- **{entity_specs}** - 实体类型列表。
- **{claim_description}** - 声明应具备何种形式的描述。默认值为：`"Any claims or facts that could be relevant to information discovery."`

有关如何更改此项的详细信息，请参阅[配置文档](../config/overview.md)。

### 生成社区报告

[提示来源](http://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/prompts/index/community_report.py)

#### Tokens

- **{input_text}** - 用于生成报告的输入文本。其中将包含实体和关系表。

## 查询提示

### 本地搜索

[提示来源](http://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/prompts/query/local_search_system_prompt.py)

#### Tokens

- **{response_type}** - 描述响应应呈现的形式。我们默认使用“multiple paragraphs”。
- **{context_data}** - 来自 GraphRAG 索引的数据表。

### 全局搜索

[映射器提示来源](http://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/prompts/query/global_search_map_system_prompt.py)

[归约器提示来源](http://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/prompts/query/global_search_reduce_system_prompt.py)

[知识提示来源](http://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/prompts/query/global_search_knowledge_system_prompt.py)

全局搜索使用 map/reduce 方法进行摘要。你可以分别独立调优这些提示。此搜索还包括调整模型训练中通用知识使用方式的能力。

#### Tokens

- **{response_type}** - 描述响应应呈现的形式（仅 reducer）。我们默认使用“multiple paragraphs”。
- **{context_data}** - 来自 GraphRAG 索引的数据表。

### 漂移搜索

[提示来源](http://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/prompts/query/drift_search_system_prompt.py)

#### Tokens

- **{response_type}** - 描述响应应呈现的形式。我们默认使用“multiple paragraphs”。
- **{context_data}** - 来自 GraphRAG 索引的数据表。
- **{community_reports}** - 要包含在摘要中的最相关社区报告。
- **{query}** - 作为注入到上下文中的查询文本。