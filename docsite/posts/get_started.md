---
title: Get Started
navtitle: Get started
layout: page
tags: [post]
---

## Requirements

[Python 3.10 or 3.11](https://www.python.org/downloads/)

To get started with the GraphRAG system, you have a few options:

👉 [Install from pypi](https://pypi.org/project/graphrag/). <br/>
👉 [Use it from source](../developing)<br/>

# Top-Level Packages

[Indexing Pipeline Overview](../index/overview)<br/>
[Query Engine Overview](../query/overview)

# Overview

The following is a simple end-to-end example for using the GraphRAG system.
It shows how to use the system to index some text, and then use the indexed data to answer questions about the documents.

# Install GraphRAG

```bash
pip install graphrag
```

# Running the Indexer

Now we need to set up a data project and some initial configuration. Let's set that up. We're using the [default configuration mode](/_posts/_config/overview/), which you can customize as needed using [environment variables](/_posts/_config/env_vars/) or using a [config file](/_posts/_config/json_yaml/).

First let's get a sample dataset ready:

```sh
mkdir -p ./ragtest/input
```

Now let's get a copy of A Christmas Carol by Charles Dickens from a trusted source

```sh
curl https://www.gutenberg.org/cache/epub/24022/pg24022.txt > ./ragtest/input/book.txt
```

Next we'll inject some required config variables:

## Set Up Environment Variables

First let's make sure to setup the required environment variables:

- `GRAPHRAG_API_KEY` - API Key for executing the model, will fallback to `OPENAI_API_KEY` if one is not provided.
- `GRAPHRAG_LLM_MODEL` - Model to use for Chat Completions.
- `GRAPHRAG_EMBEDDING_MODEL` - Model to use for Embeddings.
- `GRAPHRAG_INPUT_TYPE` - Type of input data, can be `text` or `csv`.
- `GRAPHRAG_API_BASE` - Base URL for the Azure OpenAI. Only required for Azure OpenAI users.
- `GRAPHRAG_LLM_DEPLOYMENT_NAME` - Deployment name for the Chat Completions model. Only required for Azure OpenAI users.
- `GRAPHRAG_EMBEDDING_DEPLOYMENT_NAME` - Deployment name for the Embeddings model. Only required for Azure OpenAI users.

#### <ins>OpenAI</ins>

```sh
export GRAPHRAG_API_KEY=<api_key> && \
export GRAPHRAG_LLM_MODEL=<chat_completions_model> && \
export GRAPHRAG_EMBEDDING_MODEL=<embeddings_model> && \
export GRAPHRAG_INPUT_TYPE="text"
```

#### <ins>Azure OpenAI</ins>

```sh
export GRAPHRAG_API_KEY=<api_key> && \
export GRAPHRAG_LLM_DEPLOYMENT_NAME=<chat_completions_model> && \
export GRAPHRAG_EMBEDDING_DEPLOYMENT_NAME=<embeddings_model> && \
export GRAPHRAG_INPUT_TYPE="text" && \
export GRAPHRAG_API_BASE="http://<domain>.openai.azure.com"
```

For more details about Environment Variables configuration please refer to [Environment Configuration](./_config/overview/) to the Query Engine [CLI documentation](../query/3-cli).

## Running the Indexing pipeline

Finally we'll run the pipeline!

```sh
python -m graphrag.index --root ./ragtest
```

![pipeline executing from the CLI](/img/pipeline-running.png)

This process will take some time to run. This depends on the size of your input data, what model you're using, and the text chunk size being used (these can be configured in your `.env` file).
Once the pipeline is complete, you should see a new folder called `./ragtest/output/<timestamp>/artifacts` with a series of parquet files.

# Using the Query Engine

## Running the Query Engine

Now let's ask some questions using this dataset.

Here is an example using Global search to ask a high-level question:

```sh
python -m graphrag.query \
--data ./ragtest/output/<timestamp>/artifacts \
--method global\
"What are the top themes in this story?"
```

Here is an example using Local search to ask a more specific question about a particular character:

```sh
python -m graphrag.query \
--data ./ragtest/output/<timestamp>/artifacts \
--method local \
"Who is Scrooge, and what are his main relationships?"
```

Please refer to [Query Engine](../query/overview) docs for detailed information about how to leverage our Local and Global search mechanisms for extracting meaningful insights from data after the Indexer has wrapped up execution.
