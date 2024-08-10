# GraphRAG customized by KylinMountain
- I have added websever to support streaming output immediately.
- I have fixed error when using local embedding service like LM Studio
- I have fixed index error after prompt tune
- I have fixed the strategy not loaded when setting entity extraction using NLTK.
- I have added advice question api
- I have added reference link to the entity、report or relationship refered in output, you can access it.
- Support any desktop application or web application compatible with OpenAI SDK.

# GraphRAG 定制版
- 我添加了Web服务器，以支持真即时流式输出。
- 我修复了使用本地嵌入服务（如LM Studio）时的错误。
- 我修复了提示调整后索引错误的问题。
- 我修复了在使用NLTK设置实体提取时策略未加载的问题。
- 我添加了建议问题API。
- 我添加了实体或者关系等链接到输出中，你可以直接点击访问参考实体、关系、数据源或者报告。
- 支持任意兼容OpenAI大模型桌面应用或者Web应用UI接入。

![image](https://github.com/user-attachments/assets/c251d434-4925-4012-88e7-f3b2ff40471f)


![image](https://github.com/user-attachments/assets/ab7a8d2e-aeec-4a0c-afb9-97086b9c7b2a)

# 如何安装How to install
- 克隆本项目 Clone the repo
```
git clone https://github.com/KylinMountain/graphrag.git
cd graphrag
```
- 建立虚拟环境 Create virtual env
```
conda create -n graphrag python=3.10
conda activate graphrag
```
- 安装poetry Install poetry
```
curl -sSL https://install.python-poetry.org | python3 -
```
- 安装依赖 Install dependencies
```
poetry install
pip install -r webserver/requirements.txt
```
- 初始化GraphRAG Initialize GraphRAG
```
poetry run poe index --init --root .
```
- 创建input文件夹 Create Input Foler
- 配置settings.yaml Config settings.yaml
按照GraphRAG官方配置文档配置 [GraphRAG Configuration](https://microsoft.github.io/graphrag/posts/config/json_yaml/)
- 配置webserver Config webserver

你可能需要配置以下设置，但默认即可支持本地运行。 You may need config the following item, but you can use the default param.
```yaml
    server_host: str = "http://localhost"
    server_port: int = 20213
    data: str = (
        "./output"
    )
    lancedb_uri: str = (
        "./lancedb"
    )
```
- 启动web serevr
```bash
python webserver/main.py
```
更多的参考配置，可以访问[公众号文章](https://mp.weixin.qq.com/mp/appmsgalbum?__biz=MzI0OTAzNTEwMw==&action=getalbum&album_id=3429606151455670272&uin=&key=&devicetype=iMac+MacBookPro17%2C1+OSX+OSX+14.4+build(23E214)&version=13080710&lang=zh_CN&nettype=WIFI&ascene=0&fontScale=100)和[B站视频](https://www.bilibili.com/video/BV113v8e6EZn)

# GraphRAG

👉 [Use the GraphRAG Accelerator solution](https://github.com/Azure-Samples/graphrag-accelerator) <br/>
👉 [Microsoft Research Blog Post](https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/)<br/>
👉 [Read the docs](https://microsoft.github.io/graphrag)<br/>
👉 [GraphRAG Arxiv](https://arxiv.org/pdf/2404.16130)

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

## Overview

The GraphRAG project is a data pipeline and transformation suite that is designed to extract meaningful, structured data from unstructured text using the power of LLMs.

To learn more about GraphRAG and how it can be used to enhance your LLM's ability to reason about your private data, please visit the <a href="https://www.microsoft.com/en-us/research/blog/graphrag-unlocking-llm-discovery-on-narrative-private-data/" target="_blank">Microsoft Research Blog Post.</a>

## Quickstart

To get started with the GraphRAG system we recommend trying the [Solution Accelerator](https://github.com/Azure-Samples/graphrag-accelerator) package. This provides a user-friendly end-to-end experience with Azure resources.

## Repository Guidance

This repository presents a methodology for using knowledge graph memory structures to enhance LLM outputs. Please note that the provided code serves as a demonstration and is not an officially supported Microsoft offering.

⚠️ *Warning: GraphRAG indexing can be an expensive operation, please read all of the documentation to understand the process and costs involved, and start small.*

## Diving Deeper

- To learn about our contribution guidelines, see [CONTRIBUTING.md](./CONTRIBUTING.md)
- To start developing _GraphRAG_, see [DEVELOPING.md](./DEVELOPING.md)
- Join the conversation and provide feedback in the [GitHub Discussions tab!](https://github.com/microsoft/graphrag/discussions)

## Prompt Tuning

Using _GraphRAG_ with your data out of the box may not yield the best possible results.
We strongly recommend to fine-tune your prompts following the [Prompt Tuning Guide](https://microsoft.github.io/graphrag/posts/prompt_tuning/overview/) in our documentation.

## Responsible AI FAQ

See [RAI_TRANSPARENCY.md](./RAI_TRANSPARENCY.md)

- [What is GraphRAG?](./RAI_TRANSPARENCY.md#what-is-graphrag)
- [What can GraphRAG do?](./RAI_TRANSPARENCY.md#what-can-graphrag-do)
- [What are GraphRAG’s intended use(s)?](./RAI_TRANSPARENCY.md#what-are-graphrags-intended-uses)
- [How was GraphRAG evaluated? What metrics are used to measure performance?](./RAI_TRANSPARENCY.md#how-was-graphrag-evaluated-what-metrics-are-used-to-measure-performance)
- [What are the limitations of GraphRAG? How can users minimize the impact of GraphRAG’s limitations when using the system?](./RAI_TRANSPARENCY.md#what-are-the-limitations-of-graphrag-how-can-users-minimize-the-impact-of-graphrags-limitations-when-using-the-system)
- [What operational factors and settings allow for effective and responsible use of GraphRAG?](./RAI_TRANSPARENCY.md#what-operational-factors-and-settings-allow-for-effective-and-responsible-use-of-graphrag)

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.

## Privacy

[Microsoft Privacy Statement](https://privacy.microsoft.com/en-us/privacystatement)
