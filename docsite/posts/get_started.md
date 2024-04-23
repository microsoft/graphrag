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
👉 [Use it from source](/posts/developing)<br/>

# Top-Level Packages

[Indexing Pipeline Overview](/posts/index/overview)<br/>
[Query Engine Overview](/posts/query/overview)

# Overview

The following is a simple end-to-end example for using the GraphRAG system.
It shows how to use the system to index some text, and then use the indexed data to answer questions about the documents.

# Install GraphRAG

```bash
pip install graphrag
```

# Running the Indexer

Now we need to set up a data project and some initial configuration. Let's set that up. We're using the [default configuration mode](/posts/config/overview/), which you can customize as needed using [environment variables](/posts/config/env_vars/) or using a [config file](/posts/config/json_yaml/).

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

First let's make sure to setup the required environment variables. For details on these environment variables, and what environment variables are available, see the [environment variables documentation](/posts/config/env_vars/).


#### <ins>OpenAI and Azure OpenAI</ins>
Let's set the base environment variables.

```sh
export GRAPHRAG_API_KEY="<api_key>" && \
export GRAPHRAG_LLM_MODEL="<chat_completions_model>" && \
export GRAPHRAG_LLM_MODEL_SUPPORTS_JSON="True" && \
export GRAPHRAG_EMBEDDING_MODEL="<embeddings_model>" && \
export GRAPHRAG_INPUT_TYPE="text"
```

#### <ins>Azure OpenAI</ins>

In addition, Azure OpenAI users should set the following env-vars.

```sh
export GRAPHRAG_API_BASE="https://<domain>.openai.azure.com" && \
export GRAPHRAG_API_VERSION="2024-02-15-preview" && \
export GRAPHRAG_LLM_API_TYPE = "azure_openai_chat" && \
export GRAPHRAG_LLM_DEPLOYMENT_NAME="<chat_completions_deployment_name>" && \
export GRAPHRAG_EMBEDDING_API_TYPE = "azure_openai_embedding" && \
export GRAPHRAG_EMBEDDING_DEPLOYMENT_NAME="<embeddings_deployment_name>"
```

For more details about configuring GraphRAG, see the [configuration documentation](/posts/config/overview/).
For more details about using the CLI, refer to the [CLI documentation](/posts/query/3-cli/).

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
--root ./ragtest \
--method global \
"What are the top themes in this story?"
```

Here is an example using Local search to ask a more specific question about a particular character:

```sh
python -m graphrag.query \
--root ./ragtest \
--method local \
"Who is Scrooge, and what are his main relationships?"
```

Please refer to [Query Engine](/posts/query/overview) docs for detailed information about how to leverage our Local and Global search mechanisms for extracting meaningful insights from data after the Indexer has wrapped up execution.
