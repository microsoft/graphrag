# 配置 GraphRAG 索引

要开始使用 GraphRAG，您必须生成一个配置文件。`init` 命令是最简单的入门方式。它将在指定目录中创建 `.env` 和 `settings.yaml` 文件，并包含必要的配置设置。它还会输出 GraphRAG 使用的默认 LLM 提示词。

## 用法

```sh
graphrag init [--root PATH] [--force, --no-force]
```

## 选项

- `--root PATH` - 要在其中初始化 graphrag 的项目根目录。默认为当前目录。
- `--force`, `--no-force` - 可选，默认为 --no-force。如果现有配置文件和提示词文件已存在，则覆盖它们。

## 示例

```sh
graphrag init --root ./ragtest
```

## 输出

`init` 命令将在指定目录中创建以下文件：

- `settings.yaml` - 配置设置文件。此文件包含 GraphRAG 的配置设置。
- `.env` - 环境变量文件。这些变量会在 `settings.yaml` 文件中被引用。
- `prompts/` - LLM 提示词文件夹。其中包含 GraphRAG 使用的默认提示词，您可以修改它们，或运行[自动提示词调优](../prompt_tuning/auto_prompt_tuning.md)命令来生成适配您数据的新提示词。

## 后续步骤

初始化工作区后，您可以运行[提示词调优](../prompt_tuning/auto_prompt_tuning.md)命令以使提示词适配您的数据，或者直接开始运行[索引流水线](../index/overview.md)来为您的数据建立索引。有关可用配置选项的更多信息，请参阅[YAML 详细信息页面](yaml.md)。