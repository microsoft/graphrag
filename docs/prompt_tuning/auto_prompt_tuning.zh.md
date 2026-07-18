# 自动提示词调优 ⚙️

GraphRAG 提供了为知识图谱生成创建领域自适应提示词的能力。此步骤是可选的，但强烈建议执行，因为它会在执行 Index Run 时产生更好的结果。

这些提示词通过加载输入、将其拆分为块（文本单元），然后运行一系列 LLM 调用和模板替换来生成最终提示词。我们建议使用脚本提供的默认值，但本页将提供每个参数的详细信息，以便你在需要时进一步探索和调整提示词调优算法。

<p align="center">
<img src="../../../img/auto-tune-diagram.png" alt="Figure 1: Auto Tuning Conceptual Diagram." width="850" align="center" />
</p>
<p align="center">
图 1：自动调优概念图。
</p>

## 前提条件

在运行自动调优之前，请确保你已经使用 `graphrag init` 命令初始化了工作区。这将创建必要的配置文件和默认提示词。有关初始化过程的更多信息，请参阅 [初始化文档](../config/init.md)。

## 用法

你可以通过命令行使用各种选项运行主脚本：

```bash
graphrag prompt-tune [--root ROOT] [--domain DOMAIN]  [--selection-method METHOD] [--limit LIMIT] [--language LANGUAGE] \
[--max-tokens MAX_TOKENS] [--chunk-size CHUNK_SIZE] [--n-subset-max N_SUBSET_MAX] [--k K] \
[--min-examples-required MIN_EXAMPLES_REQUIRED] [--discover-entity-types] [--output OUTPUT]
```

## 命令行选项

- `--root`（可选）：包含配置文件（settings.yaml）的项目目录路径。默认为当前目录。

- `--domain`（可选）：与你的输入数据相关的领域，例如“space science”、“microbiology”或“environmental news”。如果留空，将根据输入数据推断该领域。

- `--selection-method`（可选）：选择文档的方法。可选项包括 all、random、auto 或 top。默认为 random。

- `--limit`（可选）：在使用 random 或 top 选择时加载的文本单元数量上限。默认值为 15。

- `--language`（可选）：用于输入处理的语言。如果它与输入的语言不同，LLM 将进行翻译。默认值为 `""`，表示将从输入中自动检测。

- `--max-tokens`（可选）：用于提示词生成的最大 token 数。默认值为 2000。

- `--chunk-size`（可选）：从输入文档生成文本单元时使用的 token 大小。默认值为 200。

- `--n-subset-max`（可选）：在使用 auto 选择方法时要嵌入的文本块数量。默认值为 300。

- `--k`（可选）：在使用 auto 选择方法时要选择的文档数量。默认值为 15。

- `--min-examples-required`（可选）：实体提取提示词所需的最小示例数量。默认值为 2。

- `--discover-entity-types`（可选）：允许 LLM 自动发现并提取实体。我们建议在你的数据覆盖大量主题或具有很强随机性时使用此选项。

- `--output`（可选）：用于保存生成的提示词的文件夹。默认值为 "prompts"。

## 使用示例

```bash
python -m graphrag prompt-tune --root /path/to/project --domain "environmental news" \
--selection-method random --limit 10 --language English --max-tokens 2048 --chunk-size 256 --min-examples-required 3 \
--no-discover-entity-types --output /path/to/output
```

或者，使用最少配置（推荐）：

```bash
python -m graphrag prompt-tune --root /path/to/project --no-discover-entity-types
```

## 文档选择方法

自动调优功能会摄取输入数据，然后将其划分为大小等于 chunk size 参数的文本单元。
之后，它会使用以下选择方法之一挑选一个样本用于提示词生成：

- `random`：随机选择文本单元。这是默认且推荐的选项。
- `top`：选择前 _n_ 个文本单元。
- `all`：使用所有文本单元进行生成。仅适用于小型数据集；通常不推荐此选项。
- `auto`：将文本单元嵌入到低维空间中，并选择距离质心最近的 _k_ 个近邻。当你拥有大型数据集并希望选择具有代表性的样本时，这很有用。

## 修改配置

运行自动调优后，你应修改以下配置变量，以便在索引运行中使用新的提示词。注意：请确保将路径更新为生成的提示词的正确路径，在本示例中我们使用默认的 "prompts" 路径。

```yaml
extract_graph:
  prompt: "prompts/extract_graph.txt"

summarize_descriptions:
  prompt: "prompts/summarize_descriptions.txt"

community_reports:
  prompt: "prompts/community_report.txt"
```