---
title: GraphRAG Indexing 🤖
navtitle: Indexing Overview
layout: page
tags: [post]
---

The GraphRAG indexing package is a data pipeline and transformation suite that is designed to extract meaningful, structured data from unstructured text using LLMs.

Indexing Pipelines are configurable. They are composed of workflows, standard and custom steps, prompt templates, and input/output adapters. Our standard pipeline is designed to:

- extract entities, relationships and claims from raw text
- perform community detection in entities
- generate community summaries and reports at multiple levels of granularity
- embed entities into a graph vector space
- embed text chunks into a textual vector space

The outputs of the pipeline can be stored in a variety of formats, including JSON and Parquet - or they can be handled manually via the Python API.

## Getting Started

### Requirements

See the [requirements](/posts/developing#requirements) section in [Get Started](/posts/get_started) for details on setting up a development environment.

The Indexing Engine can be used in either a default configuration mode or with a custom pipeline.
To configure GraphRAG, see the [configuration](/posts/config/overview) documentation.
After you have a config file you can run the pipeline using the CLI or the Python API.

## Usage

### CLI

```bash
# Via Poetry
poetry run poe cli --root <data_root> # default config mode
poetry run poe cli --config your_pipeline.yml # custom config mode

# Via Node
yarn run:index --root <data_root> # default config mode
yarn run:index --config your_pipeline.yml # custom config mode

```

### Python API

```python
from graphrag.index import run_pipeline
from graphrag.index.config import PipelineWorkflowReference

workflows: list[PipelineWorkflowReference] = [
    PipelineWorkflowReference(
        steps=[
            {
                # built-in verb
                "verb": "derive",  # https://github.com/microsoft/datashaper/blob/main/python/datashaper/datashaper/verbs/derive.py
                "args": {
                    "column1": "col1",  # from above
                    "column2": "col2",  # from above
                    "to": "col_multiplied",  # new column name
                    "operator": "*",  # multiply the two columns
                },
                # Since we're trying to act on the default input, we don't need explicitly to specify an input
            }
        ]
    ),
]

dataset = pd.DataFrame([{"col1": 2, "col2": 4}, {"col1": 5, "col2": 10}])
outputs = []
async for output in await run_pipeline(dataset=dataset, workflows=workflows):
    outputs.append(output)
pipeline_result = outputs[-1]
print(pipeline_result)
```

## Further Reading

- To start developing within the _GraphRAG_ project, see [getting started](/posts/developing/)
- To understand the underlying concepts and execution model of the indexing library, see [the architecture documentation](/posts/index/0-architecture/)
- To get running with a series of examples, see [the examples documentation](https://github.com/microsoft/graphrag/blob/main/examples/README.md)
- To read more about configuring the indexing engine, see [the configuration documentation](/posts/config/overview)
