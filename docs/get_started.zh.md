# 快速开始

⚠️ GraphRAG 可能会消耗大量 LLM 资源！我们强烈建议在理解系统工作方式之前，先从这里的教程数据集开始，并考虑先使用快速/低成本模型进行实验，再决定是否投入大型索引任务。

## 要求

[Python 3.10-3.12](https://www.python.org/downloads/)

以下是在从 [pypi](https://pypi.org/project/graphrag/) 安装后，在命令行中使用 GraphRAG 的一个简单端到端示例。

它展示了如何使用该系统为一些文本建立索引，然后使用索引后的数据来回答有关文档的问题。

## 安装 GraphRAG

要开始使用，请创建一个项目空间和 python 虚拟环境来安装 `graphrag`。

### 创建项目空间

```bash
mkdir graphrag_quickstart
cd graphrag_quickstart
python -m venv .venv
```

### 激活 Python 虚拟环境 - Unix/MacOS

```bash
source .venv/bin/activate
```

### 激活 Python 虚拟环境 - Windows

```bash
.venv\Scripts\activate
```

### 安装 GraphRAG

```bash
python -m pip install graphrag
```

### 初始化 GraphRAG

要初始化工作区，首先运行 `graphrag init` 命令。

```sh
graphrag init
```

出现提示时，请在配置中指定你希望使用的默认聊天模型和嵌入模型。

这将在当前目录中创建两个文件 `.env` 和 `settings.yaml`，以及一个目录 `input`。

- `input` 使用 `graphrag` 处理的文本文件位置。
- `.env` 包含运行 GraphRAG 流水线所需的环境变量。如果你查看该文件，会看到定义了一个环境变量，
  `GRAPHRAG_API_KEY=<API_KEY>`。请将 `<API_KEY>` 替换为你自己的 OpenAI 或 Azure API 密钥。
- `settings.yaml` 包含流水线的设置。你可以修改此文件以更改流水线的设置。

### 下载示例文本

从可信来源获取 Charles Dickens 的《A Christmas Carol》副本：

```sh
curl https://www.gutenberg.org/cache/epub/24022/pg24022.txt -o ./input/book.txt
```

## 设置工作区变量

### 使用 OpenAI

如果以 OpenAI 模式运行，你只需要将 `.env` 文件中的 `GRAPHRAG_API_KEY` 值更新为你的 OpenAI API 密钥。

### 使用 Azure OpenAI

除了设置 API 密钥之外，Azure OpenAI 用户还应在 settings.yaml 文件中设置以下变量。要找到相应部分，只需搜索 `models:` 根配置；你应该会看到两个部分，一个用于默认聊天端点，另一个用于默认嵌入端点。以下是添加到聊天模型配置中的示例：

```yaml
type: chat
model_provider: azure
model: gpt-4.1
azure_deployment_name: <AZURE_DEPLOYMENT_NAME>
api_base: https://<instance>.openai.azure.com
api_version: 2024-02-15-preview # 你可以为其他版本自定义此项
```

#### 在 Azure 上使用托管身份验证

要使用托管身份验证，请编辑模型配置中的 auth_method 并删除 api_key 行：

```yaml
auth_method: azure_managed_identity # 默认 auth_method 是 is api_key
```

你还需要使用 [az login](https://learn.microsoft.com/en-us/cli/azure/authenticate-azure-cli) 登录，并选择与你的端点对应的订阅。

## 建立索引

现在我们已经准备好建立索引了！

```sh
graphrag index
```

![从 CLI 执行的流水线](img/pipeline-running.png)

此过程通常需要几分钟才能运行完成。流水线完成后，你应该会看到一个名为 `./output` 的新文件夹，其中包含一系列 parquet 文件。

# 查询

现在让我们使用这个数据集来提一些问题。

下面是一个使用全局搜索提出高层次问题的示例：

```sh
graphrag query "What are the top themes in this story?"
```

下面是一个使用本地搜索针对特定角色提出更具体问题的示例：

```sh
graphrag query \
"Who is Scrooge and what are his main relationships?" \
--method local
```

有关在索引器执行完成后，如何利用我们的本地搜索和全局搜索机制从数据中提取有意义见解的详细信息，请参阅 [Query Engine](query/overview.md) 文档。

# 深入了解

- 有关配置 GraphRAG 的更多详细信息，请参阅[配置文档](config/overview.md)。
- 要了解有关初始化的更多信息，请参阅[初始化文档](config/init.md)。
- 有关使用 CLI 的更多详细信息，请参阅 [CLI 文档](cli.md)。
- 请查看我们的[可视化指南](visualization_guide.md)，以获得更具交互性的调试和探索知识图谱体验。