# 默认配置模式（使用 YAML/JSON）

默认配置模式可以通过在数据项目根目录中使用 `settings.yml` 或 `settings.json` 文件来配置。如果此配置文件旁边存在 `.env` 文件，则会加载该文件，并且其中定义的环境变量可通过 `${ENV_VAR}` 语法用于配置文档中的令牌替换。我们在 `graphrag init` 中默认使用 YML 进行初始化，但如果你更喜欢，也可以使用等效的 JSON 形式。

其中许多配置值都有默认值。与其在此重复列出，请直接参考[代码中的常量](https://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/config/defaults.py)。

例如：

```bash
# .env
GRAPHRAG_API_KEY=some_api_key

# settings.yml
default_chat_model:
  api_key: ${GRAPHRAG_API_KEY}
```

# 配置部分

## 语言模型设置

### models

这是一组 dict，一个用于补全模型配置，一个用于嵌入模型配置。dict 的键用于在其他地方需要模型实例时引用模型配置。通过这种方式，你可以根据需要指定任意多个不同的模型，并在工作流步骤中分别引用它们。

例如：

```yml
completion_models:
  default_completion_model:
    model_provider: openai
    model: gpt-4.1
    auth_method: api_key
    api_key: ${GRAPHRAG_API_KEY}

embedding_models:
  default_embedding_model:
    model_provider: openai
    model: text-embedding-3-large
    auth_method: api_key
    api_key: ${GRAPHRAG_API_KEY}
```

#### 字段

- `type` **litellm|mock** - 要使用的 LLM 提供程序类型。GraphRAG 使用 [LiteLLM](https://docs.litellm.ai/) 调用语言模型。
- `model_provider` **str** - 要使用的模型提供程序，例如 openai、azure、anthropic 等。底层使用的是 [LiteLLM](https://docs.litellm.ai/)，它支持调用 100+ 种模型。有关模型如何被调用的详细信息，请参阅 [LiteLLm 基本用法](https://docs.litellm.ai/docs/#basic-usage)（`model_provider` 是 `/` 之前的部分，而 `model` 是 `/` 之后的部分）。有关使用 LiteLLM 的更多细节和示例，请参阅[语言模型选择](models.md)。
- `model` **str** - 模型名称。
- `call_args`: **dict[str, Any]** - 随每次模型请求发送的默认参数。例如，`{"n": 5, "max_completion_tokens": 1000, "temperature": 1.5, "organization": "..." }`
- `api_key` **str|None** - 要使用的 OpenAI API 密钥。
- `api_base` **str|None** - 要使用的 API 基础 url。
- `api_version` **str|None** - API 版本。
- `auth_method` **api_key|azure_managed_identity** - 指示你希望如何对请求进行身份验证。
- `azure_deployment_name` **str|None** - 如果你的模型托管在 Azure 上，要使用的部署名称。请注意，如果你在 Azure 上的部署名称与模型名称匹配，则无需设置此项。
- retry **RetryConfig|None** - 重试设置。default=`None`，不重试。
  - type **exponential_backoff|immediate** - 重试方式类型。default=`exponential_backoff`
  - max_retries **int|None** - 最大重试次数。default=`7`。
  - base_delay **float|None** - 使用 `exponential_backoff` 时的基础延迟。default=`2.0`。
  - jitter **bool|None** - 使用 `exponential_backoff` 时，是否在重试延迟中加入抖动。default=`True`
  - max_delay **float|None** - 最大重试延迟。default=`None`，无最大值。
- rate_limit **RateLimitConfig|None** - 速率限制设置。default=`None`，不进行速率限制。
  - type **sliding_window** - 速率限制方式类型。default=`sliding_window`
  - period_in_seconds **int|None** - `sliding_window` 速率限制的窗口大小。default=`60`，即每分钟限制请求数。
  - requests_per_period **int|None** - 每个周期内的最大请求数。default=`None`
  - tokens_per_period **int|None** - 每个周期内的最大令牌数。default=`None`
- metrics **MetricsConfig|None** - 指标设置。default=`MetricsConfig()`。有关指标的更多详细信息，请参阅[指标 notebook](https://github.com/microsoft/graphrag/blob/main/packages/graphrag-llm/notebooks/04_metrics.ipynb)。
  - type **default** - 用于处理请求指标的 `MetricsProcessor` 服务类型。default=`default`
  - store **memory** - `MetricsStore` 服务类型。default=`memory`。
  - writer **log|file** - 要使用的 `MetricsWriter` 类型。将在流程结束时写出指标。default`log`，在流程结束时使用 python 标准日志记录输出指标。
  - log_level **int|None** - 使用 `log` writer 时的日志级别。default=`20`，为指标记录 `INFO` 消息。
  - base_dir **str|None** - 使用 `file` writer 时写入指标的目录。default=`Path.cwd()`。

## 输入文件与分块

### input

我们的流水线可以从输入位置摄取 .csv、.txt 或 .json 数据。有关更多详细信息和示例，请参阅[输入页面](../index/inputs.md)。

#### 字段

- `storage` **StorageConfig**
  - `type` **file|memory|blob|cosmosdb** - 要使用的存储类型。Default=`file`
  - `encoding`**str** - 文件存储使用的编码。
  - `base_dir` **str** - 写入输出工件的基础目录，相对于根目录。
  - `connection_string` **str** - （仅 blob/cosmosdb）Azure Storage 连接字符串。
  - `container_name` **str** - （仅 blob/cosmosdb）Azure Storage 容器名称。
  - `account_url` **str** - （仅 blob）要使用的存储帐户 blob URL。
  - `database_name` **str** - （仅 cosmosdb）要使用的数据库名称。
- `type` **text|csv|json** - 要加载的输入数据类型。默认为 `text`
- `encoding` **str** - 输入文件的编码。默认为 `utf-8`
- `file_pattern` **str** - 用于匹配输入文件的正则表达式。默认值根据指定的 `type` 分别为 `.*\.csv$`、`.*\.txt$` 或 `.*\.json$`，但你可以在需要时自定义它。
- `id_column` **str** - 要使用的输入 ID 列。
- `title_column` **str** - 要使用的输入标题列。
- `text_column` **str** - 要使用的输入文本列。

### chunking

这些设置配置我们如何将文档解析为文本块。这是必要的，因为非常大的文档可能无法放入单个上下文窗口中，并且图提取的准确性可能会受到影响。另请注意输入文档配置中的 `metadata` 设置，它会将文档元数据复制到每个块中。

#### 字段

- `type` **tokens|sentence** - 要使用的分块类型。
- `encoding_model` **str** - 用于按令牌边界拆分的文本编码模型。
- `size` **int** - 以令牌计的最大块大小。
- `overlap` **int** - 以令牌计的块重叠大小。
- `prepend_metadata` **list[str]** - 从源文档中提取并预置到每个块前面的元数据字段。

## 输出与存储

### output

此部分控制流水线用于导出输出表时所使用的存储机制。

#### 字段

- `type` **file|memory|blob|cosmosdb** - 要使用的存储类型。Default=`file`
- `encoding`**str** - 文件存储使用的编码。
- `base_dir` **str** - 写入输出工件的基础目录，相对于根目录。
- `connection_string` **str** - （仅 blob/cosmosdb）Azure Storage 连接字符串。
- `container_name` **str** - （仅 blob/cosmosdb）Azure Storage 容器名称。
- `account_url` **str** - （仅 blob）要使用的存储帐户 blob URL。
- `database_name` **str** - （仅 cosmosdb）要使用的数据库名称。
- `type` **text|csv|json** - 要加载的输入数据类型。默认为 `text`
- `encoding` **str** - 输入文件的编码。默认为 `utf-8`

### update_output_storage

此部分定义了一个用于运行增量索引的辅助存储位置，以保留你的原始输出。

#### 字段

- `type` **file|memory|blob|cosmosdb** - 要使用的存储类型。Default=`file`
- `encoding`**str** - 文件存储使用的编码。
- `base_dir` **str** - 写入输出工件的基础目录，相对于根目录。
- `connection_string` **str** - （仅 blob/cosmosdb）Azure Storage 连接字符串。
- `container_name` **str** - （仅 blob/cosmosdb）Azure Storage 容器名称。
- `account_url` **str** - （仅 blob）要使用的存储帐户 blob URL。
- `database_name` **str** - （仅 cosmosdb）要使用的数据库名称。
- `type` **text|csv|json** - 要加载的输入数据类型。默认为 `text`
- `encoding` **str** - 输入文件的编码。默认为 `utf-8`

### cache

此部分控制流水线使用的缓存机制。它用于缓存 LLM 调用结果，以便在重新运行索引过程时获得更快的性能。

#### 字段

- `type` **json|memory|none** - 要使用的存储类型。Default=`json`
- `storage` **StorageConfig**
  - `type` **file|memory|blob|cosmosdb** - 要使用的存储类型。Default=`file`
  - `encoding`**str** - 文件存储使用的编码。
  - `base_dir` **str** - 写入输出工件的基础目录，相对于根目录。
  - `connection_string` **str** - （仅 blob/cosmosdb）Azure Storage 连接字符串。
  - `container_name` **str** - （仅 blob/cosmosdb）Azure Storage 容器名称。
  - `account_url` **str** - （仅 blob）要使用的存储帐户 blob URL。
  - `database_name` **str** - （仅 cosmosdb）要使用的数据库名称。

### reporting

此部分控制流水线使用的报告机制，用于记录常见事件和错误消息。默认情况下，报告会写入输出目录中的文件。不过，你也可以选择将报告写入 Azure Blob Storage 容器。

#### 字段

- `type` **file|blob** - 要使用的报告类型。Default=`file`
- `base_dir` **str** - 写入报告的基础目录，相对于根目录。
- `connection_string` **str** - （仅 blob）Azure Storage 连接字符串。
- `container_name` **str** - （仅 blob）Azure Storage 容器名称。
- `account_url` **str** - 要使用的存储帐户 blob URL。

### vector_store

系统中所有向量的存放位置。默认配置为 lancedb。这是一个 dict，其中的键用于标识各个存储参数（例如，用于文本嵌入）。

#### 字段

- `type` **lancedb|azure_ai_search|cosmosdb** - 向量存储类型。Default=`lancedb`
- `db_uri` **str** (lancedb only) - 数据库 uri。Default=`storage.base_dir/lancedb`
- `url` **str** (blob/cosmosdb only) - 要使用的数据库 / AI Search。
- `api_key` **str** (optional - AI Search only) - 要使用的 AI Search api 密钥。
- `audience` **str** (AI Search only) - 如果使用托管身份验证，则为托管身份令牌的受众。
- `connection_string` **str** - （仅 cosmosdb）Azure Storage 连接字符串。
- `database_name` **str** - （仅 cosmosdb）数据库名称。

- `index_schema` **dict[str, dict[str, str]]** (optional) - 允许你为每种嵌入进行自定义。
  - `<supported_embedding>`:
    - `index_name` **str**: (optional) - 特定嵌入索引表的名称。
    - `id_field` **str**: (optional) - 用作 id 的字段名。Default=`id`
    - `vector_field` **str**: (optional) - 用作向量的字段名。Default=`vector`
    - `vector_size` **int**: (optional) - 嵌入的向量大小。Default=`3072`

支持的嵌入有：

- `text_unit_text`
- `entity_description`
- `community_full_content`

例如：

```yaml
vector_store:
  type: lancedb
  db_uri: output/lancedb
  index_schema:
    text_unit_text:
      index_name: "text-unit-embeddings"
      id_field: "id_custom"
      vector_field: "vector_custom"
      vector_size: 3072
    entity_description:
      id_field: "id_custom"
```

## 工作流配置

这些设置控制每个单独的工作流在执行时的行为。

### workflows

**list[str]** - 这是一个按顺序运行的工作流名称列表。GraphRAG 提供了用于配置此项的内置流水线，但你也可以通过在此指定列表来精确运行你想要且仅想要的内容。如果你已经自行完成了部分处理，这会很有用。

### embed_text

默认情况下，GraphRAG 索引器只会导出查询方法所需的嵌入。不过，模型为所有纯文本字段都定义了嵌入，并且可以通过设置 `target` 和 `names` 字段进行自定义。

支持的嵌入名称有：

- `text_unit_text`
- `entity_description`
- `community_full_content`

#### 字段

- `embedding_model_id` **str** - 用于文本嵌入的模型定义名称。
- `model_instance_name` **str** - 模型单例实例的名称。默认值为 "text_embedding"。这主要影响缓存存储分区。
- `batch_size` **int** - 要使用的最大批大小。
- `batch_max_tokens` **int** - 每批的最大令牌数。
- `names` **list[str]** - 要运行的嵌入名称列表（必须在支持列表中）。

### extract_graph

调整基于语言模型的图提取过程。

#### 字段

- `completion_model_id` **str** - 用于 API 调用的模型定义名称。
- `model_instance_name` **str** - 模型单例实例的名称。默认值为 "extract_graph"。这主要影响缓存存储分区。
- `prompt` **str** - 要使用的提示文件。
- `entity_types` **list[str]** - 要识别的实体类型。
- `max_gleanings` **int** - 要使用的最大提炼循环次数。

### summarize_descriptions

#### 字段

- `completion_model_id` **str** - 用于 API 调用的模型定义名称。
- `model_instance_name` **str** - 模型单例实例的名称。默认值为 "summarize_descriptions"。这主要影响缓存存储分区。
- `prompt` **str** - 要使用的提示文件。
- `max_length` **int** - 每次摘要输出的最大令牌数。
- `max_input_length` **int** - 用于摘要的最大收集令牌数（这将限制你为给定实体或关系发送进行摘要的描述数量）。

### extract_graph_nlp

定义基于 NLP 的图提取方法设置。

#### 字段

- `normalize_edge_weights` **bool** - 是否在图构建期间对边权重进行归一化。Default=`True`。
- `concurrent_requests` **int** - 提取过程中使用的线程数。
- `async_mode` **asyncio|threaded** - 要使用的异步模式。可以是 `asyncio` 或 `threaded`。
- `text_analyzer` **dict** - NLP 模型的参数。
  - `extractor_type` **regex_english|syntactic_parser|cfg** - Default=`regex_english`。
  - `model_name` **str** - NLP 模型名称（用于基于 SpaCy 的模型）
  - `max_word_length` **int** - 允许的最长单词长度。Default=`15`。
  - `word_delimiter` **str** - 用于拆分单词的分隔符。默认值为 `' '`。
  - `include_named_entities` **bool** - 是否在名词短语中包含命名实体。Default=`True`。
  - `exclude_nouns` **list[str] | None** - 要排除的名词列表。如果为 `None`，我们将使用内部停用词列表。
  - `exclude_entity_tags` **list[str]** - 要忽略的实体标签列表。
  - `exclude_pos_tags` **list[str]** - 要忽略的词性标签列表。
  - `noun_phrase_tags` **list[str]** - 要忽略的名词短语标签列表。
  - `noun_phrase_grammars` **dict[str, str]** - 该模型的名词短语语法（仅 cfg）。

### prune_graph

手动图修剪的参数。这可用于通过移除连接过多或过于罕见的节点来优化图聚类的模块度。

#### 字段

- `min_node_freq` **int** - 允许的最小节点频率。
- `max_node_freq_std` **float | None** - 允许的最大节点频率标准差。
- `min_node_degree` **int** - 允许的最小节点度。
- `max_node_degree_std` **float | None** - 允许的最大节点度标准差。
- `min_edge_weight_pct` **float** - 允许的最小边权重百分位数。
- `remove_ego_nodes` **bool** - 移除自我中心节点。
- `lcc_only` **bool** - 仅使用最大连通分量。

### cluster_graph

这些设置用于对图执行 Leiden 分层聚类以创建社区。

#### 字段

- `max_cluster_size` **int** - 要导出的最大聚类大小。
- `use_lcc` **bool** - 是否仅使用最大连通分量。
- `seed` **int** - 如果希望每次运行结果一致，则提供一个随机种子。我们确实提供了一个默认值，以保证聚类稳定性。

### extract_claims

#### 字段

- `enabled` **bool** - 是否启用声明提取。默认关闭，因为声明提示确实需要用户进行调优。
- `completion_model_id` **str** - 用于 API 调用的模型定义名称。
- `model_instance_name` **str** - 模型单例实例的名称。默认值为 "extract_claims"。这主要影响缓存存储分区。
- `prompt` **str** - 要使用的提示文件。
- `description` **str** - 描述我们想要提取的声明类型。
- `max_gleanings` **int** - 要使用的最大提炼循环次数。

### community_reports

#### 字段

- `completion_model_id` **str** - 用于 API 调用的模型定义名称。
- `model_instance_name` **str** - 模型单例实例的名称。默认值为 "community_reporting"。这主要影响缓存存储分区。
- `graph_prompt` **str | None** - 用于基于图的摘要的社区报告提取提示。
- `text_prompt` **str | None** - 用于基于文本的摘要的社区报告提取提示。
- `max_length` **int** - 每份报告的最大输出令牌数。
- `max_input_length` **int** - 生成报告时可使用的最大输入令牌数。

### snapshots

#### 字段

- `embeddings` **bool** - 将嵌入快照导出为 parquet。
- `graphml` **bool** - 将图快照导出为 GraphML。
- `raw_graph` **bool** - 在合并前导出原始提取图。

## 查询

### local_search

#### 字段

- `prompt` **str** - 要使用的提示文件。
- `completion_model_id` **str** - 用于 Chat Completion 调用的模型定义名称。
- `embedding_model_id` **str** - 用于 Embedding 调用的模型定义名称。
- `text_unit_prop` **float** - 文本单元比例。
- `community_prop` **float** - 社区比例。
- `conversation_history_max_turns` **int** - 对话历史的最大轮数。
- `top_k_entities` **int** - 映射到的前 k 个实体。
- `top_k_relationships` **int** - 映射到的前 k 个关系。
- `max_context_tokens` **int** - 构建请求上下文时可使用的最大令牌数。

### global_search

#### 字段

- `map_prompt` **str** - 要使用的全局搜索 mapper 提示。
- `reduce_prompt` **str** - 要使用的全局搜索 reducer。
- `completion_model_id` **str** - 用于 Chat Completion 调用的模型定义名称。
- `knowledge_prompt` **str** - 要使用的知识提示文件。
- `data_max_tokens` **int** - 用于根据 reduce 响应构建最终响应时可使用的最大令牌数。
- `map_max_length` **int** - map 响应请求的最大长度，以单词计。
- `reduce_max_length` **int** - reduce 响应请求的最大长度，以单词计。
- `dynamic_search_threshold` **int** - 包含社区报告的评分阈值。
- `dynamic_search_keep_parent` **bool** - 如果任一子社区相关，则保留父社区。
- `dynamic_search_num_repeats` **int** - 对同一社区报告进行评分的次数。
- `dynamic_search_use_summary` **bool** - 使用社区摘要而不是 full_context。
- `dynamic_search_max_level` **int** - 如果已处理的社区都不相关，则要考虑的社区层级最大级别。

### drift_search

#### 字段

- `prompt` **str** - 要使用的提示文件。
- `reduce_prompt` **str** - 要使用的 reducer 提示文件。
- `completion_model_id` **str** - 用于 Chat Completion 调用的模型定义名称。
- `embedding_model_id` **str** - 用于 Embedding 调用的模型定义名称。
- `data_max_tokens` **int** - 数据 llm 的最大令牌数。
- `reduce_max_tokens` **int** - reduce 阶段的最大令牌数。仅在非 o-series 模型中使用。
- `reduce_temperature` **float** - 在 reduce 中用于令牌生成的 temperature。
- `reduce_max_completion_tokens` **int** - reduce 阶段的最大令牌数。仅用于 o-series 模型。
- `concurrency` **int** - 并发请求数。
- `drift_k_followups` **int** - 要检索的顶级全局结果数量。
- `primer_folds` **int** - 搜索预热的折数。
- `primer_llm_max_tokens` **int** - primer 中 LLM 的最大令牌数。
- `n_depth` **int** - 要执行的 drift search 步数。
- `local_search_text_unit_prop` **float** - 分配给文本单元的搜索比例。
- `local_search_community_prop` **float** - 分配给社区属性的搜索比例。
- `local_search_top_k_mapped_entities` **int** - 本地搜索期间要映射的前 K 个实体数量。
- `local_search_top_k_relationships` **int** - 本地搜索期间要映射的前 K 个关系数量。
- `local_search_max_data_tokens` **int** - 本地搜索的最大上下文大小（以令牌计）。
- `local_search_temperature` **float** - 本地搜索中用于令牌生成的 temperature。
- `local_search_top_p` **float** - 本地搜索中用于令牌生成的 top-p 值。
- `local_search_n` **int** - 本地搜索中要生成的补全数量。
- `local_search_llm_max_gen_tokens` **int** - 本地搜索中 LLM 的最大生成令牌数。仅在非 o-series 模型中使用。
- `local_search_llm_max_gen_completion_tokens` **int** - 本地搜索中 LLM 的最大生成令牌数。仅用于 o-series 模型。

### basic_search

#### 字段

- `prompt` **str** - 要使用的提示文件。
- `completion_model_id` **str** - 用于 Chat Completion 调用的模型定义名称。
- `embedding_model_id` **str** - 用于 Embedding 调用的模型定义名称。
- `k` **int** - 为构建上下文而从向量存储中检索的文本单元数量。
- `max_context_tokens` **int** - 要创建的最大上下文大小，以令牌计。