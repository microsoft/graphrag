# 自带图谱

一些用户曾询问，他们是否可以自带现有图谱，并使用 GraphRAG 对其进行摘要以供查询。实现这一点有很多种可能的方法，但这里我们将描述一种简单的方法，它能够相当容易地与现有的 GraphRAG 工作流对齐。

为了覆盖 GraphRAG 查询的基本用例，你应该拥有两个或三个从你的数据派生出的表：

- entities.parquet - 这是在数据集中发现的实体列表，即图的节点。
- relationships.parquet - 这是在数据集中发现的关系列表，即图的边。
- text_units.parquet - 这是提取图谱时所依据的源文本块。根据你打算使用的查询方法，这一项是可选的（后文会说明）。

这里描述的方法是运行一个自定义的 GraphRAG 工作流管道，该管道假定文本分块、实体提取和关系提取已经完成。

## 表

### 实体

请参阅完整的实体[表结构](./outputs.md#entities)。出于图摘要的目的，你只需要 id、title、description 以及 text_unit_ids 列表。

### 关系

请参阅完整的关系[表结构](./outputs.md#relationships)。出于图摘要的目的，你只需要 id、source、target、description、weight 以及 text_unit_ids 列表。

> 注意：`weight` 字段很重要，因为它用于正确计算 Leiden 社区！

## 工作流配置

GraphRAG 支持仅指定你所需的特定工作流步骤。对于基本的图摘要和查询，你需要在 settings.yaml 中使用以下配置：

```yaml
workflows: [create_communities, create_community_reports]
```

这将仅运行 GraphRAG [全局搜索](../query/global_search.md) 所需的最小工作流。

## 可选附加配置

如果你想运行 [本地](../query/local_search.md)、[DRIFT](../query/drift_search.md) 或 [基础](../query/overview.md#basic-search) 搜索，则需要包含 text_units 和一些嵌入。

### 文本单元

请参阅完整的 text_units [表结构](./outputs.md#text_units)。文本单元是文档的分块，其大小经过控制，以确保能够适配你的模型的上下文窗口。某些搜索方法会使用它们，因此如果你有这些数据，可能希望将其包含进来。

### 扩展配置

要执行上述其他搜索类型，你需要对部分内容进行嵌入。只需添加 embeddings 工作流：

```yaml
workflows: [create_communities, create_community_reports, generate_text_embeddings]
```

### FastGraphRAG

[FastGraphRAG](./methods.md#fastgraphrag) 在社区报告中使用 text_units，而不是实体和关系描述。如果你的图谱来源方式使其不包含描述，这可能是一个有用的替代方案。在这种情况下，你需要更新 workflows 列表，以包含社区报告工作流的文本变体：

```yaml
workflows: [create_communities, create_community_reports_text, generate_text_embeddings]
```

此方法要求你的 entities 和 relationships 表具有指向 text_unit_ids 列表的有效链接。另请注意，只有当你执行除全局搜索之外的搜索时，才仍然需要 `generate_text_embeddings`。


## 设置

综合起来：

- `output`：创建一个输出文件夹，并将你的 entities 和 relationships（以及可选的 text_units）parquet 文件放入其中。
- 按照上述说明更新你的配置，只运行你所需的那部分工作流。
- 运行 `graphrag index --root <your_project_root>`