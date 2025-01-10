# GraphRAG Indexing 🤖

The GraphRAG indexing package is a data pipeline and transformation suite that is designed to extract meaningful, structured data from unstructured text using LLMs.

Indexing Pipelines are configurable. They are composed of workflows, standard and custom steps, prompt templates, and input/output adapters. Our standard pipeline is designed to:

- extract entities, relationships and claims from raw text
- perform community detection in entities
- generate community summaries and reports at multiple levels of granularity
- embed entities into a graph vector space
- embed text chunks into a textual vector space

The outputs of the pipeline are stored as Parquet tables by default, and embeddings are written to your configured vector store.

## Getting Started

### Requirements

See the [requirements](../developing.md#requirements) section in [Get Started](../get_started.md) for details on setting up a development environment.

To configure GraphRAG, see the [configuration](../config/overview.md) documentation.
After you have a config file you can run the pipeline using the CLI or the Python API.

## Usage

### CLI

```bash
# Via Poetry
poetry run poe cli --root <data_root> # default config mode
```

### Python API

Please see the [examples folder](https://github.com/microsoft/graphrag/blob/main/examples/README.md) for a handful of functional pipelines illustrating how to create and run via a custom settings.yml or through custom python scripts.

## Further Reading

- To start developing within the _GraphRAG_ project, see [getting started](../developing.md)
- To understand the underlying concepts and execution model of the indexing library, see [the architecture documentation](../index/architecture.md)
- To get running with a series of examples, see [the examples documentation](https://github.com/microsoft/graphrag/blob/main/examples/README.md)
- To read more about configuring the indexing engine, see [the configuration documentation](../config/overview.md)
