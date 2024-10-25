# 知识图谱-检索增强生成 GraphRAG

👉 [使用GraphRAG加速策划解决方案](https://github.com/Azure-Samples/graphrag-accelerator) <br/>
👉 [Microsoft研究院发布博客](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/)<br/>
👉 [阅读官方文档](https://microsoft.github.io/graphrag)<br/>
👉 [GraphRAG Arxiv论文](https://arxiv.org/pdf/2404.16130)

<div align="left">
  <a href="https://pypi.org/project/graphrag/">
    <img alt="PyPI - Version" src="https://img.shields.io/pypi/v/graphrag">
  </a>
  <a href="https://pypi.org/project/graphrag/">
    <img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dm/graphrag">
  </a>
  <a href="https://github.com/microsoft/graphrag/issues">
    <img alt="GitHub Issues" src="https://img.shields.io/github/issues/microsoft/graphrag">
  </a>
  <a href="https://github.com/microsoft/graphrag/discussions">
    <img alt="GitHub Discussions" src="https://img.shields.io/github/discussions/microsoft/graphrag">
  </a>
</div>

## [分支新增]本页文件列表（2024.10.16ver）：

本节为像学习中的作者一样的初学者，作一些源文件中内容用途的注解：

- [.github](/.github)：**.github**文件夹包含Issues分区，拉取申请（pull request）分区和工作流分区；
- [.semversioner](/.semversioner)：**.semversioner**文件夹主要包含先前的发行版本文件，以及一个即将发布的包分区；
- [.vscode](/.vscode)：**.vscode**文件夹内含三个使用vscode时的配置文件，extension是推荐的vscode拓展插件清单，launch文件时GraphRAG的调试配置文件，settings包含所需的配置参数；
- [docs](/docs)：**docs**文件夹内含一系列官方的指导文档；详细的注解列表，将会在该文件夹README中给出；
- [examples](/examples)：**examples**正如其名，为一个示例资源；
- [example_notebooks](/examples_notebooks/community_contrib)：**example_notebooks**为社区贡献的开发笔记归档。注意：所有的笔记本将按原样提供，且不保证与最新版本的GraphRAG兼容！
- [graphrag](/graphrag)：**graphrag**为GraphRAG项目的主要源码，如无须作必要开发，不推荐**在没有基础的前提下**对此处代码作修改；
- [scripts](/scripts)：**scripts**包含三个基本运行Bash脚本；包括版本检查（semvercheck），拼写检查（spellcheck）以及一个azurite模拟器启动脚本；
- [tests](/tests)：**tests**为运行测试文件；

## 定义（原Overview）

**GraphRAG** 是一个**文本数据流转换工具**，主要功能为将文本数据**结构化**为**知识图谱**；<br>
工作原理为：使用**大预言模型(LLMs)**，以**非结构化文本**为原始数据，提取**结构化数据**（主要形式为知识图谱）作为输出。<br>
当前使用的LLM：[空]

【原po：】要了解更多关于 GraphRAG 的信息，以及如何使用它来增强LLM对您的私人数据进行推理的能力，请访问 <a href="https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/" target="_blank">Microsoft研究院发布博客.</a><br>
【原声明&警告：】<br>
⚠️ 声明：提供的源码仅用于展示，并非官方支持的 Microsoft 产品/服务。<br>
⚠️ 警告：GraphRAG索引可能是一项开销极大的操作！请在实践前阅读所有文档，以便了解所涉及的过程和成本；并参照实际负载能力，从小规模运行批次开始！

## 试用指南

### [分支新增]实操流程指南阅读顺序（2024.10.25ver）：


### 快速开始

要开始使用 GraphRAG 系统，我们建议您尝试[Solution Accelerator](https://github.com/Azure-Samples/graphrag-accelerator)包，它提供了用户友好型 Azure 资源的端到端体验。

### 拓展内容
- 阅读协作指南以了解一些基本的协作约定： [协作者指南.md](./协作者指南.md)
- 阅读开发文件，以为您的开发作基本指导： [开发指南.md](./开发指南.md)
- 您还可以在此页面加入社区交流，提供反馈： [GitHub Discussions tab!](https://github.com/microsoft/graphrag/discussions)

### 提示工程调整

**GraphRAG**直接使用未经处理的原始数据，可能无法输出理想的结果；我们强烈建议您参照 [Prompt Tuning Guide](https://microsoft.github.io/graphrag/posts/prompt_tuning/overview/) ，针对**提示工程**做出微调。

## 责任性AI（负责任AI，RAI） FAQ

请参照： [RAI_TRANSPARENCY.md](./RAI_TRANSPARENCY.md)

- [GraphRAG是什么？](./RAI_TRANSPARENCY.md#what-is-graphrag)
- [GraphRAG做什么？](./RAI_TRANSPARENCY.md#what-can-graphrag-do)
- [GraphRAG的用途？](./RAI_TRANSPARENCY.md#what-are-graphrags-intended-uses)
- [GraphRAG如何评估？性能用什么指标来衡量？](./RAI_TRANSPARENCY.md#how-was-graphrag-evaluated-what-metrics-are-used-to-measure-performance)
- [GraphRAG的受限性？如何最小化GraphRAG受限性的影响？](./RAI_TRANSPARENCY.md#what-are-the-limitations-of-graphrag-how-can-users-minimize-the-impact-of-graphrags-limitations-when-using-the-system)
- [为了有效并负责任地使用GraphRAG，应当采用什么样的操作参数和设置？](./RAI_TRANSPARENCY.md#what-operational-factors-and-settings-allow-for-effective-and-responsible-use-of-graphrag)

## 商业标识

本项目可能包含项目、产品或服务的商标或徽标。Microsoft商标或标志的授权使用，必须服从且遵循
[Microsoft's Trademark & Brand Guidelines Microsoft商标&品牌指南](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
在本项目的衍生版本中使用**Microsoft**商标、徽标等，不得引起混淆、或暗示**Microsoft**赞助。
对第三方商标或徽标的任何使用，均受这些第三方政策的约束。

## 隐私申明

[Microsoft隐私申明](https://privacy.microsoft.com/en-us/privacystatement)
