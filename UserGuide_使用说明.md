# 总过程使用指导

在您开始实操之前，强烈建议先按顺序食用`流程说明指南`文件，以便您清楚该程序每一步操作的目的是什么！

## 环境配置管理
```shell
# 最新使用`poetry`来管理前置环境；
# 更新python：

```

## 运行示例
### 原文档：
[README](/examples/README_CN汉化.md)

### 范例运行操作：
例如，要运行single_verb示例，您将运行以下命令：

```bash
cd python/graphrag
poetry shell
PYTHONPATH="$(pwd)" python examples/single_verb/run.py
```

## Try测试准备
- win shell系统傻瓜式脚本：<br>
见脚本文件夹[scripts](./scripts)：`try.bat`

### 创建Try测试目录：
```shell
# Try目录的官方等效目录为`./tests`；
# 该`./tests`目录下配置文件齐全，新建Try目录仅供简化学习使用：
mkdir -p ./try/data
mkdir -p ./try/input

# 导入测试数据文件：
# 文件中`data0.txt`，如需其他文件、路径或实现方式，更改此处指令：
cp try/data/data0.txt ./try/input/
```

### 流程步骤-1：构建索引
``` shell
# 项目初始化
# 此指令指向路径`./graphrag/index/`下的`_ini_.py`文件：
# 指令中`--root ./xxx`指定运行根目录为`./xxx`，此处以`./try`为例：
python -m graphrag.index --init --root ./try
# 运行后将会生成output文件夹，prompt文件夹，一个`.env`文件，一个`settings.yml`文件。

# 配置
# 配置原始汉化模板，见目录`./examples/custom_input/`下`pipeline_CN`文件：
# 此处用模板改为`settings.yml`作配置文件使用：
cp examples/custom_input/pipeline_CN.yml ./try
mv try/pipeline_CN.yml try/settings.yml
# 编辑settings文件，修改您所需要的配置参数、API等:

# 启动构建
# 启动命令中的`--resume`参数用于保证rate limit导致的中断，能在下次运行时继续
# `--resume`参数会根据运行批次名称，来确定继续哪个批次。
# 创建运行批次输出目录，`./output/`路径下取名即可；
# 此处为此运行批次取名为`try0`，输出将在`/try0`目录下
mkdir -p ./try/output/try0
python -m graphrag.index --root ./try --resume try0
```

### 流程步骤-2：用户查询
```shell
# `--method`参数用于指定方法是`local`还是`global`；
# `--data`参数用于指定读取哪个运行批次的索引，否则按第一个处理；
# 在`put your query text here`处填入查询内容，以双引号封装：
python -m graphrag.query --root ./try --data ./try/output/try0/artifacts --method local "put your query text here"
```

### 参考文档