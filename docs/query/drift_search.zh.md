# DRIFT 搜索 🔎

## 结合本地搜索与全局搜索

GraphRAG 是一种利用大型语言模型（LLM）从非结构化文本文档中创建知识图谱和摘要的技术，并利用它们来改进私有数据集上的检索增强生成（RAG）操作。它既能为大型私有非结构化文本文档集合提供全面的全局概览，也支持对细粒度、本地化信息的探索。通过使用 LLM 创建全面的知识图谱来连接并描述这些文档中包含的实体与关系，GraphRAG 利用数据的语义结构化能力，为各种复杂的用户查询生成响应。

DRIFT 搜索（Dynamic Reasoning and Inference with Flexible Traversal）建立在 Microsoft 的 GraphRAG 技术之上，结合了全局搜索和本地搜索的特性，使用我们的 [drift search](https://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/query/structured_search/drift_search/) 方法，以一种在计算成本与结果质量之间取得平衡的方式生成详细响应。

## 方法论

<p align="center">
<img src="../../../img/drift-search-diagram.png" alt="图 1. 完整的 DRIFT 搜索层次结构，突出显示了 DRIFT 搜索流程的三个核心阶段。" align="center" />
</p>
<p align="center"><i><small>
图 1. 完整的 DRIFT 搜索层次结构，突出显示了 DRIFT 搜索流程的三个核心阶段。A（Primer）：DRIFT 将用户查询与语义上最相关的前 K 个社区报告进行比较，生成一个宽泛的初始答案和后续问题，以引导进一步探索。B（Follow-Up）：DRIFT 使用本地搜索来优化查询，生成额外的中间答案和后续问题，以增强特异性，引导引擎走向上下文更丰富的信息。图中每个节点上的字形表示算法对继续执行查询扩展步骤的置信度。C（Output Hierarchy）：最终输出是一个按相关性排序的问题与答案层次结构，体现了全局洞察与本地细化之间的平衡组合，使结果既灵活又全面。</small></i></p>


DRIFT 搜索通过在搜索过程中纳入社区信息，为本地搜索查询引入了一种新方法。这极大地扩展了查询起点的广度，并使最终答案能够检索和使用更丰富多样的事实。这一新增能力通过为本地搜索提供更全面的选项扩展了 GraphRAG 查询引擎，该选项利用社区洞察将查询细化为详细的后续问题。

## 配置

以下是 [DRIFTSearch class](https://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/query/structured_search/drift_search/search.py) 的关键参数：

* `model`：用于生成响应的语言模型聊天补全对象
- `context_builder`：用于根据社区报告和查询信息准备上下文数据的 [context builder](https://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/query/structured_search/drift_search/drift_context.py) 对象
- `config`：用于定义 DRIFT 搜索超参数的模型。[DRIFT Config model](https://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/config/models/drift_search_config.py)
- `tokenizer`：用于跟踪算法预算的 token 编码器。
- `query_state`：在 [Query State](https://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/query/structured_search/drift_search/state.py) 中定义的状态对象，可用于跟踪 DRIFT 搜索实例的执行情况，以及后续问题和 [DRIFT actions](https://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/query/structured_search/drift_search/action.py)。

## 如何使用

可在以下 [notebook](../examples_notebooks/drift_search.ipynb) 中找到一个 drift search 场景示例。

## 了解更多

若想更深入了解 DRIFT 搜索方法，请参阅我们的 [DRIFT Search blog post](https://www.microsoft.com/en-us/research/blog/introducing-drift-search-combining-global-and-local-search-methods-to-improve-quality-and-efficiency/)