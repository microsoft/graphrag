# 索引方法

GraphRAG 是我们关于 RAG 索引方法研究的平台，这些方法旨在为语言模型生成最优的上下文窗口内容。我们有一个标准索引流水线，它使用语言模型来提取作为我们记忆模型基础的图谱。我们可能会不时引入其他索引方法。本页记录了这些选项。

## 标准 GraphRAG

这是原始[博客文章](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/)中描述的方法。标准方法在所有推理任务中都使用语言模型：

- 实体提取：提示 LLM 从每个文本单元中提取命名实体并提供描述。
- 关系提取：提示 LLM 描述每个文本单元中每对实体之间的关系。
- 实体摘要：提示 LLM 将跨文本单元中发现的某个实体每次出现的描述合并为单个摘要。
- 关系摘要：提示 LLM 将跨文本单元中发现的某个关系每次出现的描述合并为单个摘要。
- 声明提取（可选）：提示 LLM 从每个文本单元中提取并描述声明。
- 社区报告生成：收集每个社区的实体和关系描述（以及可选的声明），并用其提示 LLM 生成摘要报告。

`graphrag index --method standard`。这是默认方法，因此可以在命令行中省略 method 参数。

## FastGraphRAG

FastGraphRAG 是一种用传统自然语言处理（NLP）方法替代部分语言模型推理的方法。这是我们开发的一种更快且成本更低的混合索引替代方案：

- 实体提取：实体是使用 NLTK 和 spaCy 等 NLP 库提取的名词短语。没有描述；为此使用源文本单元。
- 关系提取：关系被定义为实体对之间在文本单元中的共现。没有描述。
- 实体摘要：不需要。
- 关系摘要：不需要。
- 声明提取：未使用。
- 社区报告生成：收集包含每个实体名词短语的直接文本单元内容，并用其提示 LLM 生成摘要报告。

`graphrag index --method fast`

FastGraphRAG 内置了一些 NLP [选项](https://microsoft.github.io/graphrag/config/yaml/#extract_graph_nlp)。默认情况下，我们使用 NLTK + 正则表达式进行名词短语提取，这种方式非常快，但主要适用于英语。我们还内置了另外两种使用 spaCy 的方法：语义解析和 CFG。默认情况下，我们为 spaCy 使用 `en_core_web_md` 模型，但请注意，你可以引用任何已安装的[受支持模型](https://spacy.io/models/)。

另请注意，我们通常还会将文本分块配置为生成更小的块（50-100 个 token）。这会产生更好的共现图。

⚠️ 关于 SpaCy 模型的说明：

此包需要 SpaCy 模型才能正常运行。如果所需模型未安装，包会在首次使用时自动下载并安装它。

你也可以通过运行 `python -m spacy download <model_name>` 手动安装，例如 `python -m spacy download en_core_web_md`。


## 选择方法

标准 GraphRAG 提供了对现实世界实体和关系的丰富描述，但比 FastGraphRAG 更昂贵。我们估计图提取约占索引成本的 75%。因此，FastGraphRAG 便宜得多，但代价是提取的图谱在 GraphRAG 之外直接使用时相关性较低，而且图谱往往噪声更大。如果高保真实体和图探索对你的用例很重要，我们建议继续使用传统 GraphRAG。如果你的用例主要面向使用全局搜索的摘要类问题，FastGraphRAG 能以更低的语言模型成本提供高质量摘要。