# 开发指南

# 要求

| Name                | Installation                                                 | Purpose                                                                             |
| ------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------- |
| Python 3.10-3.12    | [Download](https://www.python.org/downloads/)                | 该库基于 Python。                                                                   |
| uv                  | [Instructions](https://docs.astral.sh/uv/)                   | uv 用于 Python 代码库中的包管理和虚拟环境管理                                      |

# 入门

## 安装依赖

```sh
# 安装 python 依赖
uv sync --all-packages
```

## 执行索引引擎

```sh
uv run poe index <...args>
```

## 执行查询

```sh
uv run poe query <...args>
```

# Azurite

一些单元测试和冒烟测试使用 Azurite 来模拟 Azure 资源。可以通过运行以下命令启动：

```sh
./scripts/start-azurite.sh
```

或者，如果已全局安装，也可以直接在终端中运行 `azurite`。有关如何安装和使用 Azurite 的更多信息，请参阅 [Azurite documentation](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite)。

# 生命周期脚本

我们的 Python 包使用 uv 管理依赖，并使用 [poethepoet](https://pypi.org/project/poethepoet/) 管理构建脚本。

可用脚本包括：

- `uv run poe index` - 运行索引 CLI
- `uv run poe query` - 运行查询 CLI
- `uv build` - 这将构建 wheel 文件和其他可分发工件。
- `uv run poe test` - 这将执行所有测试。
- `uv run poe test_unit` - 这将执行单元测试。
- `uv run poe test_integration` - 这将执行集成测试。
- `uv run poe test_smoke` - 这将执行冒烟测试。
- `uv run poe test_verbs` - 这将执行基本工作流测试。
- `uv run poe check` - 这将对整个包执行一组静态检查，包括：
  - 格式化
  - 文档格式化
  - lint 检查
  - 安全模式
  - 类型检查
- `uv run poe fix` - 这将对整个包应用所有可用的自动修复。通常这只是格式修复。
- `uv run poe fix_unsafe` - 这将对整个包应用所有可用的自动修复，包括可能不安全的修复。
- `uv run poe format` - 显式对整个包运行格式化工具。

## 故障排除

### 运行 uv install 时出现 “RuntimeError: llvm-config failed executing, please point LLVM_CONFIG to the path for llvm-config”

请确保已安装 llvm-9 和 llvm-9-dev：

`sudo apt-get install llvm-9 llvm-9-dev`

然后在你的 bashrc 中添加

`export LLVM_CONFIG=/usr/bin/llvm-config-9`