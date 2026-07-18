# GraphRAG 索引 🤖

GraphRAG 索引包是一个数据管道和转换套件，旨在使用 LLM 从非结构化文本中提取有意义的结构化数据。

索引管道是可配置的。它们由工作流、标准和自定义步骤、提示模板以及输入/输出适配器组成。我们的标准管道旨在：

- 从原始文本中提取实体、关系和声明
- 在实体中执行社区检测
- 生成多个粒度级别的社区摘要和报告
- 将文本嵌入到向量空间中

默认情况下，管道的输出会存储为 Parquet 表，嵌入会写入你配置的向量存储。

## 入门

### 要求

有关设置开发环境的详细信息，请参阅 [Get Started](../get_started.md) 中的 [requirements](../developing.md#requirements) 部分。

要配置 GraphRAG，请参阅 [configuration](../config/overview.md) 文档。
有了配置文件后，你就可以使用 CLI 或 Python API 运行该管道。

## 用法

### CLI

```bash
uv run poe index --root <data_root> # default config mode
```

### Python API

有关建议的直接从 Python 代码调用的方法，请参阅索引 API [python file](https://github.com/microsoft/graphrag/blob/main/packages/graphrag/graphrag/api/index.py)。

## 进一步阅读

- 要开始在 _GraphRAG_ 项目中进行开发，请参阅 [getting started](../developing.md)
- 要了解索引库的底层概念和执行模型，请参阅 [the architecture documentation](../index/architecture.md)
- 要进一步了解如何配置索引引擎，请参阅 [the configuration documentation](../config/overview.md)