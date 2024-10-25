# 索引引擎示例
此目录包含几个如何使用索引引擎的示例。

大多数示例包括两种不同形式的运行管道，两者都包含在示例`run.py`
1. 主要使用Python API
2. 主要使用流水线配置文件

# 运行示例
首先运行 `poetry shell` 以激活具有所需依赖项的虚拟环境。

然后从 `python/graphrag` 目录运行 `PYTHONPATH=“$（pwd）”python examples/path_to_example/run.py `。

例如，要运行single_verb示例，您将运行以下命令：

```bash
cd python/graphrag
poetry shell
PYTHONPATH="$(pwd)" python examples/single_verb/run.py
```