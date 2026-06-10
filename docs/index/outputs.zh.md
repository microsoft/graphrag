# 输出

默认管道会生成一系列与[概念知识模型](../index/default_dataflow.md)一致的输出表。此页面描述了详细的输出表 schema。默认情况下，我们将这些表作为磁盘上的 parquet 文件写出。

## 共享字段
所有表都有两个标识符字段：

| name              | type | description |
| ----------------- | ---- | ----------- |
| id                | str  | 生成的 UUID，确保全局唯一性 |
| human_readable_id | int  | 这是每次运行创建的递增短 ID。例如，我们在打印引用的生成摘要中使用此短 ID，以便于直观地进行交叉引用。 |

## communities
这是由 Leiden 生成的最终社区列表。社区具有严格的层级结构，随着聚类亲和性范围缩小，会进一步细分为子社区。

| name               | type  | description |
| ------------------ | ----- | ----------- |
| community          | int   | 社区的 Leiden 生成聚类 ID。请注意，这些 ID 会随深度递增，因此在社区层级结构的所有层级中都是唯一的。对于此表，human_readable_id 是社区 ID 的副本，而不是普通的递增值。 |
| parent             | int   | 父社区 ID。|
| children           | int[] | 子社区 ID 列表。|
| level              | int   | 社区在层级结构中的深度。 |
| title              | str   | 社区的易读名称。 |
| entity_ids         | str[] | 属于该社区成员的实体列表。 |
| relationship_ids   | str[] | 完全位于该社区内的关系列表（source 和 target 均在该社区中）。 |
| text_unit_ids      | str[] | 该社区中表示的文本单元列表。 |
| period             | str   | 摄取日期，用于增量更新合并。ISO8601 |
| size               | int   | 社区大小（实体计数），用于增量更新合并。 |

## community_reports
这是每个社区的摘要报告列表。

| name                 | type  | description |
| -------------------- | ----- | ----------- |
| community            | int   | 此报告适用的社区短 ID。 |
| parent               | int   | 父社区 ID。 |
| children             | int[] | 子社区 ID 列表。|
| level                | int   | 此报告适用的社区层级。 |
| title                | str   | LM 生成的报告标题。 |
| summary              | str   | LM 生成的报告摘要。 |
| full_content         | str   | LM 生成的完整报告。 |
| rank                 | float | LM 根据成员实体显著性得出的报告相关性排序
| rating_explanation   | str   | LM 对该排序的解释。 |
| findings             | dict  | LM 得出的社区前 5-10 条洞察列表。包含 `summary` 和 `explanation` 值。 |
| full_content_json    | json  | LM 返回的完整 JSON 输出。大多数字段会被提取到列中，但此 JSON 会用于查询摘要，因此我们保留它，以便最终用户通过提示调优添加字段/内容。 |
| period               | str   | 摄取日期，用于增量更新合并。ISO8601 |
| size                 | int   | 社区大小（实体计数），用于增量更新合并。 |

## covariates
（可选）如果启用了 claim 提取，这里是提取出的协变量列表。请注意，claims 通常侧重于识别欺诈等恶意行为，因此并不适用于所有数据集。

| name           | type | description |
| -------------- | ---- | ----------- |
| covariate_type | str  | 在默认协变量中，这里始终为 "claim"。 |
| type           | str  | claim 类型的性质。 |
| description    | str  | LM 生成的行为描述。 |
| subject_id     | str  | 源实体的名称（即执行所声称行为的实体）。 |
| object_id      | str  | 目标实体的名称（即所声称行为作用的对象）。 |
| status         | str  | LM 对 claim 正确性的评估。[TRUE, FALSE, SUSPECTED] 之一 |
| start_date     | str  | LM 得出的所声称活动开始时间。ISO8601 |
| end_date       | str  | LM 得出的所声称活动结束时间。ISO8601 |
| source_text    | str  | 包含所声称行为的简短文本字符串。 |
| text_unit_id   | str  | 提取 claim 文本的文本单元 ID。 |

## documents
导入后的文档内容列表。

| name          | type  | description |
| ------------- | ----- | ----------- |
| title         | str   | 文件名，除非在 CSV 导入期间另有配置。 |
| text          | str   | 文档的全文。 |
| text_unit_ids | str[] | 从文档中解析出的文本单元（chunks）列表。 |
| metadata      | dict  | 如果在 CSV 导入期间指定，这里是文档元数据的 dict。 |

## entities
LM 在数据中发现的所有实体列表。

| name          | type  | description |
| ------------- | ----- | ----------- |
| title         | str   | 实体名称。 |
| type          | str   | 实体类型。默认情况下，除非进行了不同配置或使用自动调优，否则会是 "organization"、"person"、"geo" 或 "event"。 |
| description   | str   | 实体的文本描述。实体可能出现在许多文本单元中，因此这是 LM 对所有描述生成的摘要。 |
| text_unit_ids | str[] | 包含该实体的文本单元列表。 |
| frequency     | int   | 找到该实体的文本单元计数。 |
| degree        | int   | 图中的节点度（连接度）。 |

## relationships
LM 在数据中发现的所有实体到实体关系列表。这也是图的 _edge list_。

| name            | type  | description |
| --------------- | ----- | ----------- |
| source          | str   | 源实体名称。 |
| target          | str   | 目标实体名称。 |
| description     | str   | LM 生成的关系描述。另请参见实体描述的说明。 |
| weight          | float | 图中边的权重。这是对每个关系实例的 LM 生成“强度”度量求和得到的。 |
| combined_degree | int   | 源节点和目标节点度数之和。 |
| text_unit_ids   | str[] | 找到该关系的文本单元列表。 |

## text_units
从输入文档解析出的所有文本块列表。

| name              | type  | description |
| ----------------- | ----- | ----------- |
| text              | str   | 该块的原始全文。 |
| n_tokens          | int   | 该块中的 token 数量。通常这应与 `chunk_size` 配置参数匹配，最后一个块通常更短，属于例外情况。 |
| document_id       | str   | 该块来源文档的 ID。 |
| entity_ids        | str[] | 在该文本单元中找到的实体列表。 |
| relationships_ids | str[] | 在该文本单元中找到的关系列表。 |
| covariate_ids     | str[] | 在该文本单元中找到的可选协变量列表。 |